"""
Tests for lesson generation service
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.services.lesson_generation_service import LessonGenerationService
from app.services.survey_analysis_service import SurveyAnalysisService


class TestLessonGenerationService:
    
    def setup_method(self):
        """Set up test environment"""
        self.test_user_id = "test_user_123"
        self.test_subject = "python"
        
        # Mock survey results
        self.mock_survey_results = {
            'user_id': self.test_user_id,
            'subject': self.test_subject,
            'skill_level': 'intermediate',
            'topic_analysis': {
                'strengths': ['functions', 'variables'],
                'weaknesses': ['classes', 'decorators'],
                'topic_scores': {
                    'functions': {'accuracy': 0.9, 'correct': 9, 'total': 10},
                    'variables': {'accuracy': 0.8, 'correct': 8, 'total': 10},
                    'classes': {'accuracy': 0.4, 'correct': 4, 'total': 10},
                    'decorators': {'accuracy': 0.3, 'correct': 3, 'total': 10}
                }
            },
            'processed_answers': []
        }
    
    def test_get_supported_subjects(self):
        """Test getting supported subjects"""
        subjects = LessonGenerationService.get_supported_subjects()
        assert isinstance(subjects, list)
        assert 'python' in subjects
        assert 'javascript' in subjects
    
    @patch.object(SurveyAnalysisService, 'get_survey_results')
    def test_generate_personalized_lessons_success(self, mock_get_survey_results):
        """Test successful lesson generation"""
        mock_get_survey_results.return_value = self.mock_survey_results
        
        result = LessonGenerationService.generate_personalized_lessons(
            self.test_user_id, 
            self.test_subject
        )
        
        # Verify structure
        assert 'lessons' in result
        assert 'metadata' in result
        
        lessons = result['lessons']
        metadata = result['metadata']
        
        # Verify lessons
        assert isinstance(lessons, list)
        assert len(lessons) <= 5  # Should not exceed 5 lessons
        assert len(lessons) > 0    # Should have at least some lessons
        
        # Verify each lesson structure
        for lesson in lessons:
            assert LessonGenerationService.validate_lesson_structure(lesson)
            assert 'lesson_number' in lesson
            assert 'title' in lesson
            assert 'content' in lesson
            assert 'difficulty' in lesson
            assert 'topics' in lesson
        
        # Verify metadata
        assert metadata['user_id'] == self.test_user_id
        assert metadata['subject'] == self.test_subject
        assert metadata['skill_level'] == 'intermediate'
        assert metadata['total_lessons'] == len(lessons)
        assert 'generated_at' in metadata
        assert 'topic_analysis' in metadata
    
    @patch.object(SurveyAnalysisService, 'get_survey_results')
    def test_generate_lessons_no_survey_results(self, mock_get_survey_results):
        """Test lesson generation when no survey results exist"""
        mock_get_survey_results.return_value = None
        
        with pytest.raises(FileNotFoundError) as exc_info:
            LessonGenerationService.generate_personalized_lessons(
                self.test_user_id, 
                self.test_subject
            )
        
        assert "Survey results not found" in str(exc_info.value)
    
    def test_generate_lessons_unsupported_subject(self):
        """Test lesson generation for unsupported subject"""
        with pytest.raises(ValueError) as exc_info:
            LessonGenerationService.generate_personalized_lessons(
                self.test_user_id, 
                "unsupported_subject"
            )
        
        assert "not supported for lesson generation" in str(exc_info.value)
    
    def test_create_lesson_plan_intermediate_level(self):
        """Test lesson plan creation for intermediate level"""
        topic_analysis = {
            'strengths': ['functions'],
            'weaknesses': ['classes', 'decorators']
        }
        
        lesson_plan = LessonGenerationService._create_lesson_plan(
            'python', 
            'intermediate', 
            topic_analysis
        )
        
        assert isinstance(lesson_plan, list)
        assert len(lesson_plan) <= 10
        
        # Verify lesson plan structure
        for lesson_config in lesson_plan:
            assert 'title' in lesson_config
            assert 'difficulty' in lesson_config
            assert 'topics' in lesson_config
            assert 'priority' in lesson_config
    
    def test_create_lesson_plan_beginner_level(self):
        """Test lesson plan creation for beginner level"""
        topic_analysis = {
            'strengths': [],
            'weaknesses': ['variables', 'functions']
        }
        
        lesson_plan = LessonGenerationService._create_lesson_plan(
            'python', 
            'beginner', 
            topic_analysis
        )
        
        assert isinstance(lesson_plan, list)
        assert len(lesson_plan) <= 10
        
        # Should prioritize beginner content
        beginner_lessons = [l for l in lesson_plan if l['difficulty'] == 'beginner']
        assert len(beginner_lessons) > 0
    
    def test_calculate_lesson_priority(self):
        """Test lesson priority calculation"""
        template = {
            'topics': ['classes', 'objects']
        }
        strengths = {'functions', 'variables'}
        weaknesses = {'classes', 'decorators'}
        
        priority = LessonGenerationService._calculate_lesson_priority(
            template, 
            strengths, 
            weaknesses
        )
        
        assert isinstance(priority, float)
        assert priority > 5.0  # Should be boosted due to weakness overlap
    
    def test_generate_lesson_content(self):
        """Test individual lesson content generation"""
        lesson_config = {
            'title': 'Test Lesson',
            'estimated_time': '30 minutes',
            'difficulty': 'intermediate',
            'topics': ['classes'],
            'prerequisites': ['functions'],
            'content_template': '# Test Lesson\n\n## Introduction\nTest content\n\n## Summary\nTest summary'
        }
        
        topic_analysis = {
            'strengths': ['functions'],
            'weaknesses': ['classes']
        }
        
        lesson = LessonGenerationService._generate_lesson_content(
            lesson_config, 
            'intermediate', 
            topic_analysis, 
            1
        )
        
        assert lesson['lesson_number'] == 1
        assert lesson['title'] == 'Test Lesson'
        assert lesson['difficulty'] == 'intermediate'
        assert 'content' in lesson
        assert 'generated_at' in lesson
        
        # Content should be customized
        assert len(lesson['content']) > len(lesson_config['content_template'])
    
    def test_customize_content_for_user(self):
        """Test content customization based on user profile"""
        base_content = """# Test Lesson

## Introduction
Base introduction

## Summary
Base summary"""
        
        lesson_config = {
            'topics': ['classes']
        }
        
        topic_analysis = {
            'strengths': ['functions'],
            'weaknesses': ['classes']
        }
        
        customized = LessonGenerationService._customize_content_for_user(
            base_content, 
            'intermediate', 
            topic_analysis, 
            lesson_config
        )
        
        assert len(customized) > len(base_content)
        assert 'intermediate' in customized.lower() or 'existing' in customized.lower()
        assert 'classes' in customized.lower()  # Should mention the weakness
    
    def test_generate_personalized_intro(self):
        """Test personalized introduction generation"""
        intro = LessonGenerationService._generate_personalized_intro(
            'intermediate',
            ['functions', 'variables'],
            ['classes'],
            ['classes', 'objects']
        )
        
        assert isinstance(intro, str)
        assert len(intro) > 0
        assert 'intermediate' in intro.lower() or 'existing' in intro.lower()
        assert 'classes' in intro.lower()  # Should mention relevant weakness
    
    def test_generate_personalized_conclusion(self):
        """Test personalized conclusion generation"""
        conclusion = LessonGenerationService._generate_personalized_conclusion(
            'beginner',
            ['variables'],
            ['functions'],
            ['functions', 'parameters']
        )
        
        assert isinstance(conclusion, str)
        assert len(conclusion) > 0
        assert 'functions' in conclusion.lower()  # Should mention relevant weakness
    
    def test_validate_lesson_structure_valid(self):
        """Test lesson structure validation with valid lesson"""
        valid_lesson = {
            'lesson_number': 1,
            'title': 'Test Lesson',
            'estimated_time': '30 minutes',
            'difficulty': 'beginner',
            'topics': ['variables'],
            'prerequisites': [],
            'content': 'Test content that is long enough to be valid',
            'generated_at': '2024-01-01T00:00:00Z'
        }
        
        assert LessonGenerationService.validate_lesson_structure(valid_lesson) is True
    
    def test_validate_lesson_structure_invalid(self):
        """Test lesson structure validation with invalid lesson"""
        # Missing required fields
        invalid_lesson = {
            'lesson_number': 1,
            'title': 'Test Lesson'
            # Missing other required fields
        }
        
        assert LessonGenerationService.validate_lesson_structure(invalid_lesson) is False
        
        # Invalid lesson number
        invalid_lesson2 = {
            'lesson_number': 0,  # Invalid
            'title': 'Test Lesson',
            'estimated_time': '30 minutes',
            'difficulty': 'beginner',
            'topics': ['variables'],
            'content': 'Test content',
            'generated_at': '2024-01-01T00:00:00Z'
        }
        
        assert LessonGenerationService.validate_lesson_structure(invalid_lesson2) is False
        
        # Invalid difficulty
        invalid_lesson3 = {
            'lesson_number': 1,
            'title': 'Test Lesson',
            'estimated_time': '30 minutes',
            'difficulty': 'invalid_difficulty',  # Invalid
            'topics': ['variables'],
            'content': 'Test content',
            'generated_at': '2024-01-01T00:00:00Z'
        }
        
        assert LessonGenerationService.validate_lesson_structure(invalid_lesson3) is False
    
    @patch.object(SurveyAnalysisService, 'get_survey_results')
    def test_lesson_content_personalization(self, mock_get_survey_results):
        """Test that lesson content is properly personalized"""
        # Test with different skill levels and topic analyses
        test_cases = [
            {
                'skill_level': 'beginner',
                'strengths': [],
                'weaknesses': ['variables', 'functions']
            },
            {
                'skill_level': 'advanced',
                'strengths': ['functions', 'classes', 'decorators'],
                'weaknesses': []
            }
        ]
        
        for case in test_cases:
            mock_survey_results = self.mock_survey_results.copy()
            mock_survey_results['skill_level'] = case['skill_level']
            mock_survey_results['topic_analysis']['strengths'] = case['strengths']
            mock_survey_results['topic_analysis']['weaknesses'] = case['weaknesses']
            
            mock_get_survey_results.return_value = mock_survey_results
            
            result = LessonGenerationService.generate_personalized_lessons(
                self.test_user_id, 
                self.test_subject
            )
            
            # Verify personalization
            assert result['metadata']['skill_level'] == case['skill_level']
            
            # Check that lessons contain personalized content
            for lesson in result['lessons']:
                content = lesson['content'].lower()
                
                if case['skill_level'] == 'beginner':
                    assert 'new to programming' in content or 'fundamental' in content
                elif case['skill_level'] == 'advanced':
                    assert 'advanced' in content or 'sophisticated' in content
    
    def test_lesson_plan_respects_topic_analysis(self):
        """Test that lesson plan prioritizes weak topics"""
        topic_analysis = {
            'strengths': ['variables'],
            'weaknesses': ['classes', 'decorators', 'functions']
        }
        
        lesson_plan = LessonGenerationService._create_lesson_plan(
            'python', 
            'intermediate', 
            topic_analysis
        )
        
        # Count lessons covering weak topics
        weak_topic_lessons = 0
        for lesson_config in lesson_plan:
            lesson_topics = set(lesson_config.get('topics', []))
            weak_topics = set(topic_analysis['weaknesses'])
            
            if lesson_topics.intersection(weak_topics):
                weak_topic_lessons += 1
        
        # Should have lessons covering weak topics
        assert weak_topic_lessons > 0