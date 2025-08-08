#!/usr/bin/env python3
"""
Development environment setup script
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=True, 
                              capture_output=True, text=True)
        print(f"✓ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {command}")
        print(f"Error: {e.stderr}")
        return False

def setup_backend():
    """Set up the Flask backend"""
    print("\n=== Setting up Backend ===")
    
    backend_dir = Path("backend")
    
    # Check if Python is available
    if not run_command("python --version"):
        print("Python is required but not found in PATH")
        return False
    
    # Create virtual environment if it doesn't exist
    venv_dir = backend_dir / "venv"
    if not venv_dir.exists():
        print("Creating virtual environment...")
        if not run_command("python -m venv venv", cwd=backend_dir):
            return False
    
    # Install dependencies
    print("Installing Python dependencies...")
    pip_cmd = "venv\\Scripts\\pip" if os.name == 'nt' else "venv/bin/pip"
    if not run_command(f"{pip_cmd} install -r requirements.txt", cwd=backend_dir):
        return False
    
    # Initialize database
    print("Initializing database...")
    python_cmd = "venv\\Scripts\\python" if os.name == 'nt' else "venv/bin/python"
    if not run_command(f"{python_cmd} init_db.py", cwd=backend_dir):
        return False
    
    return True

def setup_frontend():
    """Set up the React frontend"""
    print("\n=== Setting up Frontend ===")
    
    frontend_dir = Path("frontend")
    
    # Check if Node.js is available
    if not run_command("node --version"):
        print("Node.js is required but not found in PATH")
        return False
    
    # Install dependencies
    print("Installing Node.js dependencies...")
    if not run_command("npm install", cwd=frontend_dir):
        return False
    
    return True

def main():
    """Main setup function"""
    print("Personalized Learning Path Generator - Development Setup")
    print("=" * 60)
    
    # Setup backend
    if not setup_backend():
        print("\n❌ Backend setup failed!")
        sys.exit(1)
    
    # Setup frontend
    if not setup_frontend():
        print("\n❌ Frontend setup failed!")
        sys.exit(1)
    
    print("\n✅ Development environment setup complete!")
    print("\nTo start development:")
    print("1. Backend: cd backend && python run.py")
    print("2. Frontend: cd frontend && npm start")

if __name__ == "__main__":
    main()