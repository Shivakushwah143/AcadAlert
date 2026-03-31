"use client";

import type { ChangeEvent } from "react";
import { useState } from "react";

import { uploadCsv } from "./services/uploadService";

type UploadStatus = {
  message: string;
  fileId: string;
};

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus | null>(null);

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
      const result = await uploadCsv(selectedFile);
      setUploadStatus({ message: result.message, fileId: result.fileId });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Upload failed.";
      setErrorMessage(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 px-6 py-16 text-zinc-900">
      <main className="w-full max-w-xl rounded-2xl bg-white p-8 shadow-sm">
        <div className="flex flex-col gap-3">
          <h1 className="text-2xl font-semibold">CSV Upload</h1>
          <p className="text-sm text-zinc-500">
            Upload a CSV file to the FastAPI backend.
          </p>
        </div>

        <div className="mt-8 flex flex-col gap-4">
          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="block w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm"
          />

          <button
            type="button"
            onClick={handleUpload}
            disabled={isLoading}
            className="inline-flex items-center justify-center rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-400"
          >
            {isLoading ? "Uploading..." : "Upload CSV"}
          </button>

          {errorMessage ? (
            <p className="text-sm text-red-600">{errorMessage}</p>
          ) : null}
          {uploadStatus ? (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
              <p className="font-medium">{uploadStatus.message}</p>
              <p className="text-emerald-700">File ID: {uploadStatus.fileId}</p>
            </div>
          ) : null}
        </div>
      </main>
    </div>
  );
}
