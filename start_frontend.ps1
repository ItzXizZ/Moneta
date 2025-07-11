#!/usr/bin/env pwsh
# Start MemoryOS Frontend Server

Write-Host "🌐 Starting MemoryOS Frontend Server..." -ForegroundColor Green

# Navigate to frontend directory
Set-Location "memory-app\frontend"

# Start HTTP server
try {
    Write-Host "Frontend available at: http://localhost:8000" -ForegroundColor Yellow
    python -m http.server 8000
}
catch {
    Write-Host "❌ Failed to start frontend: $_" -ForegroundColor Red
}
finally {
    # Return to original directory
    Set-Location "..\..\"
} 