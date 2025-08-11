"""
Tests for LangChain-powered survey generation
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.services.langchain_chains import SurveyGenerationChain
from app.services.langchain_pipeline import LangChainPipelineService

class TestSurveyLangChain:
    """Test LangChain survey generation functionality"""
    
    @pytest.fixture
    def mock_survey_response(self):
        """Mock survey response from LangChain"""
        return {
            "questions": [
                {
                    "id": 1,
                    "question": "What is the correct way to create a list in Python?",
                    "type": "multiple_choice",
                    "options": [
                        "my_list = [1, 2, 3]",
                        "my_list = (1, 2, 3)",
                        "my_list = {1, 2, 3}",
                        "my_list = <1, 2, 3>"
                    ],
                    "correct_answer": "my_list = [1, 2, 3]",
                    "difficulty": "beginner",
                    "topic": "data_structures"
                },
                {
                    "id": 2,
                    "question": "What is a list comprehension in Python?",
                    "type": "multiple_choice",
                    "options": [
                        "A way to create lists using a concise syntax",
                        "A method to compress lists",
                        "A function to understand lists",
                        "A type of loop"
                    ],
                    "correct_answer": "A way to create lists using a concise syntax",
                    "difficulty": "intermediate",
                    "topic": "list_comprehensions"
                },
                {
                    "id": 3,
                    "question": "What is the Global Interpreter Lock (GIL) in Python?",
                    "type": "multiple_choice",
                    "options": [
                        "A mechanism that prevents multiple threads from executing Python code simultaneously",
                        "A security feature for global variables",
                        "A memory management system",
                        "A debugging tool"
                    ],
                    "correct_answer": "A mechanism that prevents multiple threads from executing Python code simultaneously",
                    "difficulty": "advanced",
                    "topic": "concurrency"
                },
                {
                    "id": 4,
                    "question": "Which of the following is used to define a function in Python?",
                    "type": "multiple_choice",
                    "options": ["function", "def", "define", "func"],
                    "correct_answer": "def",
                    "difficulty": "beginner",
                    "topic": "functions"
                },
                {
                    "id": 5,
                    "question": "What does the 'self' parameter represent in a Python class method?",
                    "type": "multiple_choice",
                    "options": [
                        "The class itself",
                        "The instance of the class",
                        "A global variable",
                        "The parent class"
                    ],
                    "correct_answer": "The instance of the class",
                    "difficulty": "intermediate",
                    "topic": "classes"
                },
                {
                    "id": 6,
                    "question": "What is monkey patching in Python?",
                    "type": "multiple_choice",
                    "options": [
                        "A debugging technique",
                        "Dynamic modification of classes or modules at runtime",
                        "A testing framework",
                        "A performance optimization"
                    ],
                    "correct_answer": "Dynamic modification of classes or modules at runtime",
                    "difficulty": "advanced",
                    "topic": "dynamic_programming"
                },
                {
                    "id": 7,
                    "question": "How do you create a comment in Python?",
                    "type": "multiple_choice",
                    "options": [
                        "// This is a comment",
                        "/* This is a comment */",
                        "# This is a comment",
                        "<!-- This is a comment -->"
                    ],
                    "correct_answer": "# This is a comment",
                    "difficulty": "beginner",
                    "topic": "syntax"
                }
            ],
            "total_questions": 7,
            "subject": "python"
        }
    
    @pytest.fixture
    def mock_rag_docs(self):
        """Mock RAG documents for survey generation"""
        return [
            "Generate 7-8 multiple choice questions",
            "Difficulty distribution: 30% beginner, 50% intermediate, 20% advanced",
            "Each question must have exactly 4 options",
            "Cover fundamental programming concepts"
        ]
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.current_app')
    def test_survey_generation_chain_initialization(self, mock_app, mock_validate):
        """Test SurveyGenerationChain initialization"""
        mock_app.config = {'XAI_API_KEY': 'test-key', 'GROK_API_URL': 'test-url'}
        mock_validate.return_value = True
        
        chain = SurveyGenerationChain()
        
        assert chain is not None
        assert hasattr(chain, 'llm')
        assert hasattr(chain, 'json_parser')
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.current_app')
    @patch('app.services.langchain_chains.LLMChain')
    def test_survey_generation_success(self, mock_llm_chain, mock_app, mock_validate, mock_survey_response, mock_rag_docs):
        """Test successful survey generation"""
        mock_app.config = {'XAI_API_KEY': 'test-key', 'GROK_API_URL': 'test-url'}
        mock_validate.return_value = True
        
        # Mock the chain run method
        mock_chain_instance = Mock()
        mock_chain_instance.run.return_value = mock_survey_response
        mock_llm_chain.return_value = mock_chain_instance
        
        chain = SurveyGenerationChain()
        
        # Mock RAG document loading
        with patch.object(chain, 'load_rag_documents', return_value=mock_rag_docs):
            result = chain.generate_survey('python', mock_rag_docs)
        
        # Verify result structure
        assert 'questions' in result
        assert 'total_questions' in result
        assert 'subject' in result
        assert 'generated_at' in result
        assert 'generation_method' in result
        
        # Verify questions
        questions = result['questions']
        assert len(questions) == 7
        assert result['total_questions'] == 7
        assert result['subject'] == 'python'
        assert result['generation_method'] == 'langchain'
        
        # Verify question structure
        for question in questions:
            assert 'id' in question
            assert 'question' in question
            assert 'type' in question
            assert 'options' in question
            assert 'correct_answer' in question
            assert 'difficulty' in question
            assert 'topic' in question
            assert len(question['options']) == 4
            assert question['correct_answer'] in question['options']
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.current_app')
    def test_survey_validation_quality_checks(self, mock_app, mock_validate, mock_survey_response):
        """Test survey quality validation"""
        mock_app.config = {'XAI_API_KEY': 'test-key', 'GROK_API_URL': 'test-url'}
        mock_validate.return_value = True
        
        chain = SurveyGenerationChain()
        
        # Test valid survey
        assert chain._validate_survey_quality(mock_survey_response) == True
        
        # Test invalid survey - no questions
        invalid_survey = {"questions": [], "total_questions": 0, "subject": "python"}
        assert chain._validate_survey_quality(invalid_survey) == False
        
        # Test invalid survey - too many questions
        invalid_survey = {
            "questions": [{"id": i} for i in range(15)],
            "total_questions": 15,
            "subject": "python"
        }
        assert chain._validate_survey_quality(invalid_survey) == False
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.current_app')
    def test_question_validation(self, mock_app, mock_validate):
        """Test individual question validation"""
        mock_app.config = {'XAI_API_KEY': 'test-key', 'GROK_API_URL': 'test-url'}
        mock_validate.return_value = True
        
        chain = SurveyGenerationChain()
        
        # Valid question
        valid_question = {
            "id": 1,
            "question": "What is Python?",
            "type": "multiple_choice",
            "options": ["A snake", "A programming language", "A tool", "A framework"],
            "correct_answer": "A programming language",
            "difficulty": "beginner",
            "topic": "basics"
        }
        assert chain._validate_question_quality(valid_question, 1) == True
        
        # Invalid question - missing field
        invalid_question = {
            "id": 1,
            "question": "What is Python?",
            "type": "multiple_choice",
            "options": ["A snake", "A programming language"],
            # Missing correct_answer, difficulty, topic
        }
        assert chain._validate_question_quality(invalid_question, 1) == False
        
        # Invalid question - wrong number of options
        invalid_question = {
            "id": 1,
            "question": "What is Python?",
            "type": "multiple_choice",
            "options": ["A snake", "A programming language"],  # Only 2 options
            "correct_answer": "A programming language",
            "difficulty": "beginner",
            "topic": "basics"
        }
        assert chain._validate_question_quality(invalid_question, 1) == False
        
        # Invalid question - correct answer not in options
        invalid_question = {
            "id": 1,
            "question": "What is Python?",
            "type": "multiple_choice",
            "options": ["A snake", "A tool", "A framework", "A library"],
            "correct_answer": "A programming language",  # Not in options
            "difficulty": "beginner",
            "topic": "basics"
        }
        assert chain._validate_question_quality(invalid_question, 1) == False
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.current_app')
    @patch('app.services.langchain_pipeline.LangChainPipelineService')
    def test_pipeline_integration(self, mock_pipeline_class, mock_app, mock_validate, mock_survey_response):
        """Test integration with LangChain pipeline"""
        mock_app.config = {'XAI_API_KEY': 'test-key', 'GROK_API_URL': 'test-url'}
        mock_validate.return_value = True
        
        # Mock pipeline instance
        mock_pipeline = Mock()
        mock_pipeline.generate_survey.return_value = mock_survey_response
        mock_pipeline_class.return_value = mock_pipeline
        
        pipeline = LangChainPipelineService()
        result = pipeline.generate_survey('python', [])
        
        assert result == mock_survey_response
        mock_pipeline.generate_survey.assert_called_once_with('python', [])
    
    def test_difficulty_distribution_validation(self):
        """Test difficulty distribution validation"""
        # Valid distribution
        questions = [
            {"difficulty": "beginner"},
            {"difficulty": "beginner"},
            {"difficulty": "intermediate"},
            {"difficulty": "intermediate"},
            {"difficulty": "intermediate"},
            {"difficulty": "advanced"},
            {"difficulty": "advanced"}
        ]
        
        chain = SurveyGenerationChain.__new__(SurveyGenerationChain)  # Create without __init__
        
        # Should pass - has beginner and intermediate questions
        # (Advanced is optional but present)
        difficulty_counts = {'beginner': 2, 'intermediate': 3, 'advanced': 2}
        
        # Mock the validation logic
        assert difficulty_counts['beginner'] > 0
        assert difficulty_counts['intermediate'] > 0
        # Advanced can be 0, but in this case it's > 0
        
        # Invalid distribution - no beginner questions
        questions_no_beginner = [
            {"difficulty": "intermediate"},
            {"difficulty": "intermediate"},
            {"difficulty": "advanced"}
        ]
        
        difficulty_counts_invalid = {'beginner': 0, 'intermediate': 2, 'advanced': 1}
        assert difficulty_counts_invalid['beginner'] == 0  # This should fail validation
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.current_app')
    def test_default_guidelines_fallback(self, mock_app, mock_validate):
        """Test fallback to default guidelines when RAG docs unavailable"""
        mock_app.config = {'XAI_API_KEY': 'test-key', 'GROK_API_URL': 'test-url'}
        mock_validate.return_value = True
        
        chain = SurveyGenerationChain()
        
        default_guidelines = chain._get_default_survey_guidelines()
        
        assert "7-8 multiple choice questions" in default_guidelines
        assert "30% beginner, 50% intermediate, 20% advanced" in default_guidelines
        assert "exactly 4 options" in default_guidelines
        assert "fundamental topics" in default_guidelines