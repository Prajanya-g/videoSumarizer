#!/bin/bash

# Video Summarizer Development Startup Script

echo "🚀 Starting Video Summarizer Development Environment"
echo "=================================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed or not in PATH"
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed or not in PATH"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use"
        return 1
    else
        echo "✅ Port $1 is available"
        return 0
    fi
}

# Check if ports are available
echo "🔍 Checking port availability..."
if ! check_port 8000; then
    echo "❌ Backend port 8000 is in use. Please stop the existing service."
    exit 1
fi

if ! check_port 3000; then
    echo "❌ Frontend port 3000 is in use. Please stop the existing service."
    exit 1
fi

# Initialize database if needed
echo "🗄️  Initializing database..."
if [ ! -f "video_summarizer.db" ]; then
    echo "Creating database..."
    python init_database.py
    if [ $? -eq 0 ]; then
        echo "✅ Database initialized"
    else
        echo "❌ Database initialization failed"
        exit 1
    fi
else
    echo "✅ Database already exists"
fi

# Install frontend dependencies if needed
echo "📦 Checking frontend dependencies..."
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    if [ $? -eq 0 ]; then
        echo "✅ Frontend dependencies installed"
    else
        echo "❌ Frontend dependency installation failed"
        exit 1
    fi
    cd ..
else
    echo "✅ Frontend dependencies already installed"
fi

# Create environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating environment file..."
    cat > .env << EOF
# Database Configuration
DATABASE_URL=sqlite:///./video_summarizer.db

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_EXPIRATION_HOURS=24

# OpenAI API Key (for video processing)
OPENAI_API_KEY=your-openai-api-key-here
EOF
    echo "✅ Environment file created"
else
    echo "✅ Environment file already exists"
fi

echo ""
echo "🎯 Starting services..."
echo ""

# Function to start backend
start_backend() {
    echo "🔧 Starting backend server..."
    python -m backend.main &
    BACKEND_PID=$!
    echo "Backend PID: $BACKEND_PID"
    
    # Wait for backend to start
    echo "⏳ Waiting for backend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/ > /dev/null; then
            echo "✅ Backend is running on http://localhost:8000"
            return 0
        fi
        sleep 1
    done
    
    echo "❌ Backend failed to start"
    return 1
}

# Function to start frontend
start_frontend() {
    echo "🎨 Starting frontend server..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    echo "Frontend PID: $FRONTEND_PID"
    cd ..
    
    # Wait for frontend to start
    echo "⏳ Waiting for frontend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:3000/ > /dev/null; then
            echo "✅ Frontend is running on http://localhost:3000"
            return 0
        fi
        sleep 1
    done
    
    echo "❌ Frontend failed to start"
    return 1
}

# Start backend
if start_backend; then
    echo ""
    # Start frontend
    if start_frontend; then
        echo ""
        echo "🎉 Development environment is ready!"
        echo "=================================="
        echo "🌐 Frontend: http://localhost:3000"
        echo "🔧 Backend:  http://localhost:8000"
        echo ""
        echo "📝 Available endpoints:"
        echo "  - POST /register - User registration"
        echo "  - POST /login - User login"
        echo "  - GET /me - User profile"
        echo "  - GET /jobs - Job listing"
        echo "  - POST /upload - Video upload"
        echo "  - GET /jobs/{id} - Job details"
        echo "  - PUT /jobs/{id} - Update job"
        echo "  - DELETE /jobs/{id} - Delete job"
        echo ""
        echo "🧪 Run tests: python test_end_to_end.py"
        echo ""
        echo "Press Ctrl+C to stop all services"
        
        # Keep script running
        trap 'echo "🛑 Stopping services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT
        wait
    else
        echo "❌ Frontend startup failed"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
else
    echo "❌ Backend startup failed"
    exit 1
fi
