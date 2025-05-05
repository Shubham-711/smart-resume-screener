
import os # Import os module here as well, as it's used for path joining
from .extensions import celery, db
from .models import Resume, Job, StatusEnum
from .utils.parsers import extract_text_from_file
# Import the ENHANCED scoring function from nlp utils
from .utils.nlp import calculate_enhanced_relevance
import logging
import time # For simulating work or adding delays

# Get the logger configured in create_app
# Note: Celery might configure its own logging, but using Flask's can be useful
# from flask import current_app
# logger = current_app.logger # Using Flask's logger can sometimes cause issues in tasks
# Use Celery's logger or standard Python logging instead for tasks
logger = logging.getLogger(__name__) # Get logger for this module


# Define Celery task with name, retries, etc.
# `bind=True` allows access to task instance via `self`
# acks_late=True means task message isn't acknowledged until task finishes/fails (good for preventing task loss on worker crash)
# task_reject_on_worker_lost=True tells broker to re-queue task if worker disappears mid-execution
@celery.task(bind=True, name='app.tasks.process_resume', max_retries=3, default_retry_delay=60,
             acks_late=True, task_reject_on_worker_lost=True)
def process_resume(self, resume_id, job_id):
    """Celery task to process a single resume: parse, analyze, score."""
    task_id = self.request.id or 'unknown' # Get task ID if available
    logger.info(f"[Task ID: {task_id}] Starting processing for Resume ID: {resume_id}, Job ID: {job_id}")

    # Fetch objects within the task using the app context provided by ContextTask
    # Ensure objects exist before proceeding
    resume = Resume.query.get(resume_id)
    if not resume:
        logger.error(f"[Task ID: {task_id}] Resume ID {resume_id} not found in database. Aborting task.")
        # No retry needed if the object doesn't exist
        return {'status': 'FAILED', 'error': 'Resume database record not found'}

    job = Job.query.get(job_id)
    if not job:
        logger.error(f"[Task ID: {task_id}] Job ID {job_id} not found for Resume ID {resume_id}. Aborting task and marking resume as FAILED.")
        # Update resume status to FAILED if job is missing
        try:
            resume.status = StatusEnum.FAILED
            resume.score = None # Clear score
            # resume.error_message = "Associated Job not found"[:499] # Store error if model has field
            db.session.commit()
        except Exception as db_err:
             logger.error(f"[Task ID: {task_id}] DB error updating resume status for missing job: {db_err}", exc_info=True)
             db.session.rollback() # Rollback on error
        return {'status': 'FAILED', 'error': 'Associated Job record not found'}

    # --- Start Processing Logic within a try...except block ---
    try:
        # 1. Update Status to PROCESSING in DB
        resume.status = StatusEnum.PROCESSING
        resume.score = None # Clear previous score/errors if reprocessing
        # resume.error_message = None # Clear previous errors if field exists
        db.session.commit()
        logger.info(f"[Task ID: {task_id}] Resume ID {resume_id}: Status set to PROCESSING.")

        # 2. Get Full File Path and Extract Text
        #    Construct path based on config and stored relative path
        #    UPLOAD_FOLDER needs to be accessible by the worker process
        #    It's better to get config directly from Celery conf if possible
        upload_folder_path = celery.conf.get('UPLOAD_FOLDER')
        if not upload_folder_path:
            logger.warning(f"[Task ID: {task_id}] UPLOAD_FOLDER not found in Celery config, using default 'uploads/resumes'")
            upload_folder_path = 'uploads/resumes' # Fallback, less reliable

        # Ensure the base path is absolute for reliable os.path.join/exists
        upload_folder_abs = os.path.abspath(upload_folder_path)
        # resume.filepath should store the filename relative to the upload folder
        full_file_path = os.path.join(upload_folder_abs, resume.filepath)

        logger.info(f"[Task ID: {task_id}] Resume ID {resume_id}: Attempting to parse file at {full_file_path}")

        if not os.path.exists(full_file_path):
            # If file doesn't exist at constructed path, log error and fail
             raise FileNotFoundError(f"Resume file not found on worker at path: {full_file_path} (based on DB filepath '{resume.filepath}' and upload folder '{upload_folder_abs}')")

        # Call the parsing function from utils
        resume_text = extract_text_from_file(full_file_path)

        # Check if parsing was successful (returned non-empty text)
        if not resume_text:
            logger.error(f"[Task ID: {task_id}] Resume ID {resume_id}: Failed to extract text (empty result) from file {resume.filepath}.")
            # Raise specific error to indicate parsing failure
            raise ValueError("Failed to extract text from resume file (parser returned empty).")

        logger.info(f"[Task ID: {task_id}] Resume ID {resume_id}: Text extracted successfully (length: {len(resume_text)} chars).")

        # 3. Calculate ENHANCED Relevance Score using NLP utils
        #    Safely get required experience from the job model (defaulting to 0)
        required_years = getattr(job, 'required_experience', 0) # Assumes 'required_experience' field might exist
        if required_years is None: required_years = 0 # Handle case where field exists but is NULL

        logger.info(f"[Task ID: {task_id}] Resume ID {resume_id}: Calculating enhanced relevance against Job ID {job_id} (Req Exp: {required_years})...")
        # Call the main scoring function from nlp utils
        score_data = calculate_enhanced_relevance(resume_text, job.description, required_years)

        # 4. Update Database with final results
        resume.score = score_data.get("final_score") # Store final weighted score
        # Optional: Store component scores if model has fields
        # resume.semantic_score = score_data.get("semantic_score")
        # resume.skill_score = score_data.get("skill_score")
        # resume.experience_score = score_data.get("experience_score")
        resume.status = StatusEnum.COMPLETED # Mark as completed
        # Optional: Store extracted text snippet / skills / clear error message
        # resume.extracted_text = resume_text[:5000]
        # resume.extracted_skills = ",".join(extract_skills(resume_text))[:499]
        # resume.error_message = None

        # Commit final results to the database
        db.session.commit()
        logger.info(f"[Task ID: {task_id}] Resume ID {resume_id}: Processing COMPLETED. Final Score: {resume.score:.4f}")
        # Return success status and score
        return {'status': 'COMPLETED', 'score': resume.score}

    # --- Exception Handling Block ---
    except Exception as e:
        # Log the exception details that occurred during processing
        logger.error(f"[Task ID: {task_id}] Resume ID {resume_id}: Processing FAILED within task try block. Error: {e}", exc_info=True) # Log traceback

        # Rollback any potential partial database changes from the try block
        db.session.rollback()

        # Attempt to reliably update resume status to FAILED in DB
        try:
            # Query the resume object again within this exception handler context
            # This ensures we have a fresh object if the session was rolled back
            resume_in_error = Resume.query.get(resume_id)
            if resume_in_error:
                resume_in_error.status = StatusEnum.FAILED
                resume_in_error.score = None # Clear score on failure
                # Store error snippet if model has error_message field
                # resume_in_error.error_message = str(e)[:499]
                db.session.commit()
                logger.info(f"[Task ID: {task_id}] Resume ID {resume_id}: Status updated to FAILED in database.")
            else:
                 # Should not happen if initial check passed, but log if it does
                 logger.error(f"[Task ID: {task_id}] Resume ID {resume_id} not found during FAILED status update.")

        except Exception as db_err:
             # Log error if updating status itself fails
             logger.error(f"[Task ID: {task_id}] Database error while updating resume status to FAILED: {db_err}", exc_info=True)
             db.session.rollback() # Rollback the failed status update attempt

        # --- Retry Logic ---
        # Attempt to retry the task based on the decorator settings (max_retries, default_retry_delay)
        try:
            logger.warning(f"[Task ID: {task_id}] Resume ID {resume_id}: Attempting task retry ({self.request.retries + 1}/{self.max_retries}). Current Error: {e}")
            # Access the configured delay directly from the task instance 'self'
            # Use a default (e.g., 60) if self.default_retry_delay is somehow not set
            retry_delay = self.default_retry_delay if self.default_retry_delay is not None else 60
            # Calculate exponential backoff for the countdown
            countdown = int(retry_delay * (2 ** self.request.retries))
            # Re-raise the original exception 'e' to trigger Celery's retry mechanism
            # with the calculated countdown
            raise self.retry(exc=e, countdown=countdown)
        except self.MaxRetriesExceededError:
             # Log when retries are exhausted
             logger.error(f"[Task ID: {task_id}] Resume ID {resume_id}: Max retries ({self.max_retries}) exceeded. Task failed permanently after error: {e}")
             # Return failure status if max retries reached
             return {'status': 'FAILED', 'error': 'Max retries exceeded'}
        except Exception as retry_exc:
            # Catch potential errors during the retry call itself (less common)
            logger.error(f"[Task ID: {task_id}] Resume ID {resume_id}: CRITICAL - Error occurred during retry setup: {retry_exc}", exc_info=True)
            # Return failure if the retry mechanism itself breaks
            return {'status': 'FAILED', 'error': 'Retry mechanism failed'}