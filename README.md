# MindCoach - Personalized Learning Path Generator

MindCoach is an intelligent web application that creates customized learning experiences for programming subjects. Using AI-powered content generation through LangChain and Grok-3 Mini, the platform assesses user knowledge through dynamic surveys and generates personalized lesson content tailored to individual skill levels.

## Features

### Core Functionality
- **AI-Powered Assessments**: Dynamic survey generation using Grok-3 Mini via xAI API
- **Personalized Content**: Three-stage LangChain pipeline for curriculum, lesson planning, and content generation
- **Pay-per-Subject Model**: Subscription-based access to individual programming subjects
- **Responsive Design**: Optimized for desktop (1024px+), tablet (768px+), and mobile (767px-) devices
- **Accessibility Compliant**: WCAG 2.1 AA standards with full keyboard navigation and screen reader support

### Technical Features
- **RAG-Guided Generation**: Content quality ensured through Retrieval-Augmented Generation documents
- **Background Processing**: Asynchronous content generation with real-time progress tracking
- **File System Storage**: Organized user data structure with JSON metadata and Markdown lessons
- **Comprehensive Testing**: Unit, integration, and end-to-end testing with accessibility validation
- **Docker Containerization**: Production-ready deployment with multi-service orchestration

## Prerequisites

Before setting up the development environment, ensure you have the following installed:

### Required Software
- **Python 3.8+**: Backend development and package management
- **Node.js 16+**: Frontend development and build tools
- **npm 8+**: JavaScript package management (comes with Node.js)
- **Git**: Version control and repository management

### Optional but Recommended
- **Docker 20.10+**: Containerized deployment and development
- **Docker Compose 2.0+**: Multi-container orchestration
- **Redis 6.0+**: Task queue for background processing (if not using Docker)

### System Dependencies

#### Windows
```powershell
# Install Python from python.org or Microsoft Store
# Install Node.js from nodejs.org
# Install Git from git-scm.com
# Install Docker Desktop from docker.com
```

#### macOS
```bash
# Using Homebrew
brew install python node git
brew install --cask docker
```

#### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip python3-venv

# Install Node.js and npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# Install Git
sudo apt install git

# Install Docker
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER
```

## Quick Start Guide

### 1. Clone the Repository
```bash
git clone <repository-url>
cd personalized-learning-path-generator
```

### 2. Environment Configuration

#### Backend Environment Setup
```bash
cd backend
cp .env.example .env
```

Edit `.env` file with your configuration:
```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# xAI API Configuration (Required for AI features)
XAI_API_KEY=your-xai-api-key
GROK_API_URL=https://api.x.ai/v1

# Database Configuration
DATABASE_URL=sqlite:///mindcoach.db

# Redis Configuration (for background tasks)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

#### Frontend Environment Setup
```bash
cd frontend
# No additional environment configuration needed for development
```

### 3. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py

# Run database migrations (if any)
python migrate.py

# Start the Flask development server
python run.py
```

The backend API will be available at `http://localhost:5000`

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

The frontend application will be available at `http://localhost:3000`

### 5. Running Tests

#### Backend Tests
```bash
cd backend

# Run all tests
python run_tests.py

# Run specific test categories
pytest tests/test_api_integration.py -v
pytest tests/test_business_logic.py -v
pytest tests/test_file_system_operations.py -v
```

#### Frontend Tests
```bash
cd frontend

# Run unit tests
npm run test:run

# Run end-to-end tests
npm run test:e2e

# Run accessibility tests
npm run test:accessibility

# Run all tests
npm run test:all
```

## Environment Variables

### Backend Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key for sessions | Yes | - |
| `FLASK_ENV` | Flask environment mode | No | `production` |
| `FLASK_DEBUG` | Enable Flask debug mode | No | `False` |
| `XAI_API_KEY` | xAI API key for Grok-3 Mini | Yes | - |
| `GROK_API_URL` | xAI API endpoint URL | Yes | - |
| `DATABASE_URL` | SQLite database file path | No | `sqlite:///mindcoach.db` |
| `REDIS_URL` | Redis connection URL | No | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery message broker URL | No | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery result backend URL | No | `redis://localhost:6379/0` |

### Frontend Environment Variables

The frontend uses environment variables prefixed with `REACT_APP_`:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `REACT_APP_API_BASE_URL` | Backend API base URL | No | `http://localhost:5000` |
| `REACT_APP_ENVIRONMENT` | Application environment | No | `development` |

## Project Structure

```
├── .kiro/                          # Kiro IDE configuration
│   ├── hooks/                      # Git automation hooks
│   └── specs/                      # Feature specifications
├── backend/                        # Flask backend application
│   ├── app/
│   │   ├── __init__.py            # Flask app factory
│   │   ├── models/                # SQLAlchemy data models
│   │   │   ├── user.py           # User model
│   │   │   ├── subscription.py   # Subscription model
│   │   │   └── survey_result.py  # Survey result model
│   │   ├── services/              # Business logic services
│   │   │   ├── user_data_service.py      # File system operations
│   │   │   ├── subscription_service.py   # Subscription management
│   │   │   ├── survey_service.py         # Survey generation/processing
│   │   │   ├── lesson_service.py         # Lesson generation
│   │   │   └── langchain_pipeline.py     # AI content generation
│   │   ├── api/                   # REST API blueprints
│   │   │   ├── users.py          # User management endpoints
│   │   │   ├── subjects.py       # Subject selection endpoints
│   │   │   ├── surveys.py        # Survey endpoints
│   │   │   ├── lessons.py        # Lesson endpoints
│   │   │   └── subscriptions.py  # Subscription endpoints
│   │   └── utils/                 # Utility functions
│   ├── tests/                     # Backend test suite
│   │   ├── test_api_integration.py
│   │   ├── test_business_logic.py
│   │   ├── test_file_system_operations.py
│   │   ├── test_performance.py
│   │   └── test_utils_and_validation.py
│   ├── migrations/                # Database migration scripts
│   ├── instance/                  # Instance-specific files
│   ├── logs/                      # Application logs
│   ├── .env.example              # Environment variables template
│   ├── conftest.py               # Pytest configuration
│   ├── init_db.py                # Database initialization
│   ├── migrate.py                # Database migration runner
│   ├── requirements.txt          # Python dependencies
│   ├── run.py                    # Application entry point
│   └── run_tests.py              # Test runner script
├── frontend/                      # React frontend application
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── SubjectSelector.js    # Subject selection interface
│   │   │   ├── Survey.js             # Dynamic survey component
│   │   │   ├── LessonViewer.js       # Lesson content renderer
│   │   │   ├── PaymentGate.js        # Subscription management
│   │   │   ├── ResponsiveLayout.js   # Layout wrapper
│   │   │   └── __tests__/            # Component tests
│   │   ├── services/             # API service layer
│   │   │   ├── userService.js        # User API calls
│   │   │   ├── subjectService.js     # Subject API calls
│   │   │   ├── surveyService.js      # Survey API calls
│   │   │   ├── lessonService.js      # Lesson API calls
│   │   │   ├── subscriptionService.js # Subscription API calls
│   │   │   └── __tests__/            # Service tests
│   │   ├── hooks/                # Custom React hooks
│   │   ├── utils/                # Utility functions
│   │   ├── styles/               # CSS and styling
│   │   ├── App.js               # Main application component
│   │   ├── index.js             # React entry point
│   │   └── setupTests.js        # Test configuration
│   ├── public/                   # Static assets
│   ├── cypress/                  # End-to-end tests
│   │   ├── e2e/                 # Test specifications
│   │   ├── fixtures/            # Test data
│   │   └── support/             # Test utilities
│   ├── build/                    # Production build output
│   ├── cypress.config.js         # Cypress configuration
│   ├── package.json             # Node.js dependencies
│   ├── postcss.config.js        # PostCSS configuration
│   └── tailwind.config.js       # Tailwind CSS configuration
├── users/                        # User data storage (runtime)
│   └── <user_id>/               # Individual user directories
│       ├── selection.json       # Subject selection
│       └── <subject>/           # Subject-specific data
│           ├── survey.json      # Generated survey
│           ├── survey_answers.json # Survey responses
│           ├── curriculum_scheme.json # Learning curriculum
│           ├── lesson_plans.json # Detailed lesson plans
│           └── lesson_*.md      # Generated lesson content
├── docker-compose.yml           # Docker orchestration
├── docker-compose.dev.yml       # Development Docker setup
├── Dockerfile.backend           # Backend container definition
├── Dockerfile.frontend          # Frontend container definition
├── README.md                    # This file
└── setup_dev.py               # Development environment setup script
```

## Technology Stack

### Backend Technologies
- **Flask 2.3.3**: Web framework and API development
- **SQLAlchemy 3.0.5**: ORM for database operations
- **SQLite**: Lightweight database for development
- **LangChain**: AI orchestration and prompt management
- **Celery**: Background task processing
- **Redis**: Message broker and result backend
- **Marshmallow**: Data serialization and validation
- **pytest**: Testing framework

### Frontend Technologies
- **React 18.2.0**: User interface library
- **React Router 6.15.0**: Client-side routing
- **Tailwind CSS 3.3.3**: Utility-first CSS framework
- **Axios 1.5.0**: HTTP client for API calls
- **React Markdown**: Markdown rendering for lessons
- **Cypress**: End-to-end testing framework
- **Jest**: Unit testing framework
- **axe-core**: Accessibility testing

### AI and Content Generation
- **Grok-3 Mini**: Large language model via xAI API
- **LangChain**: AI pipeline orchestration
- **RAG Documents**: Content quality guidance system

### Development and Deployment
- **Docker**: Containerization platform
- **Docker Compose**: Multi-container orchestration
- **Git**: Version control system
- **GitHub Actions**: CI/CD pipeline (if configured)

## Development Workflow

### 1. Feature Development
1. Create feature branch from `main`
2. Implement backend API endpoints with tests
3. Create frontend components with unit tests
4. Add end-to-end tests for user workflows
5. Ensure accessibility compliance
6. Update documentation

### 2. Testing Strategy
- **Unit Tests**: Individual component/function testing
- **Integration Tests**: API endpoint and service testing
- **End-to-End Tests**: Complete user journey testing
- **Accessibility Tests**: WCAG 2.1 AA compliance validation
- **Performance Tests**: Load and response time testing

### 3. Code Quality
- **Linting**: ESLint for JavaScript, Flake8 for Python
- **Formatting**: Prettier for JavaScript, Black for Python
- **Type Checking**: PropTypes for React components
- **Security**: Regular dependency audits and updates

## Troubleshooting

### Common Issues

#### Backend Issues
- **Database Connection Errors**: Ensure SQLite file permissions and path accessibility
- **xAI API Errors**: Verify `XAI_API_KEY` and `GROK_API_URL` environment variables
- **Import Errors**: Activate virtual environment and reinstall requirements
- **Port Conflicts**: Change Flask port in `run.py` if 5000 is occupied

#### Frontend Issues
- **Build Failures**: Clear `node_modules` and reinstall with `npm install`
- **API Connection Issues**: Verify backend is running on correct port
- **Styling Issues**: Rebuild Tailwind CSS with `npm run build`
- **Test Failures**: Update snapshots with `npm test -- -u`

#### Docker Issues
- **Container Build Failures**: Check Dockerfile syntax and base image availability
- **Network Issues**: Verify Docker Compose network configuration
- **Volume Mount Issues**: Ensure proper file permissions and paths
- **Resource Constraints**: Increase Docker memory/CPU limits if needed

### Getting Help
1. Check the troubleshooting section above
2. Review application logs in `backend/logs/`
3. Run tests to identify specific issues
4. Check GitHub issues for known problems
5. Contact the development team

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.