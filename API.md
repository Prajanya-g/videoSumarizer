# 📚 Video Summarizer API Documentation

Complete API reference for the Video Summarizer backend service.

## 🔗 Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## 🔐 Authentication

All protected endpoints require a JWT token in the Authorization header:

```bash
Authorization: Bearer <your-jwt-token>
```

## 📋 Endpoints Overview

### Authentication Endpoints
- [POST /register](#post-register) - Register new user
- [POST /login](#post-login) - User login
- [GET /me](#get-me) - Get current user profile
- [PUT /me](#put-me) - Update user profile
- [DELETE /me](#delete-me) - Delete user account

### Video Processing Endpoints
- [POST /upload](#post-upload) - Upload video for processing
- [GET /jobs](#get-jobs) - List user's jobs
- [GET /api/jobs/{job_id}](#get-apijobsjob_id) - Get specific job details
- [PUT /jobs/{job_id}](#put-jobsjob_id) - Update job
- [DELETE /jobs/{job_id}](#delete-jobsjob_id) - Delete job
- [GET /result/{job_id}](#get-resultjob_id) - Get processing results

### File Serving Endpoints
- [GET /files/{job_id}/highlights.mp4](#get-filesjob_idhighlightsmp4) - Download highlights video
- [GET /files/{job_id}/thumb.jpg](#get-filesjob_idthumbjpg) - Download thumbnail
- [GET /files/{job_id}/transcript.srt](#get-filesjob_idtranscriptsrt) - Download transcript

## 🔐 Authentication Endpoints

### POST /register

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `400` - Email already registered
- `422` - Validation error

### POST /login

Authenticate user and get JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401` - Invalid email or password
- `422` - Validation error

### GET /me

Get current user profile.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses:**
- `401` - Invalid or missing token

### PUT /me

Update user profile.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "full_name": "John Smith",
  "email": "newemail@example.com"
}
```

**Response (200):**
```json
{
  "id": 1,
  "email": "newemail@example.com",
  "full_name": "John Smith",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses:**
- `400` - Email already registered
- `401` - Invalid or missing token
- `422` - Validation error

### DELETE /me

Delete user account and all associated jobs.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "confirm": true
}
```

**Response (200):**
```json
{
  "message": "Account deleted successfully"
}
```

**Error Responses:**
- `400` - Confirmation required
- `401` - Invalid or missing token

## 📹 Video Processing Endpoints

### POST /upload

Upload a video file for processing.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Request Body (multipart/form-data):**
- `file` (file) - Video file to process
- `title` (string, optional) - Job title
- `target_seconds` (integer) - Target summary duration in seconds

**Response (200):**
```json
{
  "id": 123,
  "user_id": 1,
  "title": "My Video",
  "target_seconds": 60,
  "status": "uploaded",
  "original_filename": "video.mp4",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "video_url": null,
  "thumbnail_url": null,
  "srt_url": null
}
```

**Error Responses:**
- `400` - File must be a video
- `401` - Invalid or missing token
- `413` - File too large

### GET /jobs

List user's jobs with pagination and filtering.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `limit` (integer, optional) - Number of jobs to return (default: 10, max: 100)
- `offset` (integer, optional) - Number of jobs to skip (default: 0)
- `q` (string, optional) - Search query for title or filename
- `status` (string, optional) - Filter by status (uploaded, processing, completed, failed)

**Example Request:**
```
GET /jobs?limit=20&offset=0&q=presentation&status=completed
```

**Response (200):**
```json
[
  {
    "id": 123,
    "user_id": 1,
    "title": "Presentation Video",
    "target_seconds": 60,
    "status": "completed",
    "original_filename": "presentation.mp4",
    "original_duration": 1800,
    "summary_duration": 58,
    "compression_ratio": "31.0x",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:05:00Z",
    "video_url": "/files/123/highlights.mp4",
    "thumbnail_url": "/files/123/thumb.jpg",
    "srt_url": "/files/123/transcript.srt"
  }
]
```

**Error Responses:**
- `401` - Invalid or missing token

### GET /api/jobs/{job_id}

Get specific job details.

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**
- `job_id` (integer) - Job ID

**Response (200):**
```json
{
  "id": 123,
  "user_id": 1,
  "title": "My Video",
  "target_seconds": 60,
  "status": "completed",
  "original_filename": "video.mp4",
  "original_duration": 1800,
  "summary_duration": 58,
  "compression_ratio": "31.0x",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:05:00Z",
  "video_url": "/files/123/highlights.mp4",
  "thumbnail_url": "/files/123/thumb.jpg",
  "srt_url": "/files/123/transcript.srt"
}
```

**Error Responses:**
- `401` - Invalid or missing token
- `403` - Access denied (not your job)
- `404` - Job not found

### PUT /jobs/{job_id}

Update job title or target duration.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Path Parameters:**
- `job_id` (integer) - Job ID

**Request Body:**
```json
{
  "title": "Updated Title",
  "target_seconds": 90
}
```

**Response (200):**
```json
{
  "id": 123,
  "user_id": 1,
  "title": "Updated Title",
  "target_seconds": 90,
  "status": "completed",
  "original_filename": "video.mp4",
  "original_duration": 1800,
  "summary_duration": 58,
  "compression_ratio": "31.0x",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:05:00Z",
  "video_url": "/files/123/highlights.mp4",
  "thumbnail_url": "/files/123/thumb.jpg",
  "srt_url": "/files/123/transcript.srt"
}
```

**Error Responses:**
- `400` - Validation error
- `401` - Invalid or missing token
- `403` - Access denied
- `404` - Job not found

### DELETE /jobs/{job_id}

Delete job and associated files.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Path Parameters:**
- `job_id` (integer) - Job ID

**Request Body:**
```json
{
  "confirm": true
}
```

**Response (200):**
```json
{
  "message": "Job deleted successfully"
}
```

**Error Responses:**
- `400` - Confirmation required
- `401` - Invalid or missing token
- `403` - Access denied
- `404` - Job not found

### GET /result/{job_id}

Get processing results and metadata.

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**
- `job_id` (integer) - Job ID

**Response (200) - Completed Job:**
```json
{
  "status": "done",
  "video_url": "/files/123/highlights.mp4",
  "jump_to": {
    "segments": [
      {
        "start": 0,
        "end": 15,
        "text": "Welcome to our presentation..."
      }
    ]
  },
  "thumbnail_url": "/files/123/thumb.jpg",
  "srt_url": "/files/123/transcript.srt"
}
```

**Response (200) - Processing Job:**
```json
{
  "status": "processing",
  "message": "Job still processing"
}
```

**Error Responses:**
- `401` - Invalid or missing token
- `403` - Access denied
- `404` - Job not found

## 📁 File Serving Endpoints

### GET /files/{job_id}/highlights.mp4

Download the highlights video.

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**
- `job_id` (integer) - Job ID

**Response (200):**
- Content-Type: `video/mp4`
- File stream of the highlights video

**Error Responses:**
- `401` - Invalid or missing token
- `403` - Access denied
- `404` - File not found

### GET /files/{job_id}/thumb.jpg

Download the thumbnail image.

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**
- `job_id` (integer) - Job ID

**Response (200):**
- Content-Type: `image/jpeg`
- File stream of the thumbnail image

**Error Responses:**
- `401` - Invalid or missing token
- `403` - Access denied
- `404` - File not found

### GET /files/{job_id}/transcript.srt

Download the SRT transcript file.

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**
- `job_id` (integer) - Job ID

**Response (200):**
- Content-Type: `text/plain`
- File stream of the SRT transcript

**Error Responses:**
- `401` - Invalid or missing token
- `403` - Access denied
- `404` - File not found

## 📊 Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created |
| `400` | Bad Request |
| `401` | Unauthorized |
| `403` | Forbidden |
| `404` | Not Found |
| `413` | Payload Too Large |
| `422` | Validation Error |
| `500` | Internal Server Error |

## 🔄 Job Status Values

| Status | Description |
|--------|-------------|
| `uploaded` | Video uploaded, ready for processing |
| `processing` | General processing state |
| `transcribing` | Converting audio to text |
| `ranking` | AI-powered segment ranking |
| `selecting` | Choosing best segments |
| `rendering` | Creating final video |
| `completed` | Processing finished successfully |
| `failed` | Processing encountered an error |

## 🛠️ Error Response Format

All error responses follow this format:

```json
{
  "detail": "Error message description"
}
```

## 📝 Rate Limiting

Currently no rate limiting is implemented. For production deployment, consider implementing rate limiting to prevent abuse.

## 🔒 Security Considerations

- All file uploads are validated for video file types
- JWT tokens expire after 24 hours by default
- CORS is configured for frontend integration
- File access is restricted to job owners only
- Input validation is performed on all endpoints

## 📞 Support

For API issues and questions:
- Check the interactive API documentation at `/docs`
- Review the main README.md for setup instructions
- Open an issue on GitHub for bugs or feature requests
