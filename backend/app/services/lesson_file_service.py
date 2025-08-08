"""
Lesson file management service for handling lesson storage, retrieval, and metadata management
"""

import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import logging

from app.services.file_service import FileService
from app.services.lesson_generation_service import LessonGenerationService

logger = logging.getLogger(__name__)

class LessonFileService:
    """Service for managing lesson files and metadata in the file system"""
    
    # Lesson file naming pattern
    LESSON_FILE_PATTERN = "lesson_{}.md"
    METADATA_FILE = "lesson_metadata.json"
    
    # Content validation patterns
    MIN_CONTENT_LENGTH = 100
    MAX_CONTENT_LENGTH = 50000
    
    @classmethod
    def save_lessons(cls, user_id: str, subject: str, lessons: List[Dict[str, Any]], 
                    metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save generated lessons as markdown files and metadata as JSON
        
        Args:
            user_id: The user ID
            subject: The subject
            lessons: List of lesson dictionaries
            metadata: Lesson generation metadata
            
        Returns:
            Dictionary containing save results
            
        Raises:
            ValueError: If lessons or metadata are invalid
            FileServiceError: If file operations fail
        """
        logger.info(f"Saving {len(lessons)} lessons for user {user_id}, subject {subject}")
        
        # Validate input
        cls._validate_lessons_for_save(lessons)
        cls._validate_metadata(metadata)
        
        # Ensure subject directory exists
        subject_dir = FileService.ensure_subject_directory(user_id, subject)
        
        saved_files = []
        failed_files = []
        
        try:
            # Save individual lesson files
            for lesson in lessons:
                try:
                    file_path = cls._save_lesson_file(subject_dir, lesson)
                    saved_files.append({
                        'lesson_number': lesson['lesson_number'],
                        'file_path': str(file_path),
                        'title': lesson['title']
                    })
                    logger.info(f"Saved lesson {lesson['lesson_number']}: {lesson['title']}")
                except Exception as e:
                    logger.error(f"Failed to save lesson {lesson['lesson_number']}: {str(e)}")
                    failed_files.append({
                        'lesson_number': lesson['lesson_number'],
                        'error': str(e)
                    })
            
            # Save metadata file
            metadata_path = subject_dir / cls.METADATA_FILE
            FileService.save_json(metadata_path, metadata)
            logger.info(f"Saved lesson metadata to {metadata_path}")
            
            # Create summary
            save_results = {
                'user_id': user_id,
                'subject': subject,
                'total_lessons': len(lessons),
                'saved_successfully': len(saved_files),
                'failed_saves': len(failed_files),
                'saved_files': saved_files,
                'failed_files': failed_files,
                'metadata_saved': True,
                'saved_at': datetime.utcnow().isoformat()
            }
            
            if failed_files:
                logger.warning(f"Some lessons failed to save: {len(failed_files)} out of {len(lessons)}")
            else:
                logger.info(f"Successfully saved all {len(lessons)} lessons")
            
            return save_results
            
        except Exception as e:
            logger.error(f"Critical error during lesson save operation: {str(e)}")
            raise
    
    @classmethod
    def load_lessons(cls, user_id: str, subject: str) -> Dict[str, Any]:
        """
        Load all lessons for a user and subject
        
        Args:
            user_id: The user ID
            subject: The subject
            
        Returns:
            Dictionary containing lessons and metadata
            
        Raises:
            FileNotFoundError: If lessons don't exist
        """
        logger.info(f"Loading lessons for user {user_id}, subject {subject}")
        
        subject_dir = FileService.get_subject_directory(user_id, subject)
        
        if not subject_dir.exists():
            raise FileNotFoundError(f"No lessons found for user {user_id}, subject {subject}")
        
        # Load metadata
        metadata_path = subject_dir / cls.METADATA_FILE
        metadata = FileService.load_json(metadata_path)
        
        if not metadata:
            raise FileNotFoundError(f"Lesson metadata not found for user {user_id}, subject {subject}")
        
        # Load individual lesson files
        lessons = []
        missing_lessons = []
        
        for lesson_info in metadata.get('lessons', []):
            lesson_number = lesson_info['lesson_number']
            
            try:
                lesson_content = cls._load_lesson_file(subject_dir, lesson_number)
                lesson = {
                    'lesson_number': lesson_number,
                    'title': lesson_info['title'],
                    'estimated_time': lesson_info['estimated_time'],
                    'topics': lesson_info['topics'],
                    'difficulty': lesson_info['difficulty'],
                    'content': lesson_content,
                    'file_path': str(subject_dir / cls.LESSON_FILE_PATTERN.format(lesson_number))
                }
                lessons.append(lesson)
                
            except Exception as e:
                logger.error(f"Failed to load lesson {lesson_number}: {str(e)}")
                missing_lessons.append({
                    'lesson_number': lesson_number,
                    'error': str(e)
                })
        
        # Sort lessons by lesson number
        lessons.sort(key=lambda x: x['lesson_number'])
        
        result = {
            'user_id': user_id,
            'subject': subject,
            'lessons': lessons,
            'metadata': metadata,
            'total_lessons': len(lessons),
            'missing_lessons': missing_lessons,
            'loaded_at': datetime.utcnow().isoformat()
        }
        
        if missing_lessons:
            logger.warning(f"Some lessons could not be loaded: {len(missing_lessons)}")
        else:
            logger.info(f"Successfully loaded all {len(lessons)} lessons")
        
        return result
    
    @classmethod
    def get_lesson(cls, user_id: str, subject: str, lesson_number: int) -> Dict[str, Any]:
        """
        Load a specific lesson by number
        
        Args:
            user_id: The user ID
            subject: The subject
            lesson_number: The lesson number to load
            
        Returns:
            Dictionary containing the lesson
            
        Raises:
            FileNotFoundError: If lesson doesn't exist
            ValueError: If lesson number is invalid
        """
        if lesson_number < 1 or lesson_number > 10:
            raise ValueError(f"Invalid lesson number: {lesson_number}. Must be between 1 and 10")
        
        logger.info(f"Loading lesson {lesson_number} for user {user_id}, subject {subject}")
        
        subject_dir = FileService.get_subject_directory(user_id, subject)
        
        # Load metadata to get lesson info
        metadata_path = subject_dir / cls.METADATA_FILE
        metadata = FileService.load_json(metadata_path)
        
        if not metadata:
            raise FileNotFoundError(f"Lesson metadata not found for user {user_id}, subject {subject}")
        
        # Find lesson info in metadata
        lesson_info = None
        for lesson in metadata.get('lessons', []):
            if lesson['lesson_number'] == lesson_number:
                lesson_info = lesson
                break
        
        if not lesson_info:
            raise FileNotFoundError(f"Lesson {lesson_number} not found in metadata")
        
        # Load lesson content
        lesson_content = cls._load_lesson_file(subject_dir, lesson_number)
        
        lesson = {
            'lesson_number': lesson_number,
            'title': lesson_info['title'],
            'estimated_time': lesson_info['estimated_time'],
            'topics': lesson_info['topics'],
            'difficulty': lesson_info['difficulty'],
            'content': lesson_content,
            'file_path': str(subject_dir / cls.LESSON_FILE_PATTERN.format(lesson_number)),
            'loaded_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Successfully loaded lesson {lesson_number}: {lesson_info['title']}")
        return lesson
    
    @classmethod
    def list_lessons(cls, user_id: str, subject: str) -> Dict[str, Any]:
        """
        Get a list of available lessons without loading full content
        
        Args:
            user_id: The user ID
            subject: The subject
            
        Returns:
            Dictionary containing lesson list and metadata
        """
        logger.info(f"Listing lessons for user {user_id}, subject {subject}")
        
        subject_dir = FileService.get_subject_directory(user_id, subject)
        
        # Load metadata
        metadata_path = subject_dir / cls.METADATA_FILE
        metadata = FileService.load_json(metadata_path)
        
        if not metadata:
            return {
                'user_id': user_id,
                'subject': subject,
                'lessons': [],
                'total_lessons': 0,
                'generated_at': None
            }
        
        # Check which lesson files actually exist
        available_lessons = []
        for lesson_info in metadata.get('lessons', []):
            lesson_number = lesson_info['lesson_number']
            lesson_file = subject_dir / cls.LESSON_FILE_PATTERN.format(lesson_number)
            
            if lesson_file.exists():
                available_lessons.append({
                    'lesson_number': lesson_number,
                    'title': lesson_info['title'],
                    'estimated_time': lesson_info['estimated_time'],
                    'topics': lesson_info['topics'],
                    'difficulty': lesson_info['difficulty'],
                    'file_exists': True
                })
            else:
                available_lessons.append({
                    'lesson_number': lesson_number,
                    'title': lesson_info['title'],
                    'estimated_time': lesson_info['estimated_time'],
                    'topics': lesson_info['topics'],
                    'difficulty': lesson_info['difficulty'],
                    'file_exists': False
                })
        
        # Sort by lesson number
        available_lessons.sort(key=lambda x: x['lesson_number'])
        
        return {
            'user_id': user_id,
            'subject': subject,
            'lessons': available_lessons,
            'total_lessons': len(available_lessons),
            'skill_level': metadata.get('skill_level'),
            'generated_at': metadata.get('generated_at')
        }
    
    @classmethod
    def delete_lessons(cls, user_id: str, subject: str) -> Dict[str, Any]:
        """
        Delete all lessons for a user and subject
        
        Args:
            user_id: The user ID
            subject: The subject
            
        Returns:
            Dictionary containing deletion results
        """
        logger.info(f"Deleting lessons for user {user_id}, subject {subject}")
        
        subject_dir = FileService.get_subject_directory(user_id, subject)
        
        if not subject_dir.exists():
            return {
                'user_id': user_id,
                'subject': subject,
                'deleted_files': [],
                'total_deleted': 0,
                'message': 'No lessons found to delete'
            }
        
        deleted_files = []
        
        # Delete lesson files
        for i in range(1, 11):  # Lessons 1-10
            lesson_file = subject_dir / cls.LESSON_FILE_PATTERN.format(i)
            if lesson_file.exists():
                try:
                    FileService.delete_file(lesson_file)
                    deleted_files.append(f"lesson_{i}.md")
                    logger.info(f"Deleted lesson file: {lesson_file}")
                except Exception as e:
                    logger.error(f"Failed to delete lesson file {lesson_file}: {str(e)}")
        
        # Delete metadata file
        metadata_file = subject_dir / cls.METADATA_FILE
        if metadata_file.exists():
            try:
                FileService.delete_file(metadata_file)
                deleted_files.append(cls.METADATA_FILE)
                logger.info(f"Deleted metadata file: {metadata_file}")
            except Exception as e:
                logger.error(f"Failed to delete metadata file {metadata_file}: {str(e)}")
        
        return {
            'user_id': user_id,
            'subject': subject,
            'deleted_files': deleted_files,
            'total_deleted': len(deleted_files),
            'deleted_at': datetime.utcnow().isoformat()
        }
    
    @classmethod
    def validate_lesson_content(cls, content: str) -> Dict[str, Any]:
        """
        Validate lesson content for quality and structure
        
        Args:
            content: The lesson content to validate
            
        Returns:
            Dictionary containing validation results
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'content_length': len(content),
            'structure_score': 0
        }
        
        # Check content length
        if len(content) < cls.MIN_CONTENT_LENGTH:
            validation_results['errors'].append(f"Content too short: {len(content)} characters (minimum: {cls.MIN_CONTENT_LENGTH})")
            validation_results['is_valid'] = False
        
        if len(content) > cls.MAX_CONTENT_LENGTH:
            validation_results['errors'].append(f"Content too long: {len(content)} characters (maximum: {cls.MAX_CONTENT_LENGTH})")
            validation_results['is_valid'] = False
        
        # Check for required sections
        required_sections = ['# ', '## Introduction', '## What You\'ll Learn', '## Summary']
        missing_sections = []
        
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            validation_results['errors'].append(f"Missing required sections: {', '.join(missing_sections)}")
            validation_results['is_valid'] = False
        
        # Check for code examples
        if '```' not in content:
            validation_results['warnings'].append("No code examples found")
        else:
            # Count code blocks
            code_blocks = content.count('```') // 2
            validation_results['code_blocks'] = code_blocks
            if code_blocks < 2:
                validation_results['warnings'].append("Few code examples (recommended: at least 2)")
        
        # Check for quiz section
        if '## Quiz' not in content:
            validation_results['warnings'].append("No quiz section found")
        
        # Calculate structure score
        structure_score = 0
        if '# ' in content:  # Has main title
            structure_score += 20
        if '## Introduction' in content:
            structure_score += 15
        if '## What You\'ll Learn' in content:
            structure_score += 15
        if '```' in content:  # Has code examples
            structure_score += 25
        if '## Quiz' in content:
            structure_score += 15
        if '## Summary' in content:
            structure_score += 10
        
        validation_results['structure_score'] = structure_score
        
        # Overall quality assessment
        if structure_score >= 80:
            validation_results['quality'] = 'excellent'
        elif structure_score >= 60:
            validation_results['quality'] = 'good'
        elif structure_score >= 40:
            validation_results['quality'] = 'fair'
        else:
            validation_results['quality'] = 'poor'
            validation_results['warnings'].append("Low structure score - content may be incomplete")
        
        return validation_results
    
    @classmethod
    def _save_lesson_file(cls, subject_dir: Path, lesson: Dict[str, Any]) -> Path:
        """Save a single lesson as a markdown file"""
        lesson_number = lesson['lesson_number']
        content = lesson['content']
        
        # Validate content before saving
        validation = cls.validate_lesson_content(content)
        if not validation['is_valid']:
            raise ValueError(f"Invalid lesson content: {', '.join(validation['errors'])}")
        
        # Create file path
        file_path = subject_dir / cls.LESSON_FILE_PATTERN.format(lesson_number)
        
        # Add metadata header to content
        header = f"""---
lesson_number: {lesson_number}
title: "{lesson['title']}"
estimated_time: "{lesson['estimated_time']}"
difficulty: "{lesson['difficulty']}"
topics: {json.dumps(lesson['topics'])}
generated_at: "{lesson.get('generated_at', datetime.utcnow().isoformat())}"
---

"""
        
        full_content = header + content
        
        # Save the file
        FileService.save_markdown(file_path, full_content)
        
        return file_path
    
    @classmethod
    def _load_lesson_file(cls, subject_dir: Path, lesson_number: int) -> str:
        """Load a single lesson file and extract content"""
        file_path = subject_dir / cls.LESSON_FILE_PATTERN.format(lesson_number)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Lesson file not found: {file_path}")
        
        # Load the full file content
        full_content = FileService.load_markdown(file_path)
        
        if not full_content:
            raise ValueError(f"Lesson file is empty: {file_path}")
        
        # Extract content (remove metadata header if present)
        if full_content.startswith('---'):
            # Find the end of the metadata header
            parts = full_content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2].strip()
            else:
                content = full_content
        else:
            content = full_content
        
        return content
    
    @classmethod
    def _validate_lessons_for_save(cls, lessons: List[Dict[str, Any]]) -> None:
        """Validate lessons before saving"""
        if not lessons:
            raise ValueError("Lessons list cannot be empty")
        
        if len(lessons) > 10:
            raise ValueError(f"Too many lessons: {len(lessons)} (maximum: 10)")
        
        lesson_numbers = set()
        for lesson in lessons:
            # Validate lesson structure
            if not LessonGenerationService.validate_lesson_structure(lesson):
                raise ValueError(f"Invalid lesson structure for lesson {lesson.get('lesson_number', 'unknown')}")
            
            # Check for duplicate lesson numbers
            lesson_number = lesson['lesson_number']
            if lesson_number in lesson_numbers:
                raise ValueError(f"Duplicate lesson number: {lesson_number}")
            lesson_numbers.add(lesson_number)
            
            # Validate content
            validation = cls.validate_lesson_content(lesson['content'])
            if not validation['is_valid']:
                raise ValueError(f"Invalid content for lesson {lesson_number}: {', '.join(validation['errors'])}")
    
    @classmethod
    def _validate_metadata(cls, metadata: Dict[str, Any]) -> None:
        """Validate lesson metadata"""
        required_fields = ['user_id', 'subject', 'skill_level', 'total_lessons', 'generated_at', 'lessons']
        
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Metadata missing required field: {field}")
        
        # Validate skill level
        if metadata['skill_level'] not in ['beginner', 'intermediate', 'advanced']:
            raise ValueError(f"Invalid skill level: {metadata['skill_level']}")
        
        # Validate lessons list in metadata
        if not isinstance(metadata['lessons'], list):
            raise ValueError("Metadata lessons must be a list")
        
        if len(metadata['lessons']) != metadata['total_lessons']:
            raise ValueError("Metadata total_lessons doesn't match lessons list length")