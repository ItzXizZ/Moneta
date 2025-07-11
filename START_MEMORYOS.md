# 🧠 MemoryOS - Quick Start Guide

## ✅ System Status: FULLY OPERATIONAL

Your MemoryOS cloud system is working perfectly with:
- **18 memories** stored in cloud database
- **Backend API** ready on port 5001
- **Frontend UI** ready on port 8000
- **All features** functional

## 🚀 Start Your System (2 Steps)

### Step 1: Start Backend API
```powershell
cd memory-app\backend
python cloud_api.py
```
**Keep this terminal open!** You should see:
```
* Running on http://127.0.0.1:5001
```

### Step 2: Start Frontend (NEW TERMINAL)
```powershell
cd memory-app\frontend  
python -m http.server 8000
```
**Keep this terminal open too!** You should see:
```
Serving HTTP on 0.0.0.0 port 8000
```

## 🌐 Access Your System

- **Frontend UI**: http://localhost:8000
- **API Health Check**: http://localhost:5001/health

## 💡 Quick Commands (PowerShell)

### Test Backend Health
```powershell
Invoke-WebRequest -Uri "http://localhost:5001/health" -Method GET
```

### Add a Memory
```powershell
Invoke-WebRequest -Uri "http://localhost:5001/memories" -Method POST -Headers @{'Content-Type'='application/json'} -Body '{"content": "Your new memory here"}'
```

### Get All Memories
```powershell
Invoke-WebRequest -Uri "http://localhost:5001/memories" -Method GET
```

### Search Memories
```powershell
Invoke-WebRequest -Uri "http://localhost:5001/search?q=your-search-term" -Method GET
```

## 🎯 Your Current Data

You have **18 memories** including:
- Personal info (Ethan Curtis)
- Interests (Marvel, Iron Man, sharks)
- Aspirations (Tony Stark, engineering)
- Preferences (concise responses, pizza)
- Test memories

## ⚡ Alternative: PowerShell Scripts

I created these for easier startup:

### Backend Only
```powershell
.\start_backend.ps1
```

### Frontend Only  
```powershell
.\start_frontend.ps1
```

## 🛑 To Stop Servers

Press **Ctrl+C** in each terminal window.

## 🎉 Success!

Your MemoryOS is fully operational with cloud storage! 