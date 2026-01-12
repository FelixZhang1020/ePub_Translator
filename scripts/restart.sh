#!/bin/bash

# Restart EPUB Translate Services

PROJECT_ROOT="/Users/felixzhang/VibeCoding/epub_translate"

echo "Stopping services..."
pkill -f "uvicorn app.main:app" || true
pkill -f "vite" || true
sleep 1

echo "Starting backend..."
cd "$PROJECT_ROOT/backend"
source venv/bin/activate
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
echo "Backend started"

sleep 2

echo "Starting frontend..."
cd "$PROJECT_ROOT/frontend"
nohup npm run dev > /dev/null 2>&1 &
echo "Frontend started"

echo ""
echo "✅ Services restarted!"
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
