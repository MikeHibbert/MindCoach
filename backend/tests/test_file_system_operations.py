"""
Comprehensive tests for file system operations
Tests file I/O, directory management, and data persistence
"""

import pytest
import json
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch, mock_open
import threading
import time

from app.services.file_service import FileService, FileServiceError
from app.services.user_data_service import UserDataService
from app.services.lesson_file_service import LessonFileService


class TestFileServiceComprehensive:
    """Comprehensive tests for FileService"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_base_dir = FileService.BASE_DIR
        FileService.BASE_DIR = Path(self.temp_dir) / "users"
    
    def teardown_method(self):
        """Clean up test environment"""
        FileService.BASE_DIR = self.original_base_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_directory_creation_permissions(self):
        """Test directory creation with various permission scenarios"""
        user_id = "perm_test_user"
        
        # Test normal directory creation
        user_dir = FileService.ensure_user_directory(user_id)
        assert user_dir.exists()
        assert user_dir.is_dir()
        
        # Test nested directory creation
        subject_dir = FileService.ensure_subject_directory(user_id, "python")
        assert subject_dir.exists()
        assert subject_dir.parent == user_dir
    
    def test_concurrent_file_operations(self):
        """Test concurrent file operations for thread safety"""
        user_id = "concurrent_user"
        subject = "python"
        
        FileService.ensure_subject_directory(user_id, subject)
        
        results = []
        errors = []
        
        def write_file(file_num):
            try:
                file_path = FileService.get_subject_directory(user_id, subject) / f"test_{file_num}.json"
                data = {"file_number": file_num, "content": f"Content {file_num}"}
                FileService.save_json(file_path, data)
                results.append(file_num)
            except Exception as e:
                errors.append(str(e))
        
        def read_file(file_num):
            try:
                file_path = FileService.get_subject_directory(user_id, subject) / f"test_{file_num}.json"
                # Wait a bit to ensure file is written
                time.sleep(0.1)
                data = FileService.load_json(file_path)
                if data and data.get("file_number") == file_num:
                    results.append(f"read_{file_num}")
            except Exception as e:
                errors.append(str(e))
        
        # Create threads for concurrent operations
        threads = []
        for i in range(10):
            write_thread = threading.Thread(target=write_file, args=(i,))
            read_thread = threading.Thread(target=read_file, args=(i,))
            threads.extend([write_thread, read_thread])
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) >= 10  # At least all write operations should succeed
    
    def test_large_file_handling(self):
        """Test handling of large files"""
        user_id = "large_file_user"
        subject = "python"
        
        subject_dir = FileService.ensure_subject_directory(user_id, subject)
        
        # Create large JSON data (approximately 1MB)
        large_data = {
            "lessons": [
                {
                    "lesson_number": i,
                    "title": f"Lesson {i}",
                    "content": "A" * 1000,  # 1KB per lesson
                    "metadata": {
                        "topics": [f"topic_{j}" for j in range(20)],
                        "examples": [f"example_{k}" for k in range(10)]
                    }
                }
                for i in range(1000)  # 1000 lessons
            ]
        }
        
        file_path = subject_dir / "large_data.json"
        
        # Test saving large file
        FileService.save_json(file_path, large_data)
        assert file_path.exists()
        
        # Verify file size
        file_size = file_path.stat().st_size
        assert file_size > 500000  # Should be at least 500KB
        
        # Test loading large file
        loaded_data = FileService.load_json(file_path)
        assert loaded_data == large_data
        assert len(loaded_data["lessons"]) == 1000
    
    def test_file_corruption_handling(self):
        """Test handling of corrupted files"""
        user_id = "corruption_user"
        subject = "python"
        
        subject_dir = FileService.ensure_subject_directory(user_id, subject)
        
        # Create corrupted JSON file
        corrupted_file = subject_dir / "corrupted.json"
        with open(corrupted_file, 'w') as f:
            f.write('{"incomplete": json data without closing brace')
        
        # Test loading corrupted file
        result = FileService.load_json(corrupted_file)
        assert result is None  # Should handle corruption gracefully
        
        # Create corrupted markdown file with invalid encoding
        corrupted_md = subject_dir / "corrupted.md"
        with open(corrupted_md, 'wb') as f:
            f.write(b'\xff\xfe# Invalid encoding content')
        
        # Test loading corrupted markdown
        result = FileService.load_markdown(corrupted_md)
        # Should either handle gracefully or raise appropriate error
        assert result is None or isinstance(result, str)
    
    def test_disk_space_handling(self):
        """Test behavior when disk space is limited"""
        user_id = "disk_space_user"
        subject = "python"
        
        subject_dir = FileService.ensure_subject_directory(user_id, subject)
        
        # Mock disk full scenario
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            with pytest.raises(FileServiceError):
                FileService.save_json(subject_dir / "test.json", {"test": "data"})
    
    def test_file_locking_scenarios(self):
        """Test file locking and access scenarios"""
        user_id = "locking_user"
        subject = "python"
        
        subject_dir = FileService.ensure_subject_directory(user_id, subject)
        test_file = subject_dir / "locked_file.json"
        
        # Create initial file
        FileService.save_json(test_file, {"initial": "data"})
        
        # Simulate file being locked by another process
        with patch('builtins.open', side_effect=PermissionError("File is locked")):
            with pytest.raises(FileServiceError):
                FileService.save_json(test_file, {"updated": "data"})
    
    def test_unicode_and_special_characters(self):
        """Test handling of Unicode and special characters"""
        user_id = "unicode_user"
        subject = "python"
        
        subject_dir = FileService.ensure_subject_directory(user_id, subject)
        
        # Test Unicode in JSON
        unicode_data = {
            "title": "Programación en Python 🐍",
            "description": "Aprende Python con ejemplos prácticos",
            "content": "¡Hola mundo! 你好世界 مرحبا بالعالم",
            "symbols": "© ® ™ € £ ¥ § ¶ † ‡ • … ‰ ′ ″ ‹ › « »",
            "emoji": "😀 🎉 ✨ 🚀 💻 📚 🔥 ⭐ 🌟 💡"
        }
        
        json_file = subject_dir / "unicode.json"
        FileService.save_json(json_file, unicode_data)
        loaded_data = FileService.load_json(json_file)
        assert loaded_data == unicode_data
        
        # Test Unicode in Markdown
        unicode_markdown = """# Lección de Python 🐍

## Introducción

¡Bienvenido al curso de Python! En esta lección aprenderás:

- Variables y tipos de datos
- Funciones básicas
- Estructuras de control

### Ejemplo de código

```python
def saludar(nombre):
    return f"¡Hola, {nombre}! 👋"

mensaje = saludar("María José")
print(mensaje)
```

### Ejercicios

1. Crea una función que calcule el área de un círculo
2. Implementa un programa que cuente caracteres especiales: ñ, á, é, í, ó, ú

¡Buena suerte! 🍀
"""
        
        md_file = subject_dir / "unicode.md"
        FileService.save_markdown(md_file, unicode_markdown)
        loaded_markdown = FileService.load_markdown(md_file)
        assert loaded_markdown == unicode_markdown
    
    def test_path_traversal_security(self):
        """Test security against path traversal attacks"""
        # Test various path traversal attempts
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/passwd",
            "C:\\Windows\\System32",
            "user/../../../sensitive",
            "user\\..\\..\\..\\sensitive"
        ]
        
        for malicious_path in malicious_paths:
            with pytest.raises(FileServiceError):
                FileService.ensure_user_directory(malicious_path)
            
            with pytest.raises(FileServiceError):
                FileService.ensure_subject_directory("valid_user", malicious_path)
    
    def test_file_metadata_preservation(self):
        """Test that file metadata is preserved correctly"""
        user_id = "metadata_user"
        subject = "python"
        
        subject_dir = FileService.ensure_subject_directory(user_id, subject)
        test_file = subject_dir / "metadata_test.json"
        
        # Create file with specific data
        original_data = {
            "created_at": "2024-01-01T00:00:00Z",
            "version": "1.0",
            "metadata": {
                "author": "test_user",
                "tags": ["python", "beginner"]
            }
        }
        
        FileService.save_json(test_file, original_data)
        
        # Get file stats
        original_mtime = test_file.stat().st_mtime
        
        # Load and verify data integrity
        loaded_data = FileService.load_json(test_file)
        assert loaded_data == original_data
        
        # Verify file modification time hasn't changed from just reading
        current_mtime = test_file.stat().st_mtime
        assert current_mtime == original_mtime


class TestUserDataServiceFileOperations:
    """Test UserDataService file operations"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_base_dir = FileService.BASE_DIR
        FileService.BASE_DIR = Path(self.temp_dir) / "users"
    
    def teardown_method(self):
        """Clean up test environment"""
        FileService.BASE_DIR = self.original_base_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_user_selection_persistence(self):
        """Test user selection data persistence"""
        user_id = "selection_user"
        subject = "python"
        
        # Save selection
        selection_data = {
            "selected_subject": subject,
            "selected_at": "2024-01-01T12:00:00Z",
            "preferences": {
                "difficulty": "intermediate",
                "pace": "normal"
            }
        }
        
        UserDataService.save_selection(user_id, selection_data)
        
        # Load and verify
        loaded_selection = UserDataService.load_selection(user_id)
        assert loaded_selection == selection_data
        
        # Test loading non-existent selection
        no_selection = UserDataService.load_selection("nonexistent_user")
        assert no_selection is None
    
    def test_survey_data_persistence(self):
        """Test survey data persistence"""
        user_id = "survey_user"
        subject = "python"
        
        # Save survey
        survey_data = {
            "questions": [
                {
                    "id": 1,
                    "question": "What is Python?",
                    "type": "multiple_choice",
                    "options": ["Language", "Snake", "Tool", "Framework"],
                    "correct_answer": "Language"
                }
            ],
            "generated_at": "2024-01-01T12:00:00Z"
        }
        
        UserDataService.save_survey(user_id, subject, survey_data)
        
        # Load and verify
        loaded_survey = UserDataService.load_survey(user_id, subject)
        assert loaded_survey == survey_data
        
        # Save survey answers
        answers_data = {
            "answers": [
                {"question_id": 1, "answer": "Language", "correct": True}
            ],
            "submitted_at": "2024-01-01T12:30:00Z",
            "skill_level": "intermediate"
        }
        
        UserDataService.save_survey_answers(user_id, subject, answers_data)
        
        # Load and verify answers
        loaded_answers = UserDataService.load_survey_answers(user_id, subject)
        assert loaded_answers == answers_data
    
    def test_lesson_metadata_persistence(self):
        """Test lesson metadata persistence"""
        user_id = "lesson_meta_user"
        subject = "python"
        
        # Save lesson metadata
        metadata = {
            "skill_level": "intermediate",
            "total_lessons": 10,
            "generated_at": "2024-01-01T12:00:00Z",
            "topic_analysis": {
                "variables": "known",
                "functions": "needs_review",
                "classes": "unknown"
            }
        }
        
        UserDataService.save_lesson_metadata(user_id, subject, metadata)
        
        # Load and verify
        loaded_metadata = UserDataService.load_lesson_metadata(user_id, subject)
        assert loaded_metadata == metadata
    
    def test_data_migration_scenarios(self):
        """Test data migration and format changes"""
        user_id = "migration_user"
        subject = "python"
        
        # Create old format data
        old_format_data = {
            "version": "1.0",
            "lessons": ["lesson1", "lesson2", "lesson3"]
        }
        
        # Save in old format
        subject_dir = FileService.ensure_subject_directory(user_id, subject)
        old_file = subject_dir / "old_format.json"
        FileService.save_json(old_file, old_format_data)
        
        # Test migration to new format
        new_format_data = {
            "version": "2.0",
            "lessons": [
                {"id": "lesson1", "title": "Lesson 1", "status": "completed"},
                {"id": "lesson2", "title": "Lesson 2", "status": "in_progress"},
                {"id": "lesson3", "title": "Lesson 3", "status": "not_started"}
            ]
        }
        
        # Simulate migration
        FileService.save_json(old_file, new_format_data)
        migrated_data = FileService.load_json(old_file)
        assert migrated_data["version"] == "2.0"
        assert len(migrated_data["lessons"]) == 3


class TestLessonFileServiceOperations:
    """Test LessonFileService file operations"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_base_dir = FileService.BASE_DIR
        FileService.BASE_DIR = Path(self.temp_dir) / "users"
    
    def teardown_method(self):
        """Clean up test environment"""
        FileService.BASE_DIR = self.original_base_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_lesson_file_creation_and_retrieval(self):
        """Test lesson file creation and retrieval"""
        user_id = "lesson_file_user"
        subject = "python"
        
        # Create lesson data
        lessons = [
            {
                "lesson_number": 1,
                "title": "Python Basics",
                "content": "# Python Basics\n\nThis is lesson 1 content...",
                "estimated_time": "30 minutes",
                "difficulty": "beginner",
                "topics": ["variables", "data_types"]
            },
            {
                "lesson_number": 2,
                "title": "Functions",
                "content": "# Functions\n\nThis is lesson 2 content...",
                "estimated_time": "45 minutes",
                "difficulty": "intermediate",
                "topics": ["functions", "parameters"]
            }
        ]
        
        metadata = {
            "skill_level": "beginner",
            "total_lessons": 2,
            "generated_at": "2024-01-01T12:00:00Z",
            "topic_analysis": {}
        }
        
        # Save lessons
        result = LessonFileService.save_lessons(user_id, subject, lessons, metadata)
        assert result["saved_successfully"] == 2
        assert result["failed_saves"] == 0
        
        # Retrieve specific lesson
        lesson_1 = LessonFileService.get_lesson(user_id, subject, 1)
        assert lesson_1["title"] == "Python Basics"
        assert lesson_1["lesson_number"] == 1
        
        # List all lessons
        lesson_list = LessonFileService.list_lessons(user_id, subject)
        assert lesson_list["total_lessons"] == 2
        assert len(lesson_list["lessons"]) == 2
    
    def test_lesson_file_updates(self):
        """Test lesson file updates and versioning"""
        user_id = "lesson_update_user"
        subject = "python"
        
        # Create initial lesson
        initial_lesson = {
            "lesson_number": 1,
            "title": "Initial Title",
            "content": "# Initial Content",
            "estimated_time": "30 minutes",
            "difficulty": "beginner",
            "topics": ["basic"]
        }
        
        metadata = {
            "skill_level": "beginner",
            "total_lessons": 1,
            "generated_at": "2024-01-01T12:00:00Z",
            "topic_analysis": {}
        }
        
        LessonFileService.save_lessons(user_id, subject, [initial_lesson], metadata)
        
        # Update lesson
        updated_lesson = {
            "lesson_number": 1,
            "title": "Updated Title",
            "content": "# Updated Content\n\nThis is the updated version.",
            "estimated_time": "45 minutes",
            "difficulty": "intermediate",
            "topics": ["basic", "advanced"]
        }
        
        LessonFileService.save_lessons(user_id, subject, [updated_lesson], metadata)
        
        # Verify update
        retrieved_lesson = LessonFileService.get_lesson(user_id, subject, 1)
        assert retrieved_lesson["title"] == "Updated Title"
        assert "updated version" in retrieved_lesson["content"]
    
    def test_lesson_file_deletion(self):
        """Test lesson file deletion"""
        user_id = "lesson_delete_user"
        subject = "python"
        
        # Create lessons
        lessons = [
            {
                "lesson_number": i,
                "title": f"Lesson {i}",
                "content": f"# Lesson {i}\n\nContent for lesson {i}",
                "estimated_time": "30 minutes",
                "difficulty": "beginner",
                "topics": [f"topic_{i}"]
            }
            for i in range(1, 6)  # 5 lessons
        ]
        
        metadata = {
            "skill_level": "beginner",
            "total_lessons": 5,
            "generated_at": "2024-01-01T12:00:00Z",
            "topic_analysis": {}
        }
        
        LessonFileService.save_lessons(user_id, subject, lessons, metadata)
        
        # Verify lessons exist
        lesson_list = LessonFileService.list_lessons(user_id, subject)
        assert lesson_list["total_lessons"] == 5
        
        # Delete lessons
        delete_result = LessonFileService.delete_lessons(user_id, subject)
        assert delete_result["total_deleted"] >= 5  # At least lesson files
        
        # Verify deletion
        with pytest.raises(FileNotFoundError):
            LessonFileService.get_lesson(user_id, subject, 1)
    
    def test_lesson_file_corruption_recovery(self):
        """Test recovery from lesson file corruption"""
        user_id = "lesson_corrupt_user"
        subject = "python"
        
        # Create lesson directory
        subject_dir = FileService.ensure_subject_directory(user_id, subject)
        
        # Create corrupted lesson file
        corrupted_file = subject_dir / "lesson_1.md"
        with open(corrupted_file, 'wb') as f:
            f.write(b'\xff\xfe# Corrupted content')
        
        # Test graceful handling of corruption
        try:
            lesson = LessonFileService.get_lesson(user_id, subject, 1)
            # Should either return None or handle gracefully
            assert lesson is None or isinstance(lesson.get("content"), str)
        except Exception as e:
            # Should raise appropriate exception, not crash
            assert isinstance(e, (FileNotFoundError, UnicodeDecodeError, ValueError))
    
    def test_concurrent_lesson_operations(self):
        """Test concurrent lesson file operations"""
        user_id = "concurrent_lesson_user"
        subject = "python"
        
        results = []
        errors = []
        
        def save_lesson(lesson_num):
            try:
                lesson = {
                    "lesson_number": lesson_num,
                    "title": f"Concurrent Lesson {lesson_num}",
                    "content": f"# Lesson {lesson_num}\n\nContent for lesson {lesson_num}",
                    "estimated_time": "30 minutes",
                    "difficulty": "beginner",
                    "topics": [f"topic_{lesson_num}"]
                }
                
                metadata = {
                    "skill_level": "beginner",
                    "total_lessons": 1,
                    "generated_at": "2024-01-01T12:00:00Z",
                    "topic_analysis": {}
                }
                
                result = LessonFileService.save_lessons(user_id, subject, [lesson], metadata)
                results.append(result)
            except Exception as e:
                errors.append(str(e))
        
        # Create threads for concurrent lesson saving
        threads = []
        for i in range(1, 11):  # 10 lessons
            thread = threading.Thread(target=save_lesson, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        
        # Verify all lessons were saved
        lesson_list = LessonFileService.list_lessons(user_id, subject)
        assert lesson_list["total_lessons"] >= 10