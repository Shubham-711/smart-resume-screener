# backend/app/routes/jobs.py

from flask import Blueprint, request, jsonify, current_app # Import current_app for logger
# Import necessary items from other app modules
from ..models import Job
from ..schemas import job_schema, jobs_schema
from ..extensions import db
from marshmallow import ValidationError

# Create a Blueprint object for job routes
bp = Blueprint('jobs', __name__)
# Use Flask app's configured logger
logger = current_app.logger

# --- API Endpoints ---

# POST /api/jobs - Create a new job
@bp.route('', methods=['POST'])
def create_job():
    """Creates a new job record."""
    json_data = request.get_json()
    if not json_data:
        logger.warning("Create job request failed: No JSON data received.")
        return jsonify({"error": "No input data provided"}), 400

    try:
        # Validate and deserialize input using Marshmallow schema
        # load_instance=True in schema definition creates a Job model object
        new_job = job_schema.load(json_data)
    except ValidationError as err:
        logger.warning(f"Create job request failed: Validation errors: {err.messages}")
        # Return validation errors from Marshmallow
        return jsonify({"error": "Validation failed", "messages": err.messages}), 422 # Unprocessable Entity

    # Optional: Add extra validation if needed beyond schema
    if not new_job.title or not new_job.description:
         logger.warning("Create job request failed: Missing title or description after schema load.")
         return jsonify({"error": "Missing required fields: title or description"}), 400

    try:
        # Add the new Job object to the database session
        db.session.add(new_job)
        # Commit the transaction to save it to the database
        db.session.commit()
        logger.info(f"Job created successfully with ID: {new_job.id}")
        # Serialize the created job object for the response using the schema
        return job_schema.jsonify(new_job), 201 # 201 Created status code
    except Exception as e:
        db.session.rollback() # Rollback transaction on any database error
        logger.error(f"Database error creating job: {e}", exc_info=True)
        return jsonify({"error": "Internal server error: Could not create job"}), 500


# GET /api/jobs - Get a list of all jobs
@bp.route('', methods=['GET'])
def get_jobs():
    """Retrieves a list of all jobs."""
    try:
        # Query all jobs from the database, order by creation date descending
        all_jobs = Job.query.order_by(Job.created_at.desc()).all()
        logger.info(f"Retrieved {len(all_jobs)} jobs.")
        # Serialize the list of jobs using the schema (many=True)
        return jobs_schema.jsonify(all_jobs), 200 # 200 OK status code
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}", exc_info=True)
        return jsonify({"error": "Internal server error: Could not retrieve jobs"}), 500


# GET /api/jobs/<job_id> - Get details of a specific job
@bp.route('/<int:job_id>', methods=['GET'])
def get_job(job_id):
    """Retrieves details for a specific job by its ID."""
    logger.debug(f"Request received for job ID: {job_id}")
    try:
        # Query the database for the job by ID
        # get_or_404 automatically handles the case where the ID doesn't exist by raising a 404 error
        job = Job.query.get_or_404(job_id, description=f"Job with ID {job_id} not found.")
        logger.info(f"Retrieved job with ID: {job_id}")
        # Serialize the single job object using the schema
        return job_schema.jsonify(job), 200
    except Exception as e:
         # Catch potential errors even with get_or_404 (less likely for GET, but good practice)
         logger.error(f"Error fetching job {job_id}: {e}", exc_info=True)
         return jsonify({"error": "Internal server error: Could not retrieve job details"}), 500


# PUT /api/jobs/<job_id> - Update an existing job
@bp.route('/<int:job_id>', methods=['PUT'])
def update_job(job_id):
    """Updates an existing job record."""
    # Find the existing job object or return 404
    job = Job.query.get_or_404(job_id, description=f"Job with ID {job_id} not found.")
    json_data = request.get_json()
    if not json_data:
         logger.warning(f"Update job request failed for ID {job_id}: No JSON data received.")
         return jsonify({"error": "No input data provided"}), 400

    try:
        # Load data from the request JSON into the existing job model object
        # Use partial=True to allow updating only the fields present in the request JSON
        # This modifies the 'job' object in place
        updated_job = job_schema.load(json_data, instance=job, partial=True)
    except ValidationError as err:
        logger.warning(f"Update job request failed for ID {job_id}: Validation errors: {err.messages}")
        return jsonify({"error": "Validation failed", "messages": err.messages}), 422

    try:
        # Commit the changes (SQLAlchemy tracks modifications to 'job')
        db.session.commit()
        logger.info(f"Job updated successfully with ID: {updated_job.id}")
        # Return the updated job object, serialized by the schema
        return job_schema.jsonify(updated_job), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error updating job {job_id}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error: Could not update job"}), 500


# DELETE /api/jobs/<job_id> - Delete a job
@bp.route('/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Deletes a job record and its associated resumes."""
    # Find the job or return 404
    job = Job.query.get_or_404(job_id, description=f"Job with ID {job_id} not found.")
    try:
        # Delete the job object from the database session
        # Resumes linked via cascade='all, delete-orphan' in the Job model's relationship
        # should be deleted automatically by the database cascade or SQLAlchemy's orphan handling.
        db.session.delete(job)
        # Commit the transaction
        db.session.commit()
        logger.info(f"Job deleted successfully with ID: {job_id}")
        # Return success message or 204 No Content
        # 200 with message is often clearer for clients
        return jsonify({"message": f"Job with ID {job_id} and associated resumes deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error deleting job {job_id}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error: Could not delete job"}), 500