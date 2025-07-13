# 🧠 MemoryOS Cloud System - Usage Guide

## 🚀 Quick Start

### Start the Complete System
```bash
python run_memory_system.py
```

This will:
- ✅ Test database connection
- ✅ Start backend API on http://localhost:5001
- ✅ Start frontend on http://localhost:8000
- ✅ Automatically open your browser

## 📊 Current Status
- **Total Memories**: 18 (including your migrated data)
- **Database**: Cloud-hosted on Supabase
- **API Status**: Fully operational
- **Frontend**: Web interface available

## 🌐 Access Points

### Frontend Interface
- **URL**: http://localhost:8000
- **Features**: 
  - View all memories
  - Add new memories
  - Search memories
  - Memory network visualization
  - Real-time updates

### Backend API
- **URL**: http://localhost:5001
- **Health Check**: http://localhost:5001/health

## 🔧 API Endpoints

### Core Operations
```bash
# Get all memories
GET /memories

# Add new memory
POST /memories
Body: {"content": "Your memory content"}

# Search memories  
GET /search?q=your-search-term

# Get specific memory
GET /memories/{id}

# Reinforce memory (increase score)
POST /memories/{id}/reinforce
Body: {"strength": 1.0}

# Delete memory
DELETE /memories/{id}
```

### Advanced Features
```bash
# Get memory connections
GET /connections?memory_id={id}

# Add memory connection
POST /connections
Body: {"source_id": 1, "target_id": 2, "strength": 0.8}

# Get database statistics
GET /stats

# Export to JSON
POST /export
Body: {"file_path": "backup.json"}
```

## 💡 Example Usage

### Adding a Memory (PowerShell)
```powershell
Invoke-WebRequest -Uri "http://localhost:5001/memories" -Method POST -Headers @{'Content-Type'='application/json'} -Body '{"content": "I love programming with Python"}'
```

### Searching Memories (PowerShell)
```powershell
Invoke-WebRequest -Uri "http://localhost:5001/search?q=programming" -Method GET
```

### Getting All Memories (PowerShell)
```powershell
Invoke-WebRequest -Uri "http://localhost:5001/memories" -Method GET
```

## 🎯 Your Data

### Current Memories Include:
- Personal information (name: Ethan Curtis)
- Interests (Marvel movies, Iron Man, sharks)
- Aspirations (becoming like Tony Stark, engineering)
- Preferences (concise responses, pizza)
- + Your new test memory!

### Memory Scoring System
- **Initial Score**: 1.0 for new memories
- **Reinforcement**: Scores increase when memories are accessed/relevant
- **Ranking**: Higher scored memories appear first in results

## 🛠 Troubleshooting

### If Backend Doesn't Start
```bash
cd memory-app/backend
python cloud_api.py
```

### If Frontend Doesn't Start
```bash
cd memory-app/frontend
python -m http.server 8000
```

### Check System Health
```bash
curl http://localhost:5001/health
```

## 🔒 Security Note
Your Supabase credentials are hardcoded in the Python files:
- `memory-app/backend/cloud_memory_manager.py`
- `start_cloud_system.py`
- `run_migration.py`

## 🎉 Success!
Your MemoryOS system is now fully operational with cloud storage, real-time updates, and all advanced features working perfectly! 