"""
Comprehensive integration tests for complete LangChain pipeline workflow
"""
import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock, call
from app.services.langchain_pipeline import LangChainPipelineService
from app.services.langchain_chains import (
    SurveyGenerationChain,
    CurriculumGeneratorChain,
    LessonPlannerChain,
    ContentGeneratorChain
)

class TestLangChainPipelineIntegration:
    """Integration tests for complete LangChain pipeline workflow"""
    
    @pytest.fixture
    def complete_survey_data(self):
        """Complete survey data for integration testing"""
        return {
            'user_id': 'integration-test-user',
            'subject': 'python',
            'skill_level': 'intermediate',
            'answers': [
                {'question_id': 1, 'topic': 'variables', 'correct': True, 'difficulty': 'beginner'},
                {'question_id': 2, 'topic': 'functions', 'correct': True, 'difficulty': 'intermediate'},
                {'question_id': 3, 'topic': 'classes', 'correct': False, 'difficulty': 'intermediate'},
                {'question_id': 4, 'topic': 'decorators', 'correct': False, 'difficulty': 'advanced'},
                {'question_id': 5, 'topic': 'generators', 'correct': True, 'difficulty': 'intermediate'},
                {'question_id': 6, 'topic': 'context_managers', 'correct': False, 'difficulty': 'advanced'},
                {'question_id': 7, 'topic': 'metaclasses', 'correct': False, 'difficulty': 'advanced'}
            ],
            'submitted_at': '2024-01-15T10:00:00Z'
        }
    
    @pytest.fixture
    def complete_rag_docs(self):
        """Complete RAG documents for integration testing"""
        return {
            'curriculum': [
                "Create a comprehensive 5-lesson curriculum",
                "Adapt difficulty based on skill level assessment",
                "Skip topics the learner already knows",
                "Include clear learning progression"
            ],
            'lesson_plans': [
                "Create detailed 60-minute lesson plans",
                "Include specific learning objectives",
                "Provide variety in activities and assessments",
                "Ensure proper time allocation"
            ],
            'content': [
                "Generate comprehensive lesson content",
                "Include 2 practical code examples per lesson",
                "Create 3-5 hands-on exercises",
                "Use proper markdown formatting"
            ]
        }
    
    @pytest.fixture
    def expected_curriculum_result(self):
        """Expected curriculum generation result"""
        return {
            "curriculum": {
                "subject": "python",
                "skill_level": "intermediate",
                "total_lessons": 10,
                "learning_objectives": [
                    "Master intermediate Python concepts",
                    "Build practical applications",
                    "Understand advanced programming patterns"
                ],
                "topics": [
                    {
                        "lesson_id": 1,
                        "title": "Advanced Data Structures",
                        "topics": ["dictionaries", "sets", "collections"],
                        "prerequisites": [],
                        "difficulty": "intermediate",
                        "estimated_duration": "60 minutes"
                    },
                    {
                        "lesson_id": 2,
                        "title": "Object-Oriented Programming",
                        "topics": ["classes", "inheritance", "polymorphism"],
                        "prerequisites": ["dictionaries"],
                        "difficulty": "intermediate",
                        "estimated_duration": "60 minutes"
                    }
                    # ... would have 8 more lessons
                ]
            },
            "generated_at": "2024-01-15T11:00:00Z",
            "generation_stage": "curriculum_complete"
        }
    
    @pytest.fixture
    def expected_lesson_plans_result(self):
        """Expected lesson plans generation result"""
        return {
            "lesson_plans": [
                {
                    "lesson_id": 1,
                    "title": "Advanced Data Structures",
                    "learning_objectives": [
                        "Master dictionary operations and methods",
                        "Understand set theory and operations",
                        "Utilize collections module effectively"
                    ],
                    "structure": {
                        "introduction": "5 minutes",
                        "main_content": "25 minutes",
                        "examples": "15 minutes",
                        "exercises": "15 minutes",
                        "summary": "5 minutes"
                    },
                    "activities": [
                        "Interactive dictionary manipulation",
                        "Set operations demonstration",
                        "Collections module exploration"
                    ],
                    "assessment": "Build a data processing application using advanced structures",
                    "materials_needed": ["Python IDE", "Data samples"],
                    "key_concepts": ["dictionaries", "sets", "collections"]
                },
                {
                    "lesson_id": 2,
                    "title": "Object-Oriented Programming",
                    "learning_objectives": [
                        "Create and use Python classes effectively",
                        "Implement inheritance relationships",
                        "Apply polymorphism concepts"
                    ],
                    "structure": {
                        "introduction": "5 minutes",
                        "main_content": "25 minutes",
                        "examples": "15 minutes",
                        "exercises": "15 minutes",
                        "summary": "5 minutes"
                    },
                    "activities": [
                        "Class creation workshop",
                        "Inheritance implementation",
                        "Polymorphism coding challenge"
                    ],
                    "assessment": "Design and implement a class hierarchy",
                    "materials_needed": ["Python IDE", "UML tools"],
                    "key_concepts": ["classes", "inheritance", "polymorphism"]
                }
            ],
            "generated_at": "2024-01-15T11:05:00Z",
            "generation_stage": "lesson_plans_complete"
        }
    
    @pytest.fixture
    def expected_lesson_contents(self):
        """Expected lesson content generation results"""
        return [
            {
                'lesson_id': 1,
                'content': """# Advanced Data Structures

## Introduction
Welcome to our lesson on advanced data structures in Python...

## Learning Objectives
- Master dictionary operations and methods
- Understand set theory and operations
- Utilize collections module effectively

## Core Concepts

### Dictionaries
Dictionaries are mutable, unordered collections...

### Sets
Sets are unordered collections of unique elements...

## Code Examples

### Example 1: Dictionary Comprehensions
```python
squares = {x: x**2 for x in range(10)}
```

### Example 2: Set Operations
```python
set1 = {1, 2, 3, 4}
set2 = {3, 4, 5, 6}
intersection = set1 & set2
```

## Exercises
1. Create a word frequency counter using dictionaries
2. Implement set-based data deduplication
3. Use collections.Counter for advanced counting

## Summary
In this lesson, we explored advanced data structures...
"""
            },
            {
                'lesson_id': 2,
                'content': """# Object-Oriented Programming

## Introduction
Object-oriented programming is a programming paradigm...

## Learning Objectives
- Create and use Python classes effectively
- Implement inheritance relationships
- Apply polymorphism concepts

## Core Concepts

### Classes and Objects
Classes are blueprints for creating objects...

### Inheritance
Inheritance allows classes to inherit from other classes...

## Code Examples

### Example 1: Basic Class Definition
```python
class Animal:
    def __init__(self, name):
        self.name = name
    
    def speak(self):
        pass
```

### Example 2: Inheritance
```python
class Dog(Animal):
    def speak(self):
        return f"{self.name} barks!"
```

## Exercises
1. Create a vehicle class hierarchy
2. Implement method overriding
3. Design a shape inheritance system

## Summary
Object-oriented programming provides powerful abstraction...
"""
            }
        ]
    
    @patch('app.services.langchain_pipeline.validate_environment')
    def test_pipeline_service_initialization(self, mock_validate):
        """Test complete pipeline service initialization"""
        mock_validate.return_value = True
        
        with patch('app.services.langchain_pipeline.SurveyGenerationChain') as mock_survey, \
             patch('app.services.langchain_pipeline.CurriculumGeneratorChain') as mock_curriculum, \
             patch('app.services.langchain_pipeline.LessonPlannerChain') as mock_planner, \
             patch('app.services.langchain_pipeline.ContentGeneratorChain') as mock_content:
            
            pipeline = LangChainPipelineService()
            
            # Verify all chain components are initialized
            mock_survey.assert_called_once_with(temperature=0.8, max_tokens=2000)
            mock_curriculum.assert_called_once_with(temperature=0.7, max_tokens=3000)
            mock_planner.assert_called_once_with(temperature=0.7, max_tokens=3000)
            mock_content.assert_called_once_with(temperature=0.6, max_tokens=4000)
            
            assert hasattr(pipeline, 'survey_chain')
            assert hasattr(pipeline, 'curriculum_chain')
            assert hasattr(pipeline, 'lesson_planner_chain')
            assert hasattr(pipeline, 'content_generator_chain')
    
    @patch('app.services.langchain_pipeline.validate_environment')
    @patch('app.services.langchain_pipeline.test_xai_connection')
    def test_connection_test_integration(self, mock_test_connection, mock_validate):
        """Test xAI connection test integration"""
        mock_validate.return_value = True
        mock_test_connection.return_value = (True, "Connection successful")
        
        with patch('app.services.langchain_pipeline.SurveyGenerationChain'), \
             patch('app.services.langchain_pipeline.CurriculumGeneratorChain'), \
             patch('app.services.langchain_pipeline.LessonPlannerChain'), \
             patch('app.services.langchain_pipeline.ContentGeneratorChain'):
            
            pipeline = LangChainPipelineService()
            result = pipeline.test_connection()
            
            assert result['status'] == 'success'
            assert result['message'] == 'Connection successful'
            assert 'timestamp' in result
            mock_test_connection.assert_called_once()
    
    @patch('app.services.langchain_pipeline.validate_environment')
    def test_full_pipeline_execution_success(self, mock_validate, complete_survey_data, 
                                           complete_rag_docs, expected_curriculum_result,
                                           expected_lesson_plans_result, expected_lesson_contents):
        """Test successful execution of complete pipeline"""
        mock_validate.return_value = True
        
        # Mock all chain components
        mock_survey_chain = Mock()
        mock_curriculum_chain = Mock()
        mock_planner_chain = Mock()
        mock_content_chain = Mock()
        
        # Configure mock responses
        mock_curriculum_chain.generate_curriculum.return_value = expected_curriculum_result
        mock_planner_chain.generate_lesson_plans.return_value = expected_lesson_plans_result
        mock_content_chain.generate_content.side_effect = [
            expected_lesson_contents[0]['content'],
            expected_lesson_contents[1]['content']
        ]
        
        with patch('app.services.langchain_pipeline.SurveyGenerationChain', return_value=mock_survey_chain), \
             patch('app.services.langchain_pipeline.CurriculumGeneratorChain', return_value=mock_curriculum_chain), \
             patch('app.services.langchain_pipeline.LessonPlannerChain', return_value=mock_planner_chain), \
             patch('app.services.langchain_pipeline.ContentGeneratorChain', return_value=mock_content_chain):
            
            pipeline = LangChainPipelineService()
            result = pipeline.run_full_pipeline(complete_survey_data, 'python', complete_rag_docs)
            
            # Verify pipeline execution
            assert result['status'] == 'completed'
            assert result['subject'] == 'python'
            assert 'curriculum' in result
            assert 'lesson_plans' in result
            assert 'lesson_contents' in result
            
            # Verify curriculum generation was called correctly
            mock_curriculum_chain.generate_curriculum.assert_called_once_with(
                complete_survey_data, 'python', complete_rag_docs['curriculum']
            )
            
            # Verify lesson plans generation was called correctly
            mock_planner_chain.generate_lesson_plans.assert_called_once_with(
                expected_curriculum_result, 'python', complete_rag_docs['lesson_plans']
            )
            
            # Verify content generation was called for each lesson plan
            assert mock_content_chain.generate_content.call_count == 2
            
            # Verify lesson contents structure
            lesson_contents = result['lesson_contents']
            assert len(lesson_contents) == 2
            assert lesson_contents[0]['lesson_id'] == 1
            assert lesson_contents[1]['lesson_id'] == 2
            assert 'content' in lesson_contents[0]
            assert 'content' in lesson_contents[1]
    
    @patch('app.services.langchain_pipeline.validate_environment')
    def test_pipeline_stage_failure_handling(self, mock_validate, complete_survey_data):
        """Test pipeline failure handling at different stages"""
        mock_validate.return_value = True
        
        # Test Stage 1 failure (curriculum generation)
        mock_curriculum_chain = Mock()
        mock_curriculum_chain.generate_curriculum.side_effect = Exception("Curriculum generation failed")
        
        with patch('app.services.langchain_pipeline.SurveyGenerationChain'), \
             patch('app.services.langchain_pipeline.CurriculumGeneratorChain', return_value=mock_curriculum_chain), \
             patch('app.services.langchain_pipeline.LessonPlannerChain'), \
             patch('app.services.langchain_pipeline.ContentGeneratorChain'):
            
            pipeline = LangChainPipelineService()
            
            with pytest.raises(Exception, match="Curriculum generation failed"):
                pipeline.run_full_pipeline(complete_survey_data, 'python')
    
    @patch('app.services.langchain_pipeline.validate_environment')
    def test_pipeline_with_partial_rag_docs(self, mock_validate, complete_survey_data,
                                          expected_curriculum_result, expected_lesson_plans_result):
        """Test pipeline execution with partial RAG documents"""
        mock_validate.return_value = True
        
        # Only provide curriculum RAG docs, not lesson_plans or content
        partial_rag_docs = {
            'curriculum': ['Curriculum guideline 1', 'Curriculum guideline 2']
        }
        
        mock_curriculum_chain = Mock()
        mock_planner_chain = Mock()
        mock_content_chain = Mock()
        
        mock_curriculum_chain.generate_curriculum.return_value = expected_curriculum_result
        mock_planner_chain.generate_lesson_plans.return_value = expected_lesson_plans_result
        mock_content_chain.generate_content.return_value = "Generated content"
        
        with patch('app.services.langchain_pipeline.SurveyGenerationChain'), \
             patch('app.services.langchain_pipeline.CurriculumGeneratorChain', return_value=mock_curriculum_chain), \
             patch('app.services.langchain_pipeline.LessonPlannerChain', return_value=mock_planner_chain), \
             patch('app.services.langchain_pipeline.ContentGeneratorChain', return_value=mock_content_chain):
            
            pipeline = LangChainPipelineService()
            result = pipeline.run_full_pipeline(complete_survey_data, 'python', partial_rag_docs)
            
            # Verify curriculum generation used provided RAG docs
            mock_curriculum_chain.generate_curriculum.assert_called_once_with(
                complete_survey_data, 'python', partial_rag_docs['curriculum']
            )
            
            # Verify lesson plans and content generation used empty lists for missing RAG docs
            mock_planner_chain.generate_lesson_plans.assert_called_once_with(
                expected_curriculum_result, 'python', []
            )
            
            assert result['status'] == 'completed'
    
    @patch('app.services.langchain_pipeline.validate_environment')
    def test_individual_stage_methods(self, mock_validate, complete_survey_data,
                                    expected_curriculum_result, expected_lesson_plans_result):
        """Test individual pipeline stage methods"""
        mock_validate.return_value = True
        
        mock_survey_chain = Mock()
        mock_curriculum_chain = Mock()
        mock_planner_chain = Mock()
        mock_content_chain = Mock()
        
        # Configure mock responses
        survey_result = {
            "questions": [{"id": 1, "question": "Test?"}],
            "total_questions": 1,
            "subject": "python"
        }
        mock_survey_chain.generate_survey.return_value = survey_result
        mock_curriculum_chain.generate_curriculum.return_value = expected_curriculum_result
        mock_planner_chain.generate_lesson_plans.return_value = expected_lesson_plans_result
        mock_content_chain.generate_content.return_value = "Generated lesson content"
        
        with patch('app.services.langchain_pipeline.SurveyGenerationChain', return_value=mock_survey_chain), \
             patch('app.services.langchain_pipeline.CurriculumGeneratorChain', return_value=mock_curriculum_chain), \
             patch('app.services.langchain_pipeline.LessonPlannerChain', return_value=mock_planner_chain), \
             patch('app.services.langchain_pipeline.ContentGeneratorChain', return_value=mock_content_chain):
            
            pipeline = LangChainPipelineService()
            
            # Test survey generation
            survey_result_actual = pipeline.generate_survey('python')
            assert survey_result_actual == survey_result
            mock_survey_chain.generate_survey.assert_called_once_with('python', None)
            
            # Test curriculum generation
            curriculum_result = pipeline.generate_curriculum(complete_survey_data, 'python')
            assert curriculum_result == expected_curriculum_result
            mock_curriculum_chain.generate_curriculum.assert_called_once_with(
                complete_survey_data, 'python', None
            )
            
            # Test lesson plans generation
            lesson_plans_result = pipeline.generate_lesson_plans(expected_curriculum_result, 'python')
            assert lesson_plans_result == expected_lesson_plans_result
            mock_planner_chain.generate_lesson_plans.assert_called_once_with(
                expected_curriculum_result, 'python', None
            )
            
            # Test lesson content generation
            lesson_plan = expected_lesson_plans_result['lesson_plans'][0]
            content_result = pipeline.generate_lesson_content(lesson_plan, 'python')
            assert content_result == "Generated lesson content"
            mock_content_chain.generate_content.assert_called_once_with(
                lesson_plan, 'python', None
            )
    
    @patch('app.services.langchain_pipeline.validate_environment')
    def test_pipeline_status_reporting(self, mock_validate):
        """Test pipeline status reporting"""
        mock_validate.return_value = True
        
        with patch('app.services.langchain_pipeline.SurveyGenerationChain'), \
             patch('app.services.langchain_pipeline.CurriculumGeneratorChain'), \
             patch('app.services.langchain_pipeline.LessonPlannerChain'), \
             patch('app.services.langchain_pipeline.ContentGeneratorChain'):
            
            pipeline = LangChainPipelineService()
            status = pipeline.get_pipeline_status()
            
            # Verify all components are reported as implemented
            assert status['survey_generation'] == 'implemented'
            assert status['curriculum_generation'] == 'implemented'
            assert status['lesson_planning'] == 'implemented'
            assert status['content_generation'] == 'implemented'
            assert status['rag_system'] == 'implemented'
            assert status['xai_connection'] == 'implemented'
    
    @patch('app.services.langchain_pipeline.validate_environment')
    def test_pipeline_error_propagation(self, mock_validate, complete_survey_data):
        """Test that errors are properly propagated through pipeline stages"""
        mock_validate.return_value = True
        
        # Test different types of errors at different stages
        error_scenarios = [
            ('curriculum', Exception("Network error")),
            ('lesson_plans', ValueError("Invalid data format")),
            ('content', RuntimeError("Resource exhausted"))
        ]
        
        for stage, error in error_scenarios:
            mock_curriculum_chain = Mock()
            mock_planner_chain = Mock()
            mock_content_chain = Mock()
            
            if stage == 'curriculum':
                mock_curriculum_chain.generate_curriculum.side_effect = error
            elif stage == 'lesson_plans':
                mock_curriculum_chain.generate_curriculum.return_value = {"curriculum": {}}
                mock_planner_chain.generate_lesson_plans.side_effect = error
            elif stage == 'content':
                mock_curriculum_chain.generate_curriculum.return_value = {"curriculum": {}}
                mock_planner_chain.generate_lesson_plans.return_value = {"lesson_plans": [{"lesson_id": 1}]}
                mock_content_chain.generate_content.side_effect = error
            
            with patch('app.services.langchain_pipeline.SurveyGenerationChain'), \
                 patch('app.services.langchain_pipeline.CurriculumGeneratorChain', return_value=mock_curriculum_chain), \
                 patch('app.services.langchain_pipeline.LessonPlannerChain', return_value=mock_planner_chain), \
                 patch('app.services.langchain_pipeline.ContentGeneratorChain', return_value=mock_content_chain):
                
                pipeline = LangChainPipelineService()
                
                with pytest.raises(type(error), match=str(error)):
                    pipeline.run_full_pipeline(complete_survey_data, 'python')

class TestLangChainRAGIntegration:
    """Integration tests for RAG document system with LangChain pipeline"""
    
    @patch('app.services.langchain_pipeline.validate_environment')
    def test_rag_document_loading_integration(self, mock_validate):
        """Test RAG document loading integration with pipeline"""
        mock_validate.return_value = True
        
        mock_curriculum_chain = Mock()
        
        # Mock RAG document loading
        expected_rag_docs = [
            "RAG document 1 content",
            "RAG document 2 content",
            "RAG document 3 content"
        ]
        
        with patch('app.services.langchain_pipeline.SurveyGenerationChain'), \
             patch('app.services.langchain_pipeline.CurriculumGeneratorChain', return_value=mock_curriculum_chain), \
             patch('app.services.langchain_pipeline.LessonPlannerChain'), \
             patch('app.services.langchain_pipeline.ContentGeneratorChain'):
            
            # Mock the load_rag_documents method on the chain
            mock_curriculum_chain.load_rag_documents.return_value = expected_rag_docs
            mock_curriculum_chain.generate_curriculum.return_value = {"curriculum": {}}
            
            pipeline = LangChainPipelineService()
            
            # Test that RAG documents are loaded and used
            survey_data = {'skill_level': 'intermediate', 'answers': []}
            pipeline.generate_curriculum(survey_data, 'python')
            
            # Verify RAG documents were loaded (this would be called internally by the chain)
            # In actual implementation, this would be verified through the chain's behavior
            assert mock_curriculum_chain.generate_curriculum.called
    
    @patch('app.services.langchain_pipeline.validate_environment')
    def test_rag_document_fallback_integration(self, mock_validate):
        """Test RAG document fallback when documents are unavailable"""
        mock_validate.return_value = True
        
        mock_survey_chain = Mock()
        
        # Mock RAG document loading failure
        mock_survey_chain.load_rag_documents.return_value = []
        mock_survey_chain.generate_survey.return_value = {
            "questions": [],
            "total_questions": 0,
            "subject": "python"
        }
        
        with patch('app.services.langchain_pipeline.SurveyGenerationChain', return_value=mock_survey_chain), \
             patch('app.services.langchain_pipeline.CurriculumGeneratorChain'), \
             patch('app.services.langchain_pipeline.LessonPlannerChain'), \
             patch('app.services.langchain_pipeline.ContentGeneratorChain'):
            
            pipeline = LangChainPipelineService()
            
            # Should still work with empty RAG documents (fallback to defaults)
            result = pipeline.generate_survey('python')
            
            assert result['subject'] == 'python'
            mock_survey_chain.generate_survey.assert_called_once_with('python', None)