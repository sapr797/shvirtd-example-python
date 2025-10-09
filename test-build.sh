#!/bin/bash

set -e

echo "=== Docker Build and Deploy to /opt ==="
echo "Platform: $(uname -s)"

# Configuration
PROJECT_NAME="universal-test-app"
TARGET_DIR="/opt/$PROJECT_NAME"
REPO_URL="https://github.com/your-username/your-repo.git"  # ЗАМЕНИТЕ на ваш репозиторий

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "❌ This script requires root privileges to write to /opt"
    echo "Please run with: sudo $0"
    exit 1
fi

echo "📁 Target directory: $TARGET_DIR"

# Clean and prepare target directory
echo ""
echo "🧹 Preparing target directory..."
rm -rf "$TARGET_DIR"
mkdir -p "$TARGET_DIR"

# Copy or clone project files
echo ""
echo "📥 Copying project files to /opt..."
if [ -d ".git" ]; then
    # If we're in a git repository, copy all files
    echo "Copying from local git repository..."
    cp -r . "$TARGET_DIR/"
else
    # Clone from repository
    echo "Cloning from repository..."
    git clone "$REPO_URL" "$TARGET_DIR"
fi

# Change to target directory
cd "$TARGET_DIR"

echo "✅ Project copied to $TARGET_DIR"
echo "📋 Files in target directory:"
ls -la "$TARGET_DIR"

# Common checks
check_file() {
    if [ ! -f "$1" ]; then
        echo "❌ ERROR: $1 not found in $TARGET_DIR"
        return 1
    else
        echo "✅ Found: $1"
        return 0
    fi
}

echo ""
echo "📁 Checking required files in $TARGET_DIR..."

check_file "Dockerfile.python" || exit 1
check_file "requirements.txt" || exit 1  
check_file "main.py" || exit 1

# Check Docker availability
echo ""
echo "🐳 Checking Docker..."
if command -v docker &> /dev/null; then
    echo "✅ Docker is available"
    docker --version
    if ! docker info &> /dev/null; then
        echo "❌ Docker daemon is not running"
        exit 1
    fi
else
    echo "❌ Docker not found"
    exit 1
fi

# Build and test from /opt directory
echo ""
echo "🔨 Building Docker image from $TARGET_DIR..."
docker build -t "$PROJECT_NAME" -f Dockerfile.python .

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    
    echo "🚀 Starting container..."
    docker run -d --name "$PROJECT_NAME-container" -p 5000:5000 "$PROJECT_NAME"
    
    echo "⏳ Waiting for startup..."
    sleep 10
    
    echo "🏥 Health check..."
    if command -v curl &> /dev/null; then
        response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health || echo "000")
        if [ "$response" = "200" ]; then
            echo "✅ Health check passed"
        else
            echo "⚠️ Health check failed (HTTP $response)"
            docker logs "$PROJECT_NAME-container"
        fi
    fi
    
    echo ""
    echo "🎉 Deployment completed!"
    echo "📍 Project location: $TARGET_DIR"
    echo "🐳 Container name: $PROJECT_NAME-container"
    echo "🌐 Access: http://localhost:5000"
    
else
    echo "❌ Build failed"
    exit 1
fi

echo "=== Deployment to /opt completed ==="
