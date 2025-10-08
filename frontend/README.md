# Video Summarizer Frontend

A modern React frontend for the Video Summarizer application with full CRUD operations and authentication.

## Features

- 🔐 **JWT Authentication** - Secure login/register with token storage
- 📚 **Library Page** - View all video jobs with search and filtering
- 📤 **Upload Page** - Upload videos with progress tracking
- 🎥 **Detail Page** - Watch videos with jump-to segments and transcript
- 👤 **Profile Page** - Manage user account and settings
- 🎨 **Modern UI** - Clean, responsive design with Tailwind CSS
- 🔄 **Real-time Updates** - Live status updates and progress tracking

## Tech Stack

- **React 18** - Modern React with hooks
- **TypeScript** - Type-safe development
- **React Router** - Client-side routing
- **Zustand** - Lightweight state management
- **Axios** - HTTP client with interceptors
- **Tailwind CSS** - Utility-first CSS framework
- **Vite** - Fast build tool and dev server

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn
- Backend API running on http://localhost:8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open http://localhost:3000 in your browser

### Build for Production

```bash
npm run build
```

## Project Structure

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

## Pages Overview

### 1. Login/Register Page (`/login`)
- **Login Form**: Email and password authentication
- **Register Form**: New user registration with full name
- **Auto-redirect**: Redirects to library if already authenticated
- **Error Handling**: Displays authentication errors

### 2. Library Page (`/library`)
- **Job Grid**: Displays all user's video jobs as cards
- **Search**: Search jobs by title or filename
- **Filtering**: Filter by job status (completed, processing, failed)
- **Pagination**: Limit and offset support
- **Empty State**: "No uploads yet" with call-to-action
- **Status Indicators**: Color-coded job status badges

### 3. Upload Page (`/upload`)
- **File Upload**: Drag-and-drop or click to upload
- **Form Fields**: Title (optional) and target duration
- **Progress Tracking**: Real-time upload progress
- **Validation**: File type and size validation
- **Success Handling**: Auto-redirect to detail page

### 4. Detail Page (`/detail/:jobId`)
- **Video Player**: HTML5 video with controls
- **Jump-to Segments**: Clickable transcript segments
- **Transcript Download**: SRT file download link
- **Job Management**: Edit title, delete job
- **Status Tracking**: Real-time processing status
- **Error Handling**: Failed job error messages

### 5. Profile Page (`/profile`)
- **User Info**: Display user details and account creation date
- **Edit Profile**: Update name and email
- **Account Management**: Delete account with confirmation
- **Logout**: Sign out functionality

## State Management

### Authentication Store (Zustand)
```typescript
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}
```

### Key Features:
- **Persistent Storage**: Auth state persists across browser sessions
- **Auto-logout**: Token expiration handling
- **Error Management**: Centralized error state
- **Loading States**: UI loading indicators

## API Integration

### Authentication Flow
1. **Login/Register** → Store JWT token
2. **Auto-include Token** → Axios request interceptor
3. **Token Validation** → Response interceptor handles 401s
4. **Auto-logout** → Redirect to login on auth failure

### Job Management
- **CRUD Operations**: Create, read, update, delete jobs
- **Real-time Updates**: Polling for status changes
- **File Handling**: Upload progress and error handling
- **Search & Filter**: Query parameters for job listing

## Routing

### Route Structure
```
/ → /library (redirect)
/login → Login/Register page
/library → Job listing page
/upload → Video upload page
/detail/:jobId → Video detail page
/profile → User profile page
```

### Route Protection
- **Protected Routes**: Require authentication
- **Public Routes**: Redirect if already authenticated
- **Auto-redirect**: Seamless navigation flow

## UI/UX Features

### Responsive Design
- **Mobile-first**: Optimized for all screen sizes
- **Grid Layout**: Responsive job cards
- **Navigation**: Mobile-friendly header

### Loading States
- **Spinners**: Loading indicators for async operations
- **Progress Bars**: Upload progress tracking
- **Skeleton Screens**: Placeholder content while loading

### Error Handling
- **Form Validation**: Client-side input validation
- **API Errors**: User-friendly error messages
- **Network Errors**: Connection failure handling
- **404 Pages**: Not found error pages

### Accessibility
- **Keyboard Navigation**: Full keyboard support
- **Screen Readers**: Semantic HTML structure
- **Color Contrast**: WCAG compliant colors
- **Focus Management**: Visible focus indicators

## Development

### Scripts
```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
```

### Environment Variables
```bash
VITE_API_URL=http://localhost:8000  # Backend API URL
```

### Code Style
- **TypeScript**: Strict type checking
- **ESLint**: Code linting and formatting
- **Prettier**: Code formatting
- **Husky**: Pre-commit hooks

## Testing

### Manual Testing
1. **Authentication Flow**: Login, register, logout
2. **Job Management**: Upload, edit, delete jobs
3. **Search & Filter**: Test search and filtering
4. **Responsive Design**: Test on different screen sizes
5. **Error Scenarios**: Network errors, validation errors

### Test Scenarios
- **Happy Path**: Complete user journey
- **Edge Cases**: Empty states, error states
- **Performance**: Large job lists, file uploads
- **Security**: Token handling, XSS prevention

## Deployment

### Build Process
```bash
npm run build
```

### Static Hosting
- **Netlify**: Easy deployment with drag-and-drop
- **Vercel**: Zero-config deployment
- **GitHub Pages**: Free static hosting
- **AWS S3**: Scalable static hosting

### Environment Configuration
- **Development**: http://localhost:3000
- **Production**: Configure API URL
- **CORS**: Backend must allow frontend origin

## Browser Support

- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

## Performance

### Optimization
- **Code Splitting**: Route-based code splitting
- **Lazy Loading**: Dynamic imports for pages
- **Image Optimization**: Responsive images
- **Bundle Analysis**: Webpack bundle analyzer

### Metrics
- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **Time to Interactive**: < 3.5s

## Security

### Best Practices
- **JWT Storage**: Secure token storage
- **XSS Prevention**: Input sanitization
- **CSRF Protection**: Same-origin requests
- **Content Security Policy**: CSP headers

### Authentication
- **Token Expiration**: Automatic logout
- **Secure Storage**: localStorage with validation
- **API Security**: HTTPS-only in production
- **Error Handling**: No sensitive data in errors

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Standards
- **TypeScript**: Use strict typing
- **React Hooks**: Prefer hooks over classes
- **Component Structure**: Functional components
- **Error Handling**: Comprehensive error boundaries

## License

MIT License - see LICENSE file for details.
