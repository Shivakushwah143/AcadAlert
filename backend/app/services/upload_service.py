# import os
# import uuid
# from datetime import datetime

# import pandas as pd
# from fastapi import UploadFile

# from app.database import predictions_collection, students_collection, uploads_collection

# UPLOAD_DIR = "./uploads"

# os.makedirs(UPLOAD_DIR, exist_ok=True)

# REQUIRED_COLUMNS = [
#     "student_id",
#     "student_name",
#     "attendance_percentage",
#     "internal_marks",
#     "assignment_submission_rate",
#     "semester",
#     "risk_score",
#     "risk_level",
# ]


# def _normalize_risk_level(value: str) -> str:
#     normalized = value.strip().lower()
#     if normalized == "moderate":
#         return "MEDIUM"
#     if normalized == "high":
#         return "HIGH"
#     if normalized == "low":
#         return "LOW"
#     return value.upper()


# async def save_uploaded_csv(file: UploadFile) -> str:
#     """Save uploaded CSV file and store in database"""
#     file_id = str(uuid.uuid4())
#     file_path = os.path.join(UPLOAD_DIR, f"{file_id}.csv")

#     contents = await file.read()
#     with open(file_path, "wb") as handler:
#         handler.write(contents)

#     df = pd.read_csv(file_path)

#     missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
#     if missing_columns:
#         raise ValueError(f"Missing columns: {missing_columns}")

#     students_data = []
#     predictions_data = []

#     for _, row in df.iterrows():
#         risk_level = _normalize_risk_level(str(row["risk_level"]))
#         student_record = {
#             "student_id": str(row["student_id"]),
#             "student_name": str(row["student_name"]),
#             "attendance_percentage": float(row["attendance_percentage"]),
#             "internal_marks": float(row["internal_marks"]),
#             "assignment_submission_rate": float(row["assignment_submission_rate"]),
#             "semester": int(row["semester"]),
#             "risk_score": float(row["risk_score"]),
#             "risk_level": risk_level,
#             "file_id": file_id,
#             "created_at": datetime.utcnow(),
#             "updated_at": datetime.utcnow(),
#         }

#         prediction_record = {
#             "student_id": student_record["student_id"],
#             "risk_level": risk_level,
#             "risk_score": student_record["risk_score"],
#             "predicted_at": datetime.utcnow(),
#             "file_id": file_id,
#             "student_name": student_record["student_name"],
#             "student_data": {
#                 "attendance_percentage": student_record["attendance_percentage"],
#                 "internal_marks": student_record["internal_marks"],
#                 "assignment_submission_rate": student_record[
#                     "assignment_submission_rate"
#                 ],
#                 "semester": student_record["semester"],
#             },
#         }

#         students_data.append(student_record)
#         predictions_data.append(prediction_record)

#     if students_data:
#         await students_collection.insert_many(students_data)
#     if predictions_data:
#         await predictions_collection.insert_many(predictions_data)

#     upload_record = {
#         "file_id": file_id,
#         "filename": file.filename,
#         "uploaded_at": datetime.utcnow(),
#         "record_count": len(students_data),
#         "columns": list(df.columns),
#     }
#     await uploads_collection.insert_one(upload_record)

#     return file_id


import pandas as pd
import uuid
import os
from datetime import datetime
from app.database import students_collection, uploads_collection
from fastapi import UploadFile
import logging

logger = logging.getLogger(__name__)

UPLOAD_DIR = "./uploads"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def save_uploaded_csv(file: UploadFile) -> str:
    """Save uploaded CSV file and store in database"""
    try:
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}.csv")
        
        # Read CSV content
        contents = await file.read()
        
        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Parse CSV with pandas
        df = pd.read_csv(file_path)
        
        # Validate required columns (updated to match new format)
        required_columns = [
            'student_id', 'student_name', 'attendance_percentage', 
            'internal_marks', 'assignment_submission_rate', 'semester'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing columns: {missing_columns}")
        
        # Store student data in MongoDB
        students_data = df.to_dict('records')
        for student in students_data:
            student['created_at'] = datetime.utcnow()
            student['updated_at'] = datetime.utcnow()
            student['file_id'] = file_id
            
            # Ensure numeric fields are proper numbers
            student['attendance_percentage'] = float(student['attendance_percentage'])
            student['internal_marks'] = float(student['internal_marks'])
            student['assignment_submission_rate'] = float(student['assignment_submission_rate'])
            student['semester'] = int(student['semester'])
            
            # Handle optional fields if they exist
            if 'risk_score' in student:
                student['risk_score'] = float(student['risk_score'])
            if 'risk_level' in student:
                student['risk_level'] = student['risk_level'].upper()
        
        await students_collection.insert_many(students_data)
        
        # Store upload record
        upload_record = {
            "file_id": file_id,
            "filename": file.filename,
            "uploaded_at": datetime.utcnow(),
            "record_count": len(students_data),
            "columns": list(df.columns)
        }
        await uploads_collection.insert_one(upload_record)
        
        logger.info(f"✅ CSV uploaded: {file_id} with {len(students_data)} records")
        return file_id
        
    except Exception as e:
        logger.error(f"Error processing CSV: {e}")
        raise Exception(f"Error processing CSV: {str(e)}")