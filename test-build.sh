#!/bin/bash

echo "=== Universal Docker Build Test ==="
echo "Platform: $(uname -s)"
echo "Shell: $SHELL"

# Check if we're in Windows
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "🔍 Windows environment detected"
    # Convert paths for Windows if needed
    WIN_PATH=$(pwd -W 2>/dev/null || pwd)
    echo "Working directory: $WIN_PATH"
fi

# Common checks
check_file() {
    if [ ! -f "$1" ]; then
        echo "❌ ERROR: $1 not found"
        return 1
    else
        echo "✅ Found: $1"
        return 0
    fi
}

echo ""
echo "📁 Checking required files..."

check_file "Dockerfile.python"
check_file "requirements.txt" 
check_file "main.py"

# Check Docker availability
echo ""
echo "🐳 Checking Docker..."
if command -v docker &> /dev/null; then
    echo "✅ Docker is available"
    docker --version
else
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Build and test
echo ""
echo "🔨 Building Docker image..."
docker build -t universal-test-app -f Dockerfile.python .

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    
    echo "🚀 Testing container..."
    docker run -d --name universal-test-container -p 5000:5000 universal-test-app
    
    echo "⏳ Waiting for startup..."
    sleep 15
    
    # Health check with cross-platform curl
    echo "🏥 Health check..."
    if command -v curl &> /dev/null; then
        curl -s http://localhost:5000/health || echo "⚠️  Health check failed"
    else
        echo "ℹ️  curl not available, skipping health check"
    fi
    
    echo "🧹 Cleaning up..."
    docker stop universal-test-container 2>/dev/null
    docker rm universal-test-container 2>/dev/null
    
else
    echo "❌ Build failed"
    exit 1
fi

echo "=== Test completed ==="
