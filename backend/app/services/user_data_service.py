from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path

from .file_service import FileService, FileServiceError


class UserDataServiceError(Exception):
    """Custom exception for user data service errors"""
    pass


class UserDataService:
    """Service for managing user-specific data files (selections, surveys, lessons)"""
    
    # File names for different data types
    SELECTION_FILE = "selection.json"
    SURVEY_FILE = "survey.json"
    SURVEY_ANSWERS_FILE = "survey_answers.json"
    LESSON_METADATA_FILE = "lesson_metadata.json"
    
    @classmethod
    def save_user_selection(cls, user_id: str, subject: str) -> None:
        """Save user's subject selection to selection.json"""
        try:
            # Ensure user directory exists
            user_dir = FileService.ensure_user_directory(user_id)
            selection_path = user_dir / cls.SELECTION_FILE
            
            selection_data = {
                "selected_subject": subject,
                "selected_at": datetime.utcnow().isoformat() + "Z"
            }
            
            FileService.save_json(selection_path, selection_data)
            
        except FileServiceError as e:
            raise UserDataServiceError(f"Failed to save user selection: {e}")
    
    @classmethod
    def load_user_selection(cls, user_id: str) -> Optional[Dict[str, Any]]:
        """Load user's subject selection from selection.json"""
        try:
            user_dir = FileService.get_user_directory(user_id)
            selection_path = user_dir / cls.SELECTION_FILE
            
            return FileService.load_json(selection_path)
            
        except FileServiceError as e:
            raise UserDataServiceError(f"Failed to load user selection: {e}")
    
    @classmethod
    def save_survey(cls, user_id: str, subject: str, survey_data: Dict[str, Any]) -> None:
        """Save survey questions to survey.json"""
        try:
            # Validate survey data structure
            if not isinstance(survey_data, dict):
                raise UserDataServiceError("Survey data must be a dictionary")
            
            if "questions" not in survey_data:
                raise UserDataServiceError("Survey data must contain 'questions' field")
            
            if not isinstance(survey_data["questions"], list):
                raise UserDataServiceError("Survey questions must be a list")
            
            # Ensure subject directory exists
            subject_dir = FileService.ensure_subject_directory(user_id, subject)
            survey_path = subject_dir / cls.SURVEY_FILE
            
            # Add metadata
            survey_data_with_meta = {
                **survey_data,
                "generated_at": datetime.utcnow().isoformat() + "Z"
            }
            
            FileService.save_json(survey_path, survey_data_with_meta)
            
        except FileServiceError as e:
            raise UserDataServiceError(f"Failed to save survey: {e}")
    
    @classmethod
    def load_survey(cls, user_id: str, subject: str) -> Optional[Dict[str, Any]]:
        """Load survey questions from survey.json"""
        try:
            subject_dir = FileService.get_subject_directory(user_id, subject)
            survey_path = subject_dir / cls.SURVEY_FILE
            
            return FileService.load_json(survey_path)
            
        except FileServiceError as e:
            raise UserDataServiceError(f"Failed to load survey: {e}")
    
    @classmethod
    def save_survey_answers(cls, user_id: str, subject: str, answers_data: Dict[str, Any]) -> None:
        """Save survey answers to survey_answers.json"""
        try:
            # Validate answers data structure
            if not isinstance(answers_data, dict):
                raise UserDataServiceError("Survey answers data must be a dictionary")
            
            if "answers" not in answers_data:
                raise UserDataServiceError("Survey answers data must contain 'answers' field")
            
            if not isinstance(answers_data["answers"], list):
                raise UserDataServiceError("Survey answers must be a list")
            
            # Ensure subject directory exists
            subject_dir = FileService.ensure_subject_directory(user_id, subject)
            answers_path = subject_dir / cls.SURVEY_ANSWERS_FILE
            
            # Add metadata
            answers_data_with_meta = {
                **answers_data,
                "submitted_at": datetime.utcnow().isoformat() + "Z"
            }
            
            FileService.save_json(answers_path, answers_data_with_meta)
            
        except FileServiceError as e:
            raise UserDataServiceError(f"Failed to save survey answers: {e}")
    
    @classmethod
    def load_survey_answers(cls, user_id: str, subject: str) -> Optional[Dict[str, Any]]:
        """Load survey answers from survey_answers.json"""
        try:
            subject_dir = FileService.get_subject_directory(user_id, subject)
            answers_path = subject_dir / cls.SURVEY_ANSWERS_FILE
            
            return FileService.load_json(answers_path)
            
        except FileServiceError as e:
            raise UserDataServiceError(f"Failed to load survey answers: {e}")
    
    @classmethod
    def save_lesson_metadata(cls, user_id: str, subject: str, metadata: Dict[str, Any]) -> None:
        """Save lesson metadata to lesson_metadata.json"""
        try:
            # Validate metadata structure
            if not isinstance(metadata, dict):
                raise UserDataServiceError("Lesson metadata must be a dictionary")
            
            if "lessons" not in metadata:
                raise UserDataServiceError("Lesson metadata must contain 'lessons' field")
            
            if not isinstance(metadata["lessons"], list):
                raise UserDataServiceError("Lessons must be a list")
            
            # Validate each lesson entry
            for i, lesson in enumerate(metadata["lessons"]):
                if not isinstance(lesson, dict):
                    raise UserDataServiceError(f"Lesson {i} must be a dictionary")
                
                required_fields = ["id", "title", "difficulty"]
                for field in required_fields:
                    if field not in lesson:
                        raise UserDataServiceError(f"Lesson {i} missing required field: {field}")
            
            # Ensure subject directory exists
            subject_dir = FileService.ensure_subject_directory(user_id, subject)
            metadata_path = subject_dir / cls.LESSON_METADATA_FILE
            
            # Add metadata
            metadata_with_meta = {
                **metadata,
                "generated_at": datetime.utcnow().isoformat() + "Z"
            }
            
            FileService.save_json(metadata_path, metadata_with_meta)
            
        except FileServiceError as e:
            raise UserDataServiceError(f"Failed to save lesson metadata: {e}")
    
    @classmethod
    def load_lesson_metadata(cls, user_id: str, subject: str) -> Optional[Dict[str, Any]]:
        """Load lesson metadata from lesson_metadata.json"""
        try:
            subject_dir = FileService.get_subject_directory(user_id, subject)
            metadata_path = subject_dir / cls.LESSON_METADATA_FILE
            
            return FileService.load_json(metadata_path)
            
        except FileServiceError as e:
            raise UserDataServiceError(f"Failed to load lesson metadata: {e}")
    
    @classmethod
    def save_lesson_content(cls, user_id: str, subject: str, lesson_id: int, content: str) -> None:
        """Save lesson content as markdown file"""
        try:
            if not isinstance(lesson_id, int) or lesson_id < 1:
                raise UserDataServiceError("Lesson ID must be a positive integer")
            
            if not isinstance(content, str):
                raise UserDataServiceError("Lesson content must be a string")
            
            # Ensure subject directory exists
            subject_dir = FileService.ensure_subject_directory(user_id, subject)
            lesson_path = subject_dir / f"lesson_{lesson_id}.md"
            
            FileService.save_markdown(lesson_path, content)
            
        except FileServiceError as e:
            raise UserDataServiceError(f"Failed to save lesson content: {e}")
    
    @classmethod
    def load_lesson_content(cls, user_id: str, subject: str, lesson_id: int) -> Optional[str]:
        """Load lesson content from markdown file"""
        try:
            if not isinstance(lesson_id, int) or lesson_id < 1:
                raise UserDataServiceError("Lesson ID must be a positive integer")
            
            subject_dir = FileService.get_subject_directory(user_id, subject)
            lesson_path = subject_dir / f"lesson_{lesson_id}.md"
            
            return FileService.load_markdown(lesson_path)
            
        except FileServiceError as e:
            raise UserDataServiceError(f"Failed to load lesson content: {e}")
    
    @classmethod
    def get_user_subjects(cls, user_id: str) -> List[str]:
        """Get list of subjects for which user has data"""
        try:
            user_dir = FileService.get_user_directory(user_id)
            
            if not user_dir.exists():
                return []
            
            subjects = []
            for item in user_dir.iterdir():
                if item.is_dir() and item.name not in ['.', '..']:
                    # Validate subject name
                    try:
                        FileService._validate_subject(item.name)
                        subjects.append(item.name)
                    except FileServiceError:
                        # Skip invalid directory names
                        continue
            
            return sorted(subjects)
            
        except FileServiceError as e:
            raise UserDataServiceError(f"Failed to get user subjects: {e}")
    
    @classmethod
    def get_lesson_files(cls, user_id: str, subject: str) -> List[int]:
        """Get list of lesson IDs that have content files"""
        try:
            subject_dir = FileService.get_subject_directory(user_id, subject)
            
            if not subject_dir.exists():
                return []
            
            lesson_ids = []
            for item in subject_dir.iterdir():
                if item.is_file() and item.name.startswith("lesson_") and item.name.endswith(".md"):
                    try:
                        # Extract lesson ID from filename
                        lesson_id_str = item.name[7:-3]  # Remove "lesson_" and ".md"
                        lesson_id = int(lesson_id_str)
                        lesson_ids.append(lesson_id)
                    except ValueError:
                        # Skip files with invalid lesson ID format
                        continue
            
            return sorted(lesson_ids)
            
        except FileServiceError as e:
            raise UserDataServiceError(f"Failed to get lesson files: {e}")
    
    @classmethod
    def delete_user_data(cls, user_id: str) -> None:
        """Delete all data for a user"""
        try:
            user_dir = FileService.get_user_directory(user_id)
            
            if user_dir.exists():
                import shutil
                shutil.rmtree(user_dir)
                
        except (FileServiceError, OSError) as e:
            raise UserDataServiceError(f"Failed to delete user data: {e}")
    
    @classmethod
    def delete_subject_data(cls, user_id: str, subject: str) -> None:
        """Delete all data for a user's subject"""
        try:
            subject_dir = FileService.get_subject_directory(user_id, subject)
            
            if subject_dir.exists():
                import shutil
                shutil.rmtree(subject_dir)
                
        except (FileServiceError, OSError) as e:
            raise UserDataServiceError(f"Failed to delete subject data: {e}")
    
    @classmethod
    def save_subject_selection(cls, user_id: str, subject: str) -> bool:
        """Save user's subject selection to selection.json (alias for save_user_selection)"""
        try:
            cls.save_user_selection(user_id, subject)
            return True
        except UserDataServiceError:
            return False
    
    @classmethod
    def has_subject_selection(cls, user_id: str, subject: str) -> bool:
        """Check if user has selected a specific subject"""
        try:
            selection_data = cls.load_user_selection(user_id)
            if not selection_data:
                return False
            
            return selection_data.get("selected_subject") == subject
            
        except UserDataServiceError:
            return False