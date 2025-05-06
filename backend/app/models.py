# backend/app/models.py

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
    # --- ADDED LINE ---
    required_years = db.Column(db.Integer, nullable=True) # Store required years (can be null if not specified)
    # ------------------
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resumes = db.relationship('Resume', backref=db.backref('job', lazy=True), lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Job id={self.id} title="{self.title[:30]}...">'

class Resume(db.Model):
    __tablename__ = 'resumes'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    status = db.Column(db.Enum(StatusEnum), default=StatusEnum.PENDING, nullable=False, index=True)
    score = db.Column(db.Float, nullable=True, index=True) # Final weighted score
    # Optional: Add fields to store component scores if desired for API/frontend
    # semantic_score = db.Column(db.Float, nullable=True)
    # skill_score = db.Column(db.Float, nullable=True)
    # experience_score = db.Column(db.Float, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False, index=True)
    # Optional: Store processing errors
    # error_message = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f'<Resume id={self.id} filename="{self.filename}" status={self.status.name}>'