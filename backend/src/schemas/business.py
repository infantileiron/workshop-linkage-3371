from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class CleanInput(BaseModel, str_strip_whitespace=True, extra='forbid'):
    pass


class Login(CleanInput):
    email: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=1, max_length=200)


class CourseInput(CleanInput):
    code: str = Field(pattern=r'^[A-Za-z0-9-]{2,32}$')
    title: str = Field(min_length=2, max_length=100)
    seats: int = Field(gt=0, le=500)
    category: str = Field(min_length=2, max_length=50)


class EnrollmentInput(CleanInput):
    code: str = Field(pattern=r'^[A-Za-z0-9-]{2,40}$')
    venue: str = Field(min_length=2, max_length=80)
    state: Literal['confirmed', 'cancelled']
    codes: list[str] = Field(max_length=30)

    @field_validator('codes')
    @classmethod
    def unique_courses(cls, items):
        return sorted(set(items))


class SupplementInput(CleanInput):
    version: int = Field(ge=1, le=1000000)
    venue: str = Field(min_length=2, max_length=80)
    state: Literal['confirmed', 'cancelled']
    codes: list[str] = Field(max_length=30)

    @field_validator('codes')
    @classmethod
    def unique_courses(cls, items):
        return sorted(set(items))


class AnalysisInput(CleanInput):
    title: str = Field(min_length=2, max_length=100)
    course_a: str = Field(max_length=32)
    course_b: str = Field(max_length=32)
    min_venue_n: int = Field(ge=2, le=200, default=12)

    @model_validator(mode='after')
    def check_pair(self):
        if self.course_a == self.course_b:
            raise ValueError('请选择两门不同课程')
        return self


class Publication(CleanInput):
    note: str = Field(min_length=3, max_length=400)
