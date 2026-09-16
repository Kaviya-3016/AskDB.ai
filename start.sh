#!/usr/bin/env bash
set -e

echo "========================================================="
echo "Starting QueryCraft AI - Enterprise NLP to SQL Generator"
echo "========================================================="

# Backend Setup
echo "[1/2] Setting up Backend..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
python3 -m app.db.seed
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Frontend Setup
echo "[2/2] Setting up Frontend..."
cd ../frontend
npm install
npm run dev &
FRONTEND_PID=$!

echo "========================================================="
echo "Backend running on http://localhost:8000 (Swagger: /docs)"
echo "Frontend running on http://localhost:5173"
echo "========================================================="

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
