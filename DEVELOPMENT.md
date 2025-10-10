# 🛠️ Video Summarizer Development Guide

Complete guide for developing and contributing to the Video Summarizer project.

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (3.13 recommended)
- **Node.js 16+** (18+ recommended)
- **Git** for version control
- **FFmpeg** for video processing
- **OpenAI API key** for GPT-4 and Whisper access

### Development Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd videoSumarizer
```

2. **Backend setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # If available
```

3. **Frontend setup**
```bash
cd frontend
npm install
```

4. **Environment configuration**
```bash
# Create .env file
cat > .env << EOF
# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///./video_summarizer.db

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_EXPIRATION_HOURS=24

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Development Configuration
DEBUG=True
LOG_LEVEL=DEBUG
EOF
```

5. **Initialize database**
```bash
python -c "from backend.database import create_tables; create_tables()"
```

6. **Start development servers**
```bash
# Terminal 1: Backend
make dev

# Terminal 2: Frontend
cd frontend && npm run dev
```

## 📁 Project Structure

```
videoSumarizer/
├── backend/                    # FastAPI backend
│   ├── main.py                # FastAPI application and routes
│   ├── auth.py                # JWT authentication utilities
│   ├── config.py              # Application configuration
│   ├── database.py            # Database connection and setup
│   ├── models.py              # Pydantic request/response models
│   ├── schemas.py             # SQLAlchemy database models
│   ├── services.py            # Business logic layer
│   ├── pipeline.py            # Video processing pipeline
│   ├── transcribe.py          # Whisper AI transcription
│   ├── ranker_llm.py          # GPT-4 segment ranking
│   ├── render.py              # Video rendering with FFmpeg
│   ├── logging_config.py      # Logging configuration
│   └── tests/                 # Backend tests
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── api/               # API client modules
│   │   │   ├── client.ts      # Axios configuration
│   │   │   ├── auth.ts        # Authentication API
│   │   │   └── jobs.ts        # Jobs API
│   │   ├── pages/             # React page components
│   │   │   ├── LoginPage.tsx  # Login/Register page
│   │   │   ├── LibraryPage.tsx # Job listing page
│   │   │   ├── UploadPage.tsx  # Video upload page
│   │   │   ├── DetailPage.tsx  # Video detail page
│   │   │   └── ProfilePage.tsx # User profile page
│   │   ├── store/             # Zustand state management
│   │   │   └── authStore.ts   # Authentication store
│   │   ├── App.tsx            # Main application component
│   │   ├── main.tsx           # Entry point
│   │   └── index.css          # Global styles
│   ├── package.json           # Frontend dependencies
│   ├── tsconfig.json          # TypeScript configuration
│   └── vite.config.ts         # Vite configuration
├── data/                       # File storage (created at runtime)
├── logs/                       # Application logs
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Container configuration
├── Makefile                    # Development commands
└── README.md                   # Project documentation
```

## 🔧 Development Commands

### Backend Commands

```bash
# Start development server
make dev

# Run tests
make test

# Run linting
make lint

# Format code
make format

# Clean temporary files
make clean

# Database operations
make db-init    # Initialize database
make db-reset   # Reset database
```

### Frontend Commands

```bash
cd frontend

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linting
npm run lint

# Format code
npm run format
```

## 🧪 Testing

### Backend Testing

1. **Run all tests**
```bash
pytest backend/tests/ -v
```

2. **Run specific test file**
```bash
pytest backend/tests/test_auth.py -v
```

3. **Run with coverage**
```bash
pytest backend/tests/ --cov=backend --cov-report=html
```

4. **Test database operations**
```bash
pytest backend/tests/test_database.py -v
```

### Frontend Testing

1. **Run component tests**
```bash
cd frontend
npm test
```

2. **Run with coverage**
```bash
npm run test:coverage
```

3. **Run E2E tests**
```bash
npm run test:e2e
```

### Test Data

Create test data for development:

```python
# backend/tests/fixtures.py
import pytest
from backend.database import get_db
from backend.schemas import User, Job
from backend.services import UserService, JobService

@pytest.fixture
def test_user():
    return {
        "email": "test@example.com",
        "password": "testpassword",
        "full_name": "Test User"
    }

@pytest.fixture
def test_job():
    return {
        "title": "Test Video",
        "target_seconds": 60,
        "status": "uploaded"
    }
```

## 🔍 Code Quality

### Python Code Style

1. **Black formatting**
```bash
# Format all Python files
black backend/

# Check formatting
black --check backend/
```

2. **Flake8 linting**
```bash
# Run linting
flake8 backend/

# Ignore specific rules
flake8 backend/ --ignore=E501,W503
```

3. **Type checking**
```bash
# Run mypy type checking
mypy backend/
```

### TypeScript Code Style

1. **ESLint**
```bash
cd frontend
npm run lint
```

2. **Prettier formatting**
```bash
npm run format
```

3. **Type checking**
```bash
npm run type-check
```

### Pre-commit Hooks

Set up pre-commit hooks:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.55.0
    hooks:
      - id: eslint
        files: \.(js|jsx|ts|tsx)$
        additional_dependencies:
          - eslint@^8.55.0
          - @typescript-eslint/eslint-plugin@^6.0.0
          - @typescript-eslint/parser@^6.0.0
```

## 🏗️ Architecture Patterns

### Backend Architecture

#### Service Layer Pattern
```python
# backend/services.py
class UserService:
    """Service class for user-related database operations."""
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Create a new user account."""
        # Implementation here
        pass
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email address."""
        # Implementation here
        pass
```

#### Repository Pattern
```python
# backend/repositories/user_repository.py
class UserRepository:
    """Repository for user data access."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, user_data: UserCreate) -> User:
        """Create a new user."""
        # Implementation here
        pass
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        # Implementation here
        pass
```

#### Dependency Injection
```python
# backend/main.py
from fastapi import Depends
from backend.database import get_db
from backend.services import UserService

@app.get("/me")
async def get_current_user(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user profile."""
    return current_user
```

### Frontend Architecture

#### Component Structure
```typescript
// frontend/src/components/VideoCard.tsx
interface VideoCardProps {
  job: Job;
  onEdit: (job: Job) => void;
  onDelete: (jobId: number) => void;
}

export const VideoCard: React.FC<VideoCardProps> = ({ job, onEdit, onDelete }) => {
  // Component implementation
};
```

#### Custom Hooks
```typescript
// frontend/src/hooks/useJobs.ts
export const useJobs = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchJobs = useCallback(async () => {
    // Implementation here
  }, []);

  return { jobs, loading, error, fetchJobs };
};
```

#### State Management
```typescript
// frontend/src/store/authStore.ts
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  
  login: async (email: string, password: string) => {
    // Implementation here
  },
  
  logout: () => {
    // Implementation here
  }
}));
```

## 🔄 Development Workflow

### Git Workflow

1. **Create feature branch**
```bash
git checkout -b feature/amazing-feature
```

2. **Make changes and commit**
```bash
git add .
git commit -m "feat: add amazing feature"
```

3. **Push and create PR**
```bash
git push origin feature/amazing-feature
# Create pull request on GitHub
```

### Commit Message Convention

Follow conventional commits:

```
feat: add new feature
fix: bug fix
docs: documentation changes
style: code style changes
refactor: code refactoring
test: add or update tests
chore: maintenance tasks
```

Examples:
- `feat: add video upload progress tracking`
- `fix: resolve authentication token expiration issue`
- `docs: update API documentation`
- `test: add unit tests for user service`

### Code Review Process

1. **Self-review checklist**
   - [ ] Code follows project style guidelines
   - [ ] All tests pass
   - [ ] No linting errors
   - [ ] Documentation updated if needed
   - [ ] Performance implications considered

2. **Review requirements**
   - [ ] At least one approval required
   - [ ] All CI checks must pass
   - [ ] No merge conflicts
   - [ ] Clear description of changes

## 🐛 Debugging

### Backend Debugging

1. **Enable debug logging**
```bash
export DEBUG=True
export LOG_LEVEL=DEBUG
python -m uvicorn backend.main:app --reload
```

2. **Use debugger**
```python
# Add breakpoints
import pdb; pdb.set_trace()

# Or use IDE debugger
```

3. **Check logs**
```bash
tail -f logs/video_summarizer.log
```

### Frontend Debugging

1. **Browser DevTools**
   - Network tab for API calls
   - Console for errors
   - React DevTools for component state

2. **Debug mode**
```bash
# Start with debug mode
npm run dev -- --debug
```

3. **Error boundaries**
```typescript
// frontend/src/components/ErrorBoundary.tsx
class ErrorBoundary extends React.Component {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <h1>Something went wrong.</h1>;
    }

    return this.props.children;
  }
}
```

## 📊 Performance Optimization

### Backend Optimization

1. **Database queries**
```python
# Use eager loading
jobs = db.query(Job).options(joinedload(Job.user)).all()

# Use indexes
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
```

2. **Caching**
```python
# Add Redis caching
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiration=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result))
            return result
        return wrapper
    return decorator
```

3. **Async processing**
```python
# Use background tasks for heavy operations
from fastapi import BackgroundTasks

@app.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    # Start background processing
    background_tasks.add_task(process_video, file)
    return {"message": "Processing started"}
```

### Frontend Optimization

1. **Code splitting**
```typescript
// Lazy load components
const DetailPage = lazy(() => import('./pages/DetailPage'));
const UploadPage = lazy(() => import('./pages/UploadPage'));

// Use Suspense
<Suspense fallback={<LoadingSpinner />}>
  <Routes>
    <Route path="/detail/:id" element={<DetailPage />} />
    <Route path="/upload" element={<UploadPage />} />
  </Routes>
</Suspense>
```

2. **Memoization**
```typescript
// Memoize expensive calculations
const expensiveValue = useMemo(() => {
  return computeExpensiveValue(data);
}, [data]);

// Memoize components
const VideoCard = memo(({ job, onEdit, onDelete }) => {
  // Component implementation
});
```

3. **Virtual scrolling**
```typescript
// For large lists
import { FixedSizeList as List } from 'react-window';

const JobList = ({ jobs }) => (
  <List
    height={600}
    itemCount={jobs.length}
    itemSize={120}
    itemData={jobs}
  >
    {({ index, style, data }) => (
      <div style={style}>
        <VideoCard job={data[index]} />
      </div>
    )}
  </List>
);
```

## 🔒 Security Considerations

### Backend Security

1. **Input validation**
```python
from pydantic import BaseModel, validator

class UserCreate(BaseModel):
    email: str
    password: str
    
    @validator('email')
    def validate_email(cls, v):
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
            raise ValueError('Invalid email format')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
```

2. **SQL injection prevention**
```python
# Use parameterized queries
user = db.query(User).filter(User.email == email).first()

# Never use string formatting
# BAD: f"SELECT * FROM users WHERE email = '{email}'"
```

3. **File upload security**
```python
import magic

def validate_video_file(file: UploadFile):
    # Check file type
    file_type = magic.from_buffer(file.file.read(1024), mime=True)
    if not file_type.startswith('video/'):
        raise HTTPException(400, "File must be a video")
    
    # Check file size
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large")
```

### Frontend Security

1. **XSS prevention**
```typescript
// Sanitize user input
import DOMPurify from 'dompurify';

const sanitizedContent = DOMPurify.sanitize(userContent);
```

2. **CSRF protection**
```typescript
// Include CSRF token in requests
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

axios.defaults.headers.common['X-CSRF-Token'] = csrfToken;
```

3. **Secure storage**
```typescript
// Use secure storage for sensitive data
const secureStorage = {
  setItem: (key: string, value: string) => {
    // Encrypt before storing
    const encrypted = encrypt(value);
    localStorage.setItem(key, encrypted);
  },
  
  getItem: (key: string) => {
    const encrypted = localStorage.getItem(key);
    return encrypted ? decrypt(encrypted) : null;
  }
};
```

## 📚 Documentation

### Code Documentation

1. **Python docstrings**
```python
def process_video(job_id: int, target_seconds: int) -> None:
    """
    Process a video job through the complete pipeline.
    
    Args:
        job_id: The ID of the job to process
        target_seconds: Target duration for the summary video
        
    Raises:
        ValueError: If job_id is invalid
        ProcessingError: If video processing fails
    """
    pass
```

2. **TypeScript JSDoc**
```typescript
/**
 * Upload a video file for processing.
 * 
 * @param file - The video file to upload
 * @param title - Optional title for the job
 * @param targetSeconds - Target duration in seconds
 * @returns Promise resolving to the created job
 */
async function uploadVideo(
  file: File, 
  title?: string, 
  targetSeconds: number = 60
): Promise<Job> {
  // Implementation here
}
```

### API Documentation

1. **OpenAPI/Swagger**
```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="Video Summarizer API",
    description="AI-powered video summarization service",
    version="1.0.0"
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Video Summarizer API",
        version="1.0.0",
        description="AI-powered video summarization service",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

## 🚀 Deployment

### Development Deployment

1. **Local development**
```bash
# Start backend
make dev

# Start frontend
cd frontend && npm run dev
```

2. **Docker development**
```bash
# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

### Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production deployment instructions.

## 🤝 Contributing

### Getting Started

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests**
5. **Submit a pull request**

### Development Guidelines

1. **Code style**
   - Follow existing patterns
   - Use meaningful variable names
   - Add comments for complex logic
   - Keep functions small and focused

2. **Testing**
   - Write tests for new features
   - Maintain test coverage
   - Test edge cases
   - Update tests when changing behavior

3. **Documentation**
   - Update README for new features
   - Add API documentation
   - Include code examples
   - Document breaking changes

### Pull Request Process

1. **Create PR with clear description**
2. **Link related issues**
3. **Include screenshots for UI changes**
4. **Ensure all checks pass**
5. **Request review from maintainers**

## 📞 Support

### Getting Help

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share ideas
- **Documentation**: Check README and API docs
- **Code Review**: Get feedback on your contributions

### Reporting Issues

When reporting issues, include:
- **Environment details**: OS, Python version, Node.js version
- **Steps to reproduce**: Clear reproduction steps
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Logs**: Relevant error logs and stack traces
- **Screenshots**: For UI issues

## 🎯 Roadmap

### Short-term Goals
- [ ] Add comprehensive test coverage
- [ ] Implement rate limiting
- [ ] Add monitoring and metrics
- [ ] Improve error handling
- [ ] Add API versioning

### Long-term Goals
- [ ] Microservices architecture
- [ ] Kubernetes deployment
- [ ] Multi-tenant support
- [ ] Advanced analytics
- [ ] Mobile app development

### Performance Goals
- [ ] Sub-second API response times
- [ ] Support for 4K video processing
- [ ] Real-time processing updates
- [ ] Horizontal scaling
- [ ] CDN integration
