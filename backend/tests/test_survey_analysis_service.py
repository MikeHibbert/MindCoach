"""
Unit tests for SurveyAnalysisService
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
from app.services.survey_analysis_service import SurveyAnalysisService


class TestSurveyAnalysisService:
    """Test cases for SurveyAnalysisService"""
    
    @pytest.fixture
    def sample_survey(self):
        """Sample survey for testing"""
        return {
            'subject': 'python',
            'user_id': 'test_user',
            'questions': [
                {
                    'id': 1,
                    'question': 'What is a list?',
                    'type': 'multiple_choice',
                    'options': ['A', 'B', 'C', 'D'],
                    'correct_answer': 0,
                    'difficulty': 'beginner',
                    'topic': 'data_structures'
                },
                {
                    'id': 2,
                    'question': 'What is a decorator?',
                    'type': 'multiple_choice',
                    'options': ['A', 'B', 'C', 'D'],
                    'correct_answer': 1,
                    'difficulty': 'intermediate',
                    'topic': 'decorators'
                },
                {
                    'id': 3,
                    'question': 'What is the GIL?',
                    'type': 'multiple_choice',
                    'options': ['A', 'B', 'C', 'D'],
                    'correct_answer': 2,
                    'difficulty': 'advanced',
                    'topic': 'concurrency'
                },
                {
                    'id': 4,
                    'question': 'How to define a function?',
                    'type': 'multiple_choice',
                    'options': ['A', 'B', 'C', 'D'],
                    'correct_answer': 1,
                    'difficulty': 'beginner',
                    'topic': 'functions'
                }
            ]
        }
    
    @pytest.fixture
    def sample_answers_all_correct(self):
        """Sample answers with all correct responses"""
        return [
            {'question_id': 1, 'answer': 0},
            {'question_id': 2, 'answer': 1},
            {'question_id': 3, 'answer': 2},
            {'question_id': 4, 'answer': 1}
        ]
    
    @pytest.fixture
    def sample_answers_mixed(self):
        """Sample answers with mixed correct/incorrect responses"""
        return [
            {'question_id': 1, 'answer': 0},  # correct
            {'question_id': 2, 'answer': 0},  # incorrect
            {'question_id': 3, 'answer': 2},  # correct
            {'question_id': 4, 'answer': 0}   # incorrect
        ]
    
    @patch('app.services.survey_analysis_service.SurveyAnalysisService._load_survey')
    @patch('app.services.survey_analysis_service.SurveyAnalysisService._save_survey_answers')
    @patch('app.services.survey_analysis_service.SurveyResultService.create_survey_result')
    def test_process_survey_answers_all_correct(self, mock_create_result, mock_save, mock_load, 
                                              sample_survey, sample_answers_all_correct):
        """Test processing survey answers with all correct responses"""
        mock_load.return_value = sample_survey
        
        user_id = "test_user"
        subject = "python"
        
        results = SurveyAnalysisService.process_survey_answers(
            user_id, subject, sample_answers_all_correct
        )
        
        # Verify basic structure
        assert results['user_id'] == user_id
        assert results['subject'] == subject
        assert results['total_questions'] == 4
        assert results['correct_answers'] == 4
        assert results['accuracy'] == 1.0
        assert results['skill_level'] == 'advanced'
        
        # Verify processed answers
        assert len(results['processed_answers']) == 4
        for answer in results['processed_answers']:
            assert answer['is_correct'] is True
        
        # Verify mocks were called
        mock_load.assert_called_once_with(user_id, subject)
        mock_save.assert_called_once()
        mock_create_result.assert_called_once_with(user_id, subject, 'advanced')
    
    @patch('app.services.survey_analysis_service.SurveyAnalysisService._load_survey')
    @patch('app.services.survey_analysis_service.SurveyAnalysisService._save_survey_answers')
    @patch('app.services.survey_analysis_service.SurveyResultService.create_survey_result')
    def test_process_survey_answers_mixed_performance(self, mock_create_result, mock_save, mock_load,
                                                    sample_survey, sample_answers_mixed):
        """Test processing survey answers with mixed performance"""
        mock_load.return_value = sample_survey
        
        user_id = "test_user"
        subject = "python"
        
        results = SurveyAnalysisService.process_survey_answers(
            user_id, subject, sample_answers_mixed
        )
        
        # Verify basic metrics
        assert results['total_questions'] == 4
        assert results['correct_answers'] == 2
        assert results['accuracy'] == 0.5
        
        # Verify processed answers
        correct_count = sum(1 for answer in results['processed_answers'] if answer['is_correct'])
        assert correct_count == 2
        
        # Verify topic analysis
        assert 'topic_analysis' in results
        assert 'topic_scores' in results['topic_analysis']
        
        # Verify recommendations
        assert 'recommendations' in results
        assert isinstance(results['recommendations'], list)
        assert len(results['recommendations']) > 0
    
    @patch('app.services.survey_analysis_service.SurveyAnalysisService._load_survey')
    def test_process_survey_answers_survey_not_found(self, mock_load):
        """Test processing answers when survey file doesn't exist"""
        mock_load.return_value = None
        
        user_id = "test_user"
        subject = "python"
        answers = [{'question_id': 1, 'answer': 0}]
        
        with pytest.raises(FileNotFoundError, match="Survey not found"):
            SurveyAnalysisService.process_survey_answers(user_id, subject, answers)
    
    @patch('app.services.survey_analysis_service.SurveyAnalysisService._load_survey')
    def test_process_survey_answers_invalid_answers_format(self, mock_load, sample_survey):
        """Test processing with invalid answers format"""
        mock_load.return_value = sample_survey
        
        user_id = "test_user"
        subject = "python"
        
        # Test with non-list answers
        with pytest.raises(ValueError, match="Answers must be a list"):
            SurveyAnalysisService.process_survey_answers(user_id, subject, "not a list")
        
        # Test with empty answers
        with pytest.raises(ValueError, match="Answers list cannot be empty"):
            SurveyAnalysisService.process_survey_answers(user_id, subject, [])
        
        # Test with missing question_id
        invalid_answers = [{'answer': 0}]
        with pytest.raises(ValueError, match="Each answer must have a question_id"):
            SurveyAnalysisService.process_survey_answers(user_id, subject, invalid_answers)
        
        # Test with missing answer field
        invalid_answers = [{'question_id': 1}]
        with pytest.raises(ValueError, match="Each answer must have an answer field"):
            SurveyAnalysisService.process_survey_answers(user_id, subject, invalid_answers)
        
        # Test with invalid question_id
        invalid_answers = [{'question_id': 999, 'answer': 0}]
        with pytest.raises(ValueError, match="Question ID 999 not found in survey"):
            SurveyAnalysisService.process_survey_answers(user_id, subject, invalid_answers)
        
        # Test with invalid answer value
        invalid_answers = [{'question_id': 1, 'answer': 5}]
        with pytest.raises(ValueError, match="Answer for question 1 must be an integer between 0 and 3"):
            SurveyAnalysisService.process_survey_answers(user_id, subject, invalid_answers)
    
    def test_determine_skill_level_advanced(self):
        """Test skill level determination for advanced users"""
        weighted_accuracy = 0.85
        difficulty_performance = {
            'beginner': {'correct': 2, 'total': 2},
            'intermediate': {'correct': 2, 'total': 2},
            'advanced': {'correct': 2, 'total': 2}
        }
        
        skill_level = SurveyAnalysisService._determine_skill_level(weighted_accuracy, difficulty_performance)
        assert skill_level == 'advanced'
    
    def test_determine_skill_level_intermediate(self):
        """Test skill level determination for intermediate users"""
        weighted_accuracy = 0.65
        difficulty_performance = {
            'beginner': {'correct': 2, 'total': 2},
            'intermediate': {'correct': 1, 'total': 2},
            'advanced': {'correct': 0, 'total': 2}
        }
        
        skill_level = SurveyAnalysisService._determine_skill_level(weighted_accuracy, difficulty_performance)
        assert skill_level == 'intermediate'
    
    def test_determine_skill_level_beginner(self):
        """Test skill level determination for beginner users"""
        weighted_accuracy = 0.35
        difficulty_performance = {
            'beginner': {'correct': 1, 'total': 2},
            'intermediate': {'correct': 0, 'total': 2},
            'advanced': {'correct': 0, 'total': 2}
        }
        
        skill_level = SurveyAnalysisService._determine_skill_level(weighted_accuracy, difficulty_performance)
        assert skill_level == 'beginner'
    
    def test_determine_skill_level_upgrade_based_on_advanced(self):
        """Test skill level upgrade based on good advanced performance"""
        weighted_accuracy = 0.65  # intermediate level
        difficulty_performance = {
            'beginner': {'correct': 2, 'total': 2},
            'intermediate': {'correct': 1, 'total': 2},
            'advanced': {'correct': 2, 'total': 2}  # 100% on advanced
        }
        
        skill_level = SurveyAnalysisService._determine_skill_level(weighted_accuracy, difficulty_performance)
        assert skill_level == 'advanced'
    
    def test_determine_skill_level_downgrade_based_on_beginner(self):
        """Test skill level downgrade based on poor beginner performance"""
        weighted_accuracy = 0.65  # intermediate level
        difficulty_performance = {
            'beginner': {'correct': 1, 'total': 3},  # 33% on beginner - below 50% threshold
            'intermediate': {'correct': 1, 'total': 2},  # 50% on intermediate
            'advanced': {'correct': 0, 'total': 1}  # 0% on advanced
        }
        
        skill_level = SurveyAnalysisService._determine_skill_level(weighted_accuracy, difficulty_performance)
        assert skill_level == 'beginner'
    
    def test_analyze_topic_performance(self):
        """Test topic performance analysis"""
        topic_performance = {
            'data_structures': {'correct': 4, 'total': 5},  # 80% - strength
            'functions': {'correct': 2, 'total': 3},        # 67% - neutral
            'classes': {'correct': 1, 'total': 3},          # 33% - weakness
            'decorators': {'correct': 0, 'total': 2}        # 0% - weakness
        }
        
        analysis = SurveyAnalysisService._analyze_topic_performance(topic_performance)
        
        assert 'data_structures' in analysis['strengths']
        assert 'classes' in analysis['weaknesses']
        assert 'decorators' in analysis['weaknesses']
        assert 'functions' not in analysis['strengths']
        assert 'functions' not in analysis['weaknesses']
        
        # Verify topic scores
        assert analysis['topic_scores']['data_structures']['accuracy'] == 0.8
        assert analysis['topic_scores']['classes']['accuracy'] == pytest.approx(0.333, rel=1e-2)
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        skill_level = 'intermediate'
        topic_analysis = {
            'strengths': ['functions'],
            'weaknesses': ['classes', 'decorators']
        }
        difficulty_performance = {
            'beginner': {'correct': 3, 'total': 3},
            'intermediate': {'correct': 1, 'total': 3},  # 33% - needs work
            'advanced': {'correct': 1, 'total': 2}
        }
        
        recommendations = SurveyAnalysisService._generate_recommendations(
            skill_level, topic_analysis, difficulty_performance
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Check for skill level recommendations
        intermediate_recs = [r for r in recommendations if 'complex problems' in r or 'advanced features' in r]
        assert len(intermediate_recs) > 0
        
        # Check for topic-specific recommendations
        weakness_recs = [r for r in recommendations if 'classes, decorators' in r]
        assert len(weakness_recs) > 0
        
        strength_recs = [r for r in recommendations if 'functions' in r]
        assert len(strength_recs) > 0
    
    @patch('app.services.survey_analysis_service.FileService.load_json')
    def test_get_survey_results_success(self, mock_load):
        """Test successful retrieval of survey results"""
        expected_results = {
            'user_id': 'test_user',
            'subject': 'python',
            'skill_level': 'intermediate'
        }
        mock_load.return_value = expected_results
        
        user_id = "test_user"
        subject = "python"
        
        results = SurveyAnalysisService.get_survey_results(user_id, subject)
        
        assert results == expected_results
        mock_load.assert_called_once_with(f"users/{user_id}/{subject}/survey_answers.json")
    
    @patch('app.services.survey_analysis_service.FileService.load_json')
    def test_get_survey_results_not_found(self, mock_load):
        """Test retrieval when survey results don't exist"""
        mock_load.side_effect = FileNotFoundError("File not found")
        
        user_id = "test_user"
        subject = "python"
        
        results = SurveyAnalysisService.get_survey_results(user_id, subject)
        
        assert results is None
    
    @patch('app.services.survey_analysis_service.FileService.load_json')
    def test_get_survey_results_error(self, mock_load):
        """Test retrieval with unexpected error"""
        mock_load.side_effect = Exception("Unexpected error")
        
        user_id = "test_user"
        subject = "python"
        
        with pytest.raises(Exception, match="Unexpected error"):
            SurveyAnalysisService.get_survey_results(user_id, subject)
    
    def test_validate_analysis_results_valid(self):
        """Test validation of valid analysis results"""
        valid_results = {
            'user_id': 'test_user',
            'subject': 'python',
            'processed_at': datetime.utcnow().isoformat(),
            'total_questions': 4,
            'correct_answers': 2,
            'accuracy': 0.5,
            'skill_level': 'intermediate',
            'topic_analysis': {'strengths': [], 'weaknesses': []},
            'processed_answers': [
                {
                    'question_id': 1,
                    'user_answer': 0,
                    'correct_answer': 0,
                    'is_correct': True
                }
            ],
            'recommendations': ['Practice more']
        }
        
        assert SurveyAnalysisService.validate_analysis_results(valid_results) is True
    
    def test_validate_analysis_results_missing_fields(self):
        """Test validation with missing required fields"""
        invalid_results = {
            'user_id': 'test_user',
            'subject': 'python'
            # Missing other required fields
        }
        
        assert SurveyAnalysisService.validate_analysis_results(invalid_results) is False
    
    def test_validate_analysis_results_invalid_skill_level(self):
        """Test validation with invalid skill level"""
        invalid_results = {
            'user_id': 'test_user',
            'subject': 'python',
            'processed_at': datetime.utcnow().isoformat(),
            'total_questions': 4,
            'correct_answers': 2,
            'accuracy': 0.5,
            'skill_level': 'invalid_level',  # Invalid
            'topic_analysis': {'strengths': [], 'weaknesses': []},
            'processed_answers': [],
            'recommendations': []
        }
        
        assert SurveyAnalysisService.validate_analysis_results(invalid_results) is False
    
    def test_validate_analysis_results_invalid_accuracy(self):
        """Test validation with invalid accuracy value"""
        invalid_results = {
            'user_id': 'test_user',
            'subject': 'python',
            'processed_at': datetime.utcnow().isoformat(),
            'total_questions': 4,
            'correct_answers': 2,
            'accuracy': 1.5,  # Invalid - should be between 0 and 1
            'skill_level': 'intermediate',
            'topic_analysis': {'strengths': [], 'weaknesses': []},
            'processed_answers': [],
            'recommendations': []
        }
        
        assert SurveyAnalysisService.validate_analysis_results(invalid_results) is False
    
    def test_validate_analysis_results_invalid_processed_answers(self):
        """Test validation with invalid processed answers structure"""
        invalid_results = {
            'user_id': 'test_user',
            'subject': 'python',
            'processed_at': datetime.utcnow().isoformat(),
            'total_questions': 4,
            'correct_answers': 2,
            'accuracy': 0.5,
            'skill_level': 'intermediate',
            'topic_analysis': {'strengths': [], 'weaknesses': []},
            'processed_answers': [
                {
                    'question_id': 1
                    # Missing required fields
                }
            ],
            'recommendations': []
        }
        
        assert SurveyAnalysisService.validate_analysis_results(invalid_results) is False
    
    def test_difficulty_weights_configuration(self):
        """Test that difficulty weights are properly configured"""
        weights = SurveyAnalysisService.DIFFICULTY_WEIGHTS
        
        assert weights['beginner'] == 1.0
        assert weights['intermediate'] == 1.5
        assert weights['advanced'] == 2.0
        assert weights['advanced'] > weights['intermediate'] > weights['beginner']
    
    def test_skill_level_thresholds_configuration(self):
        """Test that skill level thresholds are properly configured"""
        thresholds = SurveyAnalysisService.SKILL_LEVEL_THRESHOLDS
        
        assert thresholds['beginner'] == 0.0
        assert thresholds['intermediate'] == 0.5
        assert thresholds['advanced'] == 0.75
        assert thresholds['advanced'] > thresholds['intermediate'] > thresholds['beginner']