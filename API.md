# AcadAlert API + Frontend Flow

Base URL (local): `http://localhost:8000`

## 1) Upload CSV
**Endpoint**: `POST /api/upload`

**Request**
- `multipart/form-data`
- Field name: `file`
- File type: `.csv`

**Required CSV Headers**
```
student_id,student_name,attendance_percentage,internal_marks,assignment_submission_rate,semester,risk_score,risk_level
```

**Success Response**
```json
{
  "message": "File uploaded successfully",
  "fileId": "<uuid>",
  "status": "ready"
}
```

**Error Examples**
- Not a CSV
```json
{ "detail": "Only CSV files are allowed." }
```
- Missing columns
```json
{ "detail": "Missing columns: [...]" }
```

---

## 2) Run Predictions (optional)
**Endpoint**: `POST /api/predict-all/{fileId}`

**Success Response (shape)**
```json
{
  "message": "Predictions completed",
  "total": 100,
  "predictions": [
    {
      "student_id": "STU001",
      "risk_level": "LOW",
      "risk_score": 0.18,
      "predicted_at": "2026-03-31T12:00:00Z",
      "file_id": "<uuid>",
      "student_name": "Allison Hill",
      "student_data": {
        "attendance_percentage": 84.9,
        "internal_marks": 98.5,
        "assignment_submission_rate": 66.5,
        "semester": 2
      }
    }
  ]
}
```

---

## 3) Students List
**Endpoint**: `GET /api/students`

---

## 4) Student Details
**Endpoint**: `GET /api/student/{student_id}`

---

## 5) Dashboard Stats
**Endpoint**: `GET /api/dashboard/stats`

---

## 6) Reports (PDF)
**Generate**: `GET /api/report/{student_id}`

**Download**: `GET /api/download-report/{student_id}`

---

## UI Flow (Suggested)
1. User uploads CSV
2. Show success + `fileId`
3. Optionally call `/predict-all/{fileId}`
4. Render dashboard or table with `/students`
5. Student details with `/student/{student_id}`
6. Reports from `/report/{student_id}`
