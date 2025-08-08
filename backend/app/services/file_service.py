import os
import json
import re
from pathlib import Path
from typing import Optional, Union

class FileServiceError(Exception):
    """Custom exception for file service errors"""
    pass

class FileService:
    # Base directory for all user data
    BASE_DIR = Path("users")
    
    # Valid patterns for user_id and subject names
    VALID_USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    VALID_SUBJECT_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    
    @classmethod
    def _validate_user_id(cls, user_id: str) -> None:
        """Validate user_id format and security"""
        if not user_id or not isinstance(user_id, str):
            raise FileServiceError("User ID must be a non-empty string")
        
        if len(user_id) > 50:
            raise FileServiceError("User ID must be 50 characters or less")
        
        # Prevent directory traversal attacks - check this first
        if '..' in user_id or '/' in user_id or '\\' in user_id:
            raise FileServiceError("User ID contains invalid path characters")
        
        if not cls.VALID_USER_ID_PATTERN.match(user_id):
            raise FileServiceError("User ID contains invalid characters. Only alphanumeric, underscore, and hyphen allowed")
    
    @classmethod
    def _validate_subject(cls, subject: str) -> None:
        """Validate subject format and security"""
        if not subject or not isinstance(subject, str):
            raise FileServiceError("Subject must be a non-empty string")
        
        if len(subject) > 50:
            raise FileServiceError("Subject must be 50 characters or less")
        
        # Prevent directory traversal attacks - check this first
        if '..' in subject or '/' in subject or '\\' in subject:
            raise FileServiceError("Subject contains invalid path characters")
        
        if not cls.VALID_SUBJECT_PATTERN.match(subject):
            raise FileServiceError("Subject contains invalid characters. Only alphanumeric, underscore, and hyphen allowed")
    
    @classmethod
    def _validate_path_security(cls, path: Path) -> None:
        """Ensure path is within the allowed base directory"""
        try:
            # Resolve the path to handle any .. or symbolic links
            resolved_path = path.resolve()
            base_resolved = cls.BASE_DIR.resolve()
            
            # Check if the resolved path is within the base directory
            if not str(resolved_path).startswith(str(base_resolved)):
                raise FileServiceError("Path is outside allowed directory structure")
        except (OSError, ValueError) as e:
            raise FileServiceError(f"Invalid path: {e}")
    
    @classmethod
    def ensure_user_directory(cls, user_id: str) -> Path:
        """Create user directory structure if it doesn't exist"""
        cls._validate_user_id(user_id)
        
        user_dir = cls.BASE_DIR / user_id
        cls._validate_path_security(user_dir)
        
        try:
            user_dir.mkdir(parents=True, exist_ok=True)
            return user_dir
        except OSError as e:
            raise FileServiceError(f"Failed to create user directory: {e}")
    
    @classmethod
    def ensure_subject_directory(cls, user_id: str, subject: str) -> Path:
        """Create user/subject directory structure if it doesn't exist"""
        cls._validate_user_id(user_id)
        cls._validate_subject(subject)
        
        subject_dir = cls.BASE_DIR / user_id / subject
        cls._validate_path_security(subject_dir)
        
        try:
            subject_dir.mkdir(parents=True, exist_ok=True)
            return subject_dir
        except OSError as e:
            raise FileServiceError(f"Failed to create subject directory: {e}")
    
    @classmethod
    def get_user_directory(cls, user_id: str) -> Path:
        """Get user directory path (without creating it)"""
        cls._validate_user_id(user_id)
        
        user_dir = cls.BASE_DIR / user_id
        cls._validate_path_security(user_dir)
        return user_dir
    
    @classmethod
    def get_subject_directory(cls, user_id: str, subject: str) -> Path:
        """Get user/subject directory path (without creating it)"""
        cls._validate_user_id(user_id)
        cls._validate_subject(subject)
        
        subject_dir = cls.BASE_DIR / user_id / subject
        cls._validate_path_security(subject_dir)
        return subject_dir
    
    @classmethod
    def save_json(cls, file_path: Union[str, Path], data: dict) -> None:
        """Save data as JSON file with validation"""
        file_path = Path(file_path)
        cls._validate_path_security(file_path.parent)
        
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write JSON with proper formatting
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except (OSError, TypeError, ValueError) as e:
            raise FileServiceError(f"Failed to save JSON file: {e}")
    
    @classmethod
    def load_json(cls, file_path: Union[str, Path]) -> Optional[dict]:
        """Load data from JSON file with validation"""
        file_path = Path(file_path)
        cls._validate_path_security(file_path.parent)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError, ValueError) as e:
            raise FileServiceError(f"Failed to load JSON file: {e}")
    
    @classmethod
    def save_markdown(cls, file_path: Union[str, Path], content: str) -> None:
        """Save content as markdown file with validation"""
        file_path = Path(file_path)
        cls._validate_path_security(file_path.parent)
        
        if not isinstance(content, str):
            raise FileServiceError("Content must be a string")
        
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except OSError as e:
            raise FileServiceError(f"Failed to save markdown file: {e}")
    
    @classmethod
    def load_markdown(cls, file_path: Union[str, Path]) -> Optional[str]:
        """Load content from markdown file with validation"""
        file_path = Path(file_path)
        cls._validate_path_security(file_path.parent)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except OSError as e:
            raise FileServiceError(f"Failed to load markdown file: {e}")
    
    @classmethod
    def file_exists(cls, file_path: Union[str, Path]) -> bool:
        """Check if file exists with path validation"""
        file_path = Path(file_path)
        cls._validate_path_security(file_path.parent)
        return file_path.exists()
    
    @classmethod
    def delete_file(cls, file_path: Union[str, Path]) -> bool:
        """Delete file with path validation"""
        file_path = Path(file_path)
        cls._validate_path_security(file_path.parent)
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            return True
        except OSError as e:
            raise FileServiceError(f"Failed to delete file: {e}")