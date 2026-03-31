from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class StudentBase(BaseModel):
    student_id: str
    name: str
    attendance: float
    assignment_submission: float
    internal_marks: float
    participation_score: float
    backlogs: int
    study_hours: Optional[float] = None

class StudentCreate(StudentBase):
    pass

class StudentResponse(StudentBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True

class PredictionRequest(BaseModel):
    student_data: List[StudentBase]

class RiskFactors(BaseModel):
    factor_name: str
    current_value: float
    threshold: float
    impact: str  # "high", "medium", "low"

class PredictionResponse(BaseModel):
    student_id: str
    risk_level: RiskLevel
    risk_score: float  # 0-1 score
    risk_factors: List[RiskFactors]
    suggestions: List[str]
    predicted_at: datetime

class DashboardStats(BaseModel):
    total_students: int
    high_risk: int
    medium_risk: int
    low_risk: int
    risk_percentages: dict
    recent_predictions: List[PredictionResponse]


    