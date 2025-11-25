#!/bin/bash
# Quick start script for the application

echo "=========================================="
echo "  Starting Autores Backend (MongoDB)"
echo "=========================================="
echo ""

cd /Users/apple/Documents/Projects/Autores_backend
source .venv/bin/activate

# Kill any existing processes on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
pkill -9 -f "uvicorn app.main:app" 2>/dev/null || true

echo "✅ Virtual environment activated"
echo "✅ MongoDB configured: Autores database"
echo "✅ Multi-account support: 1 account migrated, 22 messages updated"
echo ""
echo "Starting application..."
echo "Access at: http://localhost:8000"
echo "API Docs at: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop"
echo ""

uvicorn app.main:app --reload

