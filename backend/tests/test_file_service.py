import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from app.services.file_service import FileService, FileServiceError


class TestFileService:
    
    def setup_method(self):
        """Set up test environment with temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_base_dir = FileService.BASE_DIR
        FileService.BASE_DIR = Path(self.temp_dir) / "users"
    
    def teardown_method(self):
        """Clean up test environment"""
        FileService.BASE_DIR = self.original_base_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validate_user_id_valid(self):
        """Test valid user ID validation"""
        # These should not raise exceptions
        FileService._validate_user_id("user123")
        FileService._validate_user_id("test-user")
        FileService._validate_user_id("user_123")
        FileService._validate_user_id("a")
        FileService._validate_user_id("123")
    
    def test_validate_user_id_invalid(self):
        """Test invalid user ID validation"""
        with pytest.raises(FileServiceError, match="User ID must be a non-empty string"):
            FileService._validate_user_id("")
        
        with pytest.raises(FileServiceError, match="User ID must be a non-empty string"):
            FileService._validate_user_id(None)
        
        with pytest.raises(FileServiceError, match="User ID must be 50 characters or less"):
            FileService._validate_user_id("a" * 51)
        
        with pytest.raises(FileServiceError, match="User ID contains invalid characters"):
            FileService._validate_user_id("user@123")
        
        with pytest.raises(FileServiceError, match="User ID contains invalid path characters"):
            FileService._validate_user_id("../user")
        
        with pytest.raises(FileServiceError, match="User ID contains invalid path characters"):
            FileService._validate_user_id("user/123")
        
        with pytest.raises(FileServiceError, match="User ID contains invalid path characters"):
            FileService._validate_user_id("user\\123")
    
    def test_validate_subject_valid(self):
        """Test valid subject validation"""
        # These should not raise exceptions
        FileService._validate_subject("python")
        FileService._validate_subject("javascript")
        FileService._validate_subject("data-science")
        FileService._validate_subject("web_dev")
        FileService._validate_subject("123")
    
    def test_validate_subject_invalid(self):
        """Test invalid subject validation"""
        with pytest.raises(FileServiceError, match="Subject must be a non-empty string"):
            FileService._validate_subject("")
        
        with pytest.raises(FileServiceError, match="Subject must be a non-empty string"):
            FileService._validate_subject(None)
        
        with pytest.raises(FileServiceError, match="Subject must be 50 characters or less"):
            FileService._validate_subject("a" * 51)
        
        with pytest.raises(FileServiceError, match="Subject contains invalid characters"):
            FileService._validate_subject("python@advanced")
        
        with pytest.raises(FileServiceError, match="Subject contains invalid path characters"):
            FileService._validate_subject("../python")
        
        with pytest.raises(FileServiceError, match="Subject contains invalid path characters"):
            FileService._validate_subject("python/advanced")
    
    def test_ensure_user_directory(self):
        """Test user directory creation"""
        user_id = "test_user"
        user_dir = FileService.ensure_user_directory(user_id)
        
        assert user_dir.exists()
        assert user_dir.is_dir()
        assert user_dir.name == user_id
        
        # Test idempotency - should not fail if directory already exists
        user_dir2 = FileService.ensure_user_directory(user_id)
        assert user_dir == user_dir2
    
    def test_ensure_subject_directory(self):
        """Test subject directory creation"""
        user_id = "test_user"
        subject = "python"
        
        subject_dir = FileService.ensure_subject_directory(user_id, subject)
        
        assert subject_dir.exists()
        assert subject_dir.is_dir()
        assert subject_dir.name == subject
        assert subject_dir.parent.name == user_id
        
        # Test idempotency
        subject_dir2 = FileService.ensure_subject_directory(user_id, subject)
        assert subject_dir == subject_dir2
    
    def test_get_user_directory(self):
        """Test getting user directory path without creation"""
        user_id = "test_user"
        user_dir = FileService.get_user_directory(user_id)
        
        # Directory should not exist yet
        assert not user_dir.exists()
        assert user_dir.name == user_id
    
    def test_get_subject_directory(self):
        """Test getting subject directory path without creation"""
        user_id = "test_user"
        subject = "python"
        
        subject_dir = FileService.get_subject_directory(user_id, subject)
        
        # Directory should not exist yet
        assert not subject_dir.exists()
        assert subject_dir.name == subject
        assert subject_dir.parent.name == user_id
    
    def test_save_and_load_json(self):
        """Test JSON file operations"""
        user_id = "test_user"
        subject = "python"
        
        # Create directory structure
        subject_dir = FileService.ensure_subject_directory(user_id, subject)
        file_path = subject_dir / "test.json"
        
        # Test data
        test_data = {
            "name": "Test User",
            "age": 25,
            "skills": ["python", "javascript"],
            "active": True
        }
        
        # Save JSON
        FileService.save_json(file_path, test_data)
        
        # Verify file exists
        assert file_path.exists()
        
        # Load JSON
        loaded_data = FileService.load_json(file_path)
        
        # Verify data integrity
        assert loaded_data == test_data
    
    def test_load_json_nonexistent_file(self):
        """Test loading non-existent JSON file"""
        user_id = "test_user"
        subject_dir = FileService.get_subject_directory(user_id, "python")
        file_path = subject_dir / "nonexistent.json"
        
        result = FileService.load_json(file_path)
        assert result is None
    
    def test_save_and_load_markdown(self):
        """Test markdown file operations"""
        user_id = "test_user"
        subject = "python"
        
        # Create directory structure
        subject_dir = FileService.ensure_subject_directory(user_id, subject)
        file_path = subject_dir / "lesson_1.md"
        
        # Test content
        test_content = """# Python Basics

This is a test lesson about Python basics.

## Variables

Variables in Python are created when you assign a value to them:

```python
x = 5
name = "Alice"
```

## Quiz

1. What is a variable?
2. How do you create a variable in Python?
"""
        
        # Save markdown
        FileService.save_markdown(file_path, test_content)
        
        # Verify file exists
        assert file_path.exists()
        
        # Load markdown
        loaded_content = FileService.load_markdown(file_path)
        
        # Verify content integrity
        assert loaded_content == test_content
    
    def test_load_markdown_nonexistent_file(self):
        """Test loading non-existent markdown file"""
        user_id = "test_user"
        subject_dir = FileService.get_subject_directory(user_id, "python")
        file_path = subject_dir / "nonexistent.md"
        
        result = FileService.load_markdown(file_path)
        assert result is None
    
    def test_file_exists(self):
        """Test file existence check"""
        user_id = "test_user"
        subject = "python"
        
        subject_dir = FileService.ensure_subject_directory(user_id, subject)
        file_path = subject_dir / "test.json"
        
        # File should not exist initially
        assert not FileService.file_exists(file_path)
        
        # Create file
        FileService.save_json(file_path, {"test": "data"})
        
        # File should exist now
        assert FileService.file_exists(file_path)
    
    def test_delete_file(self):
        """Test file deletion"""
        user_id = "test_user"
        subject = "python"
        
        subject_dir = FileService.ensure_subject_directory(user_id, subject)
        file_path = subject_dir / "test.json"
        
        # Create file
        FileService.save_json(file_path, {"test": "data"})
        assert file_path.exists()
        
        # Delete file
        result = FileService.delete_file(file_path)
        assert result is True
        assert not file_path.exists()
        
        # Try to delete non-existent file
        result = FileService.delete_file(file_path)
        assert result is False
    
    def test_save_json_invalid_data(self):
        """Test saving invalid JSON data"""
        user_id = "test_user"
        subject_dir = FileService.ensure_subject_directory(user_id, "python")
        file_path = subject_dir / "test.json"
        
        # Try to save non-serializable data
        with pytest.raises(FileServiceError, match="Failed to save JSON file"):
            FileService.save_json(file_path, {"func": lambda x: x})
    
    def test_save_markdown_invalid_content(self):
        """Test saving invalid markdown content"""
        user_id = "test_user"
        subject_dir = FileService.ensure_subject_directory(user_id, "python")
        file_path = subject_dir / "test.md"
        
        # Try to save non-string content
        with pytest.raises(FileServiceError, match="Content must be a string"):
            FileService.save_markdown(file_path, 123)
    
    def test_path_security_validation(self):
        """Test path security validation prevents directory traversal"""
        # These should raise security errors
        with pytest.raises(FileServiceError):
            FileService.ensure_user_directory("../../../etc")
        
        with pytest.raises(FileServiceError):
            FileService.ensure_subject_directory("user", "../../../etc")
    
    @patch('pathlib.Path.mkdir')
    def test_directory_creation_failure(self, mock_mkdir):
        """Test handling of directory creation failures"""
        mock_mkdir.side_effect = OSError("Permission denied")
        
        with pytest.raises(FileServiceError, match="Failed to create user directory"):
            FileService.ensure_user_directory("test_user")
    
    def test_unicode_content_handling(self):
        """Test handling of Unicode content in files"""
        user_id = "test_user"
        subject = "python"
        
        subject_dir = FileService.ensure_subject_directory(user_id, subject)
        
        # Test Unicode in JSON
        json_data = {
            "name": "José María",
            "description": "Programación en Python 🐍",
            "emoji": "😀"
        }
        json_path = subject_dir / "unicode.json"
        FileService.save_json(json_path, json_data)
        loaded_json = FileService.load_json(json_path)
        assert loaded_json == json_data
        
        # Test Unicode in Markdown
        markdown_content = """# Lección de Python 🐍

¡Hola! Esta es una lección con caracteres especiales:
- Español: ñ, á, é, í, ó, ú
- Emojis: 😀 🎉 ✨
- Símbolos: © ® ™
"""
        md_path = subject_dir / "unicode.md"
        FileService.save_markdown(md_path, markdown_content)
        loaded_md = FileService.load_markdown(md_path)
        assert loaded_md == markdown_content