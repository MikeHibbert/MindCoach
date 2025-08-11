"""
Performance tests for LangChain content generation speed
"""
import pytest
import time
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.services.langchain_chains import (
    SurveyGenerationChain,
    CurriculumGeneratorChain,
    LessonPlannerChain,
    ContentGeneratorChain
)
from app.services.langchain_pipeline import LangChainPipelineService

@patch('app.services.langchain_chains.validate_environment')
@patch('app.services.langchain_chains.XAILLM')
def test_survey_generation_performance(mock_llm_class, mock_validate):
    """Test survey generation performance"""
    mock_validate.return_value = True
    mock_llm_class.return_value = Mock()
    
    # Mock fast response
    mock_survey_result = {
        "questions": [
            {
                "id": i,
                "question": f"Question {i}?",
                "type": "multiple_choice",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "difficulty": "intermediate",
                "topic": f"topic_{i}"
            }
            for i in range(1, 8)
        ],
        "total_questions": 7,
        "subject": "python"
    }
    
    mock_chain = Mock()
    mock_chain.run.return_value = mock_survey_result
    
    with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
        chain = SurveyGenerationChain()
        
        # Measure performance
        start_time = time.time()
        result = chain.generate_survey('python')
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Performance assertions
        assert execution_time < 5.0  # Should complete within 5 seconds
        assert result['total_questions'] == 7
        assert len(result['questions']) == 7