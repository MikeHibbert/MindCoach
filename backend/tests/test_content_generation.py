"""
Unit tests for Content Generation Chain
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.langchain_chains import ContentGeneratorChain

class TestContentGeneratorChain:
    """Test content generation functionality"""
    
    @pytest.fixture
    def sample_lesson_plan(self):
        """Sample lesson plan for testing"""
        return {
            "lesson_id": 1,
            "title": "Advanced Variables and Data Types",
            "learning_objectives": [
                "Understand and use Python dictionaries effectively",
                "Work with sets for unique data collections",
                "Apply type hints for better code documentation"
            ],
            "structure": {
                "introduction": "5 minutes",
                "main_content": "25 minutes",
                "examples": "15 minutes",
                "exercises": "15 minutes",
                "summary": "5 minutes"
            },
            "activities": [
                "Interactive demonstration of dictionary operations",
                "Guided practice with set operations",
                "Type hints implementation exercise"
            ],
            "assessment": "Coding exercises with dictionaries and sets",
            "materials_needed": [
                "Python IDE",
                "Code examples"
            ],
            "key_concepts": [
                "dictionaries",
                "sets", 
                "type_hints"
            ],
            "difficulty": "intermediate"
        }
    
    @pytest.fixture
    def sample_rag_docs(self):
        """Sample RAG documents for testing"""
        return [
            "Create clear explanations with practical examples",
            "Include 2 code examples and 3-5 exercises per lesson",
            "Use proper markdown formatting with headers and code blocks"
        ]
    
    @pytest.fixture
    def expected_lesson_content(self):
        """Expected lesson content output"""
        return """# Advanced Variables and Data Types

## Introduction

Welcome to this lesson on advanced Python data types. In this lesson, you'll learn to work with dictionaries, sets, and type hints to write more effective Python code.

## Core Concepts

### Dictionaries
Dictionaries are key-value pairs that allow you to store and retrieve data efficiently...

### Sets
Sets are collections of unique elements that are useful for removing duplicates...

### Type Hints
Type hints provide documentation and IDE support for your code...

## Code Examples

### Example 1: Dictionary Operations
```python
# Creating and using dictionaries
student = {
    "name": "Alice",
    "age": 20,
    "courses": ["Python", "Math"]
}
print(student["name"])  # Output: Alice
```

### Example 2: Set Operations
```python
# Working with sets
numbers = {1, 2, 3, 4, 5}
even_numbers = {2, 4, 6, 8}
intersection = numbers & even_numbers
print(intersection)  # Output: {2, 4}
```

## Hands-on Exercises

### Exercise 1: Dictionary Manipulation (Beginner)
Create a dictionary representing a book with title, author, and year...

### Exercise 2: Set Operations (Intermediate)
Given two sets of student names, find students enrolled in both courses...

### Exercise 3: Type Hints Implementation (Advanced)
Add type hints to the following function...

## Summary and Next Steps

In this lesson, you learned about dictionaries, sets, and type hints. Next lesson will cover...
"""
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_content_generation_success(self, mock_llm_class, mock_validate, 
                                      sample_lesson_plan, sample_rag_docs, 
                                      expected_lesson_content):
        """Test successful content generation"""
        mock_validate.return_value = True
        
        # Mock the LLM chain
        mock_chain = Mock()
        mock_chain.run.return_value = expected_lesson_content
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            content_generator = ContentGeneratorChain()
            result = content_generator.generate_content(
                sample_lesson_plan, 
                "python", 
                sample_rag_docs
            )
        
        assert isinstance(result, str)
        assert len(result) > 100
        assert "Advanced Variables and Data Types" in result
        assert "Dictionary Operations" in result
        assert "Set Operations" in result
        assert "```python" in result
        assert "Exercise" in result
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_format_lesson_plan(self, mock_llm_class, mock_validate, sample_lesson_plan):
        """Test formatting of lesson plan for prompt"""
        mock_validate.return_value = True
        
        content_generator = ContentGeneratorChain()
        formatted_plan = content_generator._format_lesson_plan(sample_lesson_plan)
        
        assert "Lesson 1: Advanced Variables and Data Types" in formatted_plan
        assert "Learning Objectives:" in formatted_plan
        assert "Understand and use Python dictionaries effectively" in formatted_plan
        assert "Time Allocation:" in formatted_plan
        assert "Introduction: 5 minutes" in formatted_plan
        assert "Planned Activities:" in formatted_plan
        assert "Interactive demonstration" in formatted_plan
        assert "Key Concepts to Cover:" in formatted_plan
        assert "dictionaries" in formatted_plan
        assert "Assessment Method:" in formatted_plan
        assert "Materials Needed:" in formatted_plan
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_content_validation_structure(self, mock_llm_class, mock_validate, expected_lesson_content):
        """Test content structure validation"""
        mock_validate.return_value = True
        
        content_generator = ContentGeneratorChain()
        
        # Test valid content
        is_valid = content_generator._validate_content_structure(expected_lesson_content)
        assert is_valid is True
        
        # Test invalid content (too simple)
        invalid_content = "This is just a simple text without proper structure."
        is_valid = content_generator._validate_content_structure(invalid_content)
        assert is_valid is False
        
        # Test partially valid content
        partial_content = """# Title
        
        Some content with a list:
        - Item 1
        - Item 2
        
        ```python
        print("code example")
        ```
        """
        is_valid = content_generator._validate_content_structure(partial_content)
        assert is_valid is True  # Should pass with basic structure
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_content_generation_too_short(self, mock_llm_class, mock_validate, 
                                        sample_lesson_plan, sample_rag_docs):
        """Test content generation with too short output"""
        mock_validate.return_value = True
        
        # Mock very short content
        short_content = "Short content"
        
        mock_chain = Mock()
        mock_chain.run.return_value = short_content
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            content_generator = ContentGeneratorChain()
            
            with pytest.raises(ValueError, match="too short or empty"):
                content_generator.generate_content(
                    sample_lesson_plan, 
                    "python", 
                    sample_rag_docs
                )
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_content_generation_empty_output(self, mock_llm_class, mock_validate, 
                                           sample_lesson_plan, sample_rag_docs):
        """Test content generation with empty output"""
        mock_validate.return_value = True
        
        # Mock empty content
        empty_content = ""
        
        mock_chain = Mock()
        mock_chain.run.return_value = empty_content
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            content_generator = ContentGeneratorChain()
            
            with pytest.raises(ValueError, match="too short or empty"):
                content_generator.generate_content(
                    sample_lesson_plan, 
                    "python", 
                    sample_rag_docs
                )
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_prompt_template_structure(self, mock_llm_class, mock_validate):
        """Test that prompt template has correct input variables"""
        mock_validate.return_value = True
        
        content_generator = ContentGeneratorChain()
        prompt_template = content_generator.get_prompt_template()
        
        expected_variables = ["lesson_plan", "subject", "skill_level", "rag_guidelines"]
        assert set(prompt_template.input_variables) == set(expected_variables)
        
        # Check that template contains key instructions
        template_text = prompt_template.template
        assert "complete lesson content" in template_text
        assert "2 practical code examples" in template_text
        assert "3-5 hands-on exercises" in template_text
        assert "markdown formatting" in template_text
        assert "Do not include JSON structure" in template_text
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_content_generation_without_rag_docs(self, mock_llm_class, mock_validate, 
                                                sample_lesson_plan, expected_lesson_content):
        """Test content generation without RAG documents"""
        mock_validate.return_value = True
        
        mock_chain = Mock()
        mock_chain.run.return_value = expected_lesson_content
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            content_generator = ContentGeneratorChain()
            result = content_generator.generate_content(
                sample_lesson_plan, 
                "python", 
                None  # No RAG docs
            )
        
        # Should still work with default guidelines
        assert isinstance(result, str)
        assert len(result) > 100
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_lesson_plan_without_optional_fields(self, mock_llm_class, mock_validate, 
                                                sample_rag_docs, expected_lesson_content):
        """Test content generation with minimal lesson plan"""
        mock_validate.return_value = True
        
        minimal_lesson_plan = {
            "lesson_id": 1,
            "title": "Basic Lesson",
            "learning_objectives": ["Learn something"]
            # Missing most optional fields
        }
        
        mock_chain = Mock()
        mock_chain.run.return_value = expected_lesson_content
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            content_generator = ContentGeneratorChain()
            result = content_generator.generate_content(
                minimal_lesson_plan, 
                "python", 
                sample_rag_docs
            )
        
        # Should still work with minimal lesson plan
        assert isinstance(result, str)
        assert len(result) > 100
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_different_subjects(self, mock_llm_class, mock_validate, 
                              sample_lesson_plan, sample_rag_docs, expected_lesson_content):
        """Test content generation for different subjects"""
        mock_validate.return_value = True
        
        mock_chain = Mock()
        mock_chain.run.return_value = expected_lesson_content
        
        subjects = ['python', 'javascript', 'react']
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            content_generator = ContentGeneratorChain()
            
            for subject in subjects:
                result = content_generator.generate_content(
                    sample_lesson_plan, 
                    subject, 
                    sample_rag_docs
                )
                
                assert isinstance(result, str)
                assert len(result) > 100
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_different_difficulty_levels(self, mock_llm_class, mock_validate, 
                                       sample_rag_docs, expected_lesson_content):
        """Test content generation for different difficulty levels"""
        mock_validate.return_value = True
        
        mock_chain = Mock()
        mock_chain.run.return_value = expected_lesson_content
        
        difficulty_levels = ['beginner', 'intermediate', 'advanced']
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            content_generator = ContentGeneratorChain()
            
            for difficulty in difficulty_levels:
                lesson_plan = {
                    "lesson_id": 1,
                    "title": f"{difficulty.title()} Lesson",
                    "learning_objectives": ["Learn something"],
                    "difficulty": difficulty
                }
                
                result = content_generator.generate_content(
                    lesson_plan, 
                    "python", 
                    sample_rag_docs
                )
                
                assert isinstance(result, str)
                assert len(result) > 100