# from fastapi import APIRouter, File, HTTPException, UploadFile

# from app.services.upload_service import save_uploaded_csv

# router = APIRouter(prefix="/api", tags=["uploads"])


# @router.post("/upload")
# async def upload_csv(file: UploadFile = File(...)) -> dict:
#     if file.content_type != "text/csv":
#         raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

#     file_id = save_uploaded_csv(file)
#     return {
#         "message": "File uploaded successfully",
#         "fileId": file_id,
#     }


from fastapi import APIRouter, File, HTTPException, UploadFile, BackgroundTasks
from typing import List
from app.services.upload_service import save_uploaded_csv
from app.ml_model import risk_predictor
from app.database import students_collection, predictions_collection
from app.models.student import PredictionRequest, PredictionResponse, DashboardStats
from datetime import datetime
import logging

router = APIRouter(prefix="/api", tags=["uploads"])
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)) -> dict:
    """Upload CSV file with student data"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    try:
        file_id = await save_uploaded_csv(file)
        return {
            "message": "File uploaded successfully",
            "fileId": file_id,
            "status": "processing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict-all/{file_id}")
async def predict_all_students(file_id: str):
    """Run predictions on all students from uploaded file"""
    try:
        # Get all students from this file
        students = await students_collection.find({"file_id": file_id}).to_list(None)
        
        if not students:
            raise HTTPException(status_code=404, detail="No students found for this file")
        
        # Prepare data for prediction
        student_data = []
        for student in students:
            student_data.append({
                "student_id": student["student_id"],
                "name": student["name"],
                "attendance": student["attendance"],
                "assignment_submission": student["assignment_submission"],
                "internal_marks": student["internal_marks"],
                "participation_score": student["participation_score"],
                "backlogs": student["backlogs"],
                "study_hours": student.get("study_hours", 0)
            })
        
        # Get predictions
        predictions = risk_predictor.predict(student_data)
        
        # Store predictions in database
        for pred in predictions:
            pred["predicted_at"] = datetime.utcnow()
            pred["file_id"] = file_id
            
            # Find the student to update
            student = next((s for s in students if s["student_id"] == pred["student_id"]), None)
            if student:
                pred["student_name"] = student["name"]
                pred["student_data"] = {
                    "attendance": student["attendance"],
                    "internal_marks": student["internal_marks"],
                    "assignment_submission": student["assignment_submission"]
                }
            
            await predictions_collection.insert_one(pred)
        
        # Update students with risk levels
        for student, pred in zip(students, predictions):
            await students_collection.update_one(
                {"_id": student["_id"]},
                {"$set": {"risk_level": pred["risk_level"], "risk_score": pred["risk_score"]}}
            )
        
        return {
            "message": "Predictions completed",
            "total": len(predictions),
            "predictions": predictions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/students", response_model=List[dict])
async def get_all_students(skip: int = 0, limit: int = 100):
    """Get all students with their predictions"""
    try:
        students = await students_collection.find().skip(skip).limit(limit).to_list(limit)
        
        # Enrich with predictions
        for student in students:
            prediction = await predictions_collection.find_one(
                {"student_id": student["student_id"]}
            )
            if prediction:
                student["risk_level"] = prediction.get("risk_level")
                student["risk_score"] = prediction.get("risk_score")
        
        # Convert ObjectId to string
        for student in students:
            student["_id"] = str(student["_id"])
        
        return students
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/student/{student_id}")
async def get_student_details(student_id: str):
    """Get detailed information about a specific student"""
    try:
        student = await students_collection.find_one({"student_id": student_id})
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Get predictions
        prediction = await predictions_collection.find_one({"student_id": student_id})
        
        # Get risk factors and suggestions
        risk_factors = []
        suggestions = []
        
        if prediction and prediction.get("risk_level") == "HIGH":
            if student.get("attendance", 100) < 75:
                risk_factors.append({
                    "factor_name": "Attendance",
                    "current_value": student["attendance"],
                    "threshold": 75,
                    "impact": "high"
                })
                suggestions.append("Attend mandatory remedial classes to improve attendance")
            
            if student.get("internal_marks", 100) < 60:
                risk_factors.append({
                    "factor_name": "Internal Marks",
                    "current_value": student["internal_marks"],
                    "threshold": 60,
                    "impact": "high"
                })
                suggestions.append("Schedule weekly tutoring sessions")
            
            if student.get("assignment_submission", 100) < 70:
                risk_factors.append({
                    "factor_name": "Assignment Submission",
                    "current_value": student["assignment_submission"],
                    "threshold": 70,
                    "impact": "medium"
                })
                suggestions.append("Submit pending assignments and meet with academic advisor")
            
            if student.get("backlogs", 0) > 2:
                risk_factors.append({
                    "factor_name": "Backlogs",
                    "current_value": student["backlogs"],
                    "threshold": 2,
                    "impact": "high"
                })
                suggestions.append("Clear backlogs through supplementary examinations")
        
        # Convert ObjectId to string
        student["_id"] = str(student["_id"])
        
        response = {
            "student": student,
            "prediction": prediction,
            "risk_factors": risk_factors,
            "suggestions": suggestions if suggestions else ["Student is on track. Keep up the good work!"]
        }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get aggregated statistics for dashboard"""
    try:
        total_students = await students_collection.count_documents({})
        
        # Get risk distribution
        high_risk = await predictions_collection.count_documents({"risk_level": "HIGH"})
        medium_risk = await predictions_collection.count_documents({"risk_level": "MEDIUM"})
        low_risk = await predictions_collection.count_documents({"risk_level": "LOW"})
        
        # Calculate percentages
        total_predicted = high_risk + medium_risk + low_risk
        risk_percentages = {
            "high": round((high_risk / total_predicted * 100) if total_predicted > 0 else 0, 2),
            "medium": round((medium_risk / total_predicted * 100) if total_predicted > 0 else 0, 2),
            "low": round((low_risk / total_predicted * 100) if total_predicted > 0 else 0, 2)
        }
        
        # Get recent predictions
        recent_predictions = await predictions_collection.find().sort("predicted_at", -1).limit(10).to_list(10)
        
        return DashboardStats(
            total_students=total_students,
            high_risk=high_risk,
            medium_risk=medium_risk,
            low_risk=low_risk,
            risk_percentages=risk_percentages,
            recent_predictions=recent_predictions
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))