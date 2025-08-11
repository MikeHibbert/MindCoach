"""
User data service for managing user-specific data storage and retrieval
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from .file_service import FileService

logger = logging.getLogger(__name__)

class UserDataService:
    """Service for managing user-specific data storage and retrieval"""
    
    @staticmethod
    def save_curriculum_scheme(user_id: str, subject: str, curriculum_data: Dict[str, Any]) -> bool:
        """
        Save curriculum scheme data for a user and subject
        
        Args:
            user_id: User identifier
            subject: Subject name
            curriculum_data: Curriculum scheme data
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            file_path = f"users/{user_id}/{subject}/curriculum_scheme.json"
            
            # Add metadata
            curriculum_data['saved_at'] = datetime.utcnow().isoformat() + 'Z'
            curriculum_data['user_id'] = user_id
            curriculum_data['subject'] = subject
            
            FileService.save_json(file_path, curriculum_data)
            logger.info(f"Curriculum scheme saved for user {user_id}, subject {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save curriculum scheme for {user_id}/{subject}: {e}")
            return False
    
    @staticmethod
    def load_curriculum_scheme(user_id: str, subject: str) -> Optional[Dict[str, Any]]:
        """
        Load curriculum scheme data for a user and subject
        
        Args:
            user_id: User identifier
            subject: Subject name
            
        Returns:
            Curriculum scheme data or None if not found
        """
        try:
            file_path = f"users/{user_id}/{subject}/curriculum_scheme.json"
            data = FileService.load_json(file_path)
            
            if data:
                logger.debug(f"Curriculum scheme loaded for user {user_id}, subject {subject}")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load curriculum scheme for {user_id}/{subject}: {e}")
            return None
    
    @staticmethod
    def save_lesson_plans(user_id: str, subject: str, lesson_plans_data: Dict[str, Any]) -> bool:
        """
        Save lesson plans data for a user and subject
        
        Args:
            user_id: User identifier
            subject: Subject name
            lesson_plans_data: Lesson plans data
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            file_path = f"users/{user_id}/{subject}/lesson_plans.json"
            
            # Add metadata
            lesson_plans_data['saved_at'] = datetime.utcnow().isoformat() + 'Z'
            lesson_plans_data['user_id'] = user_id
            lesson_plans_data['subject'] = subject
            
            FileService.save_json(file_path, lesson_plans_data)
            logger.info(f"Lesson plans saved for user {user_id}, subject {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save lesson plans for {user_id}/{subject}: {e}")
            return False
    
    @staticmethod
    def load_lesson_plans(user_id: str, subject: str) -> Optional[Dict[str, Any]]:
        """
        Load lesson plans data for a user and subject
        
        Args:
            user_id: User identifier
            subject: Subject name
            
        Returns:
            Lesson plans data or None if not found
        """
        try:
            file_path = f"users/{user_id}/{subject}/lesson_plans.json"
            data = FileService.load_json(file_path)
            
            if data:
                logger.debug(f"Lesson plans loaded for user {user_id}, subject {subject}")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load lesson plans for {user_id}/{subject}: {e}")
            return None
    
    @staticmethod
    def save_lesson_content(user_id: str, subject: str, lesson_id: int, content: str) -> bool:
        """
        Save lesson content for a specific lesson
        
        Args:
            user_id: User identifier
            subject: Subject name
            lesson_id: Lesson identifier
            content: Lesson content (markdown)
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            file_path = f"users/{user_id}/{subject}/lesson_{lesson_id}.md"
            
            # Add metadata header to content
            metadata_header = f"""---
user_id: {user_id}
subject: {subject}
lesson_id: {lesson_id}
generated_at: {datetime.utcnow().isoformat()}Z
generation_method: langchain
---

"""
            
            full_content = metadata_header + content
            FileService.save_markdown(file_path, full_content)
            
            logger.info(f"Lesson {lesson_id} content saved for user {user_id}, subject {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save lesson {lesson_id} content for {user_id}/{subject}: {e}")
            return False
    
    @staticmethod
    def load_lesson_content(user_id: str, subject: str, lesson_id: int) -> Optional[str]:
        """
        Load lesson content for a specific lesson
        
        Args:
            user_id: User identifier
            subject: Subject name
            lesson_id: Lesson identifier
            
        Returns:
            Lesson content or None if not found
        """
        try:
            file_path = f"users/{user_id}/{subject}/lesson_{lesson_id}.md"
            content = FileService.load_markdown(file_path)
            
            if content:
                logger.debug(f"Lesson {lesson_id} content loaded for user {user_id}, subject {subject}")
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to load lesson {lesson_id} content for {user_id}/{subject}: {e}")
            return None
    
    @staticmethod
    def load_survey_answers(user_id: str, subject: str) -> Optional[Dict[str, Any]]:
        """
        Load survey answers for a user and subject
        
        Args:
            user_id: User identifier
            subject: Subject name
            
        Returns:
            Survey answers data or None if not found
        """
        try:
            file_path = f"users/{user_id}/{subject}/survey_answers.json"
            data = FileService.load_json(file_path)
            
            if data:
                logger.debug(f"Survey answers loaded for user {user_id}, subject {subject}")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load survey answers for {user_id}/{subject}: {e}")
            return None
    
    @staticmethod
    def save_generation_status(user_id: str, subject: str, status_data: Dict[str, Any]) -> bool:
        """
        Save generation status for tracking pipeline progress
        
        Args:
            user_id: User identifier
            subject: Subject name
            status_data: Status data
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            file_path = f"users/{user_id}/{subject}/generation_status.json"
            
            # Add metadata
            status_data['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            status_data['user_id'] = user_id
            status_data['subject'] = subject
            
            FileService.save_json(file_path, status_data)
            logger.debug(f"Generation status saved for user {user_id}, subject {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save generation status for {user_id}/{subject}: {e}")
            return False
    
    @staticmethod
    def load_generation_status(user_id: str, subject: str) -> Optional[Dict[str, Any]]:
        """
        Load generation status for a user and subject
        
        Args:
            user_id: User identifier
            subject: Subject name
            
        Returns:
            Generation status data or None if not found
        """
        try:
            file_path = f"users/{user_id}/{subject}/generation_status.json"
            data = FileService.load_json(file_path)
            
            if data:
                logger.debug(f"Generation status loaded for user {user_id}, subject {subject}")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load generation status for {user_id}/{subject}: {e}")
            return None
    
    @staticmethod
    def list_user_subjects(user_id: str) -> List[str]:
        """
        List all subjects for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of subject names
        """
        try:
            user_dir = f"users/{user_id}"
            if not os.path.exists(user_dir):
                return []
            
            subjects = []
            for item in os.listdir(user_dir):
                item_path = os.path.join(user_dir, item)
                if os.path.isdir(item_path) and item != '__pycache__':
                    subjects.append(item)
            
            logger.debug(f"Found {len(subjects)} subjects for user {user_id}")
            return subjects
            
        except Exception as e:
            logger.error(f"Failed to list subjects for user {user_id}: {e}")
            return []
    
    @staticmethod
    def list_user_lessons(user_id: str, subject: str) -> List[int]:
        """
        List all lesson IDs for a user and subject
        
        Args:
            user_id: User identifier
            subject: Subject name
            
        Returns:
            List of lesson IDs
        """
        try:
            subject_dir = f"users/{user_id}/{subject}"
            if not os.path.exists(subject_dir):
                return []
            
            lesson_ids = []
            for filename in os.listdir(subject_dir):
                if filename.startswith('lesson_') and filename.endswith('.md'):
                    try:
                        lesson_id = int(filename.replace('lesson_', '').replace('.md', ''))
                        lesson_ids.append(lesson_id)
                    except ValueError:
                        continue
            
            lesson_ids.sort()
            logger.debug(f"Found {len(lesson_ids)} lessons for user {user_id}, subject {subject}")
            return lesson_ids
            
        except Exception as e:
            logger.error(f"Failed to list lessons for {user_id}/{subject}: {e}")
            return []
    
    @staticmethod
    def delete_user_subject_data(user_id: str, subject: str) -> bool:
        """
        Delete all data for a user and subject
        
        Args:
            user_id: User identifier
            subject: Subject name
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            import shutil
            
            subject_dir = f"users/{user_id}/{subject}"
            if os.path.exists(subject_dir):
                shutil.rmtree(subject_dir)
                logger.info(f"Deleted all data for user {user_id}, subject {subject}")
                return True
            else:
                logger.warning(f"No data found to delete for user {user_id}, subject {subject}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete data for {user_id}/{subject}: {e}")
            return False