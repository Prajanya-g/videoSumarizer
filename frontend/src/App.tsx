/**
 * Main App component for the Video Summarizer frontend.
 * 
 * Handles routing, authentication, and application state management.
 * Provides protected and public routes with proper authentication guards.
 */

import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import LoginPage from './pages/LoginPage';
import LibraryPage from './pages/LibraryPage';
import UploadPage from './pages/UploadPage';
import DetailPage from './pages/DetailPage';
import ProfilePage from './pages/ProfilePage';

/**
 * Loading spinner component displayed during authentication checks and app initialization.
 * 
 * Provides a consistent loading experience with animated spinner and loading text.
 */
const LoadingSpinner: React.FC = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="text-center">
      <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600 mx-auto mb-4"></div>
      <p className="text-gray-600">Loading...</p>
    </div>
  </div>
);

/**
 * Protected Route Component - Guards routes that require authentication.
 * 
 * Checks if user is authenticated and has a valid token.
 * Redirects to login page if not authenticated.
 */
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading, token } = useAuthStore();
  
  // Show loading spinner while checking authentication status
  if (isLoading) {
    return <LoadingSpinner />;
  }
  
  // Redirect to login if user is not authenticated or has no token
  if (!isAuthenticated || !token) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

/**
 * Public Route Component - Guards routes that should only be accessible to unauthenticated users.
 * 
 * Redirects authenticated users to the library page to prevent access to login/register
 * when already logged in.
 */
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading, token } = useAuthStore();
  
  // Show loading spinner while checking authentication status
  if (isLoading) {
    return <LoadingSpinner />;
  }
  
  // Redirect authenticated users to library to prevent duplicate login
  if (isAuthenticated && token) {
    return <Navigate to="/library" replace />;
  }
  
  return <>{children}</>;
};

/**
 * Main App component that sets up routing and authentication.
 * 
 * Initializes authentication state on app load and provides routing
 * with proper authentication guards for protected and public routes.
 */
const App: React.FC = () => {
  const { initializeAuth, isLoading } = useAuthStore();

  // Initialize authentication state when app loads
  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  // Show loading spinner while initializing authentication
  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Public Routes - Only accessible when not authenticated */}
          <Route
            path="/login"
            element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            }
          />
          
          {/* Protected Routes - Require authentication */}
          <Route
            path="/library"
            element={
              <ProtectedRoute>
                <LibraryPage />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/upload"
            element={
              <ProtectedRoute>
                <UploadPage />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/detail/:jobId"
            element={
              <ProtectedRoute>
                <DetailPage />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />
          
          {/* Default redirect to library */}
          <Route path="/" element={<Navigate to="/library" replace />} />
          
          {/* Catch all route - redirect unknown paths to library */}
          <Route path="*" element={<Navigate to="/library" replace />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
