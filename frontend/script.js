/**
 * Frontend JavaScript for Video Summarizer
 */

class VideoSummarizer {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.currentJobId = null;
        this.pollInterval = null;
        this.currentVideo = null;
        
        this.initializeElements();
        this.attachEventListeners();
    }

    initializeElements() {
        // Get DOM elements
        this.fileInput = document.getElementById('fileInput');
        this.targetSeconds = document.getElementById('targetSeconds');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.statusContainer = document.getElementById('statusContainer');
        this.statusMessage = document.getElementById('statusMessage');
        this.progressContainer = document.getElementById('progressContainer');
        this.progressFill = document.getElementById('progressFill');
        this.stage1 = document.getElementById('stage1');
        this.stage2 = document.getElementById('stage2');
        this.stage3 = document.getElementById('stage3');
        this.stage4 = document.getElementById('stage4');
        this.resultContainer = document.getElementById('resultContainer');
        this.resultVideo = document.getElementById('resultVideo');
        this.timestampButtons = document.getElementById('timestampButtons');
        this.errorMessage = document.getElementById('errorMessage');
    }

    attachEventListeners() {
        // File input events
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // Upload button
        this.uploadBtn.addEventListener('click', () => this.uploadFile());
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.selectedFile = file;
            this.uploadBtn.disabled = false;
        }
    }

    async uploadFile() {
        if (!this.selectedFile) {
            this.showError('Please select a file first');
            return;
        }

        // Prevent spam uploads
        if (this.uploadBtn.disabled) {
            return;
        }

        try {
            // Disable upload button and show progress
            this.uploadBtn.disabled = true;
            this.uploadBtn.textContent = 'Processing...';
            this.showProgress(0, 'Uploading video...');
            this.hideMessages();

            const formData = new FormData();
            formData.append('file', this.selectedFile);
            formData.append('target_seconds', this.targetSeconds.value);

            const response = await fetch(`${this.apiBaseUrl}/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Upload failed');
            }

            const result = await response.json();
            this.currentJobId = result.job_id;
            
            this.showProgress(25, 'Video uploaded! Processing started...');
            this.startPolling();

        } catch (error) {
            this.showError(`Upload failed: ${error.message}`);
            this.resetUploadButton();
        }
    }

    async startPolling() {
        this.pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`${this.apiBaseUrl}/result/${this.currentJobId}`);
                if (!response.ok) {
                    throw new Error('Failed to get job status');
                }

                const result = await response.json();
                
                if (result.status === 'done') {
                    this.handleJobCompleted(result);
                } else if (result.status === 'processing') {
                    this.updateStatus('processing');
                } else {
                    this.updateStatus(result.status);
                }

            } catch (error) {
                console.error('Polling error:', error);
                this.showError(`Status check failed: ${error.message}`);
                this.stopPolling();
            }
        }, 2000); // Poll every 2 seconds
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    updateStatus(status) {
        const statusConfig = {
            'uploaded': { message: 'Video uploaded', progress: 25, stage: 1 },
            'processing': { message: 'Processing video...', progress: 50, stage: 2 },
            'transcribing': { message: 'Transcribing audio...', progress: 60, stage: 2 },
            'ranking': { message: 'Analyzing content...', progress: 80, stage: 3 },
            'selecting': { message: 'Selecting key segments...', progress: 85, stage: 3 },
            'rendering': { message: 'Creating highlights...', progress: 95, stage: 4 },
            'completed': { message: 'Highlights ready!', progress: 100, stage: 4 },
            'failed': { message: 'Processing failed', progress: 0, stage: 0 }
        };

        const config = statusConfig[status] || { message: 'Processing...', progress: 50, stage: 2 };
        this.showProgress(config.progress, config.message, config.stage);
    }

    async handleJobCompleted(result) {
        this.stopPolling();
        
        try {
            // Load the result video
            const videoUrl = `${this.apiBaseUrl}${result.video_url}`;
            
            // Set video source
            this.resultVideo.src = videoUrl;
            this.currentVideo = this.resultVideo;
            
            // Show result container immediately
            this.resultContainer.classList.remove('hidden');
            this.resultContainer.style.display = 'block';
            this.progressContainer.classList.add('hidden');
            this.statusContainer.classList.add('hidden');
            
            // Create timestamp buttons if jump_to data exists
            if (result.jump_to && result.jump_to.highlights) {
                this.createTimestampButtons(result.jump_to.highlights);
            }

        } catch (error) {
            console.error('Video load error:', error);
            this.showError(`Failed to load result: ${error.message}`);
        }
    }


    createTimestampButtons(highlights) {
        // Clear existing buttons
        this.timestampButtons.innerHTML = '';
        
        highlights.forEach((highlight, index) => {
            const button = document.createElement('button');
            button.className = 'timestamp-btn';
            button.textContent = `${this.formatTime(highlight.start)} - ${highlight.label}`;
            button.onclick = () => this.jumpToTime(highlight.start);
            this.timestampButtons.appendChild(button);
        });
    }

    jumpToTime(startTime) {
        if (this.currentVideo) {
            this.currentVideo.currentTime = startTime;
            this.currentVideo.play();
        }
    }

    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }

    showStatus(message, type) {
        this.statusMessage.textContent = message;
        this.statusContainer.className = `status-container status-${type}`;
        this.statusContainer.classList.remove('hidden');
    }

    showProgress(percentage, message, activeStage = 0) {
        this.progressFill.style.width = `${percentage}%`;
        this.statusMessage.textContent = message;
        this.statusContainer.className = 'status-container status-processing';
        this.statusContainer.classList.remove('hidden');
        this.progressContainer.classList.remove('hidden');

        // Update stage indicators
        [this.stage1, this.stage2, this.stage3, this.stage4].forEach((stage, index) => {
            stage.classList.remove('active', 'completed');
            if (index < activeStage) {
                stage.classList.add('completed');
            } else if (index === activeStage) {
                stage.classList.add('active');
            }
        });
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.errorMessage.classList.remove('hidden');
    }

    hideMessages() {
        this.errorMessage.classList.add('hidden');
    }

    resetUploadButton() {
        this.uploadBtn.disabled = false;
        this.uploadBtn.textContent = 'Upload & Process';
    }



    // Utility method to reset the interface
    reset() {
        this.currentJobId = null;
        this.selectedFile = null;
        this.currentVideo = null;
        this.stopPolling();
        this.hideMessages();
        this.resultContainer.classList.add('hidden');
        this.statusContainer.classList.add('hidden');
        this.progressContainer.classList.add('hidden');
        this.resetUploadButton();
        this.fileInput.value = '';
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.videoSummarizer = new VideoSummarizer();
});

// Handle page visibility changes to pause/resume polling
document.addEventListener('visibilitychange', () => {
    if (window.videoSummarizer) {
        if (document.hidden) {
            // Page is hidden, could pause polling to save resources
            console.log('Page hidden - polling continues in background');
        } else {
            // Page is visible again
            console.log('Page visible - polling active');
        }
    }
});
