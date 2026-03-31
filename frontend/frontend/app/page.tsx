// "use client";

// import type { ChangeEvent } from "react";
// import { useState } from "react";

// import { uploadCsv } from "./services/uploadService";

// type UploadStatus = {
//   message: string;
//   fileId: string;
// };

// export default function Home() {
//   const [selectedFile, setSelectedFile] = useState<File | null>(null);
//   const [isLoading, setIsLoading] = useState(false);
//   const [errorMessage, setErrorMessage] = useState<string | null>(null);
//   const [uploadStatus, setUploadStatus] = useState<UploadStatus | null>(null);

//   const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
//     const file = event.target.files?.[0] ?? null;
//     setSelectedFile(file);
//     setErrorMessage(null);
//     setUploadStatus(null);
//   };

//   const handleUpload = async () => {
//     if (!selectedFile) {
//       setErrorMessage("Please select a CSV file to upload.");
//       return;
//     }

//     setIsLoading(true);
//     setErrorMessage(null);
//     setUploadStatus(null);

//     try {
//       const result = await uploadCsv(selectedFile);
//       setUploadStatus({ message: result.message, fileId: result.fileId });
//     } catch (error) {
//       const message =
//         error instanceof Error ? error.message : "Upload failed.";
//       setErrorMessage(message);
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   return (
//     <div className="flex min-h-screen items-center justify-center bg-zinc-50 px-6 py-16 text-zinc-900">
//       <main className="w-full max-w-xl rounded-2xl bg-white p-8 shadow-sm">
//         <div className="flex flex-col gap-3">
//           <h1 className="text-2xl font-semibold">CSV Upload</h1>
//           <p className="text-sm text-zinc-500">
//             Upload a CSV file to the FastAPI backend.
//           </p>
//         </div>

//         <div className="mt-8 flex flex-col gap-4">
//           <input
//             type="file"
//             accept=".csv"
//             onChange={handleFileChange}
//             className="block w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm"
//           />

//           <button
//             type="button"
//             onClick={handleUpload}
//             disabled={isLoading}
//             className="inline-flex items-center justify-center rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-400"
//           >
//             {isLoading ? "Uploading..." : "Upload CSV"}
//           </button>

//           {errorMessage ? (
//             <p className="text-sm text-red-600">{errorMessage}</p>
//           ) : null}
//           {uploadStatus ? (
//             <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
//               <p className="font-medium">{uploadStatus.message}</p>
//               <p className="text-emerald-700">File ID: {uploadStatus.fileId}</p>
//             </div>
//           ) : null}
//         </div>
//       </main>
//     </div>
//   );
// }




"use client";

import type { ChangeEvent } from "react";
import { useState, useEffect } from "react";

// Types
type Student = {
  _id: string;
  student_id: string;
  student_name: string;
  attendance_percentage: number;
  internal_marks: number;
  assignment_submission_rate: number;
  semester: number;
  risk_score?: number;
  risk_level?: string;
};

type StudentDetails = {
  student: Student;
  prediction?: {
    risk_level: string;
    risk_score: number;
    predicted_at: string;
  };
  risk_factors: Array<{
    factor_name: string;
    current_value: number;
    threshold: number;
    impact: string;
  }>;
  suggestions: string[];
};

type DashboardStats = {
  total_students: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  risk_percentages: {
    high: number;
    medium: number;
    low: number;
  };
};

type UploadStatus = {
  message: string;
  fileId: string;
};

// API Functions
const API_BASE = "http://localhost:8000/api";

const uploadCsv = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  
  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Upload failed");
  }
  
  return response.json();
};

const runPredictions = async (fileId: string) => {
  const response = await fetch(`${API_BASE}/predict-all/${fileId}`, {
    method: "POST",
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Prediction failed");
  }
  
  return response.json();
};

const fetchStudents = async (): Promise<Student[]> => {
  const response = await fetch(`${API_BASE}/students`);
  if (!response.ok) throw new Error("Failed to fetch students");
  return response.json();
};

const fetchStudentDetails = async (studentId: string): Promise<StudentDetails> => {
  const response = await fetch(`${API_BASE}/student/${studentId}`);
  if (!response.ok) throw new Error("Failed to fetch student details");
  return response.json();
};

const fetchDashboardStats = async (): Promise<DashboardStats> => {
  const response = await fetch(`${API_BASE}/dashboard/stats`);
  if (!response.ok) throw new Error("Failed to fetch dashboard stats");
  return response.json();
};

const downloadReport = (studentId: string) => {
  window.open(`${API_BASE}/download-report/${studentId}`, "_blank");
};

export default function Home() {
  // State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [selectedStudent, setSelectedStudent] = useState<StudentDetails | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [activeTab, setActiveTab] = useState<"upload" | "dashboard">("upload");

  // Fetch data after predictions are done
  const loadData = async () => {
    try {
      const [studentsData, statsData] = await Promise.all([
        fetchStudents(),
        fetchDashboardStats(),
      ]);
      setStudents(studentsData);
      setStats(statsData);
    } catch (error) {
      console.error("Error loading data:", error);
    }
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    setErrorMessage(null);
    setUploadStatus(null);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setErrorMessage("Please select a CSV file to upload.");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    setUploadStatus(null);

    try {
      // Step 1: Upload CSV
      const uploadResult = await uploadCsv(selectedFile);
      setUploadStatus({ 
        message: uploadResult.message, 
        fileId: uploadResult.fileId 
      });

      // Step 2: Run predictions
      const predictResult = await runPredictions(uploadResult.fileId);
      setUploadStatus(prev => ({
        ...prev!,
        message: `${prev!.message}. Predictions completed for ${predictResult.total} students!`
      }));

      // Step 3: Load dashboard data
      await loadData();
      setActiveTab("dashboard");
      
    } catch (error) {
      const message = error instanceof Error ? error.message : "Upload failed.";
      setErrorMessage(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewStudent = async (studentId: string) => {
    try {
      const details = await fetchStudentDetails(studentId);
      setSelectedStudent(details);
      setShowModal(true);
    } catch (error) {
      console.error("Error fetching student details:", error);
      setErrorMessage("Failed to load student details");
    }
  };

  const getRiskColor = (riskLevel?: string) => {
    switch (riskLevel) {
      case "HIGH":
        return "bg-red-100 text-red-800 border-red-200";
      case "MEDIUM":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "LOW":
        return "bg-green-100 text-green-800 border-green-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getRiskBadge = (riskLevel?: string) => {
    if (!riskLevel) return <span className="text-gray-400">Pending</span>;
    
    const colors = {
      HIGH: "bg-red-500",
      MEDIUM: "bg-yellow-500",
      LOW: "bg-green-500"
    };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold text-white ${colors[riskLevel as keyof typeof colors]}`}>
        {riskLevel}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                AcadAlert 🎓
              </h1>
            </div>
            <div className="flex space-x-4">
              <button
                onClick={() => setActiveTab("upload")}
                className={`px-3 py-2 rounded-md text-sm font-medium transition ${
                  activeTab === "upload"
                    ? "bg-blue-100 text-blue-700"
                    : "text-gray-600 hover:bg-gray-100"
                }`}
              >
                Upload CSV
              </button>
              <button
                onClick={() => setActiveTab("dashboard")}
                className={`px-3 py-2 rounded-md text-sm font-medium transition ${
                  activeTab === "dashboard"
                    ? "bg-blue-100 text-blue-700"
                    : "text-gray-600 hover:bg-gray-100"
                }`}
              >
                Dashboard
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Upload Section */}
        {activeTab === "upload" && (
          <div className="bg-white rounded-xl shadow-sm p-8">
            <div className="flex flex-col gap-3">
              <h2 className="text-2xl font-semibold text-gray-900">Upload Student Data</h2>
              <p className="text-sm text-gray-500">
                Upload a CSV file with student information to generate risk predictions.
              </p>
            </div>

            <div className="mt-8 flex flex-col gap-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition">
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileChange}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer flex flex-col items-center"
                >
                  <svg className="w-12 h-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <span className="text-sm text-gray-600">
                    {selectedFile ? selectedFile.name : "Click to select CSV file"}
                  </span>
                  <span className="text-xs text-gray-400 mt-2">
                    Required: student_id, student_name, attendance_percentage, internal_marks, assignment_submission_rate, semester
                  </span>
                </label>
              </div>

              <button
                type="button"
                onClick={handleUpload}
                disabled={isLoading}
                className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-6 py-3 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-400"
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing...
                  </>
                ) : (
                  "Upload & Analyze"
                )}
              </button>

              {errorMessage && (
                <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                  {errorMessage}
                </div>
              )}
              
              {uploadStatus && (
                <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
                  <p className="font-medium">{uploadStatus.message}</p>
                  <p className="text-green-700 text-xs mt-1">File ID: {uploadStatus.fileId}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Dashboard Section */}
        {activeTab === "dashboard" && (
          <>
            {/* Stats Cards */}
            {stats && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div className="bg-white rounded-xl shadow-sm p-6 border-l-4 border-blue-500">
                  <p className="text-sm text-gray-500">Total Students</p>
                  <p className="text-3xl font-bold text-gray-900">{stats.total_students}</p>
                </div>
                <div className="bg-white rounded-xl shadow-sm p-6 border-l-4 border-red-500">
                  <p className="text-sm text-gray-500">High Risk</p>
                  <p className="text-3xl font-bold text-red-600">{stats.high_risk}</p>
                  <p className="text-xs text-gray-500">{stats.risk_percentages.high}%</p>
                </div>
                <div className="bg-white rounded-xl shadow-sm p-6 border-l-4 border-yellow-500">
                  <p className="text-sm text-gray-500">Medium Risk</p>
                  <p className="text-3xl font-bold text-yellow-600">{stats.medium_risk}</p>
                  <p className="text-xs text-gray-500">{stats.risk_percentages.medium}%</p>
                </div>
                <div className="bg-white rounded-xl shadow-sm p-6 border-l-4 border-green-500">
                  <p className="text-sm text-gray-500">Low Risk</p>
                  <p className="text-3xl font-bold text-green-600">{stats.low_risk}</p>
                  <p className="text-xs text-gray-500">{stats.risk_percentages.low}%</p>
                </div>
              </div>
            )}

            {/* Students Table */}
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Student Risk Analysis</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Student ID</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Attendance</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Internal Marks</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk Level</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk Score</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {students.map((student) => (
                      <tr key={student._id} className="hover:bg-gray-50 transition">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {student.student_id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {student.student_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {student.attendance_percentage}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {student.internal_marks}/100
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getRiskBadge(student.risk_level)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {student.risk_score ? `${(student.risk_score * 100).toFixed(1)}%` : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <button
                            onClick={() => handleViewStudent(student.student_id)}
                            className="text-blue-600 hover:text-blue-800 font-medium"
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {students.length === 0 && (
                  <div className="text-center py-12">
                    <p className="text-gray-500">No students loaded. Please upload a CSV file first.</p>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </main>

      {/* Student Details Modal */}
      {showModal && selectedStudent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900">
                {selectedStudent.student.student_name}
              </h2>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="px-6 py-4 space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Student ID</p>
                  <p className="font-medium">{selectedStudent.student.student_id}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Semester</p>
                  <p className="font-medium">{selectedStudent.student.semester}</p>
                </div>
              </div>

              {/* Academic Performance */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">Academic Performance</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Attendance</span>
                    <span className="font-medium">{selectedStudent.student.attendance_percentage}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${selectedStudent.student.attendance_percentage}%` }}
                    />
                  </div>
                  <div className="flex justify-between mt-3">
                    <span className="text-sm text-gray-600">Internal Marks</span>
                    <span className="font-medium">{selectedStudent.student.internal_marks}/100</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full" 
                      style={{ width: `${selectedStudent.student.internal_marks}%` }}
                    />
                  </div>
                  <div className="flex justify-between mt-3">
                    <span className="text-sm text-gray-600">Assignment Submission</span>
                    <span className="font-medium">{selectedStudent.student.assignment_submission_rate}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-purple-600 h-2 rounded-full" 
                      style={{ width: `${selectedStudent.student.assignment_submission_rate}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Risk Assessment */}
              {selectedStudent.prediction && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">Risk Assessment</h3>
                  <div className={`rounded-lg p-4 ${getRiskColor(selectedStudent.prediction.risk_level)}`}>
                    <div className="flex justify-between items-center">
                      <span className="font-semibold">Risk Level: {selectedStudent.prediction.risk_level}</span>
                      <span className="text-sm">Score: {(selectedStudent.prediction.risk_score * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Risk Factors */}
              {selectedStudent.risk_factors.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">⚠️ Key Risk Factors</h3>
                  <div className="space-y-2">
                    {selectedStudent.risk_factors.map((factor, idx) => (
                      <div key={idx} className="border-l-4 border-red-400 pl-3 py-2 bg-red-50">
                        <p className="font-medium text-sm">{factor.factor_name}</p>
                        <p className="text-sm text-gray-600">
                          Current: {factor.current_value}% | Threshold: {factor.threshold}%
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {selectedStudent.suggestions.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">💡 Recommendations</h3>
                  <ul className="space-y-2">
                    {selectedStudent.suggestions.map((suggestion, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-green-600">✓</span>
                        <span className="text-sm text-gray-700">{suggestion}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Download Report Button */}
              <div className="pt-4 border-t border-gray-200">
                <button
                  onClick={() => downloadReport(selectedStudent.student.student_id)}
                  className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
                >
                  📄 Download Full Report (PDF)
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}