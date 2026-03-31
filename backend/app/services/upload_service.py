# from pathlib import Path
# from uuid import uuid4
# import shutil
# from fastapi import UploadFile

# UPLOADS_DIR = Path(__file__).resolve().parents[2] / "uploads"


# def save_uploaded_csv(file: UploadFile) -> str:
#     file_id = str(uuid4())
#     filename = f"{file_id}.csv"
#     target_path = UPLOADS_DIR / filename

#     UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

#     with target_path.open("wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)

#     return file_id


import pandas as pd
import uuid
import os
from datetime import datetime
from app.database import students_collection, uploads_collection
from fastapi import UploadFile

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
        
        # Validate required columns
        required_columns = [
            'student_id', 'name', 'attendance', 'assignment_submission',
            'internal_marks', 'participation_score', 'backlogs'
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
        
        return file_id
        
    except Exception as e:
        raise Exception(f"Error processing CSV: {str(e)}")