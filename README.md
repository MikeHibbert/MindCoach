# Personalized Learning Path Generator

A web application that provides customized learning experiences for users across various programming subjects.

## Project Structure

```
├── backend/                 # Flask backend
│   ├── app/
│   │   ├── __init__.py     # Flask app factory
│   │   ├── models/         # SQLAlchemy models
│   │   ├── services/       # Business logic services
│   │   └── api/           # API blueprints
│   ├── run.py             # Application entry point
│   ├── init_db.py         # Database initialization
│   └── requirements.txt   # Python dependencies
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── App.js        # Main app component
│   │   └── index.js      # React entry point
│   ├── public/           # Static assets
│   ├── package.json      # Node dependencies
│   └── tailwind.config.js # Tailwind configuration
└── users/                # User data storage (created at runtime)
```

## Development Setup

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Initialize the database:
   ```bash
   python init_db.py
   ```

6. Run the Flask development server:
   ```bash
   python run.py
   ```

The backend will be available at `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

The frontend will be available at `http://localhost:3000`

## Technology Stack

- **Backend**: Flask, SQLAlchemy, SQLite
- **Frontend**: React, Tailwind CSS, React Router
- **Database**: SQLite
- **Storage**: File system for lesson content

## Features

- Responsive design (desktop, tablet, mobile)
- Subject selection and subscription management
- Knowledge assessment surveys
- Personalized lesson generation
- Accessibility compliance (WCAG 2.1 AA)

## API Endpoints

- `GET /api/subjects` - List available subjects
- `POST /api/users` - Create new user
- `POST /api/users/<user_id>/subjects/<subject>/survey/generate` - Generate survey
- `POST /api/users/<user_id>/subjects/<subject>/lessons/generate` - Generate lessons
- And more...

## Development Notes

This is the initial project structure setup. Individual features will be implemented in subsequent tasks according to the implementation plan.