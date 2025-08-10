"""
Unit tests for Curriculum Generation Chain
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.langchain_chains import CurriculumGeneratorChain

class TestCurriculumGeneratorChain:
    """Test curriculum generation functionality"""
    
    @pytest.fixture
    def sample_survey_data(self):
        """Sample survey data for testing"""
        return {
            'skill_level': 'intermediate',
            'answers': [
                {'question_id': 1, 'topic': 'variables', 'correct': True},
                {'question_id': 2, 'topic': 'functions', 'correct': True},
                {'question_id': 3, 'topic': 'classes', 'correct': False},
                {'question_id': 4, 'topic': 'modules', 'correct': False}
            ]
        }
    
    @pytest.fixture
    def sample_rag_docs(self):
        """Sample RAG documents for testing"""
        return [
            "Create a comprehensive curriculum with clear progression",
            "Include practical examples and exercises",
            "Adapt content based on learner skill level"
        ]
    
    @pytest.fixture
    def expected_curriculum_output(self):
        """Expected curriculum output structure"""
        return {
            "curriculum": {
                "subject": "python",
                "skill_level": "intermediate",
                "total_lessons": 10,
                "learning_objectives": [
                    "Master Python fundamentals",
                    "Build practical applications",
                    "Understand best practices"
                ],
                "topics": [
                    {
                        "lesson_id": 1,
                        "title": "Advanced Variables and Data Types",
                        "topics": ["dictionaries", "sets", "type_hints"],
                        "prerequisites": [],
                        "difficulty": "intermediate",
                        "estimated_duration": "45-60 minutes"
                    },
                    {
                        "lesson_id": 2,
                        "title": "Object-Oriented Programming",
                        "topics": ["classes", "inheritance", "polymorphism"],
                        "prerequisites": ["variables"],
                        "difficulty": "intermediate",
                        "estimated_duration": "45-60 minutes"
                    }
                    # ... would have 8 more lessons for total of 10
                ]
            },
            "generated_at": "2024-01-15T10:00:00Z",
            "generation_stage": "curriculum_complete"
        }
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_curriculum_generation_success(self, mock_llm_class, mock_validate, 
                                         sample_survey_data, sample_rag_docs, 
                                         expected_curriculum_output):
        """Test successful curriculum generation"""
        mock_validate.return_value = True
        
        # Mock the LLM chain
        mock_chain = Mock()
        mock_chain.run.return_value = expected_curriculum_output
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            curriculum_chain = CurriculumGeneratorChain()
            result = curriculum_chain.generate_curriculum(
                sample_survey_data, 
                "python", 
                sample_rag_docs
            )
        
        assert result["curriculum"]["subject"] == "python"
        assert result["curriculum"]["skill_level"] == "intermediate"
        assert result["curriculum"]["total_lessons"] == 10
        assert len(result["curriculum"]["learning_objectives"]) >= 2
        assert len(result["curriculum"]["topics"]) >= 2
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_extract_known_topics(self, mock_llm_class, mock_validate, sample_survey_data):
        """Test extraction of known topics from survey data"""
        mock_validate.return_value = True
        
        curriculum_chain = CurriculumGeneratorChain()
        known_topics = curriculum_chain._extract_known_topics(sample_survey_data)
        
        assert 'variables' in known_topics
        assert 'functions' in known_topics
        assert 'classes' not in known_topics
        assert 'modules' not in known_topics
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_format_survey_results(self, mock_llm_class, mock_validate, sample_survey_data):
        """Test formatting of survey results for prompt"""
        mock_validate.return_value = True
        
        curriculum_chain = CurriculumGeneratorChain()
        formatted_results = curriculum_chain._format_survey_results(sample_survey_data)
        
        assert "Skill Level: intermediate" in formatted_results
        assert "2/4 correct (50.0%)" in formatted_results
        assert "variables: 1/1 (100.0%)" in formatted_results
        assert "functions: 1/1 (100.0%)" in formatted_results
        assert "classes: 0/1 (0.0%)" in formatted_results
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_curriculum_validation_missing_structure(self, mock_llm_class, mock_validate, 
                                                   sample_survey_data, sample_rag_docs):
        """Test curriculum generation with invalid output structure"""
        mock_validate.return_value = True
        
        # Mock invalid output (missing curriculum key)
        invalid_output = {
            "invalid_key": "invalid_value"
        }
        
        mock_chain = Mock()
        mock_chain.run.return_value = invalid_output
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            curriculum_chain = CurriculumGeneratorChain()
            
            with pytest.raises(ValueError, match="does not have required structure"):
                curriculum_chain.generate_curriculum(
                    sample_survey_data, 
                    "python", 
                    sample_rag_docs
                )
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_curriculum_validation_invalid_curriculum_structure(self, mock_llm_class, mock_validate, 
                                                              sample_survey_data, sample_rag_docs):
        """Test curriculum generation with invalid curriculum structure"""
        mock_validate.return_value = True
        
        # Mock output with curriculum key but invalid structure
        invalid_output = {
            "curriculum": {
                "subject": "python"
                # Missing required keys: skill_level, total_lessons, learning_objectives, topics
            }
        }
        
        mock_chain = Mock()
        mock_chain.run.return_value = invalid_output
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            curriculum_chain = CurriculumGeneratorChain()
            
            with pytest.raises(ValueError, match="curriculum structure is invalid"):
                curriculum_chain.generate_curriculum(
                    sample_survey_data, 
                    "python", 
                    sample_rag_docs
                )
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_prompt_template_structure(self, mock_llm_class, mock_validate):
        """Test that prompt template has correct input variables"""
        mock_validate.return_value = True
        
        curriculum_chain = CurriculumGeneratorChain()
        prompt_template = curriculum_chain.get_prompt_template()
        
        expected_variables = ["survey_results", "subject", "skill_level", "rag_guidelines", "known_topics"]
        assert set(prompt_template.input_variables) == set(expected_variables)
        
        # Check that template contains key instructions
        template_text = prompt_template.template
        assert "10-lesson learning curriculum" in template_text
        assert "JSON object" in template_text
        assert "curriculum" in template_text
        assert "learning_objectives" in template_text
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_curriculum_generation_with_empty_survey(self, mock_llm_class, mock_validate, 
                                                   sample_rag_docs, expected_curriculum_output):
        """Test curriculum generation with empty survey data"""
        mock_validate.return_value = True
        
        empty_survey_data = {
            'skill_level': 'beginner',
            'answers': []
        }
        
        mock_chain = Mock()
        mock_chain.run.return_value = expected_curriculum_output
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            curriculum_chain = CurriculumGeneratorChain()
            result = curriculum_chain.generate_curriculum(
                empty_survey_data, 
                "python", 
                sample_rag_docs
            )
        
        # Should still generate valid curriculum
        assert result["curriculum"]["subject"] == "python"
        assert result["curriculum"]["total_lessons"] == 10
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_curriculum_generation_without_rag_docs(self, mock_llm_class, mock_validate, 
                                                  sample_survey_data, expected_curriculum_output):
        """Test curriculum generation without RAG documents"""
        mock_validate.return_value = True
        
        mock_chain = Mock()
        mock_chain.run.return_value = expected_curriculum_output
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            curriculum_chain = CurriculumGeneratorChain()
            result = curriculum_chain.generate_curriculum(
                sample_survey_data, 
                "python", 
                None  # No RAG docs
            )
        
        # Should still work with default guidelines
        assert result["curriculum"]["subject"] == "python"
        assert result["curriculum"]["total_lessons"] == 10
    
    @patch('app.services.langchain_chains.validate_environment')
    @patch('app.services.langchain_chains.XAILLM')
    def test_different_skill_levels(self, mock_llm_class, mock_validate, 
                                  sample_rag_docs, expected_curriculum_output):
        """Test curriculum generation for different skill levels"""
        mock_validate.return_value = True
        
        mock_chain = Mock()
        mock_chain.run.return_value = expected_curriculum_output
        
        skill_levels = ['beginner', 'intermediate', 'advanced']
        
        with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
            curriculum_chain = CurriculumGeneratorChain()
            
            for skill_level in skill_levels:
                survey_data = {
                    'skill_level': skill_level,
                    'answers': []
                }
                
                result = curriculum_chain.generate_curriculum(
                    survey_data, 
                    "python", 
                    sample_rag_docs
                )
                
                assert result["curriculum"]["subject"] == "python"
                assert result["curriculum"]["total_lessons"] == 10