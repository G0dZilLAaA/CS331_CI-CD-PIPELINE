#!/usr/bin/env bash
# Start development environment: Backend + Frontend with one command
# Backend: http://localhost:8000
# Frontend (Vite): http://localhost:5173 — API proxied via /api
# MongoDB: uses MONGODB_URI from your environment/.env

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
log() {
  echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

error() {
  echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Ensure Atlas/local Mongo connection string is configured
check_mongodb_uri() {
  if [ -n "${MONGODB_URI:-}" ]; then
    success "Using configured MongoDB connection string from MONGODB_URI"
    return 0
  fi

  if [ -f ".env" ] && grep -q '^MONGODB_URI=' ".env"; then
    success "Using MongoDB connection string from .env"
    return 0
  fi

  error "MONGODB_URI is not set."
  error "Add your MongoDB Atlas connection string to .env or export MONGODB_URI before running this script."
  return 1
}

# Wait for backend to be ready
wait_for_backend() {
  local max_attempts=30
  local attempt=1
  
  log "Waiting for backend to be ready (http://localhost:8000)..."
  while [ $attempt -le $max_attempts ]; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
      success "Backend is ready!"
      return 0
    fi
    echo -n "."
    sleep 1
    ((attempt++))
  done
  
  error "Backend failed to start"
  return 1
}

cleanup() {
  log "Shutting down services..."
  
  # Only kill processes if they were started
  if [ ! -z "${BACKEND_PID:-}" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  
  if [ ! -z "${FRONTEND_PID:-}" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  
  wait 2>/dev/null || true
  success "All services stopped"
}

# Set up trap for cleanup
trap cleanup INT TERM EXIT

# Check MongoDB connection configuration
log "Checking MongoDB connection settings..."
check_mongodb_uri || exit 1

log "Installing Backend dependencies..."
(cd Backend && npm install > /dev/null 2>&1) &
BACKEND_INSTALL_PID=$!

log "Installing frontend dependencies..."
(cd frontend && npm install > /dev/null 2>&1) &
FRONTEND_INSTALL_PID=$!

wait $BACKEND_INSTALL_PID $FRONTEND_INSTALL_PID
success "Dependencies installed"

log "Starting Backend on port 8000..."
export PORT=8000
(cd Backend && npm start) &
BACKEND_PID=$!

# Wait for backend to be ready
wait_for_backend || {
  kill $BACKEND_PID 2>/dev/null || true
  exit 1
}

log "Starting Frontend on port 5173..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

success "All services started!"
echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}  📱 Frontend: http://localhost:5173${NC}"
echo -e "${GREEN}  🔧 Backend:  http://localhost:8000${NC}"
echo -e "${GREEN}  🗄️  MongoDB:  using MONGODB_URI${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
log "Press Ctrl+C to stop all services"
echo ""

wait "$BACKEND_PID" "$FRONTEND_PID"
