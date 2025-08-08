"""
Tests for lesson file service
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.services.lesson_file_service import LessonFileService
from app.services.file_service import FileService, FileServiceError


class TestLessonFileService:
    
    def setup_method(self):
        """Set up test environment"""
        self.test_user_id = "test_user_123"
        self.test_subject = "python"
        
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.original_base_dir = FileService.BASE_DIR
        FileService.BASE_DIR = Path(self.temp_dir) / "users"
        
        # Sample lesson data
        self.sample_lessons = [
            {
                'lesson_number': 1,
                'title': 'Variables and Data Types',
                'estimated_time': '30 minutes',
                'difficulty': 'beginner',
                'topics': ['variables', 'data_types'],
                'prerequisites': [],
                'content': self._get_sample_lesson_content(),
                'generated_at': '2024-01-01T00:00:00Z'
            },
            {
                'lesson_number': 2,
                'title': 'Functions in Python',
                'estimated_time': '40 minutes',
                'difficulty': 'beginner',
                'topics': ['functions', 'parameters'],
                'prerequisites': ['variables'],
                'content': self._get_sample_lesson_content(),
                'generated_at': '2024-01-01T00:00:00Z'
            }
        ]
        
        self.sample_metadata = {
            'user_id': self.test_user_id,
            'subject': self.test_subject,
            'skill_level': 'beginner',
            'total_lessons': 2,
            'generated_at': '2024-01-01T00:00:00Z',
            'topic_analysis': {
                'strengths': ['variables'],
                'weaknesses': ['functions']
            },
            'lessons': [
                {
                    'lesson_number': 1,
                    'title': 'Variables and Data Types',
                    'estimated_time': '30 minutes',
                    'topics': ['variables', 'data_types'],
                    'difficulty': 'beginner'
                },
                {
                    'lesson_number': 2,
                    'title': 'Functions in Python',
                    'estimated_time': '40 minutes',
                    'topics': ['functions', 'parameters'],
                    'difficulty': 'beginner'
                }
            ]
        }
    
    def teardown_method(self):
        """Clean up test environment"""
        FileService.BASE_DIR = self.original_base_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _get_sample_lesson_content(self):
        """Get sample lesson content for testing"""
        return """# Sample Lesson

## Introduction
This is a sample lesson for testing purposes.

## What You'll Learn
- Basic concepts
- Practical examples
- Best practices

## Content Section

Here's some content with code examples:

```python
# Sample code
def hello_world():
    print("Hello, World!")
```

More content here with explanations.

## Quiz

1. What is the output of the code above?
   a) Hello, World!
   b) Error
   c) Nothing
   d) Hello World

**Answer: a**

## Summary

In this lesson, you learned:
- Sample concepts
- How to write basic code
- Testing fundamentals
"""
    
    def test_save_lessons_success(self):
        """Test successful lesson saving"""
        result = LessonFileService.save_lessons(
            self.test_user_id,
            self.test_subject,
            self.sample_lessons,
            self.sample_metadata
        )
        
        # Verify save results
        assert result['user_id'] == self.test_user_id
        assert result['subject'] == self.test_subject
        assert result['total_lessons'] == 2
        assert result['saved_successfully'] == 2
        assert result['failed_saves'] == 0
        assert result['metadata_saved'] is True
        assert len(result['saved_files']) == 2
        assert len(result['failed_files']) == 0
        
        # Verify files were actually created
        subject_dir = FileService.get_subject_directory(self.test_user_id, self.test_subject)
        assert (subject_dir / "lesson_1.md").exists()
        assert (subject_dir / "lesson_2.md").exists()
        assert (subject_dir / "lesson_metadata.json").exists()
    
    def test_save_lessons_invalid_lessons(self):
        """Test saving with invalid lesson data"""
        invalid_lessons = [
            {
                'lesson_number': 1,
                'title': 'Invalid Lesson'
                # Missing required fields
            }
        ]
        
        with pytest.raises(ValueError) as exc_info:
            LessonFileService.save_lessons(
                self.test_user_id,
                self.test_subject,
                invalid_lessons,
                self.sample_metadata
            )
        
        assert "Invalid lesson structure" in str(exc_info.value)
    
    def test_save_lessons_invalid_metadata(self):
        """Test saving with invalid metadata"""
        invalid_metadata = {
            'user_id': self.test_user_id
            # Missing required fields
        }
        
        with pytest.raises(ValueError) as exc_info:
            LessonFileService.save_lessons(
                self.test_user_id,
                self.test_subject,
                self.sample_lessons,
                invalid_metadata
            )
        
        assert "Metadata missing required field" in str(exc_info.value)
    
    def test_load_lessons_success(self):
        """Test successful lesson loading"""
        # First save lessons
        LessonFileService.save_lessons(
            self.test_user_id,
            self.test_subject,
            self.sample_lessons,
            self.sample_metadata
        )
        
        # Then load them
        result = LessonFileService.load_lessons(self.test_user_id, self.test_subject)
        
        # Verify loaded data
        assert result['user_id'] == self.test_user_id
        assert result['subject'] == self.test_subject
        assert result['total_lessons'] == 2
        assert len(result['lessons']) == 2
        assert len(result['missing_lessons']) == 0
        
        # Verify lesson content
        lessons = result['lessons']
        assert lessons[0]['lesson_number'] == 1
        assert lessons[0]['title'] == 'Variables and Data Types'
        assert 'content' in lessons[0]
        assert len(lessons[0]['content']) > 0
    
    def test_load_lessons_not_found(self):
        """Test loading lessons that don't exist"""
        with pytest.raises(FileNotFoundError) as exc_info:
            LessonFileService.load_lessons("nonexistent_user", "python")
        
        assert "No lessons found" in str(exc_info.value)
    
    def test_get_lesson_success(self):
        """Test getting a specific lesson"""
        # First save lessons
        LessonFileService.save_lessons(
            self.test_user_id,
            self.test_subject,
            self.sample_lessons,
            self.sample_metadata
        )
        
        # Get specific lesson
        lesson = LessonFileService.get_lesson(self.test_user_id, self.test_subject, 1)
        
        # Verify lesson data
        assert lesson['lesson_number'] == 1
        assert lesson['title'] == 'Variables and Data Types'
        assert lesson['difficulty'] == 'beginner'
        assert 'content' in lesson
        assert 'loaded_at' in lesson
    
    def test_get_lesson_invalid_number(self):
        """Test getting lesson with invalid number"""
        with pytest.raises(ValueError) as exc_info:
            LessonFileService.get_lesson(self.test_user_id, self.test_subject, 0)
        
        assert "Invalid lesson number" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            LessonFileService.get_lesson(self.test_user_id, self.test_subject, 11)
        
        assert "Invalid lesson number" in str(exc_info.value)
    
    def test_get_lesson_not_found(self):
        """Test getting lesson that doesn't exist"""
        with pytest.raises(FileNotFoundError):
            LessonFileService.get_lesson("nonexistent_user", "python", 1)
    
    def test_list_lessons_success(self):
        """Test listing lessons"""
        # First save lessons
        LessonFileService.save_lessons(
            self.test_user_id,
            self.test_subject,
            self.sample_lessons,
            self.sample_metadata
        )
        
        # List lessons
        result = LessonFileService.list_lessons(self.test_user_id, self.test_subject)
        
        # Verify results
        assert result['user_id'] == self.test_user_id
        assert result['subject'] == self.test_subject
        assert result['total_lessons'] == 2
        assert result['skill_level'] == 'beginner'
        assert len(result['lessons']) == 2
        
        # Verify lesson info
        lessons = result['lessons']
        assert lessons[0]['lesson_number'] == 1
        assert lessons[0]['file_exists'] is True
        assert 'content' not in lessons[0]  # Should not include full content
    
    def test_list_lessons_no_lessons(self):
        """Test listing lessons when none exist"""
        result = LessonFileService.list_lessons("nonexistent_user", "python")
        
        assert result['total_lessons'] == 0
        assert len(result['lessons']) == 0
        assert result['generated_at'] is None
    
    def test_delete_lessons_success(self):
        """Test successful lesson deletion"""
        # First save lessons
        LessonFileService.save_lessons(
            self.test_user_id,
            self.test_subject,
            self.sample_lessons,
            self.sample_metadata
        )
        
        # Verify files exist
        subject_dir = FileService.get_subject_directory(self.test_user_id, self.test_subject)
        assert (subject_dir / "lesson_1.md").exists()
        assert (subject_dir / "lesson_metadata.json").exists()
        
        # Delete lessons
        result = LessonFileService.delete_lessons(self.test_user_id, self.test_subject)
        
        # Verify deletion results
        assert result['user_id'] == self.test_user_id
        assert result['subject'] == self.test_subject
        assert result['total_deleted'] > 0
        assert 'lesson_1.md' in result['deleted_files']
        assert 'lesson_metadata.json' in result['deleted_files']
        
        # Verify files are actually deleted
        assert not (subject_dir / "lesson_1.md").exists()
        assert not (subject_dir / "lesson_metadata.json").exists()
    
    def test_delete_lessons_no_lessons(self):
        """Test deleting lessons when none exist"""
        result = LessonFileService.delete_lessons("nonexistent_user", "python")
        
        assert result['total_deleted'] == 0
        assert len(result['deleted_files']) == 0
        assert 'No lessons found' in result['message']
    
    def test_validate_lesson_content_valid(self):
        """Test content validation with valid content"""
        valid_content = self._get_sample_lesson_content()
        
        validation = LessonFileService.validate_lesson_content(valid_content)
        
        assert validation['is_valid'] is True
        assert len(validation['errors']) == 0
        assert validation['content_length'] > 0
        assert validation['structure_score'] > 0
        assert validation['quality'] in ['excellent', 'good', 'fair', 'poor']
    
    def test_validate_lesson_content_too_short(self):
        """Test content validation with too short content"""
        short_content = "Too short"
        
        validation = LessonFileService.validate_lesson_content(short_content)
        
        assert validation['is_valid'] is False
        assert any("too short" in error.lower() for error in validation['errors'])
    
    def test_validate_lesson_content_missing_sections(self):
        """Test content validation with missing required sections"""
        incomplete_content = """# Title
        
Some content but missing required sections."""
        
        validation = LessonFileService.validate_lesson_content(incomplete_content)
        
        assert validation['is_valid'] is False
        assert any("missing required sections" in error.lower() for error in validation['errors'])
    
    def test_validate_lesson_content_warnings(self):
        """Test content validation warnings"""
        content_without_code = """# Sample Lesson

## Introduction
This lesson has no code examples.

## What You'll Learn
- Concepts without code

## Summary
Summary without code examples."""
        
        validation = LessonFileService.validate_lesson_content(content_without_code)
        
        # Should be valid but have warnings
        assert validation['is_valid'] is True
        assert any("no code examples" in warning.lower() for warning in validation['warnings'])
    
    def test_save_lesson_file_with_metadata_header(self):
        """Test that saved lesson files include metadata header"""
        # Save lessons
        LessonFileService.save_lessons(
            self.test_user_id,
            self.test_subject,
            self.sample_lessons,
            self.sample_metadata
        )
        
        # Read raw file content
        subject_dir = FileService.get_subject_directory(self.test_user_id, self.test_subject)
        lesson_file = subject_dir / "lesson_1.md"
        
        with open(lesson_file, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        # Verify metadata header is present
        assert raw_content.startswith('---')
        assert 'lesson_number: 1' in raw_content
        assert 'title: "Variables and Data Types"' in raw_content
        assert 'difficulty: "beginner"' in raw_content
    
    def test_load_lesson_file_strips_metadata_header(self):
        """Test that loaded lesson content strips metadata header"""
        # Save lessons
        LessonFileService.save_lessons(
            self.test_user_id,
            self.test_subject,
            self.sample_lessons,
            self.sample_metadata
        )
        
        # Load lesson
        lesson = LessonFileService.get_lesson(self.test_user_id, self.test_subject, 1)
        
        # Verify content doesn't include metadata header
        assert not lesson['content'].startswith('---')
        assert 'lesson_number:' not in lesson['content']
        assert lesson['content'].startswith('# Sample Lesson')
    
    def test_validate_lessons_for_save_duplicate_numbers(self):
        """Test validation catches duplicate lesson numbers"""
        duplicate_lessons = [
            {
                'lesson_number': 1,
                'title': 'Lesson 1',
                'estimated_time': '30 minutes',
                'difficulty': 'beginner',
                'topics': ['variables'],
                'content': self._get_sample_lesson_content(),
                'generated_at': '2024-01-01T00:00:00Z'
            },
            {
                'lesson_number': 1,  # Duplicate
                'title': 'Another Lesson 1',
                'estimated_time': '30 minutes',
                'difficulty': 'beginner',
                'topics': ['functions'],
                'content': self._get_sample_lesson_content(),
                'generated_at': '2024-01-01T00:00:00Z'
            }
        ]
        
        with pytest.raises(ValueError) as exc_info:
            LessonFileService._validate_lessons_for_save(duplicate_lessons)
        
        assert "Duplicate lesson number" in str(exc_info.value)
    
    def test_validate_lessons_for_save_too_many_lessons(self):
        """Test validation catches too many lessons"""
        too_many_lessons = []
        for i in range(1, 12):  # 11 lessons (too many)
            too_many_lessons.append({
                'lesson_number': i,
                'title': f'Lesson {i}',
                'estimated_time': '30 minutes',
                'difficulty': 'beginner',
                'topics': ['variables'],
                'content': self._get_sample_lesson_content(),
                'generated_at': '2024-01-01T00:00:00Z'
            })
        
        with pytest.raises(ValueError) as exc_info:
            LessonFileService._validate_lessons_for_save(too_many_lessons)
        
        assert "Too many lessons" in str(exc_info.value)
    
    def test_validate_metadata_invalid_skill_level(self):
        """Test metadata validation with invalid skill level"""
        invalid_metadata = self.sample_metadata.copy()
        invalid_metadata['skill_level'] = 'invalid_level'
        
        with pytest.raises(ValueError) as exc_info:
            LessonFileService._validate_metadata(invalid_metadata)
        
        assert "Invalid skill level" in str(exc_info.value)
    
    def test_validate_metadata_mismatched_lesson_count(self):
        """Test metadata validation with mismatched lesson count"""
        invalid_metadata = self.sample_metadata.copy()
        invalid_metadata['total_lessons'] = 5  # Doesn't match lessons list length
        
        with pytest.raises(ValueError) as exc_info:
            LessonFileService._validate_metadata(invalid_metadata)
        
        assert "total_lessons doesn't match lessons list length" in str(exc_info.value)
    
    def test_lesson_file_pattern(self):
        """Test lesson file naming pattern"""
        assert LessonFileService.LESSON_FILE_PATTERN.format(1) == "lesson_1.md"
        assert LessonFileService.LESSON_FILE_PATTERN.format(10) == "lesson_10.md"
    
    def test_content_quality_scoring(self):
        """Test content quality scoring system"""
        # Excellent content
        excellent_content = """# Excellent Lesson

## Introduction
Great introduction

## What You'll Learn
- Learning objectives

```python
# Code example 1
print("Hello")
```

More content here.

```python
# Code example 2
def test():
    pass
```

## Quiz
1. Question here?

## Summary
Great summary"""
        
        validation = LessonFileService.validate_lesson_content(excellent_content)
        assert validation['quality'] in ['excellent', 'good']
        assert validation['structure_score'] >= 60
        
        # Poor content
        poor_content = "# Poor Lesson\n\nNot much content here."
        
        validation = LessonFileService.validate_lesson_content(poor_content)
        assert validation['quality'] in ['poor', 'fair']
        assert validation['structure_score'] < 60