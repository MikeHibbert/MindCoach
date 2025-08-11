"""
Integration tests for LangChain pipeline workflow
Tests for subtask 22.1: Integration tests for complete pipeline workflow
"""
import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
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
            'skill_level': 'intermediate',
            'answers': [
                {'question_id': 1, 'topic': 'variables', 'correct': True, 'difficulty': 'beginner'},
                {'question_id': 2, 'topic': 'functions', 'correct': True, 'difficulty': 'intermediate'},
                {'question_id': 3, 'topic': 'classes', 'correct': False, 'difficulty': 'intermediate'},
                {'question_id': 4, 'topic': 'modules', 'correct': False, 'difficulty': 'advanced'},
                {'question_id': 5, 'topic': 'error_handling', 'correct': True, 'difficulty': 'intermediate'}
            ],
            'total_questions': 5,
            'correct_answers': 3,
            'percentage': 60.0
        }
    
    @pytest.fixture
    def complete_curriculum_data(self):
        """Complete curriculum data for integration testing"""
        return {
            "curriculum": {
                "subject": "python",
                "skill_level": "intermediate",
                "total_lessons": 3,
                "learning_objectives": [
                    "Master intermediate Python concepts",
                    "Build practical applications",
                    "Understand object-oriented programming"
                ],
                "topics": [
                    {
                        "lesson_id": 1,
                        "title": "Advanced Functions and Modules",
                        "topics": ["functions", "modules", "packages"],
                        "prerequisites": ["variables"],
                        "difficulty": "intermediate",
                        "estimated_duration": "60 minutes"
                    },
                    {
                        "lesson_id": 2,
                        "title": "Object-Oriented Programming",
                        "topics": ["classes", "inheritance", "polymorphism"],
                        "prerequisites": ["functions"],
                        "difficulty": "intermediate",
                        "estimated_duration": "60 minutes"
                    },
                    {
                        "lesson_id": 3,
                        "title": "Error Handling and Debugging",
                        "topics": ["exceptions", "debugging", "testing"],
                        "prerequisites": ["classes"],
                        "difficulty": "advanced",
                        "estimated_duration": "60 minutes"
                    }
                ]
            },
            "generated_at": "2024-01-15T10:00:00Z",
            "generation_stage": "curriculum_complete"
        }
    
    @pytest.fixture
    def complete_lesson_plans_data(self):
        """Complete lesson plans data for integration testing"""
        return {
            "lesson_plans": [
                {
                    "lesson_id": 1,
                    "title": "Advanced Functions and Modules",
                    "learning_objectives": [
                        "Create and use advanced function features",
                        "Organize code using modules and packages",
                        "Implement function decorators"
                    ],
                    "structure": {
                        "introduction": "5 minutes",
                        "main_content": "25 minutes",
                        "examples": "15 minutes",
                        "exercises": "15 minutes",
                        "summary": "5 minutes"
                    },
                    "activities": [
                        "Function parameter variations demonstration",
                        "Module creation and import exercises",
                        "Package structure building"
                    ],
                    "assessment": "Build a multi-module Python application",
                    "materials_needed": [
                        "Python IDE",
                        "Module examples",
                        "Package templates"
                    ],
                    "key_concepts": [
                        "functions",
                        "modules",
                        "packages"
                    ]
                },
                {
                    "lesson_id": 2,
                    "title": "Object-Oriented Programming",
                    "learning_objectives": [
                        "Design and implement Python classes",
                        "Use inheritance to create class hierarchies",
                        "Apply polymorphism in practical scenarios"
                    ],
                    "structure": {
                        "introduction": "5 minutes",
                        "main_content": "25 minutes",
                        "examples": "15 minutes",
                        "exercises": "15 minutes",
                        "summary": "5 minutes"
                    },
                    "activities": [
                        "Class design workshop",
                        "Inheritance implementation",
                        "Polymorphism coding challenge"
                    ],
                    "assessment": "Design a class hierarchy for a real-world scenario",
                    "materials_needed": [
                        "Python IDE",
                        "OOP examples",
                        "UML diagrams"
                    ],
                    "key_concepts": [
                        "classes",
                        "inheritance",
                        "polymorphism"
                    ]
                }
            ],
            "generated_at": "2024-01-15T10:05:00Z",
            "generation_stage": "lesson_plans_complete"
        }
    
    @pytest.fixture
    def sample_lesson_contents(self):
        """Sample lesson contents for integration testing"""
        return [
            {
                "lesson_id": 1,
                "content": """# Advanced Functions and Modules

## Introduction

Welcome to this lesson on advanced Python functions and modules. You'll learn how to create more sophisticated functions and organize your code effectively.

## Core Concepts

### Advanced Function Features
- Default parameters
- Variable-length arguments (*args, **kwargs)
- Lambda functions
- Decorators

### Modules and Packages
- Creating modules
- Import statements
- Package structure
- __init__.py files

## Code Examples

### Example 1: Advanced Function Parameters
```python
def greet(name, greeting="Hello", *args, **kwargs):
    message = f"{greeting}, {name}!"
    if args:
        message += f" Additional info: {', '.join(args)}"
    if kwargs:
        message += f" Extra: {kwargs}"
    return message

# Usage
print(greet("Alice"))
print(greet("Bob", "Hi", "Python", "Developer", age=25, city="NYC"))
```

### Example 2: Module Creation
```python
# math_utils.py
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

# main.py
import math_utils

result = math_utils.add(5, 3)
print(f"5 + 3 = {result}")
```

## Hands-on Exercises

### Exercise 1: Function with Default Parameters
Create a function that calculates the area of a rectangle with optional parameters.

### Exercise 2: Create a Utility Module
Build a module with mathematical utility functions.

### Exercise 3: Package Structure
Create a package with multiple modules for different functionalities.

## Summary

You've learned about advanced function features and how to organize code using modules and packages.
"""
            },
            {
                "lesson_id": 2,
                "content": """# Object-Oriented Programming

## Introduction

This lesson covers the fundamentals of Object-Oriented Programming (OOP) in Python, including classes, inheritance, and polymorphism.

## Core Concepts

### Classes and Objects
- Class definition
- Instance creation
- Attributes and methods
- Constructor (__init__)

### Inheritance
- Parent and child classes
- Method overriding
- super() function

### Polymorphism
- Method overriding
- Duck typing
- Abstract base classes

## Code Examples

### Example 1: Basic Class
```python
class Car:
    def __init__(self, make, model, year):
        self.make = make
        self.model = model
        self.year = year
        self.odometer = 0
    
    def drive(self, miles):
        self.odometer += miles
        print(f"Drove {miles} miles. Total: {self.odometer}")
    
    def __str__(self):
        return f"{self.year} {self.make} {self.model}"

# Usage
my_car = Car("Toyota", "Camry", 2020)
print(my_car)
my_car.drive(100)
```

### Example 2: Inheritance
```python
class ElectricCar(Car):
    def __init__(self, make, model, year, battery_capacity):
        super().__init__(make, model, year)
        self.battery_capacity = battery_capacity
        self.charge_level = 100
    
    def charge(self):
        self.charge_level = 100
        print("Car is fully charged!")
    
    def drive(self, miles):
        super().drive(miles)
        self.charge_level -= miles * 0.1
        print(f"Battery level: {self.charge_level:.1f}%")

# Usage
tesla = ElectricCar("Tesla", "Model 3", 2021, 75)
tesla.drive(50)
tesla.charge()
```

## Hands-on Exercises

### Exercise 1: Create a Person Class
Design a Person class with attributes and methods.

### Exercise 2: Implement Inheritance
Create a Student class that inherits from Person.

### Exercise 3: Polymorphism Challenge
Create different animal classes that implement the same interface.

## Summary

You've learned the core concepts of OOP in Python and how to apply them in practical scenarios.
"""
            }
        ]
    
    @pytest.fixture
    def rag_documents(self):
        """Sample RAG documents for integration testing"""
        return {
            'curriculum': [
                "Create a comprehensive curriculum with clear progression",
                "Adapt content based on learner skill level",
                "Include practical applications and real-world examples"
            ],
            'lesson_plans': [
                "Design detailed lesson plans with clear time allocations",
                "Include specific learning objectives for each lesson",
                "Provide variety in activities and assessment methods"
            ],
            'content': [
                "Create engaging content with practical examples",
                "Include exactly 2 code examples with detailed explanations",
                "Provide 3-5 hands-on exercises of varying difficulty",
                "Use proper markdown formatting with headers and code blocks"
            ]
        }
    
    @patch('app.services.langchain_pipeline.validate_environment')
    @patch('app.services.langchain_pipeline.SurveyGenerationChain')
    @patch('app.services.langchain_pipeline.CurriculumGeneratorChain')
    @patch('app.services.langchain_pipeline.LessonPlannerChain')
    @patch('app.services.langchain_pipeline.ContentGeneratorChain')
    def test_complete_pipeline_integration(self, mock_content_chain_class, mock_lesson_chain_class,
                                         mock_curriculum_chain_class, mock_survey_chain_class, mock_validate,
                                         complete_survey_data, complete_curriculum_data, 
                                         complete_lesson_plans_data, sample_lesson_contents, rag_documents):
        """Test complete pipeline integration from survey to lesson content"""
        mock_validate.return_value = True
        
        # Mock curriculum generation
        mock_curriculum_chain = Mock()
        mock_curriculum_chain.generate_curriculum.return_value = complete_curriculum_data
        mock_curriculum_chain_class.return_value = mock_curriculum_chain
        
        # Mock lesson planning
        mock_lesson_chain = Mock()
        mock_lesson_chain.generate_lesson_plans.return_value = complete_lesson_plans_data
        mock_lesson_chain_class.return_value = mock_lesson_chain
        
        # Mock content generation
        mock_content_chain = Mock()
        mock_content_chain.generate_content.side_effect = [
            sample_lesson_contents[0]["content"],
            sample_lesson_contents[1]["content"]
        ]
        mock_content_chain_class.return_value = mock_content_chain
        
        # Run complete pipeline
        pipeline = LangChainPipelineService()
        result = pipeline.run_full_pipeline(complete_survey_data, "python", rag_documents)
        
        # Verify pipeline completion
        assert result["status"] == "completed"
        assert result["subject"] == "python"
        
        # Verify curriculum stage
        assert "curriculum" in result
        curriculum = result["curriculum"]["curriculum"]
        assert curriculum["subject"] == "python"
        assert curriculum["skill_level"] == "intermediate"
        assert len(curriculum["topics"]) == 3
        
        # Verify lesson plans stage
        assert "lesson_plans" in result
        lesson_plans = result["lesson_plans"]["lesson_plans"]
        assert len(lesson_plans) == 2
        assert lesson_plans[0]["lesson_id"] == 1
        assert lesson_plans[1]["lesson_id"] == 2
        
        # Verify content generation stage
        assert "lesson_contents" in result
        lesson_contents = result["lesson_contents"]
        assert len(lesson_contents) == 2
        assert lesson_contents[0]["lesson_id"] == 1
        assert lesson_contents[1]["lesson_id"] == 2
        assert "# Advanced Functions and Modules" in lesson_contents[0]["content"]
        assert "# Object-Oriented Programming" in lesson_contents[1]["content"]
        
        # Verify all stages were called with correct parameters
        mock_curriculum_chain.generate_curriculum.assert_called_once_with(
            complete_survey_data, "python", rag_documents['curriculum']
        )
        mock_lesson_chain.generate_lesson_plans.assert_called_once_with(
            complete_curriculum_data, "python", rag_documents['lesson_plans']
        )
        assert mock_content_chain.generate_content.call_count == 2
    
    @patch('app.services.langchain_pipeline.validate_environment')
    @patch('app.services.langchain_pipeline.SurveyGenerationChain')
    @patch('app.services.langchain_pipeline.CurriculumGeneratorChain')
    @patch('app.services.langchain_pipeline.LessonPlannerChain')
    @patch('app.services.langchain_pipeline.ContentGeneratorChain')
    def test_pipeline_stage_failure_handling(self, mock_content_chain_class, mock_lesson_chain_class,
                                            mock_curriculum_chain_class, mock_survey_chain_class, mock_validate,
                                            complete_survey_data):
        """Test pipeline handling of stage failures"""
        mock_validate.return_value = True
        
        # Mock curriculum generation failure
        mock_curriculum_chain = Mock()
        mock_curriculum_chain.generate_curriculum.side_effect = Exception("Curriculum generation failed")
        mock_curriculum_chain_class.return_value = mock_curriculum_chain
        
        pipeline = LangChainPipelineService()
        
        # Should propagate the exception
        with pytest.raises(Exception, match="Curriculum generation failed"):
            pipeline.run_full_pipeline(complete_survey_data, "python")
        
        # Verify curriculum stage was called but failed
        mock_curriculum_chain.generate_curriculum.assert_called_once()
    
    @patch('app.services.langchain_pipeline.validate_environment')
    @patch('app.services.langchain_pipeline.SurveyGenerationChain')
    @patch('app.services.langchain_pipeline.CurriculumGeneratorChain')
    @patch('app.services.langchain_pipeline.LessonPlannerChain')
    @patch('app.services.langchain_pipeline.ContentGeneratorChain')
    def test_pipeline_with_different_skill_levels(self, mock_content_chain_class, mock_lesson_chain_class,
                                                 mock_curriculum_chain_class, mock_survey_chain_class, mock_validate,
                                                 complete_curriculum_data, complete_lesson_plans_data, sample_lesson_contents):
        """Test pipeline with different skill levels"""
        mock_validate.return_value = True
        
        skill_levels = ['beginner', 'intermediate', 'advanced']
        
        # Mock all chains
        mock_curriculum_chain = Mock()
        mock_curriculum_chain.generate_curriculum.return_value = complete_curriculum_data
        mock_curriculum_chain_class.return_value = mock_curriculum_chain
        
        mock_lesson_chain = Mock()
        mock_lesson_chain.generate_lesson_plans.return_value = complete_lesson_plans_data
        mock_lesson_chain_class.return_value = mock_lesson_chain
        
        mock_content_chain = Mock()
        mock_content_chain.generate_content.return_value = sample_lesson_contents[0]["content"]
        mock_content_chain_class.return_value = mock_content_chain
        
        pipeline = LangChainPipelineService()
        
        for skill_level in skill_levels:
            survey_data = {
                'skill_level': skill_level,
                'answers': [
                    {'question_id': 1, 'topic': 'variables', 'correct': True}
                ]
            }
            
            result = pipeline.run_full_pipeline(survey_data, "python")
            
            assert result["status"] == "completed"
            assert result["subject"] == "python"
            
            # Verify curriculum generation was called with correct skill level
            call_args = mock_curriculum_chain.generate_curriculum.call_args[0]
            assert call_args[0]['skill_level'] == skill_level
    
    @patch('app.services.langchain_pipeline.validate_environment')
    @patch('app.services.langchain_pipeline.SurveyGenerationChain')
    @patch('app.services.langchain_pipeline.CurriculumGeneratorChain')
    @patch('app.services.langchain_pipeline.LessonPlannerChain')
    @patch('app.services.langchain_pipeline.ContentGeneratorChain')
    def test_pipeline_performance_benchmarks(self, mock_content_chain_class, mock_lesson_chain_class,
                                           mock_curriculum_chain_class, mock_survey_chain_class, mock_validate,
                                           complete_survey_data, complete_curriculum_data, 
                                           complete_lesson_plans_data, sample_lesson_contents):
        """Test pipeline performance benchmarks"""
        mock_validate.return_value = True
        
        # Add realistic delays to simulate API calls
        def slow_curriculum_generation(*args, **kwargs):
            time.sleep(0.1)  # Simulate 100ms API call
            return complete_curriculum_data
        
        def slow_lesson_planning(*args, **kwargs):
            time.sleep(0.1)  # Simulate 100ms API call
            return complete_lesson_plans_data
        
        def slow_content_generation(*args, **kwargs):
            time.sleep(0.05)  # Simulate 50ms API call per lesson
            return sample_lesson_contents[0]["content"]
        
        # Mock chains with delays
        mock_curriculum_chain = Mock()
        mock_curriculum_chain.generate_curriculum.side_effect = slow_curriculum_generation
        mock_curriculum_chain_class.return_value = mock_curriculum_chain
        
        mock_lesson_chain = Mock()
        mock_lesson_chain.generate_lesson_plans.side_effect = slow_lesson_planning
        mock_lesson_chain_class.return_value = mock_lesson_chain
        
        mock_content_chain = Mock()
        mock_content_chain.generate_content.side_effect = slow_content_generation
        mock_content_chain_class.return_value = mock_content_chain
        
        pipeline = LangChainPipelineService()
        
        # Measure execution time
        start_time = time.time()
        result = pipeline.run_full_pipeline(complete_survey_data, "python")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Verify completion
        assert result["status"] == "completed"
        
        # Performance expectations (with mocked delays)
        # Should complete within reasonable time even with simulated API delays
        assert execution_time < 2.0  # Less than 2 seconds for full pipeline
        
        # Verify all stages were executed
        mock_curriculum_chain.generate_curriculum.assert_called_once()
        mock_lesson_chain.generate_lesson_plans.assert_called_once()
        # Content generation called for each lesson plan
        assert mock_content_chain.generate_content.call_count == len(complete_lesson_plans_data["lesson_plans"])
    
    @patch('app.services.langchain_pipeline.validate_environment')
    @patch('app.services.langchain_pipeline.SurveyGenerationChain')
    def test_individual_stage_integration(self, mock_survey_chain_class, mock_validate):
        """Test individual stage integration"""
        mock_validate.return_value = True
        
        # Test survey generation stage
        expected_survey = {
            "questions": [
                {
                    "id": 1,
                    "question": "What is Python?",
                    "type": "multiple_choice",
                    "options": ["A language", "A snake", "A tool", "A framework"],
                    "correct_answer": "A language",
                    "difficulty": "beginner",
                    "topic": "basics"
                }
            ],
            "total_questions": 1,
            "subject": "python"
        }
        
        mock_survey_chain = Mock()
        mock_survey_chain.generate_survey.return_value = expected_survey
        mock_survey_chain_class.return_value = mock_survey_chain
        
        with patch('app.services.langchain_pipeline.CurriculumGeneratorChain'), \
             patch('app.services.langchain_pipeline.LessonPlannerChain'), \
             patch('app.services.langchain_pipeline.ContentGeneratorChain'):
            
            pipeline = LangChainPipelineService()
            result = pipeline.generate_survey("python", ["rag_doc"])
        
        assert result == expected_survey
        mock_survey_chain.generate_survey.assert_called_once_with("python", ["rag_doc"])
    
    @patch('app.services.langchain_pipeline.validate_environment')
    @patch('app.services.langchain_pipeline.SurveyGenerationChain')
    @patch('app.services.langchain_pipeline.CurriculumGeneratorChain')
    @patch('app.services.langchain_pipeline.LessonPlannerChain')
    @patch('app.services.langchain_pipeline.ContentGeneratorChain')
    def test_pipeline_data_flow_integrity(self, mock_content_chain_class, mock_lesson_chain_class,
                                        mock_curriculum_chain_class, mock_survey_chain_class, mock_validate,
                                        complete_survey_data, complete_curriculum_data, 
                                        complete_lesson_plans_data, sample_lesson_contents):
        """Test data flow integrity between pipeline stages"""
        mock_validate.return_value = True
        
        # Mock chains to capture and verify data flow
        mock_curriculum_chain = Mock()
        mock_curriculum_chain.generate_curriculum.return_value = complete_curriculum_data
        mock_curriculum_chain_class.return_value = mock_curriculum_chain
        
        mock_lesson_chain = Mock()
        mock_lesson_chain.generate_lesson_plans.return_value = complete_lesson_plans_data
        mock_lesson_chain_class.return_value = mock_lesson_chain
        
        mock_content_chain = Mock()
        mock_content_chain.generate_content.side_effect = [
            sample_lesson_contents[0]["content"],
            sample_lesson_contents[1]["content"]
        ]
        mock_content_chain_class.return_value = mock_content_chain
        
        pipeline = LangChainPipelineService()
        result = pipeline.run_full_pipeline(complete_survey_data, "python")
        
        # Verify data flow: survey_data -> curriculum_generation
        curriculum_call_args = mock_curriculum_chain.generate_curriculum.call_args[0]
        assert curriculum_call_args[0] == complete_survey_data  # Survey data passed correctly
        assert curriculum_call_args[1] == "python"  # Subject passed correctly
        
        # Verify data flow: curriculum_data -> lesson_planning
        lesson_call_args = mock_lesson_chain.generate_lesson_plans.call_args[0]
        assert lesson_call_args[0] == complete_curriculum_data  # Curriculum data passed correctly
        assert lesson_call_args[1] == "python"  # Subject passed correctly
        
        # Verify data flow: lesson_plans -> content_generation
        content_calls = mock_content_chain.generate_content.call_args_list
        assert len(content_calls) == 2  # Called for each lesson plan
        
        # Check first content generation call
        first_call_args = content_calls[0][0]
        assert first_call_args[0] == complete_lesson_plans_data["lesson_plans"][0]  # First lesson plan
        assert first_call_args[1] == "python"  # Subject passed correctly
        
        # Check second content generation call
        second_call_args = content_calls[1][0]
        assert second_call_args[0] == complete_lesson_plans_data["lesson_plans"][1]  # Second lesson plan
        assert second_call_args[1] == "python"  # Subject passed correctly
    
    @patch('app.services.langchain_pipeline.validate_environment')
    @patch('app.services.langchain_pipeline.SurveyGenerationChain')
    @patch('app.services.langchain_pipeline.CurriculumGeneratorChain')
    @patch('app.services.langchain_pipeline.LessonPlannerChain')
    @patch('app.services.langchain_pipeline.ContentGeneratorChain')
    def test_pipeline_with_empty_lesson_plans(self, mock_content_chain_class, mock_lesson_chain_class,
                                            mock_curriculum_chain_class, mock_survey_chain_class, mock_validate,
                                            complete_survey_data, complete_curriculum_data):
        """Test pipeline handling when lesson plans stage returns empty results"""
        mock_validate.return_value = True
        
        # Mock curriculum generation
        mock_curriculum_chain = Mock()
        mock_curriculum_chain.generate_curriculum.return_value = complete_curriculum_data
        mock_curriculum_chain_class.return_value = mock_curriculum_chain
        
        # Mock lesson planning with empty results
        empty_lesson_plans = {
            "lesson_plans": [],
            "generated_at": "2024-01-15T10:05:00Z",
            "generation_stage": "lesson_plans_complete"
        }
        mock_lesson_chain = Mock()
        mock_lesson_chain.generate_lesson_plans.return_value = empty_lesson_plans
        mock_lesson_chain_class.return_value = mock_lesson_chain
        
        # Content generation should not be called
        mock_content_chain = Mock()
        mock_content_chain_class.return_value = mock_content_chain
        
        pipeline = LangChainPipelineService()
        result = pipeline.run_full_pipeline(complete_survey_data, "python")
        
        # Verify pipeline completed but with empty content
        assert result["status"] == "completed"
        assert result["lesson_contents"] == []  # No content generated
        
        # Verify content generation was not called
        mock_content_chain.generate_content.assert_not_called()

class TestMockXAIAPIIntegration:
    """Tests for mocked xAI API interactions"""
    
    @patch('app.services.langchain_base.requests.post')
    @patch('app.services.langchain_base.current_app')
    def test_xai_api_call_success(self, mock_app, mock_post):
        """Test successful xAI API call"""
        mock_app.config = {'XAI_API_KEY': 'test-key', 'GROK_API_URL': 'https://test.api.com'}
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response from Grok"}}]
        }
        mock_post.return_value = mock_response
        
        from app.services.langchain_base import XAILLM
        
        llm = XAILLM()
        result = llm._call("Test prompt")
        
        assert result == "Test response from Grok"
        
        # Verify API call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://test.api.com/chat/completions"
        
        # Verify request headers
        headers = call_args[1]['headers']
        assert headers['Authorization'] == 'Bearer test-key'
        assert headers['Content-Type'] == 'application/json'
        
        # Verify request payload
        payload = call_args[1]['json']
        assert payload['model'] == 'grok-3-mini'
        assert payload['messages'][0]['content'] == 'Test prompt'
    
    @patch('app.services.langchain_base.requests.post')
    @patch('app.services.langchain_base.current_app')
    def test_xai_api_rate_limit_retry(self, mock_app, mock_post):
        """Test xAI API rate limit handling with retry"""
        mock_app.config = {'XAI_API_KEY': 'test-key', 'GROK_API_URL': 'https://test.api.com'}
        
        # Mock rate limit response followed by success
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.text = "Rate limited"
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Success after retry"}}]
        }
        
        mock_post.side_effect = [rate_limit_response, success_response]
        
        from app.services.langchain_base import XAILLM
        
        llm = XAILLM()
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = llm._call("Test prompt")
        
        assert result == "Success after retry"
        assert mock_post.call_count == 2
    
    @patch('app.services.langchain_base.requests.post')
    @patch('app.services.langchain_base.current_app')
    def test_xai_api_server_error_retry(self, mock_app, mock_post):
        """Test xAI API server error handling with retry"""
        mock_app.config = {'XAI_API_KEY': 'test-key', 'GROK_API_URL': 'https://test.api.com'}
        
        # Mock server error response followed by success
        server_error_response = Mock()
        server_error_response.status_code = 500
        server_error_response.text = "Internal server error"
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Success after server recovery"}}]
        }
        
        mock_post.side_effect = [server_error_response, success_response]
        
        from app.services.langchain_base import XAILLM
        from app.services.langchain_base import XAIAPIError
        
        llm = XAILLM()
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = llm._call("Test prompt")
        
        assert result == "Success after server recovery"
        assert mock_post.call_count == 2
    
    @patch('app.services.langchain_base.requests.post')
    @patch('app.services.langchain_base.current_app')
    def test_xai_api_client_error_no_retry(self, mock_app, mock_post):
        """Test xAI API client error (no retry)"""
        mock_app.config = {'XAI_API_KEY': 'test-key', 'GROK_API_URL': 'https://test.api.com'}
        
        # Mock client error response (400 Bad Request)
        client_error_response = Mock()
        client_error_response.status_code = 400
        client_error_response.text = "Bad request"
        mock_post.return_value = client_error_response
        
        from app.services.langchain_base import XAILLM
        from app.services.langchain_base import XAIAPIError
        
        llm = XAILLM()
        
        with pytest.raises(XAIAPIError, match="API error 400"):
            llm._call("Test prompt")
        
        # Should not retry for client errors
        mock_post.assert_called_once()
    
    @patch('app.services.langchain_base.requests.post')
    @patch('app.services.langchain_base.current_app')
    def test_xai_api_timeout_retry(self, mock_app, mock_post):
        """Test xAI API timeout handling with retry"""
        mock_app.config = {'XAI_API_KEY': 'test-key', 'GROK_API_URL': 'https://test.api.com'}
        
        # Mock timeout followed by success
        import requests
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Success after timeout recovery"}}]
        }
        
        mock_post.side_effect = [requests.exceptions.Timeout(), success_response]
        
        from app.services.langchain_base import XAILLM
        
        llm = XAILLM()
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = llm._call("Test prompt")
        
        assert result == "Success after timeout recovery"
        assert mock_post.call_count == 2