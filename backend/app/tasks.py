from .extensions import celery, db
from .models import Resume, Job, StatusEnum
from .utils.parsers import extract_text_from_file
# Import the ENHANCED scoring function from nlp utils
from .utils.nlp import calculate_enhanced_relevance
import logging
import time # For simulating work or adding delays

logger = logging.getLogger(__name__)


# Define Celery task with name, retries, etc.
# `bind=True` allows access to task instance via `self`
@celery.task(bind=True, name='app.tasks.process_resume', max_retries=3, default_retry_delay=60,
             acks_late=True, task_reject_on_worker_lost=True) # Settings for reliability
def process_resume(self, resume_id, job_id):
    """Celery task to process a single resume: parse, analyze, score."""
    task_id = self.request.id
    logger.info(f"[Task ID: {task_id}] Starting processing for Resume ID: {resume_id}, Job ID: {job_id}")

    # Fetch objects within the task using the app context provided by ContextTask
    # Ensure objects exist
    resume = Resume.query.get(resume_id)
    if not resume:
        logger.error(f"[Task ID: {task_id}] Resume ID {resume_id} not found. Aborting task.")
        return {'status': 'FAILED', 'error': 'Resume not found'}

    job = Job.query.get(job_id)
    if not job:
        logger.error(f"[Task ID: {task_id}] Job ID {job_id} not found for Resume ID {resume_id}. Aborting task.")
        # Update resume status to FAILED if job is missing
        try:
            resume.status = StatusEnum.FAILED
            resume.score = None # Clear score
            resume.error_message = "Associated Job not found"[:499] # Store error if model has field
            db.session.commit()
        except Exception as db_err:
             logger.error(f"[Task ID: {task_id}] DB error updating resume status for missing job: {db_err}", exc_info=True)
             db.session.rollback() # Rollback on error
        return {'status': 'FAILED', 'error': 'Job not found'}

    # --- Start Processing ---
    try:
        # 1. Update Status to PROCESSING
        resume.status = StatusEnum.PROCESSING
        resume.score = None # Clear previous score/errors if reprocessing
        # resume.error_message = None # Clear previous errors
        db.session.commit()
        logger.info(f"[Task ID: {task_id}] Resume ID {resume_id}: Status set to PROCESSING.")

        # 2. Extract Text from the resume file
        # Construct full path - UPLOAD_FOLDER needs to be accessible by worker
        # This assumes worker runs from 'backend' dir or UPLOAD_FOLDER is absolute/resolvable
        # If using cloud storage, use SDK here (e.g., boto3)
        try:
            # Assuming resume.filepath is relative to UPLOAD_FOLDER set in config
            full_file_path = os.path.join(celery.conf.get('UPLOAD_FOLDER', 'uploads/resumes'), resume.filepath)
            if not os.path.exists(full_file_path):
                 # Try absolute path if relative didn't work (less ideal)
                 full_file_path = resume.filepath
                 if not os.path.exists(full_file_path):
                     raise FileNotFoundError(f"Resume file not found at expected paths based on: {resume.filepath}")

            logger.info(f"[Task ID: {task_id}] Resume ID {resume_id}: Attempting to parse file at {full_file_path}")
            resume_text = extract_text_from_file(full_file_path)
        except FileNotFoundError as fnf_err:
             logger.error(f"[Task ID: {task_id}] Resume ID {resume_id}: {fnf_err}")
             raise # Re-raise to trigger main exception handling
        except Exception as parse_err:
            logger.error(f"[Task ID: {task_id}] Resume ID {resume_id}: Error during text extraction: {parse_err}", exc_info=True)
            raise ValueError(f"Failed to extract text from resume file: {parse_err}") from parse_err


        if not resume_text:
            logger.error(f"[Task ID: {task_id}] Resume ID {resume_id}: Failed to extract text (empty result) from file {resume.filepath}.")
            raise ValueError("Failed to extract text from resume file (empty result).")

        logger.info(f"[Task ID: {task_id}] Resume ID {resume_id}: Text extracted successfully (length: {len(resume_text)}).")

        # 3. Calculate ENHANCED Relevance Score using NLP utils
        #    Need to get required experience from the job model (if implemented)
        #    Using 0 as default if not available on job model
        required_years = getattr(job, 'required_experience', 0) # Safely get attribute or default
        if required_years is None: required_years = 0 # Handle case where field exists but is NULL

        logger.info(f"[Task ID: {task_id}] Resume ID {resume_id}: Calculating enhanced relevance against Job ID {job_id} (Req Exp: {required_years})...")
        score_data = calculate_enhanced_relevance(resume_text, job.description, required_years)

        # 4. Update Database with final results
        resume.score = score_data.get("final_score") # Store final weighted score
        # Optional: Store component scores if model has fields
        # resume.semantic_score = score_data.get("semantic_score")
        # resume.skill_score = score_data.get("skill_score")
        # resume.experience_score = score_data.get("experience_score")
        resume.status = StatusEnum.COMPLETED
        # Optional: Store extracted text / skills / clear error message
        # resume.extracted_text = resume_text[:5000] # Store snippet maybe
        # resume.extracted_skills = ",".join(extract_skills(resume_text))[:499] # If needed
        # resume.error_message = None

        db.session.commit()
        logger.info(f"[Task ID: {task_id}] Resume ID {resume_id}: Processing COMPLETED. Score: {resume.score:.4f}")
        return {'status': 'COMPLETED', 'score': resume.score}

    except Exception as e:
        # Log the exception details
        logger.error(f"[Task ID: {task_id}] Resume ID {resume_id}: Processing FAILED. Error: {e}", exc_info=True) # exc_info=True logs traceback

        # Rollback potential partial commits from within the try block
        db.session.rollback()

        # Update status to FAILED reliably
        try:
            # Query again inside except block to ensure we have the latest session state
            resume_in_error = Resume.query.get(resume_id)
            if resume_in_error:
                resume_in_error.status = StatusEnum.FAILED
                resume_in_error.score = None # Clear score on failure
                # resume_in_error.error_message = str(e)[:499] # Store error snippet if model has field
                db.session.commit()
        except Exception as db_err:
             logger.error(f"[Task ID: {task_id}] DB error updating resume status to FAILED: {db_err}", exc_info=True)
             db.session.rollback()

        # Retry logic using Celery's built-in mechanism
        try:
            # self.request.retries is number of times task has been retried
            logger.warning(f"[Task ID: {task_id}] Resume ID {resume_id}: Retrying task (Attempt {self.request.retries + 1}/{self.max_retries})... Error: {e}")
            # The 'exc=e' argument passes the exception info for Celery's retry mechanism
            # Use exponential backoff: 60s, 120s, 240s
            raise self.retry(exc=e, countdown=int(default_retry_delay * (2 ** self.request.retries)))
        except self.MaxRetriesExceededError:
             logger.error(f"[Task ID: {task_id}] Resume ID {resume_id}: Max retries exceeded. Task failed permanently.")
             return {'status': 'FAILED', 'error': 'Max retries exceeded'}
        except Exception as retry_exc: # Catch potential errors during retry itself
            logger.error(f"[Task ID: {task_id}] Resume ID {resume_id}: Error occurred during retry setup: {retry_exc}")
            # Don't retry further if retry mechanism fails
            return {'status': 'FAILED', 'error': 'Retry mechanism failed'}