from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Response models built from SQLAlchemy objects (replaces repeated ``class Config``)."""

    model_config = ConfigDict(from_attributes=True)


class StrictInput(BaseModel):
    """Request bodies: reject unknown fields (mass-assignment) and trim whitespace."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
