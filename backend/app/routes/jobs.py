# backend/app/routes/jobs.py

from flask import Blueprint, request, jsonify, current_app # Import current_app for logger
# Import using relative path (..) to go up one level from 'routes' to 'app'
from ..models import Job
from ..schemas import job_schema, jobs_schema
from ..extensions import db
from marshmallow import ValidationError

# Create a Blueprint object for job routes, named 'jobs'
bp = Blueprint('jobs', __name__)
# Use Flask app's configured logger for consistency
logger = current_app.logger

# --- API Endpoints for /api/jobs ---

# POST /api/jobs - Create a new job
@bp.route('', methods=['POST'])
def create_job():
    """Creates a new job record based on JSON data in the request body."""
    json_data = request.get_json()
    if not json_data:
        logger.warning("Create job request failed: No JSON data provided.")
        return jsonify({"error": "No input data provided"}), 400

    try:
        # Validate and deserialize input using the JobSchema
        # load_instance=True in schema definition creates a Job model object directly
        new_job = job_schema.load(json_data)
    except ValidationError as err:
        # Log validation errors and return them to the client
        logger.warning(f"Create job request failed: Validation errors: {err.messages}")
        return jsonify({"error": "Validation failed", "messages": err.messages}), 422 # Unprocessable Entity

    # Although schema might enforce required fields, explicit checks can add clarity
    if not new_job.title or not new_job.description:
         logger.warning("Create job request failed: Missing title or description after schema load (should be caught by schema).")
         # This might indicate an issue with the schema definition if reached
         return jsonify({"error": "Missing required fields: title or description"}), 400

    try:
        # Add the new Job object to the database session
        db.session.add(new_job)
        # Commit the transaction to save the record to the database
        db.session.commit()
        logger.info(f"Job created successfully with ID: {new_job.id}, Title: '{new_job.title}'")
        # Serialize the newly created job object for the response using the schema
        return job_schema.jsonify(new_job), 201 # Return 201 Created status code
    except Exception as e:
        # Rollback the transaction in case of any database error during commit
        db.session.rollback()
        logger.error(f"Database error occurred while creating job: {e}", exc_info=True)
        return jsonify({"error": "Internal server error: Could not create job"}), 500


# GET /api/jobs - Get a list of all jobs
@bp.route('', methods=['GET'])
def get_jobs():
    """Retrieves a list of all job records, ordered by creation date."""
    try:
        # Query all jobs from the database
        # Order by creation date descending to show newest first
        all_jobs = Job.query.order_by(Job.created_at.desc()).all()
        logger.info(f"Retrieved {len(all_jobs)} jobs.")
        # Serialize the list of job objects using the schema (many=True)
        return jobs_schema.jsonify(all_jobs), 200 # Return 200 OK status code
    except Exception as e:
        logger.error(f"Error fetching list of jobs: {e}", exc_info=True)
        return jsonify({"error": "Internal server error: Could not retrieve jobs"}), 500


# GET /api/jobs/<job_id> - Get details of a specific job
@bp.route('/<int:job_id>', methods=['GET'])
def get_job(job_id):
    """Retrieves details for a specific job by its unique ID."""
    logger.debug(f"Request received for job ID: {job_id}")
    try:
        # Use Flask-SQLAlchemy's get_or_404 to query by primary key (ID)
        # It automatically raises a 404 Not Found error if no job with that ID exists
        job = Job.query.get_or_404(job_id, description=f"Job with ID {job_id} not found.")
        logger.info(f"Retrieved job details for ID: {job_id}")
        # Serialize the single job object using the schema
        return job_schema.jsonify(job), 200
    except Exception as e:
         # Catch other potential errors during serialization or unexpected issues
         logger.error(f"Error fetching job details for ID {job_id}: {e}", exc_info=True)
         return jsonify({"error": "Internal server error: Could not retrieve job details"}), 500


# PUT /api/jobs/<job_id> - Update an existing job
@bp.route('/<int:job_id>', methods=['PUT'])
def update_job(job_id):
    """Updates an existing job record based on JSON data in the request body."""
    # Find the existing job object by ID or raise 404
    job = Job.query.get_or_404(job_id, description=f"Job with ID {job_id} not found.")

    json_data = request.get_json()
    if not json_data:
         logger.warning(f"Update job request failed for ID {job_id}: No JSON data provided.")
         return jsonify({"error": "No input data provided"}), 400

    try:
        # Load data from the request JSON into the existing 'job' model object
        # Use partial=True to allow updating only the fields present in the request JSON
        # This modifies the 'job' object in place (SQLAlchemy tracks changes)
        updated_job = job_schema.load(json_data, instance=job, partial=True)
    except ValidationError as err:
        logger.warning(f"Update job request failed for ID {job_id}: Validation errors: {err.messages}")
        return jsonify({"error": "Validation failed", "messages": err.messages}), 422

    try:
        # Commit the changes tracked by SQLAlchemy to the database
        db.session.commit()
        logger.info(f"Job updated successfully for ID: {updated_job.id}")
        # Return the updated job object, serialized by the schema
        return job_schema.jsonify(updated_job), 200
    except Exception as e:
        # Rollback transaction on database error
        db.session.rollback()
        logger.error(f"Database error updating job {job_id}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error: Could not update job"}), 500


# DELETE /api/jobs/<job_id> - Delete a job
@bp.route('/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Deletes a job record and, due to cascade settings, its associated resumes."""
    # Find the job by ID or raise 404
    job = Job.query.get_or_404(job_id, description=f"Job with ID {job_id} not found.")
    try:
        # Remove the job object from the database session
        db.session.delete(job)
        # Commit the transaction to finalize deletion
        # The cascade='all, delete-orphan' setting in the Job model's 'resumes' relationship
        # should handle the automatic deletion of associated Resume records.
        db.session.commit()
        logger.info(f"Job deleted successfully for ID: {job_id}")
        # Return a success message (200 OK is common) or 204 No Content
        return jsonify({"message": f"Job with ID {job_id} and associated resumes deleted successfully."}), 200
    except Exception as e:
        # Rollback transaction on database error
        db.session.rollback()
        logger.error(f"Database error deleting job {job_id}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error: Could not delete job"}), 500