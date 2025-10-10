# 🚀 Video Summarizer Deployment Guide

Complete guide for deploying the Video Summarizer application to production.

## 📋 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows
- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: 20GB+ free space
- **CPU**: 2+ cores recommended

### Software Requirements
- **Python**: 3.11+ (3.13 recommended)
- **Node.js**: 16+ (18+ recommended)
- **FFmpeg**: Latest version
- **Docker**: 20.10+ (for containerized deployment)
- **Nginx**: 1.18+ (for reverse proxy)

## 🏗️ Deployment Options

### Option 1: Docker Deployment (Recommended)

#### Using Docker Compose

1. **Clone and configure**
```bash
git clone <repository-url>
cd videoSumarizer
```

2. **Create environment file**
```bash
cat > .env << EOF
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///./video_summarizer.db

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_EXPIRATION_HOURS=24

# CORS Configuration
CORS_ORIGINS=https://your-domain.com,http://localhost:3000

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=False
LOG_LEVEL=INFO
EOF
```

3. **Start services**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Manual Docker Build

1. **Build the image**
```bash
docker build -t video-summarizer .
```

2. **Run the container**
```bash
docker run -d \
  --name video-summarizer \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -e JWT_SECRET=your_secret \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  video-summarizer
```

### Option 2: Manual Deployment

#### Backend Deployment

1. **System setup**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.11 python3.11-venv python3-pip ffmpeg -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

2. **Application setup**
```bash
# Clone repository
git clone <repository-url>
cd videoSumarizer

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from backend.database import create_tables; create_tables()"
```

3. **Create systemd service**
```bash
sudo tee /etc/systemd/system/video-summarizer.service > /dev/null << EOF
[Unit]
Description=Video Summarizer API
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/videoSumarizer
Environment=PATH=/path/to/videoSumarizer/venv/bin
ExecStart=/path/to/videoSumarizer/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable video-summarizer
sudo systemctl start video-summarizer
```

#### Frontend Deployment

1. **Build frontend**
```bash
cd frontend
npm install
npm run build
```

2. **Serve with Nginx**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/videoSumarizer/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔧 Production Configuration

### Environment Variables

Create a production `.env` file:

```bash
# OpenAI Configuration (Required)
OPENAI_API_KEY=your_production_openai_key

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/video_summarizer
# OR for SQLite (development only)
# DATABASE_URL=sqlite:///./video_summarizer.db

# JWT Configuration
JWT_SECRET=your-very-secure-jwt-secret-key-minimum-32-characters
JWT_EXPIRATION_HOURS=24

# CORS Configuration
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=False
LOG_LEVEL=INFO

# File Storage
MAX_FILE_SIZE=500MB
CLEANUP_AFTER_HOURS=168  # 7 days
```

### Database Configuration

#### PostgreSQL (Recommended for Production)

1. **Install PostgreSQL**
```bash
sudo apt install postgresql postgresql-contrib -y
```

2. **Create database and user**
```bash
sudo -u postgres psql
CREATE DATABASE video_summarizer;
CREATE USER video_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE video_summarizer TO video_user;
\q
```

3. **Update DATABASE_URL**
```bash
DATABASE_URL=postgresql://video_user:secure_password@localhost/video_summarizer
```

### Nginx Configuration

Create `/etc/nginx/sites-available/video-summarizer`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # File upload size
    client_max_body_size 500M;
    
    # Frontend static files
    location / {
        root /path/to/videoSumarizer/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # File serving
    location /files/ {
        proxy_pass http://localhost:8000/files/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/video-summarizer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔒 SSL Configuration

### Using Let's Encrypt (Recommended)

1. **Install Certbot**
```bash
sudo apt install certbot python3-certbot-nginx -y
```

2. **Obtain SSL certificate**
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

3. **Auto-renewal**
```bash
sudo crontab -e
# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Monitoring and Logging

### Log Configuration

1. **Create log directory**
```bash
sudo mkdir -p /var/log/video-summarizer
sudo chown www-data:www-data /var/log/video-summarizer
```

2. **Configure log rotation**
```bash
sudo tee /etc/logrotate.d/video-summarizer > /dev/null << EOF
/var/log/video-summarizer/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}
EOF
```

### Health Checks

Create a health check endpoint:

```bash
# Test API health
curl -f http://localhost:8000/health || exit 1

# Test database connection
curl -f http://localhost:8000/api/jobs || exit 1
```

### Monitoring Script

Create `/usr/local/bin/video-summarizer-monitor.sh`:

```bash
#!/bin/bash
# Health check script for Video Summarizer

API_URL="http://localhost:8000"
LOG_FILE="/var/log/video-summarizer/health.log"

# Check if API is responding
if ! curl -f -s "$API_URL/health" > /dev/null; then
    echo "$(date): API health check failed" >> "$LOG_FILE"
    # Restart service
    systemctl restart video-summarizer
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "$(date): Disk usage critical: ${DISK_USAGE}%" >> "$LOG_FILE"
fi
```

Make it executable and add to cron:
```bash
sudo chmod +x /usr/local/bin/video-summarizer-monitor.sh
sudo crontab -e
# Add: */5 * * * * /usr/local/bin/video-summarizer-monitor.sh
```

## 🚀 Cloud Deployment

### AWS Deployment

#### Using EC2

1. **Launch EC2 instance**
   - Instance type: t3.medium or larger
   - OS: Ubuntu 20.04 LTS
   - Security groups: Allow HTTP (80), HTTPS (443), SSH (22)

2. **Configure instance**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3.11 python3.11-venv python3-pip nodejs npm ffmpeg nginx -y

# Clone and setup application
git clone <repository-url>
cd videoSumarizer
# ... follow manual deployment steps
```

3. **Configure security groups**
   - Allow inbound traffic on ports 22, 80, 443
   - Restrict SSH access to your IP

#### Using ECS

1. **Create ECS cluster**
2. **Build and push Docker image**
```bash
# Build image
docker build -t video-summarizer .

# Tag for ECR
docker tag video-summarizer:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/video-summarizer:latest

# Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/video-summarizer:latest
```

3. **Create ECS task definition**
4. **Deploy service**

### Google Cloud Deployment

#### Using Cloud Run

1. **Build and push image**
```bash
# Build image
docker build -t gcr.io/PROJECT_ID/video-summarizer .

# Push to Google Container Registry
docker push gcr.io/PROJECT_ID/video-summarizer
```

2. **Deploy to Cloud Run**
```bash
gcloud run deploy video-summarizer \
  --image gcr.io/PROJECT_ID/video-summarizer \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Azure Deployment

#### Using Container Instances

1. **Build and push image**
```bash
# Build image
docker build -t video-summarizer .

# Tag for Azure Container Registry
docker tag video-summarizer your-registry.azurecr.io/video-summarizer:latest

# Push to ACR
docker push your-registry.azurecr.io/video-summarizer:latest
```

2. **Deploy container instance**
```bash
az container create \
  --resource-group myResourceGroup \
  --name video-summarizer \
  --image your-registry.azurecr.io/video-summarizer:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --environment-variables \
    OPENAI_API_KEY=your_key \
    JWT_SECRET=your_secret
```

## 🔧 Performance Optimization

### Backend Optimization

1. **Use production WSGI server**
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

2. **Database optimization**
```sql
-- Create indexes for better performance
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at);
```

3. **Caching (Redis)**
```bash
# Install Redis
sudo apt install redis-server -y

# Configure Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### Frontend Optimization

1. **Build optimization**
```bash
# Production build with optimizations
npm run build

# Analyze bundle size
npm run build -- --analyze
```

2. **CDN Configuration**
```nginx
# Add CDN headers
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header Vary "Accept-Encoding";
}
```

## 🛡️ Security Hardening

### Server Security

1. **Firewall configuration**
```bash
# Install UFW
sudo apt install ufw -y

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

2. **SSH hardening**
```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Set these options:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

3. **Fail2ban installation**
```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Application Security

1. **Rate limiting implementation**
```python
# Add to backend/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to endpoints
@app.post("/upload")
@limiter.limit("5/minute")
async def upload_video(request: Request, ...):
    # ... existing code
```

2. **Input validation**
```python
# Add file type validation
ALLOWED_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv'}
ALLOWED_MIME_TYPES = {'video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska'}

def validate_video_file(file: UploadFile):
    if not file.filename:
        raise HTTPException(400, "No filename provided")
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type {file_ext} not allowed")
    
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(400, f"MIME type {file.content_type} not allowed")
```

## 📊 Backup and Recovery

### Database Backup

1. **PostgreSQL backup**
```bash
# Create backup script
sudo tee /usr/local/bin/backup-db.sh > /dev/null << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/video-summarizer"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

# Backup database
pg_dump video_summarizer > "$BACKUP_DIR/db_backup_$DATE.sql"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "db_backup_*.sql" -mtime +7 -delete
EOF

sudo chmod +x /usr/local/bin/backup-db.sh

# Add to cron
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-db.sh
```

2. **SQLite backup**
```bash
# For SQLite databases
cp video_summarizer.db "backup_$(date +%Y%m%d_%H%M%S).db"
```

### File Backup

1. **Backup uploaded files**
```bash
# Create backup script for files
sudo tee /usr/local/bin/backup-files.sh > /dev/null << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/video-summarizer/files"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

# Backup data directory
tar -czf "$BACKUP_DIR/files_backup_$DATE.tar.gz" /path/to/videoSumarizer/data/

# Keep only last 7 days
find "$BACKUP_DIR" -name "files_backup_*.tar.gz" -mtime +7 -delete
EOF

sudo chmod +x /usr/local/bin/backup-files.sh
```

## 🔄 Updates and Maintenance

### Application Updates

1. **Create update script**
```bash
sudo tee /usr/local/bin/update-video-summarizer.sh > /dev/null << 'EOF'
#!/bin/bash
cd /path/to/videoSumarizer

# Backup current version
cp -r . ../videoSumarizer-backup-$(date +%Y%m%d_%H%M%S)

# Pull latest changes
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Update frontend
cd frontend
npm install
npm run build

# Restart services
sudo systemctl restart video-summarizer
sudo systemctl reload nginx
EOF

sudo chmod +x /usr/local/bin/update-video-summarizer.sh
```

2. **Automated updates**
```bash
# Add to cron for weekly updates
sudo crontab -e
# Add: 0 3 * * 0 /usr/local/bin/update-video-summarizer.sh
```

## 🆘 Troubleshooting

### Common Issues

1. **Service won't start**
```bash
# Check service status
sudo systemctl status video-summarizer

# Check logs
sudo journalctl -u video-summarizer -f

# Check configuration
sudo nginx -t
```

2. **Database connection issues**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U video_user -d video_summarizer
```

3. **File permission issues**
```bash
# Fix permissions
sudo chown -R www-data:www-data /path/to/videoSumarizer
sudo chmod -R 755 /path/to/videoSumarizer
```

### Performance Issues

1. **High memory usage**
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Restart service if needed
sudo systemctl restart video-summarizer
```

2. **Slow response times**
```bash
# Check disk space
df -h

# Check system load
uptime
top
```

## 📞 Support

For deployment issues:
- Check the main README.md for setup instructions
- Review logs in `/var/log/video-summarizer/`
- Open an issue on GitHub with deployment details
- Include system information and error logs
