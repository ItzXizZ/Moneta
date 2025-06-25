# Moneta - Bringing Elegance to AI

## 🚀 Features

- **Intelligent Memory Search**: Semantic search using sentence transformers
- **Dynamic Memory Reinforcement**: Memories get stronger when recalled frequently
- **Network-based Memory Connections**: Related memories strengthen each other
- **ChatGPT Integration**: Full OpenAI API integration with memory injection
- **Real-time Memory Extraction**: Automatically extracts memories from conversations
- **Web Interface**: Beautiful purple-themed chat interface
- **File Watching**: Real-time memory updates across all components

## 📋 Prerequisites

- Python 3.8+
- OpenAI API Key

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ItzXizZ/Moneta.git
   cd Moneta
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r memory-app/requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   MEMORY_RELEVANCE_THRESHOLD=0.2
   MEMORY_REINFORCEMENT_RATE=0.3
   FLASK_DEBUG=True
   FLASK_PORT=4000
   ```

## 🚀 Usage

### ChatGPT Interface with Memory
```bash
python chatgpt_openai.py
```
Open http://localhost:4000 in your browser

### Memory Management Interface
```bash
cd memory-app/backend
python api.py
```
Open http://localhost:5000 in your browser

### Testing Memory System
```bash
python test_memory_reinforcement.py
python test_chatgpt_reinforcement.py
```

## 🧠 How It Works

### Memory Reinforcement System
- **Direct Recall**: +0-1 points based on relevance score
- **1st Degree Neighbors**: +30% of direct reinforcement
- **2nd Degree Neighbors**: +9% (30% of 30%)
- **3rd Degree Neighbors**: +2.7% (30% of 9%)

### Memory Extraction
- Automatically extracts up to 5 memories per conversation
- Uses OpenAI GPT-3.5 to analyze conversations intelligently
- Formats memories in first-person for consistency

### Similarity Thresholds
- **0.35+**: Minimum for connections
- **0.5-0.7**: Moderate connections (2x weight)
- **0.7+**: Strong connections (3x weight)

## 📁 Project Structure

```
MemoryOS/
├── chatgpt_openai.py          # Main ChatGPT interface
├── memory-app/
│   ├── backend/
│   │   ├── api.py             # Memory management API
│   │   ├── memory_manager.py  # Core memory system
│   │   └── data/
│   │       └── memories.json  # Memory storage
│   ├── frontend/              # Web interface files
│   └── requirements.txt       # Dependencies
├── test_*.py                  # Test files
├── .env                       # Environment variables (create this)
├── .gitignore                 # Git ignore file
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `MEMORY_RELEVANCE_THRESHOLD`: Minimum relevance for memory recall (default: 0.2)
- `MEMORY_REINFORCEMENT_RATE`: Reinforcement propagation rate (default: 0.3)
- `FLASK_DEBUG`: Enable Flask debug mode (default: True)
- `FLASK_PORT`: Port for ChatGPT interface (default: 4000)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

If you encounter any issues:
1. Check that your `.env` file is properly configured
2. Ensure all dependencies are installed
3. Verify your OpenAI API key is valid
4. Check the console for error messages

## 🔮 Future Features

- [ ] Multiple AI model support
- [ ] Memory categories and tagging
- [ ] Export/import functionality
- [ ] Advanced analytics dashboard
- [ ] Memory visualization graphs 
