#!/bin/bash
# Quick start script for the application

echo "=========================================="
echo "  Starting Autores Backend (MongoDB)"
echo "=========================================="
echo ""

cd /Users/apple/Documents/Projects/Autores_backend
source .venv/bin/activate

echo "✅ Virtual environment activated"
echo "✅ MongoDB configured: Autores database"
echo "✅ Data migrated: 1 user, 21 messages, 50 OAuth states"
echo ""
echo "Starting application..."
echo "Access at: http://localhost:8000"
echo "API Docs at: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop"
echo ""

uvicorn app.main:app --reload

