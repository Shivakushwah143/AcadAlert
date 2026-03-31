# from datetime import datetime
# from typing import List
# import logging

# from fastapi import APIRouter, File, HTTPException, UploadFile

# from app.database import predictions_collection, students_collection
# from app.ml_model import risk_predictor
# from app.models.student import DashboardStats
# from app.services.upload_service import save_uploaded_csv

# router = APIRouter(prefix="/api", tags=["uploads"])
# logger = logging.getLogger(__name__)


# @router.post("/upload")
# async def upload_csv(file: UploadFile = File(...)) -> dict:
#     if not file.filename.endswith(".csv"):
#         raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

#     try:
#         file_id = await save_uploaded_csv(file)
#         return {
#             "message": "File uploaded successfully",
#             "fileId": file_id,
#             "status": "ready",
#         }
#     except ValueError as exc:
#         raise HTTPException(status_code=400, detail=str(exc))
#     except Exception as exc:
#         raise HTTPException(status_code=500, detail=str(exc))


# @router.post("/predict-all/{file_id}")
# async def predict_all_students(file_id: str):
#     try:
#         students = await students_collection.find({"file_id": file_id}).to_list(None)

#         if not students:
#             raise HTTPException(status_code=404, detail="No students found for this file")

#         student_data = []
#         for student in students:
#             student_data.append(
#                 {
#                     "student_id": student["student_id"],
#                     "student_name": student["student_name"],
#                     "attendance_percentage": student["attendance_percentage"],
#                     "internal_marks": student["internal_marks"],
#                     "assignment_submission_rate": student[
#                         "assignment_submission_rate"
#                     ],
#                     "semester": student["semester"],
#                 }
#             )

#         predictions = risk_predictor.predict(student_data)

#         for pred in predictions:
#             pred["predicted_at"] = datetime.utcnow()
#             pred["file_id"] = file_id

#             student = next(
#                 (s for s in students if s["student_id"] == pred["student_id"]),
#                 None,
#             )
#             if student:
#                 pred["student_name"] = student["student_name"]
#                 pred["student_data"] = {
#                     "attendance_percentage": student["attendance_percentage"],
#                     "internal_marks": student["internal_marks"],
#                     "assignment_submission_rate": student[
#                         "assignment_submission_rate"
#                     ],
#                     "semester": student["semester"],
#                 }

#             await predictions_collection.insert_one(pred)

#         for student, pred in zip(students, predictions):
#             await students_collection.update_one(
#                 {"_id": student["_id"]},
#                 {
#                     "$set": {
#                         "risk_level": pred["risk_level"],
#                         "risk_score": pred["risk_score"],
#                     }
#                 },
#             )

#         return {
#             "message": "Predictions completed",
#             "total": len(predictions),
#             "predictions": predictions,
#         }

#     except Exception as exc:
#         raise HTTPException(status_code=500, detail=str(exc))


# @router.get("/students", response_model=List[dict])
# async def get_all_students(skip: int = 0, limit: int = 100):
#     try:
#         students = (
#             await students_collection.find().skip(skip).limit(limit).to_list(limit)
#         )

#         for student in students:
#             prediction = await predictions_collection.find_one(
#                 {"student_id": student["student_id"]}
#             )
#             if prediction:
#                 student["risk_level"] = prediction.get("risk_level")
#                 student["risk_score"] = prediction.get("risk_score")

#         for student in students:
#             student["_id"] = str(student["_id"])

#         return students
#     except Exception as exc:
#         raise HTTPException(status_code=500, detail=str(exc))


# @router.get("/student/{student_id}")
# async def get_student_details(student_id: str):
#     try:
#         student = await students_collection.find_one({"student_id": student_id})
#         if not student:
#             raise HTTPException(status_code=404, detail="Student not found")

#         prediction = await predictions_collection.find_one({"student_id": student_id})

#         risk_factors = []
#         suggestions = []

#         if prediction and prediction.get("risk_level") == "HIGH":
#             if student.get("attendance_percentage", 100) < 75:
#                 risk_factors.append(
#                     {
#                         "factor_name": "Attendance",
#                         "current_value": student["attendance_percentage"],
#                         "threshold": 75,
#                         "impact": "high",
#                     }
#                 )
#                 suggestions.append("Improve attendance to reach 75% or more")

#             if student.get("internal_marks", 100) < 60:
#                 risk_factors.append(
#                     {
#                         "factor_name": "Internal Marks",
#                         "current_value": student["internal_marks"],
#                         "threshold": 60,
#                         "impact": "high",
#                     }
#                 )
#                 suggestions.append("Schedule weekly tutoring sessions")

#             if student.get("assignment_submission_rate", 100) < 70:
#                 risk_factors.append(
#                     {
#                         "factor_name": "Assignment Submission",
#                         "current_value": student["assignment_submission_rate"],
#                         "threshold": 70,
#                         "impact": "medium",
#                     }
#                 )
#                 suggestions.append("Submit pending assignments on time")

#         student["_id"] = str(student["_id"])

#         response = {
#             "student": student,
#             "prediction": prediction,
#             "risk_factors": risk_factors,
#             "suggestions": suggestions
#             if suggestions
#             else ["Student is on track. Keep up the good work!"],
#         }

#         return response
#     except Exception as exc:
#         raise HTTPException(status_code=500, detail=str(exc))


# @router.get("/dashboard/stats", response_model=DashboardStats)
# async def get_dashboard_stats():
#     try:
#         total_students = await students_collection.count_documents({})

#         high_risk = await predictions_collection.count_documents({"risk_level": "HIGH"})
#         medium_risk = await predictions_collection.count_documents(
#             {"risk_level": "MEDIUM"}
#         )
#         low_risk = await predictions_collection.count_documents({"risk_level": "LOW"})

#         total_predicted = high_risk + medium_risk + low_risk
#         risk_percentages = {
#             "high": round((high_risk / total_predicted * 100) if total_predicted else 0, 2),
#             "medium": round(
#                 (medium_risk / total_predicted * 100) if total_predicted else 0, 2
#             ),
#             "low": round((low_risk / total_predicted * 100) if total_predicted else 0, 2),
#         }

#         recent_predictions = (
#             await predictions_collection.find()
#             .sort("predicted_at", -1)
#             .limit(10)
#             .to_list(10)
#         )

#         return DashboardStats(
#             total_students=total_students,
#             high_risk=high_risk,
#             medium_risk=medium_risk,
#             low_risk=low_risk,
#             risk_percentages=risk_percentages,
#             recent_predictions=recent_predictions,
#         )
#     except Exception as exc:
#         raise HTTPException(status_code=500, detail=str(exc))


# @router.get("/report/{student_id}")
# async def generate_report(student_id: str):
#     from app.services.pdf_service import generate_student_report

#     try:
#         student = await students_collection.find_one({"student_id": student_id})
#         if not student:
#             raise HTTPException(status_code=404, detail="Student not found")

#         prediction = await predictions_collection.find_one({"student_id": student_id})

#         risk_factors = []
#         suggestions = []

#         if prediction and prediction.get("risk_level") == "HIGH":
#             if student.get("attendance_percentage", 100) < 75:
#                 risk_factors.append(
#                     {
#                         "factor_name": "Attendance",
#                         "current_value": student["attendance_percentage"],
#                         "threshold": 75,
#                         "impact": "high",
#                     }
#                 )
#                 suggestions.append("Improve attendance to reach 75% or more")

#             if student.get("internal_marks", 100) < 60:
#                 risk_factors.append(
#                     {
#                         "factor_name": "Internal Marks",
#                         "current_value": student["internal_marks"],
#                         "threshold": 60,
#                         "impact": "high",
#                     }
#                 )
#                 suggestions.append("Schedule weekly tutoring sessions")

#             if student.get("assignment_submission_rate", 100) < 70:
#                 risk_factors.append(
#                     {
#                         "factor_name": "Assignment Submission",
#                         "current_value": student["assignment_submission_rate"],
#                         "threshold": 70,
#                         "impact": "medium",
#                     }
#                 )
#                 suggestions.append("Submit pending assignments on time")

#         if not suggestions:
#             suggestions = [
#                 "Continue maintaining good academic performance",
#                 "Participate in co-curricular activities",
#                 "Review progress regularly",
#             ]

#         pdf_path = await generate_student_report(
#             student_data=student,
#             prediction_data=prediction
#             or {"risk_level": "LOW", "risk_score": 0},
#             risk_factors=risk_factors,
#             suggestions=suggestions,
#         )

#         return {
#             "message": "Report generated successfully",
#             "report_path": pdf_path,
#             "download_url": f"/api/download-report/{student_id}",
#         }

#     except Exception as exc:
#         raise HTTPException(status_code=500, detail=str(exc))


# @router.get("/download-report/{student_id}")
# async def download_report(student_id: str):
#     from fastapi.responses import FileResponse
#     import glob
#     import os

#     try:
#         reports_dir = "./reports"
#         pattern = f"report_{student_id}_*.pdf"
#         reports = glob.glob(os.path.join(reports_dir, pattern))

#         if not reports:
#             raise HTTPException(status_code=404, detail="No report found for this student")

#         latest_report = max(reports, key=os.path.getctime)

#         return FileResponse(
#             latest_report,
#             media_type="application/pdf",
#             filename=f"AcadAlert_Report_{student_id}.pdf",
#         )

#     except Exception as exc:
#         raise HTTPException(status_code=500, detail=str(exc))


from fastapi import APIRouter, File, HTTPException, UploadFile, BackgroundTasks
from typing import List
from bson import ObjectId  # Add this import
from app.services.upload_service import save_uploaded_csv
from app.ml_model import risk_predictor
from app.database import students_collection, predictions_collection
from app.models.student import PredictionRequest, PredictionResponse, DashboardStats
from datetime import datetime
import logging

router = APIRouter(prefix="/api", tags=["uploads"])
logger = logging.getLogger(__name__)

# Helper function to convert ObjectId to string
def convert_objectid_to_str(obj):
    """Recursively convert ObjectId to string in a dictionary/list"""
    if isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj

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
            "status": "ready"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict-all/{file_id}")
async def predict_all_students(file_id: str):
    """Run predictions on all students from uploaded file"""
    try:
        students = await students_collection.find({"file_id": file_id}).to_list(None)

        if not students:
            raise HTTPException(status_code=404, detail="No students found for this file")

        student_data = []
        for student in students:
            student_data.append(
                {
                    "student_id": student.get("student_id"),
                    "student_name": student.get("student_name"),
                    "attendance_percentage": student.get("attendance_percentage"),
                    "internal_marks": student.get("internal_marks"),
                    "assignment_submission_rate": student.get("assignment_submission_rate"),
                    "semester": student.get("semester"),
                    "risk_score": student.get("risk_score", 0),
                    "risk_level": student.get("risk_level", "MEDIUM"),
                }
            )

        predictions = risk_predictor.predict(student_data)

        for i, pred in enumerate(predictions):
            pred["predicted_at"] = datetime.utcnow()
            pred["file_id"] = file_id
            pred["student_id"] = student_data[i]["student_id"]
            pred["student_name"] = student_data[i]["student_name"]
            pred["student_data"] = {
                "attendance_percentage": student_data[i]["attendance_percentage"],
                "internal_marks": student_data[i]["internal_marks"],
                "assignment_submission_rate": student_data[i]["assignment_submission_rate"],
                "semester": student_data[i]["semester"],
            }

            await predictions_collection.insert_one(pred)

            await students_collection.update_one(
                {"student_id": student_data[i]["student_id"], "file_id": file_id},
                {
                    "$set": {
                        "risk_level": pred["risk_level"],
                        "risk_score": pred["risk_score"],
                        "predicted_at": datetime.utcnow(),
                    }
                },
            )

        from app.services.pdf_service import generate_student_report

        for student, pred in zip(students, predictions):
            await generate_student_report(
                student_data=student,
                prediction_data=pred,
                risk_factors=[],
                suggestions=[
                    "Continue maintaining good academic performance",
                    "Review progress regularly",
                ],
            )

        response_data = {
            "message": "Predictions completed",
            "total": len(predictions),
            "predictions": convert_objectid_to_str(predictions),
        }

        return response_data

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/students")
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
        
        # Convert ObjectId to string for response
        students = convert_objectid_to_str(students)  # Fix: Convert ObjectIds
        
        return students
    except Exception as e:
        logger.error(f"Error fetching students: {e}")
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
            attendance = student.get("attendance_percentage", 100)
            if attendance < 75:
                risk_factors.append({
                    "factor_name": "Attendance",
                    "current_value": attendance,
                    "threshold": 75,
                    "impact": "high"
                })
                suggestions.append("Attend mandatory remedial classes to improve attendance")
            
            internal_marks = student.get("internal_marks", 100)
            if internal_marks < 60:
                risk_factors.append({
                    "factor_name": "Internal Marks",
                    "current_value": internal_marks,
                    "threshold": 60,
                    "impact": "high"
                })
                suggestions.append("Schedule weekly tutoring sessions")
            
            assignment_rate = student.get("assignment_submission_rate", 100)
            if assignment_rate < 70:
                risk_factors.append({
                    "factor_name": "Assignment Submission",
                    "current_value": assignment_rate,
                    "threshold": 70,
                    "impact": "medium"
                })
                suggestions.append("Submit pending assignments and meet with academic advisor")
        
        # If no risk factors found (low/medium risk), add general suggestions
        if not suggestions:
            suggestions = [
                "Continue maintaining good academic performance",
                "Participate in extra-curricular activities",
                "Consider advanced courses or specializations"
            ]
        
        # Prepare response
        response = {
            "student": convert_objectid_to_str(student),  # Fix: Convert ObjectIds
            "prediction": convert_objectid_to_str(prediction) if prediction else None,  # Fix: Convert ObjectIds
            "risk_factors": risk_factors,
            "suggestions": suggestions
        }
        
        return response
    except Exception as e:
        logger.error(f"Error fetching student details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/stats")
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
        
        # Convert ObjectId to string for response
        recent_predictions = convert_objectid_to_str(recent_predictions)  # Fix: Convert ObjectIds
        
        return {
            "total_students": total_students,
            "high_risk": high_risk,
            "medium_risk": medium_risk,
            "low_risk": low_risk,
            "risk_percentages": risk_percentages,
            "recent_predictions": recent_predictions
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report/{student_id}")
async def generate_report(student_id: str):
    """Generate PDF report for a student"""
    from app.services.pdf_service import generate_student_report
    
    try:
        # Get student data
        student = await students_collection.find_one({"student_id": student_id})
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Get predictions
        prediction = await predictions_collection.find_one({"student_id": student_id})
        
        # Get risk factors and suggestions (reuse logic from get_student_details)
        risk_factors = []
        suggestions = []
        
        if prediction and prediction.get("risk_level") == "HIGH":
            if student.get("attendance_percentage", 100) < 75:
                risk_factors.append({
                    "factor_name": "Attendance",
                    "current_value": student["attendance_percentage"],
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
            
            if student.get("assignment_submission_rate", 100) < 70:
                risk_factors.append({
                    "factor_name": "Assignment Submission",
                    "current_value": student["assignment_submission_rate"],
                    "threshold": 70,
                    "impact": "medium"
                })
                suggestions.append("Submit pending assignments and meet with academic advisor")
        
        if not suggestions:
            suggestions = [
                "Continue maintaining good academic performance",
                "Participate in extra-curricular activities",
                "Consider advanced courses or specializations"
            ]
        
        # Generate PDF
        pdf_path = await generate_student_report(
            student_data=convert_objectid_to_str(student),  # Fix: Convert ObjectIds
            prediction_data=convert_objectid_to_str(prediction) if prediction else {"risk_level": "LOW", "risk_score": 0},
            risk_factors=risk_factors,
            suggestions=suggestions
        )
        
        return {
            "message": "Report generated successfully",
            "report_path": pdf_path,
            "download_url": f"/api/download-report/{student_id}"
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download-report/{student_id}")
async def download_report(student_id: str):
    """Download PDF report for a student"""
    from fastapi.responses import FileResponse
    import os
    import glob
    
    try:
        # Find the latest report for this student
        reports_dir = "./reports"
        pattern = f"report_{student_id}_*.pdf"
        
        reports = glob.glob(os.path.join(reports_dir, pattern))
        
        if not reports:
            raise HTTPException(status_code=404, detail="No report found for this student")
        
        # Get the latest report
        latest_report = max(reports, key=os.path.getctime)
        
        return FileResponse(
            latest_report,
            media_type='application/pdf',
            filename=f"AcadAlert_Report_{student_id}.pdf"
        )
        
    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
