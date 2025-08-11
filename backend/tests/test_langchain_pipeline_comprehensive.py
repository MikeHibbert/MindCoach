"""
Comprehensive unit tests for LangChain pipeline components
Tests for subtask 22.1: Create LangChain pipeline tests
"""
import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock, call
from app.services.langchain_chains import (
    SurveyGenerationChain,
    CurriculumGeneratorChain,
    LessonPlannerChain,
    ContentGeneratorChain,
    BaseLangChainService,
    ContentGenerationChain
)
from app.services.langchain_pipeline import LangChainPipelineService
from app.services.langchain_base import (
    XAILLM,
    XAIAPIError,
    JSONOutputParser,
    MarkdownOutputParser
)

class TestBaseLangChainService:
    """Test base LangChain service functionality"""
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_base_service_initialization(self, mock_llm_class, mock_validate):
        """Test base service initialization with default parameters"""
        mock_validate.return_value = True
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        # Create a concrete implementation for testing
        class TestService(BaseLangChainService):
            def get_prompt_template(self):
                from langchain_core.prompts import PromptTemplate
                return PromptTemplate(
                    input_variables=["test_var"],
                    template="Test template with {test_var}"
                )
        
        service = TestService()
        
        assert service.llm == mock_llm
        assert service.json_parser is not None
        assert service.markdown_parser is not None
        mock_llm_class.assert_called_once_with(temperature=0.7, max_tokens=2000)
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_base_service_custom_parameters(self, mock_llm_class, mock_validate):
        """Test base service initialization with custom parameters"""
        mock_validate.return_value = True
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        class TestService(BaseLangChainService):
            def get_prompt_template(self):
                from langchain_core.prompts import PromptTemplate
                return PromptTemplate(
                    input_variables=["test_var"],
                    template="Test template with {test_var}"
                )
        
        service = TestService(temperature=0.5, max_tokens=1500)
        
        mock_llm_class.assert_called_once_with(temperature=0.5, max_tokens=1500)
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    @patch('app.services.langchain_chains.LLMChain')
    def test_create_chain(self, mock_llm_chain_class, mock_llm_class, mock_validate):
        """Test chain creation"""
        mock_validate.return_value = True
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        mock_chain = Mock()
        mock_llm_chain_class.return_value = mock_chain
        
        class TestService(BaseLangChainService):
            def get_prompt_template(self):
                from langchain_core.prompts import PromptTemplate
                return PromptTemplate(
                    input_variables=["test_var"],
                    template="Test template with {test_var}"
                )
        
        service = TestService()
        chain = service.create_chain()
        
        assert chain == mock_chain
        mock_llm_chain_class.assert_called_once()
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    @patch('app.services.langchain_chains.LLMChain')
    def test_generate_with_retry_success_first_attempt(self, mock_llm_chain_class, mock_llm_class, mock_validate):
        """Test successful generation on first attempt"""
        mock_validate.return_value = True
        mock_chain = Mock()
        mock_chain.run.return_value = "Success result"
        
        class TestService(BaseLangChainService):
            def get_prompt_template(self):
                from langchain_core.prompts import PromptTemplate
                return PromptTemplate(
                    input_variables=["test_var"],
                    template="Test template with {test_var}"
                )
        
        service = TestService()
        result = service.generate_with_retry(mock_chain, {"test_var": "test_value"})
        
        assert result == "Success result"
        mock_chain.run.assert_called_once_with(test_var="test_value")
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_generate_with_retry_json_parsing_error_then_success(self, mock_llm_class, mock_validate):
        """Test retry logic for JSON parsing errors"""
        mock_validate.return_value = True
        
        mock_chain = Mock()
        # First call fails with JSON error, second succeeds
        mock_chain.run.side_effect = [
            ValueError("Invalid JSON in response"),
            "Success result"
        ]
        
        class TestService(BaseLangChainService):
            def get_prompt_template(self):
                from langchain_core.prompts import PromptTemplate
                return PromptTemplate(
                    input_variables=["test_var"],
                    template="Test template with {test_var}"
                )
        
        service = TestService()
        result = service.generate_with_retry(mock_chain, {"test_var": "test_value"}, max_attempts=3)
        
        assert result == "Success result"
        assert mock_chain.run.call_count == 2
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_generate_with_retry_exhausts_attempts(self, mock_llm_class, mock_validate):
        """Test retry logic when all attempts are exhausted"""
        mock_validate.return_value = True
        
        mock_chain = Mock()
        mock_chain.run.side_effect = ValueError("Persistent error")
        
        class TestService(BaseLangChainService):
            def get_prompt_template(self):
                from langchain_core.prompts import PromptTemplate
                return PromptTemplate(
                    input_variables=["test_var"],
                    template="Test template with {test_var}"
                )
        
        service = TestService()
        
        with pytest.raises(Exception, match="All 3 generation attempts failed"):
            service.generate_with_retry(mock_chain, {"test_var": "test_value"}, max_attempts=3)
        
        assert mock_chain.run.call_count == 3

class TestContentGenerationChain:
    """Test content generation chain base functionality"""
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_content_generation_chain_initialization(self, mock_llm_class, mock_validate):
        """Test content generation chain initialization"""
        mock_validate.return_value = True
        
        class TestContentChain(ContentGenerationChain):
            def get_prompt_template(self):
                from langchain_core.prompts import PromptTemplate
                return PromptTemplate(
                    input_variables=["test_var"],
                    template="Test template with {test_var}"
                )
        
        chain = TestContentChain()
        
        assert chain.llm is not None
        mock_llm_class.assert_called_once_with(temperature=0.7, max_tokens=3000)
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    @patch('app.services.langchain_chains.rag_service')
    def test_load_rag_documents(self, mock_rag_service, mock_llm_class, mock_validate):
        """Test RAG document loading"""
        mock_validate.return_value = True
        mock_rag_service.load_documents_for_stage.return_value = ["doc1", "doc2"]
        
        class TestContentChain(ContentGenerationChain):
            def get_prompt_template(self):
                from langchain_core.prompts import PromptTemplate
                return PromptTemplate(
                    input_variables=["test_var"],
                    template="Test template with {test_var}"
                )
        
        chain = TestContentChain()
        docs = chain.load_rag_documents("test_type", "python")
        
        assert docs == ["doc1", "doc2"]
        mock_rag_service.load_documents_for_stage.assert_called_once_with("test_type", "python")
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_validate_output_success(self, mock_llm_class, mock_validate):
        """Test successful output validation"""
        mock_validate.return_value = True
        
        class TestContentChain(ContentGenerationChain):
            def get_prompt_template(self):
                from langchain_core.prompts import PromptTemplate
                return PromptTemplate(
                    input_variables=["test_var"],
                    template="Test template with {test_var}"
                )
        
        chain = TestContentChain()
        
        # Test with valid output
        valid_output = {"key1": "value1", "key2": "value2"}
        result = chain.validate_output(valid_output, ["key1", "key2"])
        assert result is True
        
        # Test without expected keys (should pass)
        result = chain.validate_output(valid_output)
        assert result is True
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_validate_output_failure(self, mock_llm_class, mock_validate):
        """Test output validation failure"""
        mock_validate.return_value = True
        
        class TestContentChain(ContentGenerationChain):
            def get_prompt_template(self):
                from langchain_core.prompts import PromptTemplate
                return PromptTemplate(
                    input_variables=["test_var"],
                    template="Test template with {test_var}"
                )
        
        chain = TestContentChain()
        
        # Test with missing keys
        invalid_output = {"key1": "value1"}
        result = chain.validate_output(invalid_output, ["key1", "key2", "key3"])
        assert result is False

class TestSurveyGenerationChainComprehensive:
    """Comprehensive tests for survey generation chain"""
    
    @pytest.fixture
    def sample_rag_docs(self):
        """Sample RAG documents for testing"""
        return [
            "Generate 7-8 multiple choice questions",
            "Difficulty distribution: 30% beginner, 50% intermediate, 20% advanced",
            "Each question has exactly 4 options",
            "Only one correct answer per question"
        ]
    
    @pytest.fixture
    def valid_survey_response(self):
        """Valid survey response for testing"""
        return {
            "questions": [
                {
                    "id": 1,
                    "question": "What is Python?",
                    "type": "multiple_choice",
                    "options": ["A programming language", "A snake", "A tool", "A framework"],
                    "correct_answer": "A programming language",
                    "difficulty": "beginner",
                    "topic": "basics"
                },
                {
                    "id": 2,
                    "question": "How do you create a list in Python?",
                    "type": "multiple_choice",
                    "options": ["[]", "{}", "()", "||"],
                    "correct_answer": "[]",
                    "difficulty": "intermediate",
                    "topic": "data_structures"
                }
            ],
            "total_questions": 2,
            "subject": "python"
        }
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    @patch('app.services.langchain_chains.LLMChain')
    def test_survey_generation_complete_workflow(self, mock_llm_chain_class, mock_llm_class, 
                                               mock_validate, sample_rag_docs, valid_survey_response):
        """Test complete survey generation workflow"""
        mock_validate.return_value = True
        
        mock_chain = Mock()
        mock_chain.run.return_value = valid_survey_response
        mock_llm_chain_class.return_value = mock_chain
        
        survey_chain = SurveyGenerationChain()
        result = survey_chain.generate_survey("python", sample_rag_docs)
        
        # Verify structure
        assert result["subject"] == "python"
        assert result["total_questions"] == 2
        assert len(result["questions"]) == 2
        assert "generated_at" in result
        assert result["generation_method"] == "langchain"
        assert result["model"] == "grok-3-mini"
        
        # Verify chain was called correctly
        mock_chain.run.assert_called_once()
        call_args = mock_chain.run.call_args[1]
        assert call_args["subject"] == "python"
        assert "rag_guidelines" in call_args
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_survey_quality_validation_success(self, mock_llm_class, mock_validate, valid_survey_response):
        """Test survey quality validation with valid survey"""
        mock_validate.return_value = True
        
        survey_chain = SurveyGenerationChain()
        result = survey_chain._validate_survey_quality(valid_survey_response)
        
        assert result is True
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_survey_quality_validation_invalid_question_count(self, mock_llm_class, mock_validate):
        """Test survey quality validation with invalid question count"""
        mock_validate.return_value = True
        
        invalid_survey = {
            "questions": [],  # No questions
            "total_questions": 0,
            "subject": "python"
        }
        
        survey_chain = SurveyGenerationChain()
        result = survey_chain._validate_survey_quality(invalid_survey)
        
        assert result is False
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_survey_quality_validation_missing_difficulties(self, mock_llm_class, mock_validate):
        """Test survey quality validation with missing difficulty levels"""
        mock_validate.return_value = True
        
        # All questions are advanced - missing beginner and intermediate
        invalid_survey = {
            "questions": [
                {
                    "id": 1,
                    "question": "Test question",
                    "type": "multiple_choice",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "difficulty": "advanced",
                    "topic": "test"
                }
            ],
            "total_questions": 1,
            "subject": "python"
        }
        
        survey_chain = SurveyGenerationChain()
        result = survey_chain._validate_survey_quality(invalid_survey)
        
        assert result is False
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_question_quality_validation_success(self, mock_llm_class, mock_validate):
        """Test individual question quality validation with valid question"""
        mock_validate.return_value = True
        
        valid_question = {
            "id": 1,
            "question": "What is Python?",
            "type": "multiple_choice",
            "options": ["A programming language", "A snake", "A tool", "A framework"],
            "correct_answer": "A programming language",
            "difficulty": "beginner",
            "topic": "basics"
        }
        
        survey_chain = SurveyGenerationChain()
        result = survey_chain._validate_question_quality(valid_question, 1)
        
        assert result is True
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_question_quality_validation_missing_fields(self, mock_llm_class, mock_validate):
        """Test question quality validation with missing required fields"""
        mock_validate.return_value = True
        
        invalid_question = {
            "id": 1,
            "question": "What is Python?",
            # Missing: type, options, correct_answer, difficulty, topic
        }
        
        survey_chain = SurveyGenerationChain()
        result = survey_chain._validate_question_quality(invalid_question, 1)
        
        assert result is False
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_question_quality_validation_invalid_options(self, mock_llm_class, mock_validate):
        """Test question quality validation with invalid options"""
        mock_validate.return_value = True
        
        invalid_question = {
            "id": 1,
            "question": "What is Python?",
            "type": "multiple_choice",
            "options": ["A", "B"],  # Only 2 options instead of 4
            "correct_answer": "A",
            "difficulty": "beginner",
            "topic": "basics"
        }
        
        survey_chain = SurveyGenerationChain()
        result = survey_chain._validate_question_quality(invalid_question, 1)
        
        assert result is False
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_question_quality_validation_invalid_correct_answer(self, mock_llm_class, mock_validate):
        """Test question quality validation with correct answer not in options"""
        mock_validate.return_value = True
        
        invalid_question = {
            "id": 1,
            "question": "What is Python?",
            "type": "multiple_choice",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "E",  # Not in options
            "difficulty": "beginner",
            "topic": "basics"
        }
        
        survey_chain = SurveyGenerationChain()
        result = survey_chain._validate_question_quality(invalid_question, 1)
        
        assert result is False
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    @patch('app.services.langchain_chains.LLMChain')
    def test_survey_generation_with_default_guidelines(self, mock_llm_chain_class, mock_llm_class, 
                                                     mock_validate, valid_survey_response):
        """Test survey generation without RAG documents (uses default guidelines)"""
        mock_validate.return_value = True
        
        mock_chain = Mock()
        mock_chain.run.return_value = valid_survey_response
        mock_llm_chain_class.return_value = mock_chain
        
        survey_chain = SurveyGenerationChain()
        result = survey_chain.generate_survey("python", None)  # No RAG docs
        
        assert result["subject"] == "python"
        
        # Verify default guidelines were used
        call_args = mock_chain.run.call_args[1]
        assert "Generate 7-8 multiple choice questions" in call_args["rag_guidelines"]

class TestContentGeneratorChainComprehensive:
    """Comprehensive tests for content generator chain"""
    
    @pytest.fixture
    def sample_lesson_plan(self):
        """Sample lesson plan for testing"""
        return {
            "lesson_id": 1,
            "title": "Python Variables and Data Types",
            "learning_objectives": [
                "Understand Python variable assignment",
                "Work with different data types",
                "Apply type conversion techniques"
            ],
            "structure": {
                "introduction": "5 minutes",
                "main_content": "25 minutes",
                "examples": "15 minutes",
                "exercises": "15 minutes",
                "summary": "5 minutes"
            },
            "activities": [
                "Variable assignment demonstration",
                "Data type exploration",
                "Type conversion exercises"
            ],
            "assessment": "Coding exercises with variables and data types",
            "materials_needed": [
                "Python IDE",
                "Code examples"
            ],
            "key_concepts": [
                "variables",
                "data_types",
                "type_conversion"
            ]
        }
    
    @pytest.fixture
    def sample_rag_docs(self):
        """Sample RAG documents for content generation"""
        return [
            "Create clear, engaging content with practical examples",
            "Include exactly 2 code examples with detailed explanations",
            "Provide 3-5 hands-on exercises of varying difficulty",
            "Use proper markdown formatting"
        ]
    
    @pytest.fixture
    def valid_lesson_content(self):
        """Valid lesson content for testing"""
        return """# Python Variables and Data Types

## Introduction

Welcome to this lesson on Python variables and data types. In this lesson, you'll learn how to store and manipulate data in Python.

## Core Concepts

### Variables
Variables in Python are containers for storing data values. Unlike other programming languages, Python has no command for declaring a variable.

### Data Types
Python has several built-in data types including integers, floats, strings, and booleans.

## Code Examples

### Example 1: Variable Assignment
```python
# Assigning values to variables
name = "Alice"
age = 25
height = 5.6
is_student = True

print(f"Name: {name}, Age: {age}")
```

### Example 2: Type Conversion
```python
# Converting between data types
number_str = "42"
number_int = int(number_str)
number_float = float(number_str)

print(f"String: {number_str}, Int: {number_int}, Float: {number_float}")
```

## Hands-on Exercises

### Exercise 1: Basic Variables
Create variables for your personal information and print them.

### Exercise 2: Type Conversion
Convert a string input to different numeric types.

### Exercise 3: Data Type Checking
Use the `type()` function to check variable types.

## Summary

In this lesson, you learned about Python variables and data types, including how to assign values and convert between types.
"""
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    @patch('app.services.langchain_chains.LLMChain')
    def test_content_generation_complete_workflow(self, mock_llm_chain_class, mock_llm_class, 
                                                mock_validate, sample_lesson_plan, sample_rag_docs, 
                                                valid_lesson_content):
        """Test complete content generation workflow"""
        mock_validate.return_value = True
        
        mock_chain = Mock()
        mock_chain.run.return_value = valid_lesson_content
        mock_llm_chain_class.return_value = mock_chain
        
        content_chain = ContentGeneratorChain()
        result = content_chain.generate_content(sample_lesson_plan, "python", sample_rag_docs)
        
        # Verify content structure
        assert len(result) > 100  # Should be substantial content
        assert "# Python Variables and Data Types" in result
        assert "```python" in result  # Should contain code blocks
        assert "Exercise" in result  # Should contain exercises
        
        # Verify chain was called correctly
        mock_chain.run.assert_called_once()
        call_args = mock_chain.run.call_args[1]
        assert call_args["subject"] == "python"
        assert "lesson_plan" in call_args
        assert "rag_guidelines" in call_args
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_format_lesson_plan(self, mock_llm_class, mock_validate, sample_lesson_plan):
        """Test lesson plan formatting for prompt"""
        mock_validate.return_value = True
        
        content_chain = ContentGeneratorChain()
        formatted_plan = content_chain._format_lesson_plan(sample_lesson_plan)
        
        assert "Lesson 1: Python Variables and Data Types" in formatted_plan
        assert "Learning Objectives:" in formatted_plan
        assert "Understand Python variable assignment" in formatted_plan
        assert "Time Allocation:" in formatted_plan
        assert "Introduction: 5 minutes" in formatted_plan
        assert "Key Concepts to Cover:" in formatted_plan
        assert "variables" in formatted_plan
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_validate_content_structure_success(self, mock_llm_class, mock_validate, valid_lesson_content):
        """Test content structure validation with valid content"""
        mock_validate.return_value = True
        
        content_chain = ContentGeneratorChain()
        result = content_chain._validate_content_structure(valid_lesson_content)
        
        assert result is True
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_validate_content_structure_missing_elements(self, mock_llm_class, mock_validate):
        """Test content structure validation with missing elements"""
        mock_validate.return_value = True
        
        # Content without code blocks or proper structure
        invalid_content = "This is just plain text without proper structure."
        
        content_chain = ContentGeneratorChain()
        result = content_chain._validate_content_structure(invalid_content)
        
        assert result is False
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    @patch('app.services.langchain_chains.LLMChain')
    def test_content_generation_empty_content_error(self, mock_llm_chain_class, mock_llm_class, 
                                                  mock_validate, sample_lesson_plan):
        """Test content generation with empty/short content raises error"""
        mock_validate.return_value = True
        
        mock_chain = Mock()
        mock_chain.run.return_value = "Short"  # Too short content
        mock_llm_chain_class.return_value = mock_chain
        
        content_chain = ContentGeneratorChain()
        
        with pytest.raises(ValueError, match="Generated content is too short or empty"):
            content_chain.generate_content(sample_lesson_plan, "python")

class TestLangChainPipelineServiceComprehensive:
    """Comprehensive tests for LangChain pipeline service"""
    
    @pytest.fixture
    def sample_survey_data(self):
        """Sample survey data for testing"""
        return {
            'skill_level': 'intermediate',
            'answers': [
                {'question_id': 1, 'topic': 'variables', 'correct': True},
                {'question_id': 2, 'topic': 'functions', 'correct': False}
            ]
        }
    
    @pytest.fixture
    def sample_curriculum_data(self):
        """Sample curriculum data for testing"""
        return {
            "curriculum": {
                "subject": "python",
                "skill_level": "intermediate",
                "total_lessons": 2,
                "learning_objectives": ["Learn Python basics"],
                "topics": [
                    {
                        "lesson_id": 1,
                        "title": "Variables",
                        "topics": ["variables", "assignment"],
                        "prerequisites": [],
                        "difficulty": "intermediate"
                    }
                ]
            }
        }
    
    @pytest.fixture
    def sample_lesson_plans_data(self):
        """Sample lesson plans data for testing"""
        return {
            "lesson_plans": [
                {
                    "lesson_id": 1,
                    "title": "Variables",
                    "learning_objectives": ["Understand variables"],
                    "structure": {"introduction": "5 minutes"},
                    "activities": ["Variable demo"],
                    "assessment": "Coding exercise"
                }
            ]
        }
    
    @patch('app.services.langchain_pipeline.validate_environment')
    @patch('app.services.langchain_pipeline.SurveyGenerationChain')
    @patch('app.services.langchain_pipeline.CurriculumGeneratorChain')
    @patch('app.services.langchain_pipeline.LessonPlannerChain')
    @patch('app.services.langchain_pipeline.ContentGeneratorChain')
    def test_pipeline_initialization_all_chains(self, mock_content_chain, mock_lesson_chain, 
                                               mock_curriculum_chain, mock_survey_chain, mock_validate):
        """Test pipeline service initializes all chain components"""
        mock_validate.return_value = True
        
        pipeline = LangChainPipelineService()
        
        # Verify all chains were initialized
        mock_survey_chain.assert_called_once_with(temperature=0.8, max_tokens=2000)
        mock_curriculum_chain.assert_called_once_with(temperature=0.7, max_tokens=3000)
        mock_lesson_chain.assert_called_once_with(temperature=0.7, max_tokens=3000)
        mock_content_chain.assert_called_once_with(temperature=0.6, max_tokens=4000)
    
    @patch('app.services.langchain_pipeline.validate_environment')
    @patch('app.services.langchain_pipeline.SurveyGenerationChain')
    def test_generate_survey_success(self, mock_survey_chain_class, mock_validate, sample_survey_data):
        """Test successful survey generation"""
        mock_validate.return_value = True
        
        mock_survey_chain = Mock()
        mock_survey_chain.generate_survey.return_value = {"questions": [], "subject": "python"}
        mock_survey_chain_class.return_value = mock_survey_chain
        
        with patch('app.services.langchain_pipeline.CurriculumGeneratorChain'), \
             patch('app.services.langchain_pipeline.LessonPlannerChain'), \
             patch('app.services.langchain_pipeline.ContentGeneratorChain'):
            
            pipeline = LangChainPipelineService()
            result = pipeline.generate_survey("python", ["rag_doc"])
        
        assert result["subject"] == "python"
        mock_survey_chain.generate_survey.assert_called_once_with("python", ["rag_doc"])
    
    @patch('app.services.langchain_pipeline.validate_environment')
    @patch('app.services.langchain_pipeline.CurriculumGeneratorChain')
    def test_generate_curriculum_success(self, mock_curriculum_chain_class, mock_validate, 
                                       sample_survey_data, sample_curriculum_data):
        """Test successful curriculum generation"""
        mock_validate.return_value = True
        
        mock_curriculum_chain = Mock()
        mock_curriculum_chain.generate_curriculum.return_value = sample_curriculum_data
        mock_curriculum_chain_class.return_value = mock_curriculum_chain
        
        with patch('app.services.langchain_pipeline.SurveyGenerationChain'), \
             patch('app.services.langchain_pipeline.LessonPlannerChain'), \
             patch('app.services.langchain_pipeline.ContentGeneratorChain'):
            
            pipeline = LangChainPipelineService()
            result = pipeline.generate_curriculum(sample_survey_data, "python", ["rag_doc"])
        
        assert result["curriculum"]["subject"] == "python"
        mock_curriculum_chain.generate_curriculum.assert_called_once_with(sample_survey_data, "python", ["rag_doc"])
    
    @patch('app.services.langchain_pipeline.validate_environment')
    @patch('app.services.langchain_pipeline.LessonPlannerChain')
    def test_generate_lesson_plans_success(self, mock_lesson_chain_class, mock_validate, 
                                         sample_curriculum_data, sample_lesson_plans_data):
        """Test successful lesson plans generation"""
        mock_validate.return_value = True
        
        mock_lesson_chain = Mock()
        mock_lesson_chain.generate_lesson_plans.return_value = sample_lesson_plans_data
        mock_lesson_chain_class.return_value = mock_lesson_chain
        
        with patch('app.services.langchain_pipeline.SurveyGenerationChain'), \
             patch('app.services.langchain_pipeline.CurriculumGeneratorChain'), \
             patch('app.services.langchain_pipeline.ContentGeneratorChain'):
            
            pipeline = LangChainPipelineService()
            result = pipeline.generate_lesson_plans(sample_curriculum_data, "python", ["rag_doc"])
        
        assert len(result["lesson_plans"]) == 1
        mock_lesson_chain.generate_lesson_plans.assert_called_once_with(sample_curriculum_data, "python", ["rag_doc"])
    
    @patch('app.services.langchain_pipeline.validate_environment')
    @patch('app.services.langchain_pipeline.ContentGeneratorChain')
    def test_generate_lesson_content_success(self, mock_content_chain_class, mock_validate):
        """Test successful lesson content generation"""
        mock_validate.return_value = True
        
        lesson_plan = {"lesson_id": 1, "title": "Test Lesson"}
        expected_content = "# Test Lesson\n\nLesson content here..."
        
        mock_content_chain = Mock()
        mock_content_chain.generate_content.return_value = expected_content
        mock_content_chain_class.return_value = mock_content_chain
        
        with patch('app.services.langchain_pipeline.SurveyGenerationChain'), \
             patch('app.services.langchain_pipeline.CurriculumGeneratorChain'), \
             patch('app.services.langchain_pipeline.LessonPlannerChain'):
            
            pipeline = LangChainPipelineService()
            result = pipeline.generate_lesson_content(lesson_plan, "python", ["rag_doc"])
        
        assert result == expected_content
        mock_content_chain.generate_content.assert_called_once_with(lesson_plan, "python", ["rag_doc"])
    
    @patch('app.services.langchain_pipeline.validate_environment')
    @patch('app.services.langchain_pipeline.SurveyGenerationChain')
    @patch('app.services.langchain_pipeline.CurriculumGeneratorChain')
    @patch('app.services.langchain_pipeline.LessonPlannerChain')
    @patch('app.services.langchain_pipeline.ContentGeneratorChain')
    def test_run_full_pipeline_success(self, mock_content_chain_class, mock_lesson_chain_class,
                                     mock_curriculum_chain_class, mock_survey_chain_class, mock_validate,
                                     sample_survey_data, sample_curriculum_data, sample_lesson_plans_data):
        """Test successful full pipeline execution"""
        mock_validate.return_value = True
        
        # Mock all chain responses
        mock_curriculum_chain = Mock()
        mock_curriculum_chain.generate_curriculum.return_value = sample_curriculum_data
        mock_curriculum_chain_class.return_value = mock_curriculum_chain
        
        mock_lesson_chain = Mock()
        mock_lesson_chain.generate_lesson_plans.return_value = sample_lesson_plans_data
        mock_lesson_chain_class.return_value = mock_lesson_chain
        
        mock_content_chain = Mock()
        mock_content_chain.generate_content.return_value = "# Lesson Content"
        mock_content_chain_class.return_value = mock_content_chain
        
        pipeline = LangChainPipelineService()
        result = pipeline.run_full_pipeline(sample_survey_data, "python")
        
        # Verify pipeline result structure
        assert result["status"] == "completed"
        assert result["subject"] == "python"
        assert "curriculum" in result
        assert "lesson_plans" in result
        assert "lesson_contents" in result
        assert len(result["lesson_contents"]) == 1
        
        # Verify all stages were called
        mock_curriculum_chain.generate_curriculum.assert_called_once()
        mock_lesson_chain.generate_lesson_plans.assert_called_once()
        mock_content_chain.generate_content.assert_called_once()
    
    @patch('app.services.langchain_pipeline.validate_environment')
    def test_get_pipeline_status(self, mock_validate):
        """Test pipeline status reporting"""
        mock_validate.return_value = True
        
        with patch('app.services.langchain_pipeline.SurveyGenerationChain'), \
             patch('app.services.langchain_pipeline.CurriculumGeneratorChain'), \
             patch('app.services.langchain_pipeline.LessonPlannerChain'), \
             patch('app.services.langchain_pipeline.ContentGeneratorChain'):
            
            pipeline = LangChainPipelineService()
            status = pipeline.get_pipeline_status()
        
        # Verify all components are implemented
        assert status["survey_generation"] == "implemented"
        assert status["curriculum_generation"] == "implemented"
        assert status["lesson_planning"] == "implemented"
        assert status["content_generation"] == "implemented"
        assert status["rag_system"] == "implemented"
        assert status["xai_connection"] == "implemented"

class TestPerformanceAndIntegration:
    """Performance and integration tests for LangChain components"""
    
    @patch('app.services.langchain_pipeline.validate_environment')
    @patch('app.services.langchain_pipeline.SurveyGenerationChain')
    def test_survey_generation_performance(self, mock_survey_chain_class, mock_validate):
        """Test survey generation performance"""
        mock_validate.return_value = True
        
        mock_survey_chain = Mock()
        mock_survey_chain.generate_survey.return_value = {"questions": [], "subject": "python"}
        mock_survey_chain_class.return_value = mock_survey_chain
        
        with patch('app.services.langchain_pipeline.CurriculumGeneratorChain'), \
             patch('app.services.langchain_pipeline.LessonPlannerChain'), \
             patch('app.services.langchain_pipeline.ContentGeneratorChain'):
            
            pipeline = LangChainPipelineService()
            
            # Measure execution time
            start_time = time.time()
            pipeline.generate_survey("python")
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # Should complete quickly (mocked, so should be very fast)
            assert execution_time < 1.0  # Less than 1 second
    
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
        
        assert result["status"] == "success"
        assert result["message"] == "Connection successful"
        assert "timestamp" in result
        mock_test_connection.assert_called_once()
    
    @patch('app.services.langchain_pipeline.validate_environment')
    @patch('app.services.langchain_pipeline.SurveyGenerationChain')
    def test_error_handling_and_recovery(self, mock_survey_chain_class, mock_validate):
        """Test error handling and recovery mechanisms"""
        mock_validate.return_value = True
        
        mock_survey_chain = Mock()
        mock_survey_chain.generate_survey.side_effect = Exception("API Error")
        mock_survey_chain_class.return_value = mock_survey_chain
        
        with patch('app.services.langchain_pipeline.CurriculumGeneratorChain'), \
             patch('app.services.langchain_pipeline.LessonPlannerChain'), \
             patch('app.services.langchain_pipeline.ContentGeneratorChain'):
            
            pipeline = LangChainPipelineService()
            
            # Should propagate the exception
            with pytest.raises(Exception, match="API Error"):
                pipeline.generate_survey("python")