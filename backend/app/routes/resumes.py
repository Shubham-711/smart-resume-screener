# backend/app/routes/resumes.py

from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
import os
import uuid # For generating unique filenames

# Import necessary items from other app modules
from ..models import Resume, Job, StatusEnum
from ..schemas import resume_schema, resumes_schema
from ..extensions import db, celery # Import celery instance
from ..tasks import process_resume # Import the Celery task definition

# Create a Blueprint object for resume routes
bp = Blueprint('resumes', __name__)
# Use Flask app's configured logger
logger = current_app.logger

# --- Helper Functions ---

def allowed_file(filename):
    """Checks if the file extension is allowed based on Flask app config."""
    # Get allowed extensions from Flask config, provide default if not set
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'docx'})
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_safe_upload_path(job_id, filename):
    """Generates a safe, unique relative path for the uploaded file and the absolute path for saving."""
    # Secure the original filename (remove risky characters like '..', '/')
    base_filename = secure_filename(filename)
    if not base_filename: # Handle cases where filename becomes empty after securing
        base_filename = "untitled"

    # Generate a unique prefix to prevent collisions and add obscurity
    unique_prefix = uuid.uuid4().hex[:8] # Use first 8 chars of a UUID

    # Split name and extension
    name, ext = os.path.splitext(base_filename)
    if not ext: # Handle files potentially missing extension after securing
        # Try to guess from original filename if possible, otherwise default
        original_ext = os.path.splitext(filename)[1].lower()
        if original_ext and original_ext != '.':
             ext = original_ext
        else:
             ext = '.bin' # Default binary extension if unknown
    ext = ext.lower() # Ensure extension is lowercase

    # Construct unique filename: original_name_prefix.ext
    unique_filename = f"{name}_{unique_prefix}{ext}"

    # Define the path relative to the UPLOAD_FOLDER (this is stored in DB)
    # Example: 'Software_Engineer_Resume_a1b2c3d4.pdf'
    relative_path = unique_filename

    # Get the absolute path to the configured UPLOAD_FOLDER for saving the file
    upload_folder_abs = os.path.abspath(current_app.config['UPLOAD_FOLDER'])
    save_path_abs = os.path.join(upload_folder_abs, relative_path)

    # Ensure the base upload directory exists (create_app should handle this, but safety check)
    if not os.path.exists(upload_folder_abs):
        try:
            os.makedirs(upload_folder_abs)
            logger.info(f"Created missing upload folder: {upload_folder_abs}")
        except OSError as e:
             logger.error(f"Fatal: Failed to create upload folder {upload_folder_abs}: {e}", exc_info=True)
             # If folder cannot be created, we cannot save files
             raise IOError(f"Upload folder cannot be created: {upload_folder_abs}") from e

    return relative_path, save_path_abs # Return relative path for DB, absolute path for saving

# --- API Routes ---

# POST /api/jobs/<job_id>/resumes - Upload one or more resumes for a specific job
@bp.route('/jobs/<int:job_id>/resumes', methods=['POST'])
def upload_resumes(job_id):
    """Handles uploading multiple resume files for a given job."""
    # Ensure the target job exists, otherwise return 404
    job = Job.query.get_or_404(job_id, description=f"Job with ID {job_id} not found.")

    # Check if the file part 'files[]' is present in the request
    if 'files[]' not in request.files:
        logger.warning(f"Resume upload failed for job {job_id}: No 'files[]' part in request.")
        return jsonify({"error": "No file part in the request. Use key 'files[]'."}), 400

    # Get the list of files associated with the 'files[]' key
    files = request.files.getlist('files[]')

    # Check if any files were actually selected
    if not files or all(f.filename == '' for f in files):
        logger.warning(f"Resume upload failed for job {job_id}: No files selected.")
        return jsonify({"error": "No selected files"}), 400

    uploaded_resume_objects = [] # List to hold successfully created Resume model objects
    errors = {} # Dictionary to hold errors for specific files

    for file in files:
        # Check if file object exists and filename has an allowed extension
        if file and allowed_file(file.filename):
            original_filename = file.filename # Store original filename for DB/display
            try:
                # Generate safe paths (relative for DB, absolute for saving)
                relative_path, save_path_abs = get_safe_upload_path(job_id, original_filename)

                # Save the uploaded file stream to the absolute disk path
                file.save(save_path_abs)
                logger.info(f"Saved uploaded file '{original_filename}' to '{save_path_abs}' (relative: '{relative_path}')")

                # Create a new Resume database record
                new_resume = Resume(
                    filename=original_filename, # Store original filename
                    filepath=relative_path,     # Store RELATIVE path in DB
                    job_id=job.id,              # Link to the parent job
                    status=StatusEnum.PENDING   # Initial status
                )
                db.session.add(new_resume)
                # Flush session to assign an ID to new_resume before queuing the task
                # The task needs the ID to look up the resume record later
                db.session.flush()

                # Trigger the Celery background task asynchronously
                # Pass primitive, serializable IDs to the task
                task = process_resume.delay(new_resume.id, job.id)
                logger.info(f"Queued resume processing task {task.id} for new Resume ID {new_resume.id} (Job: {job_id}, File: {original_filename})")

                # Add the successfully processed Resume object to our list for the response
                uploaded_resume_objects.append(new_resume)

            except Exception as e:
                # Log any error during file saving or task queuing
                logger.error(f"Error processing uploaded file '{original_filename}' for job {job_id}: {e}", exc_info=True)
                # Rollback potential partial flush for this specific file's resume object
                # Ensures the failed resume record isn't committed later if others succeed
                db.session.rollback()
                errors[original_filename] = f"Failed to save or queue file for processing: {str(e)[:100]}" # Store brief error

        elif file and file.filename: # File was present but not allowed type or had empty name after securing
             logger.warning(f"Skipped file '{file.filename}' for job {job_id}: File type not allowed or invalid.")
             errors[file.filename] = "File type not allowed or invalid file."


    # --- Handle Response after processing all files ---
    if not uploaded_resume_objects and errors:
         # Case: No files succeeded, only errors occurred
         logger.warning(f"Resume upload completed for job {job_id}, but all files failed.")
         return jsonify({"error": "No files were successfully uploaded.", "details": errors}), 400
    elif uploaded_resume_objects:
        # Case: At least one file was successfully uploaded and queued
        try:
            # Commit all successfully added Resume DB records from the loop at once
            db.session.commit()
            logger.info(f"Successfully committed {len(uploaded_resume_objects)} new resume records for job {job_id}.")

            # Prepare response data for successfully uploaded resumes using Marshmallow schema
            success_response_data = resumes_schema.dump(uploaded_resume_objects)
            status_code = 201 # 201 Created

            # If some files failed alongside successes, return 207 Multi-Status with both results
            if errors:
                 logger.warning(f"Resume upload completed for job {job_id} with {len(errors)} errors alongside {len(uploaded_resume_objects)} successes.")
                 final_response = {"uploaded": success_response_data, "errors": errors}
                 status_code = 207 # Multi-Status

            else:
                 # Only successes, return the list directly
                 final_response = success_response_data

            return jsonify(final_response), status_code

        except Exception as e:
            # Handle potential DB commit errors after files were already saved to disk
            db.session.rollback()
            logger.error(f"Database commit failed after processing uploads for job {job_id}: {e}", exc_info=True)
            # Note: Files might be saved on disk but DB records aren't committed.
            # A cleanup strategy might be needed for orphaned files in production.
            return jsonify({"error": "Internal server error: Failed to finalize resume uploads."}), 500
    else:
        # Should not be reached if initial checks work, but as a fallback
        logger.error(f"Unexpected state after resume upload loop (no successes, no errors?) for job {job_id}.")
        return jsonify({"error": "An unexpected error occurred during upload processing."}), 500


# GET /api/jobs/<job_id>/resumes - Get resumes for a specific job, ranked
@bp.route('/jobs/<int:job_id>/resumes', methods=['GET'])
def get_job_resumes(job_id):
    """Retrieves a ranked list of resumes associated with a specific job."""
    # Ensure the job exists
    job = Job.query.get_or_404(job_id, description=f"Job with ID {job_id} not found.")
    logger.debug(f"Fetching resumes for job ID: {job_id}")
    try:
        # Query resumes related to this job
        # Order by score descending (handling NULLs - non-null scores first), then by upload date
        resumes_query = job.resumes.order_by(
            db.desc(Resume.score.isnot(None)), # Put resumes with a score first
            db.desc(Resume.score),             # Then order by score descending
            Resume.uploaded_at.asc()           # Finally by upload time ascending
        )
        resumes = resumes_query.all() # Execute the query

        logger.info(f"Retrieved {len(resumes)} resumes for job ID: {job_id}")
        # Serialize the list of resume objects using the schema
        return resumes_schema.jsonify(resumes), 200
    except Exception as e:
        logger.error(f"Error fetching resumes for job {job_id}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error: Could not retrieve resumes for this job."}), 500


# GET /api/resumes/<resume_id> - Get status/details of a single resume
@bp.route('/resumes/<int:resume_id>', methods=['GET'])
def get_resume_status(resume_id):
     """Retrieves details and status for a single resume by its ID."""
     logger.debug(f"Fetching status for resume ID: {resume_id}")
     try:
        # Find the resume by ID or return 404
        resume = Resume.query.get_or_404(resume_id, description=f"Resume with ID {resume_id} not found.")

        # Optional: Add logic here to check Celery task status if you store task_id on the Resume model
        # task_info = {}
        # if resume.task_id:
        #    try:
        #        task = process_resume.AsyncResult(resume.task_id)
        #        task_info = {'task_id': resume.task_id, 'task_status': task.state}
        #    except Exception as celery_err:
        #        logger.warning(f"Could not get Celery task status for task ID {resume.task_id}: {celery_err}")

        logger.info(f"Retrieved status for resume ID: {resume_id} (Status: {resume.status.name})")
        # Serialize the single resume object
        # You could merge task_info here if needed: `**resume_schema.dump(resume), **task_info`
        return resume_schema.jsonify(resume), 200
     except Exception as e:
        logger.error(f"Error fetching resume status {resume_id}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error: Could not retrieve resume details."}), 500


# GET /api/resumes/<resume_id>/download - Download the original resume file
@bp.route('/resumes/<int:resume_id>/download', methods=['GET'])
def download_resume(resume_id):
    """Provides the original resume file for download."""
    logger.debug(f"Request to download resume ID: {resume_id}")
    # !!! IMPORTANT: Implement Authentication & Authorization Here !!!
    # This endpoint should be protected to ensure only authorized users can download resumes.
    # Example (requires Flask-Login or similar):
    # from flask_login import current_user, login_required
    # @login_required
    # ...
    # if not current_user.has_permission_for_resume(resume_id):
    #    return jsonify({"error": "Forbidden"}), 403

    try:
        # Find the resume record or return 404
        resume = Resume.query.get_or_404(resume_id, description=f"Resume with ID {resume_id} not found.")

        # Get the absolute path to the UPLOAD_FOLDER from config
        directory_abs = os.path.abspath(current_app.config['UPLOAD_FOLDER'])
        # resume.filepath should contain the unique filename relative to the upload folder
        file_path_relative = resume.filepath

        logger.info(f"Attempting to send file: Directory='{directory_abs}', Relative Path='{file_path_relative}', Suggested Download Name='{resume.filename}'")

        # Use Flask's send_from_directory for security (prevents path traversal attacks)
        # It safely joins the directory and filename
        return send_from_directory(
            directory=directory_abs,         # The absolute directory containing the file
            path=file_path_relative,         # The relative path/filename within that directory
            as_attachment=True,              # Send as attachment, prompting download dialog
            download_name=resume.filename    # Suggest the original filename to the user's browser
        )
    except FileNotFoundError:
        # This occurs if the file is missing from disk (e.g., deleted manually)
        # but the database record still exists.
        logger.error(f"Resume file not found on server disk for Resume ID {resume_id}. Expected relative path '{resume.filepath}' within '{directory_abs}'")
        return jsonify({"error": "File not found on server disk."}), 404
    except Exception as e:
        # Catch other potential errors (e.g., permissions, network issues)
        logger.error(f"Error during download attempt for resume {resume_id}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error: Could not download file."}), 500