from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class StudentBase(BaseModel):
    student_id: str
    student_name: str
    attendance_percentage: float
    internal_marks: float
    assignment_submission_rate: float
    semester: int
    risk_score: float
    risk_level: RiskLevel


class StudentCreate(StudentBase):
    pass


class StudentResponse(StudentBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class PredictionRequest(BaseModel):
    student_data: List[StudentBase]


class RiskFactors(BaseModel):
    factor_name: str
    current_value: float
    threshold: float
    impact: str


class PredictionResponse(BaseModel):
    student_id: str
    risk_level: RiskLevel
    risk_score: float
    predicted_at: datetime


class DashboardStats(BaseModel):
    total_students: int
    high_risk: int
    medium_risk: int
    low_risk: int
    risk_percentages: dict
    recent_predictions: List[PredictionResponse]
