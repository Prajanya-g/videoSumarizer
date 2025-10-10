# Video Summarizer Frontend

A modern React frontend for the Video Summarizer application with full CRUD operations and authentication.

## ✨ Features

- 🔐 **JWT Authentication** - Secure login/register with token storage
- 📚 **Library Page** - View all video jobs with search and filtering
- 📤 **Upload Page** - Upload videos with progress tracking
- 🎥 **Detail Page** - Watch videos with jump-to segments and transcript
- 👤 **Profile Page** - Manage user account and settings
- 🎨 **Modern UI** - Clean, responsive design with Tailwind CSS
- 🔄 **Real-time Updates** - Live status updates and progress tracking

## 🛠️ Tech Stack

- **React 18** - Modern React with hooks
- **TypeScript** - Type-safe development
- **React Router** - Client-side routing
- **Zustand** - Lightweight state management
- **Axios** - HTTP client with interceptors
- **Tailwind CSS** - Utility-first CSS framework
- **Vite** - Fast build tool and dev server

## 🚀 Quick Start

### Prerequisites

- **Node.js 16+** (recommended 18+)
- **npm or yarn** package manager
- **Backend API** running on http://localhost:8000

### Installation

1. **Install dependencies**
```bash
npm install
```

2. **Start development server**
```bash
npm run dev
```

3. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## 📁 Project Structure

```
src/
├── api/                 # API client and endpoints
│   ├── client.ts       # Axios configuration
│   ├── auth.ts         # Authentication API
│   └── jobs.ts         # Jobs API
├── store/              # State management
│   └── authStore.ts    # Authentication store
├── pages/              # Page components
│   ├── LoginPage.tsx   # Login/Register page
│   ├── LibraryPage.tsx # Job listing page
│   ├── UploadPage.tsx  # Video upload page
│   ├── DetailPage.tsx  # Video detail page
│   └── ProfilePage.tsx # User profile page
├── App.tsx             # Main app component
├── main.tsx            # Entry point
└── index.css           # Global styles
```

## 🎨 Key Features

### Authentication
- **JWT-based login/register** with persistent sessions
- **Auto-logout** on token expiration
- **Protected routes** with automatic redirects

### Video Management
- **Upload interface** with drag-and-drop support
- **Real-time progress** tracking during processing
- **Interactive player** with jump-to-segment navigation
- **Transcript display** with downloadable SRT files

### User Experience
- **Responsive design** optimized for all devices
- **Loading states** and error handling
- **Search and filtering** for job management
- **Accessibility** compliant with WCAG guidelines

## 🔧 Development

### Available Scripts
```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
```

### Environment Variables
```bash
VITE_API_URL=http://localhost:8000  # Backend API URL
```

## 📱 Browser Support

- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

## 📚 Documentation

For detailed development information, see:
- [Main README](../README.md) - Complete project overview
- [API Documentation](../API.md) - Backend API reference
- [Development Guide](../DEVELOPMENT.md) - Development setup and guidelines
- [Deployment Guide](../DEPLOYMENT.md) - Production deployment instructions