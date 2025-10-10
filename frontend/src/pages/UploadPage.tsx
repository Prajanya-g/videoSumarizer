/**
 * Upload Page Component
 * 
 * Handles video file uploads and initiates the AI-powered summarization process.
 * Provides a user-friendly interface for selecting files, setting parameters,
 * and tracking upload progress.
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { jobsApi } from '../api/jobs';

const UploadPage: React.FC = () => {
  // File selection state
  const [file, setFile] = useState<File | null>(null);
  
  // Job configuration state
  const [title, setTitle] = useState('');  // Optional job title
  const [targetSeconds, setTargetSeconds] = useState(60);  // Target summary duration
  
  // Upload process state
  const [isUploading, setIsUploading] = useState(false);  // Upload in progress flag
  const [uploadProgress, setUploadProgress] = useState(0);  // Progress percentage
  const [error, setError] = useState<string | null>(null);  // Error message
  const [jobId, setJobId] = useState<number | null>(null);  // Created job ID
  
  const navigate = useNavigate();

  /**
   * Handle file selection from input element.
   * 
   * Validates file selection and clears any previous errors.
   */
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);  // Clear any previous errors
    }
  };

  /**
   * Handle form submission for video upload.
   * 
   * Validates file selection, shows upload progress, and creates a new job.
   * Redirects to job detail page upon successful upload.
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate file selection
    if (!file) {
      setError('Please select a video file');
      return;
    }

    try {
      setIsUploading(true);
      setError(null);
      setUploadProgress(0);

      // Simulate upload progress for better UX
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;  // Stop at 90% until actual upload completes
          }
          return prev + 10;
        });
      }, 200);

      // Create job with file and configuration
      const job = await jobsApi.createJob(file, {
        title: title || undefined,
        target_seconds: targetSeconds || 60
      });

      clearInterval(progressInterval);
      setUploadProgress(100);
      setJobId(job.id);

      // Wait a moment then navigate to detail page
      setTimeout(() => {
        navigate(`/detail/${job.id}`);
      }, 1000);

    } catch (err: any) {
      const errorMessage = err.message || err.response?.data?.detail || 'Upload failed';
      setError(errorMessage);
      setUploadProgress(0);
      console.error('Upload error:', err);
    } finally {
      setIsUploading(false);
    }
  };

  /**
   * Render the appropriate upload state component.
   * 
   * Returns the correct UI based on current upload state (uploading, completed, or null).
   */
  const renderUploadState = () => {
    if (isUploading) {
      return (
        <div className="text-center">
          <div className="mb-4">
            <div className="w-16 h-16 mx-auto mb-4">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600"></div>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Uploading Video...
            </h3>
            <p className="text-gray-600 mb-4">
              Please wait while we upload and process your video
            </p>
          </div>
          
          <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
            <div
              className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
          
          <p className="text-sm text-gray-500">
            {uploadProgress}% complete
          </p>
        </div>
      );
    }

    if (jobId) {
      return (
        <div className="text-center">
          <div className="text-green-600 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Upload Complete!
          </h3>
          <p className="text-gray-600 mb-4">
            Your video is being processed. Redirecting to detail page...
          </p>
          <div className="animate-pulse">
            <div className="w-8 h-8 mx-auto bg-indigo-600 rounded-full"></div>
          </div>
        </div>
      );
    }

    return null;
  };

  const handleBack = () => {
    navigate('/library');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Upload Video</h1>
              <p className="text-gray-600">Create a new video summary</p>
            </div>
            <button
              onClick={handleBack}
              className="text-gray-700 hover:text-gray-900"
            >
              ← Back to Library
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          {!isUploading && !jobId ? (
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* File Upload */}
              <div>
                <label htmlFor="fileInput" className="block text-sm font-medium text-gray-700 mb-2">
                  Video File
                </label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                  <input
                    id="fileInput"
                    type="file"
                    accept="video/*"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  <label
                    htmlFor="fileInput"
                    className="cursor-pointer"
                  >
                    {file ? (
                      <div>
                        <div className="text-green-600 mb-2">
                          <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        </div>
                        <p className="text-sm text-gray-900">{file.name}</p>
                        <p className="text-xs text-gray-500">
                          {(file.size / (1024 * 1024)).toFixed(2)} MB
                        </p>
                      </div>
                    ) : (
                      <div>
                        <svg className="w-12 h-12 mx-auto text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
                        </svg>
                        <p className="mt-2 text-sm text-gray-600">
                          Click to upload or drag and drop
                        </p>
                        <p className="text-xs text-gray-500">
                          MP4, MOV, AVI up to 100MB
                        </p>
                      </div>
                    )}
                  </label>
                </div>
              </div>

              {/* Title */}
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                  Title (Optional)
                </label>
                <input
                  type="text"
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Enter video title"
                />
              </div>

              {/* Target Duration */}
              <div>
                <label htmlFor="targetSeconds" className="block text-sm font-medium text-gray-700 mb-2">
                  Target Duration (seconds)
                </label>
                <input
                  type="number"
                  id="targetSeconds"
                  value={targetSeconds}
                  onChange={(e) => {
                    const value = e.target.value;
                    if (value === '') {
                      setTargetSeconds(0);
                    } else {
                      const numValue = parseInt(value);
                      if (!isNaN(numValue)) {
                        setTargetSeconds(numValue);
                      }
                    }
                  }}
                  min="10"
                  max="300"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  How long should the summary be? (10-300 seconds)
                </p>
              </div>

              {error && (
                <div className="text-red-600 text-sm">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={!file}
                className="w-full py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Upload and Process Video
              </button>
            </form>
          ) : renderUploadState()}
        </div>
      </div>
    </div>
  );
};

export default UploadPage;
