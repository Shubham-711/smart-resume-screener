from .extensions import db
from datetime import datetime
import enum

# Define Enum for status choices
class StatusEnum(enum.Enum):
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'

    def __str__(self):
        return self.value

class Job(db.Model):
    __tablename__ = 'jobs' # Explicit table name
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    # Optional: Add field for required experience years if you enhance JD parsing
    # required_experience = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # One-to-Many relationship: One Job has many Resumes
    # lazy='dynamic' allows further querying on job.resumes
    # cascade ensures resumes are deleted if the parent job is deleted
    resumes = db.relationship('Resume', backref=db.backref('job', lazy=True), lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Job id={self.id} title="{self.title[:30]}...">'

class Resume(db.Model):
    __tablename__ = 'resumes'
    id = db.Column(db.Integer, primary_key=True)
    # Store original filename for user display
    filename = db.Column(db.String(255), nullable=False)
    # Store the relative path within the UPLOAD_FOLDER or the full cloud storage URL/key
    # Needs to be resolvable by the Celery worker
    filepath = db.Column(db.String(512), nullable=False)
    # Use the Enum for status tracking
    status = db.Column(db.Enum(StatusEnum), default=StatusEnum.PENDING, nullable=False, index=True)
    # Store the final calculated score
    score = db.Column(db.Float, nullable=True, index=True) # Score from 0.0 to 1.0
    # Optional: Store component scores if needed for display/analysis
    # semantic_score = db.Column(db.Float, nullable=True)
    # skill_score = db.Column(db.Float, nullable=True)
    # experience_score = db.Column(db.Float, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Many-to-One relationship: Many Resumes belong to one Job
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False, index=True) # Added ondelete
    # Optional: Store extracted text or key entities if needed for quick viewing/re-scoring
    # extracted_text = db.Column(db.Text, nullable=True)
    # extracted_skills = db.Column(db.Text, nullable=True) # e.g., store as JSON string or comma-separated
    # error_message = db.Column(db.String(500), nullable=True) # Store processing errors

    def __repr__(self):
        return f'<Resume id={self.id} filename="{self.filename}" status={self.status.name}>'

# Add User model here if/when implementing authentication