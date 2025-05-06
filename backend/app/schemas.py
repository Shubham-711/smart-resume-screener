# backend/app/schemas.py

from marshmallow import fields, ValidationError, validates_schema, validates
from .extensions import ma
from .models import Job, Resume, StatusEnum

# Custom field for Enum serialization/deserialization
class EnumField(fields.Field):
    """Custom Marshmallow field for Enums."""
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None: return None
        return value.value
    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return StatusEnum(value) # Adjust if using other enums
        except ValueError as e:
            valid_values = [item.value for item in StatusEnum] # Adjust for other enums
            raise ValidationError(f"Invalid status value '{value}'. Must be one of: {valid_values}") from e

class ResumeSchema(ma.SQLAlchemyAutoSchema):
    status = EnumField(attribute="status")
    class Meta:
        model = Resume
        load_instance = True
        # Remove job_id from explicit fields list (let AutoSchema handle it)
        fields = ("id", "filename", "status", "score", "uploaded_at",
                  # "semantic_score", "skill_score", "experience_score" # Uncomment if added to model
                  )
        dump_only = ("id", "uploaded_at", "score", "status",
                     # "semantic_score", "skill_score", "experience_score" # Uncomment if added to model
                     )

class JobSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Job
        load_instance = True
        # --- MODIFIED LINE ---
        # Add required_years to the fields handled by the schema
        fields = ("id", "title", "description", "required_years", "created_at")
        # ---------------------
        dump_only = ("id", "created_at") # Read-only fields

    # Optional: Add simple validation for required_years
    @validates("required_years")
    def validate_years(self, value , **kwargs):
        if value is not None and value < 0:
            raise ValidationError("Required years cannot be negative.")


# Instantiate schemas
job_schema = JobSchema()
jobs_schema = JobSchema(many=True)
resume_schema = ResumeSchema()
resumes_schema = ResumeSchema(many=True)