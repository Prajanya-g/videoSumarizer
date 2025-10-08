import apiClient from './client';

export interface Job {
  id: number;
  user_id: number;
  title: string | null;
  target_seconds: number;
  status: string;
  original_filename: string | null;
  original_duration: number | null;
  summary_duration: number | null;
  compression_ratio: string | null;
  created_at: string;
  updated_at: string;
  error_message: string | null;
  video_url: string | null;
  thumbnail_url: string | null;
  srt_url: string | null;
}

export interface JobCreateRequest {
  title?: string;
  target_seconds: number;
}

export interface JobUpdateRequest {
  title?: string;
  target_seconds?: number;
}

export interface JobListParams {
  limit?: number;
  offset?: number;
  q?: string;
  status?: string;
}

export interface JobResult {
  status: string;
  video_url?: string;
  jump_to?: {
    segments: Array<{
      start: number;
      end: number;
      text: string;
    }>;
  };
  thumbnail_url?: string;
  srt_url?: string;
  message?: string;
}

export const jobsApi = {
  getJobs: async (params?: JobListParams): Promise<Job[]> => {
    const response = await apiClient.get('/jobs', { params });
    return response.data;
  },

  getJob: async (jobId: number): Promise<Job> => {
    const response = await apiClient.get(`/api/jobs/${jobId}`);
    return response.data;
  },

  createJob: async (file: File, data: JobCreateRequest): Promise<Job> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_seconds', data.target_seconds.toString());
    if (data.title) {
      formData.append('title', data.title);
    }

    const response = await apiClient.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  updateJob: async (jobId: number, data: JobUpdateRequest): Promise<Job> => {
    const response = await apiClient.put(`/jobs/${jobId}`, data);
    return response.data;
  },

  deleteJob: async (jobId: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/jobs/${jobId}`, {
      data: { confirm: true }
    });
    return response.data;
  },

  getJobResult: async (jobId: number): Promise<JobResult> => {
    const response = await apiClient.get(`/result/${jobId}`);
    return response.data;
  }
};
