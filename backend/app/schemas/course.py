from pydantic import BaseModel, UUID4
from typing import List, Optional


class CourseLevelResponse(BaseModel):
    id: UUID4
    order: int
    type: str
    total_steps: int

    status: str
    stars: int

    class Config:
        from_attributes = True


class CourseUnitResponse(BaseModel):
    id: UUID4
    order: int
    topic: str
    description: Optional[str] = None
    icon: Optional[str] = None
    levels: List[CourseLevelResponse] = []

    class Config:
        from_attributes = True


class CourseSectionResponse(BaseModel):
    id: UUID4
    order: int
    title: str
    description: Optional[str] = None
    units: List[CourseUnitResponse] = []

    class Config:
        from_attributes = True


class ActiveCourseResponse(BaseModel):
    enrollment_id: UUID4
    course_template_id: UUID4
    target_language: str
    theme: Optional[str] = None
    cefr_level: str
    sections: List[CourseSectionResponse]


class CourseGenerateRequest(BaseModel):
    interests: List[str] = []
    level: str = "A1"
    regenerate: bool = True


class ProgressUpdateRequest(BaseModel):
    level_template_id: UUID4
    status: Optional[str] = None
    stars: Optional[int] = None
    xp_gained: Optional[int] = None
