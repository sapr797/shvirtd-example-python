#!/bin/bash

echo "=== Testing Docker Build ==="

# Check if Dockerfile.python exists
if [ ! -f "Dockerfile.python" ]; then
    echo "❌ ERROR: Dockerfile.python not found"
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ ERROR: requirements.txt not found"
    exit 1
fi

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "❌ ERROR: main.py not found"
    exit 1
fi

echo "✅ All required files found"

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t fastapi-app -f Dockerfile.python .

if [ $? -eq 0 ]; then
    echo "✅ Docker build successful"
    
    # Test running the container
    echo "🚀 Testing container startup..."
    docker run -d --name test-app -p 5000:5000 fastapi-app
    
    # Wait for app to start
    sleep 10
    
    # Check if app is responding
    if curl -s http://localhost:5000/health > /dev/null; then
        echo "✅ Application is running and responding"
    else
        echo "⚠️  Application started but health check failed"
    fi
    
    # Cleanup
    echo "🧹 Cleaning up test container..."
    docker stop test-app > /dev/null 2>&1
    docker rm test-app > /dev/null 2>&1
    
else
    echo "❌ Docker build failed"
    exit 1
fi

echo "=== Test completed ==="
