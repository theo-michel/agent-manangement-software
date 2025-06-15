# Agent Management Software

A powerful task orchestration platform built for the **Unaite & Hugging Face Hackathon (June 15th, 2025)**. This project provides an intelligent agent management system with a Trello-like interface for creating, managing, and executing AI-powered tasks with real-world integrations.

## Table of Contents
* [About](#about)
* [Features](#features)
* [Hackathon Information](#hackathon-information)
* [Architecture](#architecture)
* [Setup](#setup)
  * [Installing Required Tools](#installing-required-tools)
  * [Setting Up Environment Variables](#setting-up-environment-variables)
  * [Running the Database](#running-the-database)
  * [Build the project](#build-the-project)
* [Running the Application](#running-the-application)
* [API Endpoints](#api-endpoints)
* [Agent Types](#agent-types)
* [Testing](#testing)
* [Database Migrations](#database-migrations)
* [Project Structure](#project-structure)
* [Contributing](#contributing)

## About

This **Agent Management Software** is our submission for the Unaite & Hugging Face Hackathon on June 15th, 2025. The platform combines artificial intelligence agents with real-world task execution capabilities, featuring a visual Trello-style board interface for managing complex workflows.

The system enables users to:
- Create task cards from natural language prompts using AI
- Execute tasks with specialized agents (research, phone calls, image generation)
- Track task dependencies and execution status
- Integrate with external services (Hugging Face models, phone systems, web search)

## Features

### 🤖 **AI-Powered Task Creation**
- Natural language to structured task conversion
- Intelligent task dependency detection
- Automatic task categorization and prioritization

### 📋 **Visual Task Management**
- Trello-style board interface with drag-and-drop
- Real-time task status updates
- Visual execution progress tracking
- Automated task flow based on dependencies

### 🔍 **Intelligent Agents**
- **Deep Search Agent**: Web research with comprehensive analysis
- **New Card Agent**: Task creation from natural language prompts
- **Image Generation Agent**: AI-powered image creation using Stable Diffusion
- **Phone Call Agent**: Automated outbound calls with real phone integration

### 🎯 **Real-World Integrations**
- **Hugging Face**: Image generation with Stable Diffusion XL
- **Anthropic Claude**: Advanced language processing
- **Web Search**: DuckDuckGo integration for research tasks
- **Phone System**: Real phone call capabilities via VAPI
- **Database**: Persistent task and execution tracking

### ⚡ **Advanced Execution Features**
- Asynchronous task processing
- Execution time tracking and performance metrics
- Error handling and retry mechanisms
- Real-time status updates and notifications

## Hackathon Information

**Event**: Unaite & Hugging Face Hackathon  
**Date**: June 15th, 2025  
**Theme**: Agent Management and Task Orchestration  

This project demonstrates the integration of multiple AI services and real-world APIs to create a comprehensive agent management platform that can handle complex multi-step workflows.

## Architecture

### Backend Stack
- **[FastAPI](https://fastapi.tiangolo.com/)**: High-performance Python web framework
- **[SQLAlchemy](https://www.sqlalchemy.org/)**: Database ORM for task persistence
- **[PostgreSQL](https://www.postgresql.org/)**: Primary database for task storage
- **[Pydantic](https://docs.pydantic.dev/)**: Data validation and serialization
- **[Anthropic Claude](https://www.anthropic.com/)**: Advanced language processing
- **[Hugging Face](https://huggingface.co/)**: Image generation models
- **[SmolaAgents](https://github.com/huggingface/smolagents)**: Agent framework
- **[VAPI](https://vapi.ai/)**: Phone call integration
- **[uv](https://docs.astral.sh/uv/)**: Fast Python package management

### Frontend Stack
- **[Next.js 15](https://nextjs.org/)**: React framework with App Router
- **[React 19](https://react.dev/)**: Latest React with concurrent features
- **[TypeScript](https://www.typescriptlang.org/)**: Type-safe development
- **[Tailwind CSS](https://tailwindcss.com/)**: Utility-first styling
- **[Shadcn/ui](https://ui.shadcn.com/)**: Modern React components
- **[DND Kit](https://dndkit.com/)**: Drag-and-drop functionality
- **[Framer Motion](https://www.framer.com/motion/)**: Smooth animations

### Integration Services
- **Hugging Face Inference API**: For image generation with billing to "agents-hack"
- **Anthropic Claude Sonnet 4**: For advanced text processing and task creation
- **DuckDuckGo Search**: For web research capabilities
- **VAPI**: For real phone call integrations

## Setup

### Installing Required Tools

#### 1. uv
Install uv for Python dependency management:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 2. Node.js and pnpm
Install Node.js from [nodejs.org](https://nodejs.org/), then install pnpm:
```bash
npm install -g pnpm
```

#### 3. Docker
Install Docker from [docker.com](https://www.docker.com/) for containerized database.

### Setting Up Environment Variables

**Backend (`backend/.env`)**:
```bash
cd backend && cp .env.example .env
```

Required environment variables:
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/agent_management

# AI Services
ANTHROPIC_API_KEY=your_anthropic_api_key_here
HF_TOKEN=your_hugging_face_token_here

# Phone Integration
VAPI_API_KEY=your_vapi_api_key_here
VAPI_PHONE_NUMBER_ID=your_vapi_phone_number_id

# API Configuration
CORS_ORIGINS=["http://localhost:3000"]
OPENAPI_URL=/openapi.json
```

**Frontend (`nextjs-frontend/.env.local`)**:
```bash
cd nextjs-frontend && cp .env.example .env.local
```

```bash
API_BASE_URL=http://localhost:8000
```

### Running the Database

Start PostgreSQL with Docker:
```bash
docker compose up -d db
```

Apply database migrations:
```bash
pnpm db:migrate
```

### Build the Project

#### Backend
```bash
cd backend
uv sync
```

#### Frontend
```bash
cd nextjs-frontend
pnpm install
```

## Running the Application

### Start Backend
```bash
make start-backend
# or manually: cd backend && uv run uvicorn app.main:app --reload
```

### Start Frontend
```bash
make start-frontend
# or manually: cd nextjs-frontend && pnpm dev
```

### Access Points
- **Frontend Application**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## API Endpoints

### Core Endpoints

#### `/chat/agent` - Generic Agent Processing
```bash
POST /chat/agent
{
  "prompt": "Analyze the current AI market trends",
  "context": {}
}
```

#### `/chat/new-card` - Task Card Creation
```bash
POST /chat/new-card
{
  "prompt": "Research the German EV market and call the team with results"
}
```

#### `/chat/deep-search` - Web Research
```bash
POST /chat/deep-search
{
  "prompt": "What are the latest developments in renewable energy?"
}
```

#### `/chat/generate-image` - Image Generation
```bash
POST /chat/generate-image
{
  "prompt": "A futuristic solar panel array at sunset"
}
```

#### `/chat/outbound-call` - Phone Integration
```bash
POST /chat/outbound-call
{
  "phone_number": "+33643451397",
  "message": "Hello, this is an automated call with project updates."
}
```

## Agent Types

### 1. Deep Search Agent
- **Purpose**: Comprehensive web research
- **Technology**: SmolaAgents + DuckDuckGo
- **Features**: Multi-step research, source analysis, comprehensive reporting

### 2. New Card Agent
- **Purpose**: Convert natural language to structured tasks
- **Technology**: Claude Sonnet 4
- **Features**: Dependency detection, task categorization, smart scheduling

### 3. Image Generation Agent
- **Purpose**: AI-powered image creation
- **Technology**: Hugging Face Stable Diffusion XL
- **Features**: High-quality image generation, base64 encoding, fast processing

### 4. Phone Call Agent
- **Purpose**: Real-world phone integrations
- **Technology**: VAPI
- **Features**: Automated calls, contact management, call logging

## Testing

### Backend Tests
```bash
make test-backend
# or: cd backend && uv run pytest
```

### Frontend Tests
```bash
make test-frontend
# or: cd nextjs-frontend && pnpm test
```

### Live Integration Tests
Test real API integrations:
```bash
# Test image generation (requires HF_TOKEN)
python backend/test_live_image_generation.py

# Test new card creation
python backend/test_live_new_card.py

# Test outbound calls (requires VAPI credentials)
python backend/test_outbound_call.py

# Test all endpoints
python backend/test_api.py
```

## Database Migrations

### Creating Migrations
```bash
pnpm db:migrate:generate -m "add new feature"
```

### Applying Migrations
```bash
pnpm db:migrate
```

### Available Commands
- `pnpm db:migrate:status` - Check migration status
- `pnpm db:migrate:history` - View migration history
- `pnpm db:migrate:downgrade` - Rollback last migration
- `pnpm db:migrate:reset` - Reset and reapply all migrations

## Project Structure

```
agent-management-software/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── services/
│   │   │   ├── agent/         # Agent implementations
│   │   │   ├── chat/          # Chat services
│   │   │   └── vapi/          # Phone integration
│   │   ├── routes/            # API endpoints
│   │   └── models/            # Database models
│   ├── api/                   # Standalone API scripts
│   ├── tests/                 # Test files
│   └── alembic_migrations/    # Database migrations
├── nextjs-frontend/           # Next.js frontend
│   ├── app/                   # Next.js App Router
│   ├── components/
│   │   ├── trello/           # Task board components
│   │   └── ui/               # UI components
│   ├── lib/                  # Utility libraries
│   └── hooks/                # React hooks
├── local-shared-data/         # Shared data directory
├── docker-compose.yml         # Database container
├── Makefile                   # Development commands
└── README.md                  # This file
```

## Contributing

This project was built for the Unaite & Hugging Face Hackathon. For development:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/enhancement`
3. Make your changes and test thoroughly
4. Ensure all tests pass: `make test-backend && make test-frontend`
5. Submit a pull request

### Development Guidelines

- Follow TypeScript/Python best practices
- Add tests for new functionality
- Update documentation as needed
- Use meaningful commit messages
- Test integrations with actual APIs when possible

## License

This project is licensed under the MIT License. Built with ❤️ for the Unaite & Hugging Face Hackathon 2025.
