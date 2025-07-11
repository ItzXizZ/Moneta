#!/usr/bin/env pwsh
# Start MemoryOS Backend API

Write-Host "🚀 Starting MemoryOS Backend API..." -ForegroundColor Green

# Navigate to backend directory
Set-Location "memory-app\backend"

# Start the Flask API server
try {
    python cloud_api.py
}
catch {
    Write-Host "❌ Failed to start backend: $_" -ForegroundColor Red
}
finally {
    # Return to original directory
    Set-Location "..\..\"
} 