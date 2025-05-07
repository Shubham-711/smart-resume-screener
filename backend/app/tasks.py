# backend/app/tasks.py

import os 
from .extensions import celery, db
from .models import Resume, Job, StatusEnum
from .utils.parsers import extract_text_from_file
# Import the ENHANCED scoring function from nlp utils
from .utils.nlp import calculate_enhanced_relevance
import time
import logging


# Use Celery's logger or standard Python logging for tasks
logger = logging.getLogger(__name__) # Get logger for this module


@celery.task(bind=True, name='app.tasks.process_resume', max_retries=3, default_retry_delay=60,
             acks_late=True, task_reject_on_worker_lost=True)
def process_resume(self, resume_id, job_id):
    task_id = self.request.id or 'unknown'
    logger.info(f"[Task ID: {task_id}] Starting processing for Resume ID: {resume_id}, Job ID: {job_id}")

    retries = 0
    MAX_DB_FETCH_RETRIES = 3 # Try 3 times
    RETRY_DB_FETCH_DELAY = 1 # Wait 1 second between tries

    resume = None
    while retries < MAX_DB_FETCH_RETRIES and resume is None:
        resume = Resume.query.get(resume_id)
        if resume is None:
            retries += 1
            if retries < MAX_DB_FETCH_RETRIES:
                 logger.warning(f"[Task ID: {task_id}] Resume ID {resume_id} not found on attempt {retries}. Waiting {RETRY_DB_FETCH_DELAY}s before retry...")
                 time.sleep(RETRY_DB_FETCH_DELAY) # Add import time at the top
        else:
            break # Found it!

    if resume is None: # Check after retries
        logger.error(f"[Task ID: {task_id}] Resume ID {resume_id} not found in database after {MAX_DB_FETCH_RETRIES} attempts. Aborting task.")
        return {'status': 'FAILED', 'error': 'Resume database record not found'}

    # Fetch objects from DB
    resume = Resume.query.get(resume_id)
    if not resume:
        logger.error(f"[Task ID: {task_id}] Resume ID {resume_id} not found in database. Aborting task.")
        return {'status': 'FAILED', 'error': 'Resume database record not found'}

    job = Job.query.get(job_id)
    if not job:
        logger.error(f"[Task ID: {task_id}] Job ID {job_id} not found for Resume ID {resume_id}. Aborting task and marking resume as FAILED.")
        try:
            resume.status = StatusEnum.FAILED
            resume.score = None
            # resume.error_message = "Associated Job not found"[:499]
            db.session.commit()
        except Exception as db_err:
             logger.error(f"[Task ID: {task_id}] DB error updating resume status for missing job: {db_err}", exc_info=True)
             db.session.rollback()
        return {'status': 'FAILED', 'error': 'Associated Job record not found'}

    # --- Start Processing Logic ---
    try:
        # 1. Update Status to PROCESSING
        resume.status = StatusEnum.PROCESSING
        resume.score = None
        # resume.error_message = None
        db.session.commit()
        logger.info(f"[Task ID: {task_id}] Resume ID {resume_id}: Status set to PROCESSING.")

        # 2. Get Full File Path and Extract Text
        upload_folder_path = celery.conf.get('UPLOAD_FOLDER')
        if not upload_folder_path:
            logger.warning(f"[Task ID: {task_id}] UPLOAD_FOLDER not found in Celery config, using default 'uploads/resumes'")
            upload_folder_path = 'uploads/resumes'

        upload_folder_abs = os.path.abspath(upload_folder_path)
        full_file_path = os.path.join(upload_folder_abs, resume.filepath)

        logger.info(f"[Task ID: {task_id}] Resume ID {resume_id}: Attempting to parse file at {full_file_path}")

        if not os.path.exists(full_file_path):
             raise FileNotFoundError(f"Resume file not found on worker at path: {full_file_path} (based on DB filepath '{resume.filepath}' and upload folder '{upload_folder_abs}')")

        resume_text = extract_text_from_file(full_file_path)

        if not resume_text:
            logger.error(f"[Task ID: {task_id}] Resume ID {resume_id}: Failed to extract text (empty result) from file {resume.filepath}.")
            raise ValueError("Failed to extract text from resume file (parser returned empty).")

        logger.info(f"[Task ID: {task_id}] Resume ID {resume_id}: Text extracted successfully (length: {len(resume_text)} chars).")

        # 3. Calculate ENHANCED Relevance Score
        required_years = job.required_years if job.required_years is not None else 0
        logger.info(f"[Task ID: {task_id}] Resume ID {resume_id}: Calculating enhanced relevance against Job ID {job_id} (Req Exp from DB: {required_years})...")
        score_data = calculate_enhanced_relevance(resume_text, job.description, required_years)

        # 4. Update Database with final results
        resume.score = score_data.get("final_score")
        # Optional: Store component scores
        # resume.semantic_score = score_data.get("semantic_score")
        # resume.skill_score = score_data.get("skill_score")
        # resume.experience_score = score_data.get("experience_score")
        resume.status = StatusEnum.COMPLETED

        db.session.commit()
        logger.info(f"[Task ID: {task_id}] Resume ID {resume_id}: Processing COMPLETED. Final Score: {resume.score:.4f}")
        return {'status': 'COMPLETED', 'score': resume.score}

    # --- Exception Handling Block ---
    except Exception as e:
        # Log the original error that occurred during processing
        logger.error(f"[Task ID: {task_id}] Resume ID {resume_id}: Processing FAILED within task try block. Error: {type(e).__name__}: {e}", exc_info=True)
        db.session.rollback() # Rollback any partial DB changes from try block

        # Attempt to update resume status to FAILED in the database
        try:
            resume_in_error = Resume.query.get(resume_id)
            if resume_in_error:
                resume_in_error.status = StatusEnum.FAILED
                resume_in_error.score = None
                # resume_in_error.error_message = str(e)[:499] # Store error if field exists
                db.session.commit()
                logger.info(f"[Task ID: {task_id}] Resume ID {resume_id}: Status updated to FAILED in database.")
            else:
                 logger.error(f"[Task ID: {task_id}] Resume ID {resume_id} not found during FAILED status update.")
        except Exception as db_err:
             logger.error(f"[Task ID: {task_id}] Database error while updating resume status to FAILED: {db_err}", exc_info=True)
             db.session.rollback() # Rollback the status update attempt itself

        # --- MODIFIED Retry Logic ---
        # Check if retries are exhausted BEFORE calling self.retry()
        if self.request.retries >= self.max_retries:
            logger.error(f"[Task ID: {task_id}] Resume ID {resume_id}: Max retries ({self.max_retries}) exceeded. Task failed permanently after error: {type(e).__name__}: {e}")
            return {'status': 'FAILED', 'error': 'Max retries exceeded'}
        else:
            # If not exhausted, attempt to retry explicitly
            try:
                logger.warning(f"[Task ID: {task_id}] Resume ID {resume_id}: Attempting task retry ({self.request.retries + 1}/{self.max_retries}). Current Error: {type(e).__name__}")
                retry_delay = self.default_retry_delay if self.default_retry_delay is not None else 60
                countdown = int(retry_delay * (2 ** self.request.retries)) # Exponential backoff

                # Explicitly call retry() instead of raising it directly here.
                # Pass the original exception 'e'. Celery's retry() method will raise
                # a specific Retry exception internally if successful.
                self.retry(exc=e, countdown=countdown)

                # This part might not be reached if retry() successfully raises its internal exception
                logger.info(f"[Task ID: {task_id}] Resume ID {resume_id}: Explicit retry called.")
                return {'status': 'RETRYING', 'error': str(e)}

            except Exception as retry_exc:
                # Catch potential errors during the explicit self.retry() call itself
                logger.error(f"[Task ID: {task_id}] Resume ID {resume_id}: CRITICAL - Error occurred during explicit retry call: {retry_exc}", exc_info=True)
                # If the retry mechanism itself fails, mark as failed permanently
                return {'status': 'FAILED', 'error': 'Retry mechanism failed during explicit call'}
        # --- End of MODIFIED Retry Logic ---