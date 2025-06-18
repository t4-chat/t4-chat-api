# 🚀 AI Vibe API - T3 ChatCloneathon Entry

> **Competing in the [T3 ChatCloneathon](https://cloneathon.t3.chat)** - Building the future of AI chat experiences! 🏆

A powerful, feature-rich FastAPI-based AI chat service that brings together multiple LLM providers in one unified platform. Built with ❤️ for the T3 ChatCloneathon competition.

## 🎬 Demo Video

**[🎥 Watch Our Demo Video](https://youtu.be/l3B9tGeLSQg)** - See AI Vibe API in action!

## 🎯 Competition Features

### ✅ Core Requirements (All Implemented!)

- **🤖 Chat with Various LLMs** - Supports 9 major AI providers including OpenAI, Anthropic, Google Gemini, DeepSeek, XAI, Groq, Together AI, Meta Llama, Qwen, and OpenRouter
- **🔐 Authentication & Sync** - Google OAuth integration with full chat history synchronization
- **🌐 Browser Friendly** - RESTful API, perfect for web frontends
- **⚡ Easy to Try** - One-command setup with Docker Compose + comprehensive API documentation

### 🌟 Bonus Features (Going Above & Beyond!)

- **📎 Attachment Support** - File upload and processing capabilities
- **🌐 Web Search** - Real-time web search integration for up-to-date information
- **🎨 Image Generation** - AI-powered image creation capabilities
- **🔧 Tool Calling** - Advanced function calling and tool integration
- **✨ Syntax Highlighting** - Beautiful code formatting and highlighting
- **🌳 Chat Branching** - Create alternative conversation paths
- **💬 Chat Sharing** - Share conversations with others via unique links
- **🔑 Bring Your Own Key** - Support for user-provided API keys
- **📊 Usage Tracking** - Advanced utilization monitoring and budget controls
- **🛡️ Rate Limiting** - Built-in protection against abuse
- **🎨 Admin Dashboard** - Comprehensive admin tools for managing models and usage

## 🏗️ Architecture

```
src/
├── api/           # FastAPI routes and middleware
├── services/      # Business logic layer
├── storage/       # Database models and repositories
├── containers/    # Dependency injection
├── logging/       # Structured logging
├── utils/         # Shared utilities
├── config.py      # Application configuration
└── main.py        # Application entry point
```

## 🚀 Quick Start

### Prerequisites

- 🐍 Python 3.12+
- 🐘 PostgreSQL
- 🐳 Docker & Docker Compose (recommended)

### 1. Clone & Setup Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd t4-chat-api

# Create conda environment
conda create -n t4-chat-api python=3.12
conda activate t4-chat-api

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file with your configuration:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/t4-chat

# Authentication
GOOGLE_CLIENT_ID=your_google_client_id
JWT_SECRET_KEY=your_super_secret_jwt_key
API_KEY_ENCRYPTION_KEY=your_encryption_key

# AI Provider API Keys (add your own or use BYOK feature)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
DEEPSEEK_API_KEY=your_deepseek_key
GEMINI_API_KEY=your_gemini_key
XAI_API_KEY=your_xai_key
GROQ_API_KEY=your_groq_key
TOGETHERAI_API_KEY=your_together_key
LLAMA_API_KEY=your_llama_key
OPENROUTER_API_KEY=your_openrouter_key

# Optional: Cloud Storage
GCP_BUCKET_NAME=your_bucket_name
GCP_PROJECT_ID=your_project_id
```

### 3. Database Setup

**Using Docker (Recommended for Judges!)** 🎯
```bash
# Start PostgreSQL with one command
sh docker-compose.sh
```

**Manual Setup**
```bash

# Run migrations
alembic upgrade head

# Seed with test data (optional)
python scripts/seed_data.py
```

### 4. Run the Application

**Development Mode**
```bash
uvicorn src.main:app --reload --port 9001
```

**Docker Compose (Production-like)**
```bash
docker-compose up -d
```

🎉 **Your API is now running at:** `http://localhost:9001`

## 📚 API Documentation

Once running, explore the full API:

- **📖 Interactive Docs:** `http://localhost:9001/docs`
- **🔧 ReDoc:** `http://localhost:9001/redoc`

## 🔥 Key Features

### Multi-Provider AI Chat
- Support for 9 major AI providers
- Automatic failover and load balancing
- Model-specific optimizations
- Advanced tool calling capabilities

### Advanced Chat Management
- Real-time streaming responses
- **Message branching and selection** - Create alternative conversation paths
- Chat pinning and organization
- Conversation sharing with authentication sync
- **Syntax highlighting** - Beautiful code formatting
- Web search integration
- AI image generation

### Enterprise-Ready
- PostgreSQL with connection pooling
- Comprehensive error handling
- Rate limiting and abuse protection
- OpenTelemetry observability
- Background task processing

### User Experience
- **Google OAuth authentication with full sync** - Complete chat history synchronization across devices
- File upload and processing capabilities
- Beautiful syntax highlighting for code
- Usage tracking and budgets
- Admin dashboard and controls

## 🛠️ Development Commands

### Database Operations
```bash
# Create new migration
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check current version
alembic current

# View migration history
alembic history
```

### Testing & Development
```bash
# Run with auto-reload
uvicorn src.main:app --reload --port 9001

# Set up test environment
python scripts/setup_test_environment.py

# View logs
docker-compose logs -f api
```

## 🏆 Competition Highlights

### Why AI Vibe API Stands Out

1. **🎯 Complete Feature Set** - Implements all core requirements plus numerous bonus features
2. **🏗️ Production-Ready Architecture** - Built with scalability and maintainability in mind
3. **🔧 Easy Setup** - Judges can get it running in minutes with Docker Compose
4. **📊 Rich Features** - Goes beyond basic chat with sharing, admin tools, and advanced management
5. **🌟 Multiple AI Providers** - True multi-LLM support with 9 different providers

### For Judges & Evaluators

```bash
# Quick evaluation setup
git clone <repo-url>
cd t4-chat-api
cp .env.example .env  # Add your API keys
sh docker-compose.sh  # Starts database
docker-compose up -d  # Starts full application
# Visit http://localhost:9001/docs to explore!
```

## 📄 License

Open source under MIT License - built for the T3 ChatCloneathon competition! 🎉

## 🤝 Team

Built with passion for the T3 ChatCloneathon by our amazing team! 

---

*Made with ❤️ for the [T3 ChatCloneathon](https://cloneathon.t3.chat) - Competing for the $10,000+ prize pool! 🏆* 