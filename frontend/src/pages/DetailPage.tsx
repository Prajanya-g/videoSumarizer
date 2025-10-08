import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { jobsApi, Job, JobResult } from '../api/jobs';

const DetailPage: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const videoRef = useRef<HTMLVideoElement>(null);
  
  const [job, setJob] = useState<Job | null>(null);
  const [result, setResult] = useState<JobResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editTargetSeconds, setEditTargetSeconds] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (jobId) {
      fetchJobDetails();
    }
  }, [jobId]);

  const fetchJobDetails = async () => {
    try {
      setIsLoading(true);
      const [jobData, resultData] = await Promise.all([
        jobsApi.getJob(parseInt(jobId!)),
        jobsApi.getJobResult(parseInt(jobId!))
      ]);
      setJob(jobData);
      setResult(resultData);
      setEditTitle(jobData.title || '');
      setEditTargetSeconds(jobData.target_seconds);
      setError(null);
    } catch (err: any) {
      const errorMessage = err.message || err.response?.data?.detail || 'Failed to fetch job details';
      setError(errorMessage);
      console.error('Error fetching job details:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = async () => {
    if (!job) return;
    
    try {
      const updatedJob = await jobsApi.updateJob(job.id, {
        title: editTitle,
        target_seconds: editTargetSeconds
      });
      setJob(updatedJob);
      setIsEditing(false);
    } catch (err: any) {
      const errorMessage = err.message || err.response?.data?.detail || 'Failed to update job';
      setError(errorMessage);
      console.error('Error updating job:', err);
    }
  };

  const handleDelete = async () => {
    if (!job || !window.confirm('Are you sure you want to delete this job? This action cannot be undone.')) {
      return;
    }
    
    try {
      setIsDeleting(true);
      await jobsApi.deleteJob(job.id);
      navigate('/library');
    } catch (err: any) {
      const errorMessage = err.message || err.response?.data?.detail || 'Failed to delete job';
      setError(errorMessage);
      setIsDeleting(false);
      console.error('Error deleting job:', err);
    }
  };

  const jumpToSegment = (start: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = start;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'processing':
      case 'transcribing':
      case 'ranking':
      case 'selecting':
      case 'rendering':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'uploaded':
        return 'Uploaded';
      case 'processing':
        return 'Processing';
      case 'transcribing':
        return 'Transcribing';
      case 'ranking':
        return 'Ranking';
      case 'selecting':
        return 'Selecting';
      case 'rendering':
        return 'Rendering';
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      default:
        return status;
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-lg mb-4">Error: {error}</div>
          <button
            onClick={() => navigate('/library')}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
          >
            Back to Library
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <button
                onClick={() => navigate('/library')}
                className="text-indigo-600 hover:text-indigo-500 mb-2"
              >
                ← Back to Library
              </button>
              <h1 className="text-3xl font-bold text-gray-900">
                {isEditing ? (
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    className="border border-gray-300 rounded px-2 py-1"
                  />
                ) : (
                  job.title || job.original_filename || 'Untitled'
                )}
              </h1>
              <div className="flex items-center space-x-4 mt-2">
                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(job.status)}`}>
                  {getStatusText(job.status)}
                </span>
                <span className="text-sm text-gray-500">
                  Created {new Date(job.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
            <div className="flex space-x-2">
              {!isEditing ? (
                <>
                  <button
                    onClick={() => setIsEditing(true)}
                    className="px-4 py-2 text-indigo-600 hover:text-indigo-500"
                  >
                    Edit
                  </button>
                  <button
                    onClick={handleDelete}
                    disabled={isDeleting}
                    className="px-4 py-2 text-red-600 hover:text-red-500 disabled:opacity-50"
                  >
                    {isDeleting ? 'Deleting...' : 'Delete'}
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={handleEdit}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                  >
                    Save
                  </button>
                  <button
                    onClick={() => {
                      setIsEditing(false);
                      setEditTitle(job.title || '');
                      setEditTargetSeconds(job.target_seconds);
                    }}
                    className="px-4 py-2 text-gray-600 hover:text-gray-500"
                  >
                    Cancel
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {job.status === 'completed' && result?.status === 'done' ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Video Player */}
            <div>
              <div className="bg-black rounded-lg overflow-hidden">
                <video
                  ref={videoRef}
                  controls
                  className="w-full h-auto"
                  poster={job.thumbnail_url ? `http://localhost:8000${job.thumbnail_url}` : undefined}
                >
                  <source
                    src={`http://localhost:8000${result.video_url}`}
                    type="video/mp4"
                  />
                  Your browser does not support the video tag.
                </video>
              </div>
              
              {/* Jump-to Segments */}
              {result.jump_to?.segments && (
                <div className="mt-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Jump to Segments</h3>
                  <div className="space-y-2">
                    {result.jump_to.segments.map((segment, index) => (
                      <button
                        key={index}
                        onClick={() => jumpToSegment(segment.start)}
                        className="w-full text-left p-3 bg-white rounded-lg border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 transition-colors"
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <p className="text-sm text-gray-900">{segment.text}</p>
                            <p className="text-xs text-gray-500 mt-1">
                              {Math.floor(segment.start / 60)}:{(segment.start % 60).toFixed(0).padStart(2, '0')} - 
                              {Math.floor(segment.end / 60)}:{(segment.end % 60).toFixed(0).padStart(2, '0')}
                            </p>
                          </div>
                          <div className="ml-2 text-indigo-600">
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M8 5v10l8-5-8-5z" />
                            </svg>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Transcript */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Transcript</h3>
              {result.srt_url ? (
                <div className="bg-white rounded-lg border border-gray-200 p-4">
                  <a
                    href={`http://localhost:8000${result.srt_url}`}
                    download
                    className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 mb-4"
                  >
                    <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                    Download SRT
                  </a>
                  <p className="text-sm text-gray-600">
                    Click the download button to get the full transcript file.
                  </p>
                </div>
              ) : (
                <div className="bg-gray-100 rounded-lg p-4 text-center text-gray-500">
                  Transcript not available
                </div>
              )}
            </div>
          </div>
        ) : job.status === 'failed' ? (
          <div className="text-center py-12">
            <div className="text-red-600 text-lg mb-4">Processing Failed</div>
            {job.error_message && (
              <p className="text-gray-600 mb-4">Error: {job.error_message}</p>
            )}
            <button
              onClick={() => navigate('/library')}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
            >
              Back to Library
            </button>
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {getStatusText(job.status)}
            </h3>
            <p className="text-gray-600">
              Your video is being processed. This may take a few minutes.
            </p>
            <button
              onClick={fetchJobDetails}
              className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
            >
              Refresh Status
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default DetailPage;
