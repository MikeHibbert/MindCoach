import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from app.services.user_data_service import UserDataService, UserDataServiceError
from app.services.file_service import FileService


class TestUserDataService:
    
    def setup_method(self):
        """Set up test environment with temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_base_dir = FileService.BASE_DIR
        FileService.BASE_DIR = Path(self.temp_dir) / "users"
    
    def teardown_method(self):
        """Clean up test environment"""
        FileService.BASE_DIR = self.original_base_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_load_user_selection(self):
        """Test saving and loading user selection"""
        user_id = "test_user"
        subject = "python"
        
        # Save selection
        UserDataService.save_user_selection(user_id, subject)
        
        # Load selection
        selection = UserDataService.load_user_selection(user_id)
        
        assert selection is not None
        assert selection["selected_subject"] == subject
        assert "selected_at" in selection
        
        # Verify timestamp format
        selected_at = selection["selected_at"]
        assert selected_at.endswith("Z")
        # Should be able to parse as ISO format
        datetime.fromisoformat(selected_at.replace("Z", "+00:00"))
    
    def test_load_nonexistent_user_selection(self):
        """Test loading selection for non-existent user"""
        result = UserDataService.load_user_selection("nonexistent_user")
        assert result is None
    
    def test_save_and_load_survey(self):
        """Test saving and loading survey data"""
        user_id = "test_user"
        subject = "python"
        
        survey_data = {
            "questions": [
                {
                    "id": 1,
                    "question": "What is a Python list?",
                    "type": "multiple_choice",
                    "options": ["Array", "Dictionary", "Ordered collection", "Function"],
                    "difficulty": "beginner"
                },
                {
                    "id": 2,
                    "question": "How do you create a virtual environment?",
                    "type": "text",
                    "difficulty": "intermediate"
                }
            ]
        }
        
        # Save survey
        UserDataService.save_survey(user_id, subject, survey_data)
        
        # Load survey
        loaded_survey = UserDataService.load_survey(user_id, subject)
        
        assert loaded_survey is not None
        assert loaded_survey["questions"] == survey_data["questions"]
        assert "generated_at" in loaded_survey
        
        # Verify timestamp format
        generated_at = loaded_survey["generated_at"]
        assert generated_at.endswith("Z")
        datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    
    def test_save_survey_invalid_data(self):
        """Test saving invalid survey data"""
        user_id = "test_user"
        subject = "python"
        
        # Test non-dict data
        with pytest.raises(UserDataServiceError, match="Survey data must be a dictionary"):
            UserDataService.save_survey(user_id, subject, "invalid")
        
        # Test missing questions field
        with pytest.raises(UserDataServiceError, match="Survey data must contain 'questions' field"):
            UserDataService.save_survey(user_id, subject, {"other": "data"})
        
        # Test non-list questions
        with pytest.raises(UserDataServiceError, match="Survey questions must be a list"):
            UserDataService.save_survey(user_id, subject, {"questions": "invalid"})
    
    def test_save_and_load_survey_answers(self):
        """Test saving and loading survey answers"""
        user_id = "test_user"
        subject = "python"
        
        answers_data = {
            "answers": [
                {
                    "question_id": 1,
                    "answer": "Ordered collection",
                    "correct": True
                },
                {
                    "question_id": 2,
                    "answer": "python -m venv myenv",
                    "correct": True
                }
            ],
            "skill_level": "intermediate"
        }
        
        # Save answers
        UserDataService.save_survey_answers(user_id, subject, answers_data)
        
        # Load answers
        loaded_answers = UserDataService.load_survey_answers(user_id, subject)
        
        assert loaded_answers is not None
        assert loaded_answers["answers"] == answers_data["answers"]
        assert loaded_answers["skill_level"] == answers_data["skill_level"]
        assert "submitted_at" in loaded_answers
        
        # Verify timestamp format
        submitted_at = loaded_answers["submitted_at"]
        assert submitted_at.endswith("Z")
        datetime.fromisoformat(submitted_at.replace("Z", "+00:00"))
    
    def test_save_survey_answers_invalid_data(self):
        """Test saving invalid survey answers data"""
        user_id = "test_user"
        subject = "python"
        
        # Test non-dict data
        with pytest.raises(UserDataServiceError, match="Survey answers data must be a dictionary"):
            UserDataService.save_survey_answers(user_id, subject, "invalid")
        
        # Test missing answers field
        with pytest.raises(UserDataServiceError, match="Survey answers data must contain 'answers' field"):
            UserDataService.save_survey_answers(user_id, subject, {"other": "data"})
        
        # Test non-list answers
        with pytest.raises(UserDataServiceError, match="Survey answers must be a list"):
            UserDataService.save_survey_answers(user_id, subject, {"answers": "invalid"})
    
    def test_save_and_load_lesson_metadata(self):
        """Test saving and loading lesson metadata"""
        user_id = "test_user"
        subject = "python"
        
        metadata = {
            "lessons": [
                {
                    "id": 1,
                    "title": "Python Basics",
                    "difficulty": "beginner",
                    "topics": ["variables", "data_types"],
                    "estimated_time": "30 minutes"
                },
                {
                    "id": 2,
                    "title": "Control Structures",
                    "difficulty": "intermediate",
                    "topics": ["if_statements", "loops"],
                    "estimated_time": "45 minutes"
                }
            ],
            "skill_level": "intermediate"
        }
        
        # Save metadata
        UserDataService.save_lesson_metadata(user_id, subject, metadata)
        
        # Load metadata
        loaded_metadata = UserDataService.load_lesson_metadata(user_id, subject)
        
        assert loaded_metadata is not None
        assert loaded_metadata["lessons"] == metadata["lessons"]
        assert loaded_metadata["skill_level"] == metadata["skill_level"]
        assert "generated_at" in loaded_metadata
        
        # Verify timestamp format
        generated_at = loaded_metadata["generated_at"]
        assert generated_at.endswith("Z")
        datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    
    def test_save_lesson_metadata_invalid_data(self):
        """Test saving invalid lesson metadata"""
        user_id = "test_user"
        subject = "python"
        
        # Test non-dict data
        with pytest.raises(UserDataServiceError, match="Lesson metadata must be a dictionary"):
            UserDataService.save_lesson_metadata(user_id, subject, "invalid")
        
        # Test missing lessons field
        with pytest.raises(UserDataServiceError, match="Lesson metadata must contain 'lessons' field"):
            UserDataService.save_lesson_metadata(user_id, subject, {"other": "data"})
        
        # Test non-list lessons
        with pytest.raises(UserDataServiceError, match="Lessons must be a list"):
            UserDataService.save_lesson_metadata(user_id, subject, {"lessons": "invalid"})
        
        # Test invalid lesson structure
        with pytest.raises(UserDataServiceError, match="Lesson 0 must be a dictionary"):
            UserDataService.save_lesson_metadata(user_id, subject, {"lessons": ["invalid"]})
        
        # Test missing required fields
        with pytest.raises(UserDataServiceError, match="Lesson 0 missing required field: id"):
            UserDataService.save_lesson_metadata(user_id, subject, {"lessons": [{"title": "Test"}]})
    
    def test_save_and_load_lesson_content(self):
        """Test saving and loading lesson content"""
        user_id = "test_user"
        subject = "python"
        lesson_id = 1
        
        content = """# Python Basics

This is a comprehensive lesson about Python basics.

## Variables

Variables in Python are created when you assign a value to them:

```python
x = 5
name = "Alice"
is_student = True
```

## Data Types

Python has several built-in data types:
- int: Integer numbers
- float: Decimal numbers
- str: Text strings
- bool: True/False values

## Quiz

1. What is the result of `type(5.0)`?
2. How do you create a string variable?
"""
        
        # Save lesson content
        UserDataService.save_lesson_content(user_id, subject, lesson_id, content)
        
        # Load lesson content
        loaded_content = UserDataService.load_lesson_content(user_id, subject, lesson_id)
        
        assert loaded_content == content
    
    def test_save_lesson_content_invalid_data(self):
        """Test saving invalid lesson content"""
        user_id = "test_user"
        subject = "python"
        
        # Test invalid lesson ID
        with pytest.raises(UserDataServiceError, match="Lesson ID must be a positive integer"):
            UserDataService.save_lesson_content(user_id, subject, 0, "content")
        
        with pytest.raises(UserDataServiceError, match="Lesson ID must be a positive integer"):
            UserDataService.save_lesson_content(user_id, subject, -1, "content")
        
        with pytest.raises(UserDataServiceError, match="Lesson ID must be a positive integer"):
            UserDataService.save_lesson_content(user_id, subject, "invalid", "content")
        
        # Test invalid content
        with pytest.raises(UserDataServiceError, match="Lesson content must be a string"):
            UserDataService.save_lesson_content(user_id, subject, 1, 123)
    
    def test_load_lesson_content_invalid_id(self):
        """Test loading lesson content with invalid ID"""
        user_id = "test_user"
        subject = "python"
        
        with pytest.raises(UserDataServiceError, match="Lesson ID must be a positive integer"):
            UserDataService.load_lesson_content(user_id, subject, 0)
    
    def test_load_nonexistent_lesson_content(self):
        """Test loading non-existent lesson content"""
        user_id = "test_user"
        subject = "python"
        lesson_id = 1
        
        result = UserDataService.load_lesson_content(user_id, subject, lesson_id)
        assert result is None
    
    def test_get_user_subjects(self):
        """Test getting list of user subjects"""
        user_id = "test_user"
        
        # Initially no subjects
        subjects = UserDataService.get_user_subjects(user_id)
        assert subjects == []
        
        # Create some subject directories with data
        UserDataService.save_survey(user_id, "python", {"questions": []})
        UserDataService.save_survey(user_id, "javascript", {"questions": []})
        UserDataService.save_survey(user_id, "data-science", {"questions": []})
        
        # Get subjects
        subjects = UserDataService.get_user_subjects(user_id)
        assert sorted(subjects) == ["data-science", "javascript", "python"]
    
    def test_get_user_subjects_nonexistent_user(self):
        """Test getting subjects for non-existent user"""
        subjects = UserDataService.get_user_subjects("nonexistent_user")
        assert subjects == []
    
    def test_get_lesson_files(self):
        """Test getting list of lesson files"""
        user_id = "test_user"
        subject = "python"
        
        # Initially no lessons
        lesson_ids = UserDataService.get_lesson_files(user_id, subject)
        assert lesson_ids == []
        
        # Create some lesson files
        UserDataService.save_lesson_content(user_id, subject, 1, "Lesson 1 content")
        UserDataService.save_lesson_content(user_id, subject, 3, "Lesson 3 content")
        UserDataService.save_lesson_content(user_id, subject, 2, "Lesson 2 content")
        
        # Get lesson IDs (should be sorted)
        lesson_ids = UserDataService.get_lesson_files(user_id, subject)
        assert lesson_ids == [1, 2, 3]
    
    def test_get_lesson_files_nonexistent_subject(self):
        """Test getting lesson files for non-existent subject"""
        user_id = "test_user"
        subject = "nonexistent"
        
        lesson_ids = UserDataService.get_lesson_files(user_id, subject)
        assert lesson_ids == []
    
    def test_delete_user_data(self):
        """Test deleting all user data"""
        user_id = "test_user"
        
        # Create some data
        UserDataService.save_user_selection(user_id, "python")
        UserDataService.save_survey(user_id, "python", {"questions": []})
        UserDataService.save_lesson_content(user_id, "python", 1, "content")
        
        # Verify data exists
        assert UserDataService.load_user_selection(user_id) is not None
        assert UserDataService.load_survey(user_id, "python") is not None
        
        # Delete user data
        UserDataService.delete_user_data(user_id)
        
        # Verify data is gone
        assert UserDataService.load_user_selection(user_id) is None
        assert UserDataService.load_survey(user_id, "python") is None
        assert UserDataService.get_user_subjects(user_id) == []
    
    def test_delete_subject_data(self):
        """Test deleting subject-specific data"""
        user_id = "test_user"
        
        # Create data for multiple subjects
        UserDataService.save_survey(user_id, "python", {"questions": []})
        UserDataService.save_survey(user_id, "javascript", {"questions": []})
        UserDataService.save_lesson_content(user_id, "python", 1, "content")
        
        # Verify data exists
        assert UserDataService.load_survey(user_id, "python") is not None
        assert UserDataService.load_survey(user_id, "javascript") is not None
        
        # Delete python subject data
        UserDataService.delete_subject_data(user_id, "python")
        
        # Verify python data is gone but javascript remains
        assert UserDataService.load_survey(user_id, "python") is None
        assert UserDataService.load_survey(user_id, "javascript") is not None
        
        subjects = UserDataService.get_user_subjects(user_id)
        assert subjects == ["javascript"]
    
    def test_delete_nonexistent_data(self):
        """Test deleting non-existent data (should not raise errors)"""
        # These should not raise exceptions
        UserDataService.delete_user_data("nonexistent_user")
        UserDataService.delete_subject_data("nonexistent_user", "nonexistent_subject")
    
    def test_integration_workflow(self):
        """Test complete workflow integration"""
        user_id = "test_user"
        subject = "python"
        
        # 1. User selects subject
        UserDataService.save_user_selection(user_id, subject)
        selection = UserDataService.load_user_selection(user_id)
        assert selection["selected_subject"] == subject
        
        # 2. System generates survey
        survey_data = {
            "questions": [
                {"id": 1, "question": "What is Python?", "type": "multiple_choice", "difficulty": "beginner"}
            ]
        }
        UserDataService.save_survey(user_id, subject, survey_data)
        
        # 3. User submits answers
        answers_data = {
            "answers": [{"question_id": 1, "answer": "Programming language", "correct": True}],
            "skill_level": "beginner"
        }
        UserDataService.save_survey_answers(user_id, subject, answers_data)
        
        # 4. System generates lessons
        metadata = {
            "lessons": [
                {"id": 1, "title": "Python Basics", "difficulty": "beginner"},
                {"id": 2, "title": "Variables", "difficulty": "beginner"}
            ],
            "skill_level": "beginner"
        }
        UserDataService.save_lesson_metadata(user_id, subject, metadata)
        
        # 5. System creates lesson content
        UserDataService.save_lesson_content(user_id, subject, 1, "# Python Basics\nContent here...")
        UserDataService.save_lesson_content(user_id, subject, 2, "# Variables\nMore content...")
        
        # 6. Verify all data is accessible
        assert UserDataService.load_survey(user_id, subject) is not None
        assert UserDataService.load_survey_answers(user_id, subject) is not None
        assert UserDataService.load_lesson_metadata(user_id, subject) is not None
        assert UserDataService.load_lesson_content(user_id, subject, 1) is not None
        assert UserDataService.load_lesson_content(user_id, subject, 2) is not None
        
        # 7. Verify file listing
        subjects = UserDataService.get_user_subjects(user_id)
        assert subject in subjects
        
        lesson_ids = UserDataService.get_lesson_files(user_id, subject)
        assert lesson_ids == [1, 2]