from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PlannerBlockCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    subject: str | None = Field(default=None, max_length=80)
    study_date: date
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.end_time <= self.start_time:
            raise ValueError("End time must be after start time")
        return self


class PlannerBlockUpdate(BaseModel):
    completed: bool


class PlannerBlockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    subject: str | None
    study_date: date
    start_time: time
    end_time: time
    completed: bool
    created_at: datetime
