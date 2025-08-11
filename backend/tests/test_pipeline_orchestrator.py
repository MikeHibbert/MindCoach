"""
Tests for Pipeline Orchestrator
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from app.services.pipeline_orchestrator import (
    PipelineOrchestrator, 
    PipelineStage, 
    PipelineStatus, 
    PipelineProgress
)

class TestPipelineOrchestrator:
    """Test Pipeline Orchestrator functionality"""
    
    @pytest.fixture
    def mock_survey_data(self):
        """Mock survey data for testing"""
        return {
            'user_id': 'test-user',
            'subject': 'python',
            'skill_level': 'intermediate',
            'answers': [
                {'question_id': 1, 'correct': True, 'topic': 'variables'},
                {'question_id': 2, 'correct': False, 'topic': 'functions'},
                {'question_id': 3, 'correct': True, 'topic': 'classes'}
            ]
        }
    
    @pytest.fixture
    def mock_curriculum_data(self):
        """Mock curriculum data for testing"""
        return {
            'curriculum': {
                'subject': 'python',
                'skill_level': 'intermediate',
                'total_lessons': 3,
                'learning_objectives': ['Learn Python basics', 'Build projects'],
                'topics': [
                    {'lesson_id': 1, 'title': 'Variables and Data Types'},
                    {'lesson_id': 2, 'title': 'Functions and Scope'},
                    {'lesson_id': 3, 'title': 'Classes and Objects'}
                ]
            }
        }
    
    @pytest.fixture
    def mock_lesson_plans_data(self):
        """Mock lesson plans data for testing"""
        return {
            'lesson_plans': [
                {
                    'lesson_id': 1,
                    'title': 'Variables and Data Types',
                    'learning_objectives': ['Understand variables', 'Use data types'],
                    'structure': {'introduction': '5 min', 'main_content': '20 min'}
                },
                {
                    'lesson_id': 2,
                    'title': 'Functions and Scope',
                    'learning_objectives': ['Define functions', 'Understand scope'],
                    'structure': {'introduction': '5 min', 'main_content': '20 min'}
                },
                {
                    'lesson_id': 3,
                    'title': 'Classes and Objects',
                    'learning_objectives': ['Create classes', 'Use objects'],
                    'structure': {'introduction': '5 min', 'main_content': '20 min'}
                }
            ]
        }
    
    @patch('app.services.pipeline_orchestrator.LangChainPipelineService')
    def test_orchestrator_initialization(self, mock_pipeline_service):
        """Test orchestrator initialization"""
        orchestrator = PipelineOrchestrator()
        
        assert orchestrator is not None
        assert hasattr(orchestrator, 'pipeline_service')
        assert hasattr(orchestrator, 'active_pipelines')
        assert hasattr(orchestrator, 'progress_callbacks')
        assert len(orchestrator.active_pipelines) == 0
    
    def test_pipeline_progress_dataclass(self):
        """Test PipelineProgress dataclass functionality"""
        progress = PipelineProgress(
            user_id='test-user',
            subject='python',
            current_stage=PipelineStage.CURRICULUM_GENERATION,
            status=PipelineStatus.IN_PROGRESS,
            progress_percentage=25.0,
            stages_completed=1,
            total_stages=3,
            current_step='Generating curriculum'
        )
        
        # Test to_dict conversion
        progress_dict = progress.to_dict()
        
        assert progress_dict['user_id'] == 'test-user'
        assert progress_dict['subject'] == 'python'
        assert progress_dict['current_stage'] == 'curriculum_generation'
        assert progress_dict['status'] == 'in_progress'
        assert progress_dict['progress_percentage'] == 25.0
        assert progress_dict['stages_completed'] == 1
        assert progress_dict['total_stages'] == 3
        assert progress_dict['current_step'] == 'Generating curriculum'
    
    @patch('app.services.pipeline_orchestrator.LangChainPipelineService')
    @patch('app.services.pipeline_orchestrator.UserDataService')
    def test_start_full_pipeline(self, mock_user_data_service, mock_pipeline_service, mock_survey_data):
        """Test starting a full pipeline"""
        # Mock pipeline service methods
        mock_pipeline_instance = Mock()
        mock_pipeline_service.return_value = mock_pipeline_instance
        
        orchestrator = PipelineOrchestrator()
        
        # Mock progress callback
        progress_callback = Mock()
        
        # Start pipeline
        pipeline_id = orchestrator.start_full_pipeline(
            'test-user', 
            'python', 
            mock_survey_data,
            progress_callback
        )
        
        # Verify pipeline was created
        assert pipeline_id in orchestrator.active_pipelines
        assert pipeline_id.startswith('test-user_python_')
        
        # Verify progress tracking
        progress = orchestrator.active_pipelines[pipeline_id]
        assert progress.user_id == 'test-user'
        assert progress.subject == 'python'
        assert progress.status == PipelineStatus.IN_PROGRESS
        assert progress.total_stages == 3
        
        # Verify callback was registered
        assert pipeline_id in orchestrator.progress_callbacks
        assert progress_callback in orchestrator.progress_callbacks[pipeline_id]
    
    @patch('app.services.pipeline_orchestrator.LangChainPipelineService')
    def test_get_pipeline_progress(self, mock_pipeline_service):
        """Test getting pipeline progress"""
        orchestrator = PipelineOrchestrator()
        
        # Create a mock pipeline
        progress = PipelineProgress(
            user_id='test-user',
            subject='python',
            current_stage=PipelineStage.LESSON_PLANNING,
            status=PipelineStatus.IN_PROGRESS,
            progress_percentage=66.6,
            stages_completed=2,
            total_stages=3,
            current_step='Creating lesson plans'
        )
        
        pipeline_id = 'test-pipeline-123'
        orchestrator.active_pipelines[pipeline_id] = progress
        
        # Get progress
        result = orchestrator.get_pipeline_progress(pipeline_id)
        
        assert result is not None
        assert result['user_id'] == 'test-user'
        assert result['subject'] == 'python'
        assert result['current_stage'] == 'lesson_planning'
        assert result['status'] == 'in_progress'
        assert result['progress_percentage'] == 66.6
        assert result['stages_completed'] == 2
        
        # Test non-existent pipeline
        result = orchestrator.get_pipeline_progress('non-existent')
        assert result is None
    
    @patch('app.services.pipeline_orchestrator.LangChainPipelineService')
    def test_cancel_pipeline(self, mock_pipeline_service):
        """Test cancelling a pipeline"""
        orchestrator = PipelineOrchestrator()
        
        # Create a mock running pipeline
        progress = PipelineProgress(
            user_id='test-user',
            subject='python',
            current_stage=PipelineStage.CONTENT_GENERATION,
            status=PipelineStatus.IN_PROGRESS,
            progress_percentage=80.0,
            stages_completed=2,
            total_stages=3,
            current_step='Generating content'
        )
        
        pipeline_id = 'test-pipeline-123'
        orchestrator.active_pipelines[pipeline_id] = progress
        
        # Cancel pipeline
        result = orchestrator.cancel_pipeline(pipeline_id)
        
        assert result == True
        assert progress.status == PipelineStatus.CANCELLED
        assert progress.error_message == "Pipeline cancelled by user"
        
        # Test cancelling non-existent pipeline
        result = orchestrator.cancel_pipeline('non-existent')
        assert result == False
        
        # Test cancelling already completed pipeline
        progress.status = PipelineStatus.COMPLETED
        result = orchestrator.cancel_pipeline(pipeline_id)
        assert result == False
    
    @patch('app.services.pipeline_orchestrator.LangChainPipelineService')
    def test_get_active_pipelines(self, mock_pipeline_service):
        """Test getting all active pipelines"""
        orchestrator = PipelineOrchestrator()
        
        # Create multiple mock pipelines
        progress1 = PipelineProgress(
            user_id='user1',
            subject='python',
            current_stage=PipelineStage.CURRICULUM_GENERATION,
            status=PipelineStatus.IN_PROGRESS,
            progress_percentage=25.0,
            stages_completed=0,
            total_stages=3,
            current_step='Starting curriculum generation'
        )
        
        progress2 = PipelineProgress(
            user_id='user2',
            subject='javascript',
            current_stage=PipelineStage.CONTENT_GENERATION,
            status=PipelineStatus.IN_PROGRESS,
            progress_percentage=90.0,
            stages_completed=2,
            total_stages=3,
            current_step='Generating final lessons'
        )
        
        orchestrator.active_pipelines['pipeline1'] = progress1
        orchestrator.active_pipelines['pipeline2'] = progress2
        
        # Get all active pipelines
        result = orchestrator.get_active_pipelines()
        
        assert len(result) == 2
        assert 'pipeline1' in result
        assert 'pipeline2' in result
        assert result['pipeline1']['user_id'] == 'user1'
        assert result['pipeline2']['user_id'] == 'user2'
        assert result['pipeline1']['subject'] == 'python'
        assert result['pipeline2']['subject'] == 'javascript'
    
    @patch('app.services.pipeline_orchestrator.LangChainPipelineService')
    def test_get_pipeline_statistics(self, mock_pipeline_service):
        """Test getting pipeline statistics"""
        orchestrator = PipelineOrchestrator()
        
        # Create pipelines with different statuses
        progress1 = PipelineProgress(
            user_id='user1', subject='python',
            current_stage=PipelineStage.CURRICULUM_GENERATION,
            status=PipelineStatus.IN_PROGRESS,
            progress_percentage=25.0, stages_completed=0, total_stages=3,
            current_step='In progress'
        )
        
        progress2 = PipelineProgress(
            user_id='user2', subject='javascript',
            current_stage=PipelineStage.CONTENT_GENERATION,
            status=PipelineStatus.COMPLETED,
            progress_percentage=100.0, stages_completed=3, total_stages=3,
            current_step='Completed'
        )
        
        progress3 = PipelineProgress(
            user_id='user3', subject='react',
            current_stage=PipelineStage.LESSON_PLANNING,
            status=PipelineStatus.FAILED,
            progress_percentage=50.0, stages_completed=1, total_stages=3,
            current_step='Failed'
        )
        
        orchestrator.active_pipelines['pipeline1'] = progress1
        orchestrator.active_pipelines['pipeline2'] = progress2
        orchestrator.active_pipelines['pipeline3'] = progress3
        
        # Get statistics
        stats = orchestrator.get_pipeline_statistics()
        
        assert stats['total_pipelines'] == 3
        assert stats['active_count'] == 1
        assert stats['completed_count'] == 1
        assert stats['failed_count'] == 1
        assert stats['status_distribution']['in_progress'] == 1
        assert stats['status_distribution']['completed'] == 1
        assert stats['status_distribution']['failed'] == 1
    
    @patch('app.services.pipeline_orchestrator.LangChainPipelineService')
    @patch('app.services.pipeline_orchestrator.UserDataService')
    def test_retry_failed_pipeline(self, mock_user_data_service, mock_pipeline_service, mock_survey_data):
        """Test retrying a failed pipeline"""
        orchestrator = PipelineOrchestrator()
        
        # Create a failed pipeline
        progress = PipelineProgress(
            user_id='test-user',
            subject='python',
            current_stage=PipelineStage.LESSON_PLANNING,
            status=PipelineStatus.FAILED,
            progress_percentage=50.0,
            stages_completed=1,
            total_stages=3,
            current_step='Failed at lesson planning',
            error_message='Test error'
        )
        
        pipeline_id = 'test-pipeline-123'
        orchestrator.active_pipelines[pipeline_id] = progress
        
        # Mock UserDataService to return survey data
        mock_user_data_service.load_survey_answers.return_value = mock_survey_data
        
        # Mock successful retry execution
        with patch.object(orchestrator, '_execute_pipeline_stages') as mock_execute:
            result = orchestrator.retry_failed_pipeline(pipeline_id)
            
            assert result == True
            assert progress.status == PipelineStatus.IN_PROGRESS
            assert progress.error_message is None
            mock_execute.assert_called_once_with(pipeline_id, mock_survey_data)
        
        # Test retrying non-existent pipeline
        result = orchestrator.retry_failed_pipeline('non-existent')
        assert result == False
        
        # Test retrying non-failed pipeline
        progress.status = PipelineStatus.COMPLETED
        result = orchestrator.retry_failed_pipeline(pipeline_id)
        assert result == False
    
    @patch('app.services.pipeline_orchestrator.LangChainPipelineService')
    def test_cleanup_completed_pipelines(self, mock_pipeline_service):
        """Test cleaning up old completed pipelines"""
        orchestrator = PipelineOrchestrator()
        
        # Create old completed pipeline
        old_time = '2024-01-01T10:00:00Z'
        progress1 = PipelineProgress(
            user_id='user1', subject='python',
            current_stage=PipelineStage.CONTENT_GENERATION,
            status=PipelineStatus.COMPLETED,
            progress_percentage=100.0, stages_completed=3, total_stages=3,
            current_step='Completed', completed_at=old_time
        )
        
        # Create recent completed pipeline
        recent_time = '2024-12-01T10:00:00Z'
        progress2 = PipelineProgress(
            user_id='user2', subject='javascript',
            current_stage=PipelineStage.CONTENT_GENERATION,
            status=PipelineStatus.COMPLETED,
            progress_percentage=100.0, stages_completed=3, total_stages=3,
            current_step='Completed', completed_at=recent_time
        )
        
        # Create active pipeline
        progress3 = PipelineProgress(
            user_id='user3', subject='react',
            current_stage=PipelineStage.CURRICULUM_GENERATION,
            status=PipelineStatus.IN_PROGRESS,
            progress_percentage=25.0, stages_completed=0, total_stages=3,
            current_step='In progress'
        )
        
        orchestrator.active_pipelines['old-pipeline'] = progress1
        orchestrator.active_pipelines['recent-pipeline'] = progress2
        orchestrator.active_pipelines['active-pipeline'] = progress3
        
        # Add callbacks for cleanup test
        orchestrator.progress_callbacks['old-pipeline'] = [Mock()]
        orchestrator.progress_callbacks['recent-pipeline'] = [Mock()]
        
        # Cleanup with very short max age to remove old pipeline
        orchestrator.cleanup_completed_pipelines(max_age_hours=0.001)
        
        # Old completed pipeline should be removed
        assert 'old-pipeline' not in orchestrator.active_pipelines
        assert 'old-pipeline' not in orchestrator.progress_callbacks
        
        # Recent and active pipelines should remain
        assert 'recent-pipeline' in orchestrator.active_pipelines
        assert 'active-pipeline' in orchestrator.active_pipelines