"""
Unit tests for SurveyGenerationService
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch
from app.services.survey_generation_service import SurveyGenerationService


class TestSurveyGenerationService:
    """Test cases for SurveyGenerationService"""
    
    def test_generate_survey_python_success(self):
        """Test successful survey generation for Python"""
        user_id = "test_user_123"
        subject = "python"
        
        survey = SurveyGenerationService.generate_survey(subject, user_id)
        
        # Verify basic structure
        assert survey['subject'] == subject
        assert survey['user_id'] == user_id
        assert survey['subject_name'] == 'Python Programming'
        assert 'questions' in survey
        assert 'generated_at' in survey
        assert 'metadata' in survey
        
        # Verify question count
        expected_count = SurveyGenerationService.SUBJECT_CONFIG[subject]['question_count']
        assert survey['total_questions'] == expected_count
        assert len(survey['questions']) == expected_count
        
        # Verify question structure
        for question in survey['questions']:
            assert 'id' in question
            assert 'question' in question
            assert 'type' in question
            assert 'options' in question
            assert 'correct_answer' in question
            assert 'difficulty' in question
            assert 'topic' in question
            assert question['type'] == 'multiple_choice'
            assert isinstance(question['options'], list)
            assert len(question['options']) == 4
            assert isinstance(question['correct_answer'], int)
            assert 0 <= question['correct_answer'] < len(question['options'])
            assert question['difficulty'] in ['beginner', 'intermediate', 'advanced']
    
    def test_generate_survey_javascript_success(self):
        """Test successful survey generation for JavaScript"""
        user_id = "test_user_456"
        subject = "javascript"
        
        survey = SurveyGenerationService.generate_survey(subject, user_id)
        
        # Verify basic structure
        assert survey['subject'] == subject
        assert survey['user_id'] == user_id
        assert survey['subject_name'] == 'JavaScript Programming'
        assert 'questions' in survey
        
        # Verify question count
        expected_count = SurveyGenerationService.SUBJECT_CONFIG[subject]['question_count']
        assert survey['total_questions'] == expected_count
        assert len(survey['questions']) == expected_count
    
    def test_generate_survey_unsupported_subject(self):
        """Test survey generation with unsupported subject"""
        user_id = "test_user_789"
        subject = "unsupported_subject"
        
        with pytest.raises(ValueError, match="Subject 'unsupported_subject' is not supported"):
            SurveyGenerationService.generate_survey(subject, user_id)
    
    def test_generate_survey_difficulty_distribution(self):
        """Test that survey respects difficulty distribution"""
        user_id = "test_user_distribution"
        subject = "python"
        
        survey = SurveyGenerationService.generate_survey(subject, user_id)
        
        # Count questions by difficulty
        difficulty_counts = {'beginner': 0, 'intermediate': 0, 'advanced': 0}
        for question in survey['questions']:
            difficulty_counts[question['difficulty']] += 1
        
        # Verify distribution matches expected
        expected_dist = SurveyGenerationService.SUBJECT_CONFIG[subject]['difficulty_distribution']
        total_questions = survey['total_questions']
        
        expected_beginner = int(total_questions * expected_dist['beginner'])
        expected_intermediate = int(total_questions * expected_dist['intermediate'])
        expected_advanced = int(total_questions * expected_dist['advanced'])
        
        # Allow for rounding adjustments
        assert difficulty_counts['beginner'] >= expected_beginner
        assert difficulty_counts['intermediate'] >= expected_intermediate
        assert difficulty_counts['advanced'] >= expected_advanced
        
        # Verify metadata contains distribution info
        assert 'difficulty_distribution' in survey['metadata']
        assert survey['metadata']['difficulty_distribution']['beginner'] == difficulty_counts['beginner']
    
    def test_generate_survey_unique_question_ids(self):
        """Test that all questions have unique IDs"""
        user_id = "test_user_ids"
        subject = "python"
        
        survey = SurveyGenerationService.generate_survey(subject, user_id)
        
        question_ids = [q['id'] for q in survey['questions']]
        assert len(question_ids) == len(set(question_ids)), "Question IDs should be unique"
        assert min(question_ids) == 1, "Question IDs should start from 1"
        assert max(question_ids) == len(question_ids), "Question IDs should be consecutive"
    
    def test_generate_survey_topics_coverage(self):
        """Test that survey covers various topics"""
        user_id = "test_user_topics"
        subject = "python"
        
        survey = SurveyGenerationService.generate_survey(subject, user_id)
        
        # Verify topics are covered
        topics_covered = survey['metadata']['topics_covered']
        assert isinstance(topics_covered, list)
        assert len(topics_covered) > 0
        
        # Verify all question topics are in the covered list
        question_topics = [q['topic'] for q in survey['questions']]
        for topic in question_topics:
            assert topic in topics_covered
    
    def test_get_supported_subjects(self):
        """Test getting list of supported subjects"""
        subjects = SurveyGenerationService.get_supported_subjects()
        
        assert isinstance(subjects, list)
        assert 'python' in subjects
        assert 'javascript' in subjects
        assert len(subjects) >= 2
    
    def test_get_subject_info_success(self):
        """Test getting subject information"""
        subject = "python"
        info = SurveyGenerationService.get_subject_info(subject)
        
        assert info['name'] == 'Python Programming'
        assert 'question_count' in info
        assert 'difficulty_distribution' in info
        assert 'topics' in info
        assert isinstance(info['topics'], list)
    
    def test_get_subject_info_unsupported(self):
        """Test getting info for unsupported subject"""
        subject = "unsupported"
        
        with pytest.raises(ValueError, match="Subject 'unsupported' is not supported"):
            SurveyGenerationService.get_subject_info(subject)
    
    def test_validate_survey_structure_valid(self):
        """Test validation of valid survey structure"""
        valid_survey = {
            'subject': 'python',
            'user_id': 'test_user',
            'questions': [
                {
                    'id': 1,
                    'question': 'Test question?',
                    'type': 'multiple_choice',
                    'options': ['A', 'B', 'C', 'D'],
                    'correct_answer': 0,
                    'difficulty': 'beginner',
                    'topic': 'test_topic'
                }
            ],
            'generated_at': datetime.utcnow().isoformat()
        }
        
        assert SurveyGenerationService.validate_survey_structure(valid_survey) is True
    
    def test_validate_survey_structure_missing_fields(self):
        """Test validation of survey with missing fields"""
        invalid_survey = {
            'subject': 'python',
            'user_id': 'test_user'
            # Missing 'questions' and 'generated_at'
        }
        
        assert SurveyGenerationService.validate_survey_structure(invalid_survey) is False
    
    def test_validate_survey_structure_invalid_questions(self):
        """Test validation of survey with invalid question structure"""
        invalid_survey = {
            'subject': 'python',
            'user_id': 'test_user',
            'questions': [
                {
                    'id': 1,
                    'question': 'Test question?'
                    # Missing required question fields
                }
            ],
            'generated_at': datetime.utcnow().isoformat()
        }
        
        assert SurveyGenerationService.validate_survey_structure(invalid_survey) is False
    
    def test_validate_survey_structure_non_list_questions(self):
        """Test validation of survey with non-list questions"""
        invalid_survey = {
            'subject': 'python',
            'user_id': 'test_user',
            'questions': 'not a list',
            'generated_at': datetime.utcnow().isoformat()
        }
        
        assert SurveyGenerationService.validate_survey_structure(invalid_survey) is False
    
    @patch('random.shuffle')
    @patch('random.sample')
    def test_generate_survey_randomization(self, mock_sample, mock_shuffle):
        """Test that survey generation uses randomization"""
        user_id = "test_user_random"
        subject = "python"
        
        # Mock random.sample to return predictable results
        def mock_sample_side_effect(population, k):
            return population[:k]
        mock_sample.side_effect = mock_sample_side_effect
        
        survey = SurveyGenerationService.generate_survey(subject, user_id)
        
        # Verify random functions were called
        assert mock_sample.called
        assert mock_shuffle.called
        
        # Verify shuffle was called with the questions list
        mock_shuffle.assert_called_once()
        shuffled_arg = mock_shuffle.call_args[0][0]
        assert isinstance(shuffled_arg, list)
        assert len(shuffled_arg) == survey['total_questions']
    
    def test_generate_survey_consistent_structure_multiple_calls(self):
        """Test that multiple survey generations have consistent structure"""
        user_id = "test_user_consistent"
        subject = "python"
        
        survey1 = SurveyGenerationService.generate_survey(subject, user_id)
        survey2 = SurveyGenerationService.generate_survey(subject, user_id)
        
        # Both surveys should have same basic structure
        assert survey1['subject'] == survey2['subject']
        assert survey1['total_questions'] == survey2['total_questions']
        assert len(survey1['questions']) == len(survey2['questions'])
        
        # Questions might be different due to randomization, but structure should be same
        for q1, q2 in zip(survey1['questions'], survey2['questions']):
            assert set(q1.keys()) == set(q2.keys())
            assert len(q1['options']) == len(q2['options'])
    
    def test_generate_survey_handles_insufficient_questions(self):
        """Test survey generation when more questions needed than available"""
        # This test verifies the logic that handles cases where we need more questions
        # than available in a difficulty level (though current templates have enough)
        user_id = "test_user_insufficient"
        subject = "python"
        
        # Temporarily modify the config to require more questions
        original_config = SurveyGenerationService.SUBJECT_CONFIG[subject].copy()
        SurveyGenerationService.SUBJECT_CONFIG[subject]['question_count'] = 50
        
        try:
            survey = SurveyGenerationService.generate_survey(subject, user_id)
            
            # Should still generate a survey, possibly with repeated questions
            assert survey['total_questions'] == 50
            assert len(survey['questions']) == 50
            
            # All questions should still have valid structure
            for question in survey['questions']:
                assert 'id' in question
                assert 'difficulty' in question
                assert question['difficulty'] in ['beginner', 'intermediate', 'advanced']
        
        finally:
            # Restore original config
            SurveyGenerationService.SUBJECT_CONFIG[subject] = original_config