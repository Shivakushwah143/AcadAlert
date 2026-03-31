export type UploadResponse = {
  message: string;
  fileId: string;
};

export const uploadCsv = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("http://localhost:8000/api/upload", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Upload failed with status ${response.status}.`);
  }

  return (await response.json()) as UploadResponse;
};
