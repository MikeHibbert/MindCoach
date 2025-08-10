"""
Tests for business logic and service layer components
Tests the core business rules, validation, and service interactions
"""

import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app import create_app, db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.survey_result import SurveyResult
from app.services.user_service import UserService
from app.services.subscription_service import SubscriptionService
from app.services.survey_result_service import SurveyResultService
from app.services.survey_analysis_service import SurveyAnalysisService
from app.services.lesson_generation_service import LessonGenerationService
from app.services.payment_gate_service import PaymentGateService


@pytest.fixture(scope='function')
def app():
    """Create test Flask application"""
    test_dir = tempfile.mkdtemp()
    
    config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    }
    
    app = create_app(config)
    
    with app.app_context():
        db.create_all()
        
        with patch('app.services.file_service.FileService.BASE_DIR') as mock_base_dir:
            mock_base_dir.return_value = test_dir
            yield app
        
        db.drop_all()
    
    shutil.rmtree(test_dir, ignore_errors=True)


class TestUserBusinessLogic:
    """Test user-related business logic"""
    
    def test_user_creation_business_rules(self, app):
        """Test business rules for user creation"""
        with app.app_context():
            # Test valid user creation
            user = UserService.create_user('valid_user', 'valid@example.com')
            assert user is not None
            assert user.user_id == 'valid_user'
            assert user.email == 'valid@example.com'
            assert user.created_at is not None
            
            # Test duplicate user creation (should return existing user)
            duplicate_user = UserService.create_user('valid_user', 'different@example.com')
            assert duplicate_user.user_id == 'valid_user'
            assert duplicate_user.email == 'valid@example.com'  # Original email preserved
            
            # Test user creation without email
            user_no_email = UserService.create_user('no_email_user')
            assert user_no_email is not None
            assert user_no_email.email is None
    
    def test_user_validation_rules(self, app):
        """Test user validation business rules"""
        with app.app_context():
            # Test invalid user IDs
            invalid_user_ids = [
                '',           # Empty string
                None,         # None value
                'a' * 51,     # Too long
                'user@test',  # Invalid characters
                '../user',    # Path traversal
                'user/test'   # Path separator
            ]
            
            for invalid_id in invalid_user_ids:
                with pytest.raises((ValueError, TypeError)):
                    UserService.create_user(invalid_id, 'test@example.com')
            
            # Test invalid emails
            invalid_emails = [
                'invalid-email',      # No @ symbol
                '@example.com',       # No local part
                'user@',              # No domain
                'user@.com',          # Invalid domain
                'user space@test.com' # Space in local part
            ]
            
            for invalid_email in invalid_emails:
                with pytest.raises(ValueError):
                    UserService.create_user('test_user', invalid_email)
    
    def test_user_update_business_rules(self, app):
        """Test business rules for user updates"""
        with app.app_context():
            # Create initial user
            user = UserService.create_user('update_user', 'original@example.com')
            original_created_at = user.created_at
            
            # Test valid email update
            updated_user = UserService.update_user('update_user', email='updated@example.com')
            assert updated_user.email == 'updated@example.com'
            assert updated_user.created_at == original_created_at  # Should not change
            assert updated_user.updated_at > original_created_at   # Should be updated
            
            # Test invalid email update
            with pytest.raises(ValueError):
                UserService.update_user('update_user', email='invalid-email')
            
            # Test updating non-existent user
            result = UserService.update_user('nonexistent_user', email='test@example.com')
            assert result is None


class TestSubscriptionBusinessLogic:
    """Test subscription-related business logic"""
    
    def test_subscription_creation_rules(self, app):
        """Test business rules for subscription creation"""
        with app.app_context():
            # Create test user
            user = UserService.create_user('sub_user', 'sub@example.com')
            
            # Test valid subscription creation
            subscription = SubscriptionService.create_subscription(
                'sub_user', 'python', 'active'
            )
            assert subscription is not None
            assert subscription.user_id == 'sub_user'
            assert subscription.subject == 'python'
            assert subscription.status == 'active'
            assert subscription.purchased_at is not None
            
            # Test duplicate subscription (should update existing)
            duplicate_sub = SubscriptionService.create_subscription(
                'sub_user', 'python', 'cancelled'
            )
            assert duplicate_sub.id == subscription.id  # Same subscription
            assert duplicate_sub.status == 'cancelled'  # Updated status
    
    def test_subscription_expiration_logic(self, app):
        """Test subscription expiration business logic"""
        with app.app_context():
            user = UserService.create_user('exp_user', 'exp@example.com')
            
            # Create active subscription with future expiration
            future_date = datetime.utcnow() + timedelta(days=30)
            active_sub = SubscriptionService.create_subscription(
                'exp_user', 'python', 'active', future_date
            )
            
            # Should be active
            assert SubscriptionService.has_active_subscription('exp_user', 'python') == True
            
            # Create expired subscription
            past_date = datetime.utcnow() - timedelta(days=1)
            expired_sub = SubscriptionService.create_subscription(
                'exp_user', 'javascript', 'active', past_date
            )
            
            # Should not be active due to expiration
            assert SubscriptionService.has_active_subscription('exp_user', 'javascript') == False
            
            # Test cancelled subscription
            cancelled_sub = SubscriptionService.create_subscription(
                'exp_user', 'java', 'cancelled', future_date
            )
            
            # Should not be active due to cancelled status
            assert SubscriptionService.has_active_subscription('exp_user', 'java') == False
    
    def test_subscription_business_validation(self, app):
        """Test subscription validation business rules"""
        with app.app_context():
            # Test subscription for non-existent user
            with pytest.raises(ValueError):
                SubscriptionService.create_subscription(
                    'nonexistent_user', 'python', 'active'
                )
            
            # Test invalid subject
            user = UserService.create_user('val_user', 'val@example.com')
            
            invalid_subjects = ['', None, 'a' * 51, 'subject@test', '../subject']
            for invalid_subject in invalid_subjects:
                with pytest.raises((ValueError, TypeError)):
                    SubscriptionService.create_subscription(
                        'val_user', invalid_subject, 'active'
                    )
            
            # Test invalid status
            invalid_statuses = ['', None, 'invalid_status', 123]
            for invalid_status in invalid_statuses:
                with pytest.raises((ValueError, TypeError)):
                    SubscriptionService.create_subscription(
                        'val_user', 'python', invalid_status
                    )


class TestSurveyBusinessLogic:
    """Test survey-related business logic"""
    
    def test_survey_analysis_logic(self, app):
        """Test survey analysis business logic"""
        with app.app_context():
            user = UserService.create_user('survey_user', 'survey@example.com')
            
            # Test beginner level analysis
            beginner_answers = [
                {'question_id': 1, 'answer': 'wrong', 'correct': False},
                {'question_id': 2, 'answer': 'wrong', 'correct': False},
                {'question_id': 3, 'answer': 'correct', 'correct': True}
            ]
            
            with patch('app.services.survey_analysis_service.SurveyAnalysisService._load_survey') as mock_survey:
                mock_survey.return_value = {
                    'questions': [
                        {'id': 1, 'topic': 'variables', 'difficulty': 'beginner'},
                        {'id': 2, 'topic': 'functions', 'difficulty': 'beginner'},
                        {'id': 3, 'topic': 'loops', 'difficulty': 'beginner'}
                    ]
                }
                
                result = SurveyAnalysisService.process_survey_answers(
                    'survey_user', 'python', beginner_answers
                )
                
                assert result['skill_level'] == 'beginner'  # Low accuracy = beginner
                assert result['accuracy'] == pytest.approx(33.33, rel=1e-2)
                assert result['total_questions'] == 3
                assert result['correct_answers'] == 1
            
            # Test advanced level analysis
            advanced_answers = [
                {'question_id': 1, 'answer': 'correct', 'correct': True},
                {'question_id': 2, 'answer': 'correct', 'correct': True},
                {'question_id': 3, 'answer': 'correct', 'correct': True},
                {'question_id': 4, 'answer': 'correct', 'correct': True},
                {'question_id': 5, 'answer': 'correct', 'correct': True}
            ]
            
            with patch('app.services.survey_analysis_service.SurveyAnalysisService._load_survey') as mock_survey:
                mock_survey.return_value = {
                    'questions': [
                        {'id': i, 'topic': f'topic_{i}', 'difficulty': 'advanced'}
                        for i in range(1, 6)
                    ]
                }
                
                result = SurveyAnalysisService.process_survey_answers(
                    'survey_user', 'python', advanced_answers
                )
                
                assert result['skill_level'] == 'advanced'  # High accuracy = advanced
                assert result['accuracy'] == 100.0
    
    def test_survey_topic_analysis(self, app):
        """Test survey topic analysis business logic"""
        with app.app_context():
            user = UserService.create_user('topic_user', 'topic@example.com')
            
            # Mixed performance across topics
            mixed_answers = [
                {'question_id': 1, 'answer': 'correct', 'correct': True},   # variables
                {'question_id': 2, 'answer': 'correct', 'correct': True},   # variables
                {'question_id': 3, 'answer': 'wrong', 'correct': False},    # functions
                {'question_id': 4, 'answer': 'wrong', 'correct': False},    # functions
                {'question_id': 5, 'answer': 'correct', 'correct': True}    # loops
            ]
            
            with patch('app.services.survey_analysis_service.SurveyAnalysisService._load_survey') as mock_survey:
                mock_survey.return_value = {
                    'questions': [
                        {'id': 1, 'topic': 'variables', 'difficulty': 'beginner'},
                        {'id': 2, 'topic': 'variables', 'difficulty': 'intermediate'},
                        {'id': 3, 'topic': 'functions', 'difficulty': 'beginner'},
                        {'id': 4, 'topic': 'functions', 'difficulty': 'intermediate'},
                        {'id': 5, 'topic': 'loops', 'difficulty': 'beginner'}
                    ]
                }
                
                result = SurveyAnalysisService.process_survey_answers(
                    'topic_user', 'python', mixed_answers
                )
                
                topic_analysis = result['topic_analysis']
                assert topic_analysis['variables']['accuracy'] == 100.0  # 2/2 correct
                assert topic_analysis['functions']['accuracy'] == 0.0    # 0/2 correct
                assert topic_analysis['loops']['accuracy'] == 100.0      # 1/1 correct
    
    def test_survey_recommendations_logic(self, app):
        """Test survey recommendation generation logic"""
        with app.app_context():
            user = UserService.create_user('rec_user', 'rec@example.com')
            
            # Test recommendations for weak areas
            weak_answers = [
                {'question_id': 1, 'answer': 'wrong', 'correct': False},
                {'question_id': 2, 'answer': 'wrong', 'correct': False},
                {'question_id': 3, 'answer': 'correct', 'correct': True}
            ]
            
            with patch('app.services.survey_analysis_service.SurveyAnalysisService._load_survey') as mock_survey:
                mock_survey.return_value = {
                    'questions': [
                        {'id': 1, 'topic': 'variables', 'difficulty': 'beginner'},
                        {'id': 2, 'topic': 'variables', 'difficulty': 'beginner'},
                        {'id': 3, 'topic': 'functions', 'difficulty': 'beginner'}
                    ]
                }
                
                result = SurveyAnalysisService.process_survey_answers(
                    'rec_user', 'python', weak_answers
                )
                
                recommendations = result['recommendations']
                assert any('variables' in rec.lower() for rec in recommendations)
                assert any('focus' in rec.lower() or 'review' in rec.lower() for rec in recommendations)


class TestLessonGenerationBusinessLogic:
    """Test lesson generation business logic"""
    
    def test_lesson_personalization_logic(self, app):
        """Test lesson personalization based on skill level"""
        with app.app_context():
            user = UserService.create_user('lesson_user', 'lesson@example.com')
            
            # Create survey result for intermediate level
            survey_result = SurveyResultService.create_survey_result(
                'lesson_user', 'python', 'intermediate'
            )
            
            with patch('app.services.survey_analysis_service.SurveyAnalysisService.get_survey_results') as mock_results:
                mock_results.return_value = {
                    'skill_level': 'intermediate',
                    'topic_analysis': {
                        'variables': {'accuracy': 90.0, 'status': 'known'},
                        'functions': {'accuracy': 60.0, 'status': 'needs_review'},
                        'classes': {'accuracy': 30.0, 'status': 'unknown'}
                    }
                }
                
                result = LessonGenerationService.generate_personalized_lessons(
                    'lesson_user', 'python'
                )
                
                # Should generate lessons appropriate for intermediate level
                assert result['metadata']['skill_level'] == 'intermediate'
                
                # Should skip topics that are well known
                lesson_topics = []
                for lesson in result['lessons']:
                    lesson_topics.extend(lesson.get('topics', []))
                
                # Variables should be skipped or minimal since accuracy is 90%
                # Functions and classes should be included since they need work
                assert lesson_topics.count('variables') < lesson_topics.count('functions')
    
    def test_lesson_content_validation(self, app):
        """Test lesson content validation business rules"""
        with app.app_context():
            # Test that generated lessons meet quality standards
            with patch('app.services.lesson_generation_service.LessonGenerationService._generate_lesson_content') as mock_generate:
                mock_generate.return_value = {
                    'title': 'Test Lesson',
                    'content': '# Test Lesson\n\nThis is a test lesson with proper structure.',
                    'estimated_time': '30 minutes',
                    'difficulty': 'intermediate',
                    'topics': ['test_topic']
                }
                
                result = LessonGenerationService.generate_personalized_lessons(
                    'lesson_user', 'python'
                )
                
                # Validate lesson structure
                for lesson in result['lessons']:
                    assert 'title' in lesson
                    assert 'content' in lesson
                    assert 'estimated_time' in lesson
                    assert 'difficulty' in lesson
                    assert 'topics' in lesson
                    
                    # Content should be substantial
                    assert len(lesson['content']) > 100
                    
                    # Title should be descriptive
                    assert len(lesson['title']) > 5
                    
                    # Should have topics
                    assert len(lesson['topics']) > 0
    
    def test_lesson_progression_logic(self, app):
        """Test lesson progression and dependency logic"""
        with app.app_context():
            user = UserService.create_user('prog_user', 'prog@example.com')
            
            with patch('app.services.survey_analysis_service.SurveyAnalysisService.get_survey_results') as mock_results:
                mock_results.return_value = {
                    'skill_level': 'beginner',
                    'topic_analysis': {
                        'variables': {'accuracy': 20.0, 'status': 'unknown'},
                        'functions': {'accuracy': 10.0, 'status': 'unknown'},
                        'classes': {'accuracy': 0.0, 'status': 'unknown'}
                    }
                }
                
                result = LessonGenerationService.generate_personalized_lessons(
                    'prog_user', 'python'
                )
                
                lessons = result['lessons']
                
                # Lessons should be ordered by difficulty/prerequisites
                # Basic concepts should come before advanced ones
                lesson_titles = [lesson['title'].lower() for lesson in lessons]
                
                # Variables should come before functions
                var_index = next((i for i, title in enumerate(lesson_titles) if 'variable' in title), -1)
                func_index = next((i for i, title in enumerate(lesson_titles) if 'function' in title), -1)
                
                if var_index != -1 and func_index != -1:
                    assert var_index < func_index


class TestPaymentGateBusinessLogic:
    """Test payment gate and access control business logic"""
    
    def test_access_control_logic(self, app):
        """Test access control business logic"""
        with app.app_context():
            user = UserService.create_user('access_user', 'access@example.com')
            
            # Test access without subscription
            has_access = PaymentGateService.check_subject_access('access_user', 'python')
            assert has_access == False
            
            # Create active subscription
            subscription = SubscriptionService.create_subscription(
                'access_user', 'python', 'active',
                datetime.utcnow() + timedelta(days=30)
            )
            
            # Test access with active subscription
            has_access = PaymentGateService.check_subject_access('access_user', 'python')
            assert has_access == True
            
            # Test access to different subject
            has_access = PaymentGateService.check_subject_access('access_user', 'javascript')
            assert has_access == False
    
    def test_subscription_purchase_workflow(self, app):
        """Test subscription purchase workflow business logic"""
        with app.app_context():
            user = UserService.create_user('purchase_user', 'purchase@example.com')
            
            # Test purchase initiation
            purchase_info = PaymentGateService.initiate_purchase('purchase_user', 'python')
            assert purchase_info is not None
            assert purchase_info['subject'] == 'python'
            assert purchase_info['user_id'] == 'purchase_user'
            assert 'price' in purchase_info
            
            # Test purchase completion
            purchase_result = PaymentGateService.complete_purchase(
                'purchase_user', 'python', 'test_payment_id'
            )
            assert purchase_result['success'] == True
            assert purchase_result['subscription']['status'] == 'active'
            
            # Verify subscription was created
            has_access = PaymentGateService.check_subject_access('purchase_user', 'python')
            assert has_access == True
    
    def test_subscription_expiration_handling(self, app):
        """Test subscription expiration handling business logic"""
        with app.app_context():
            user = UserService.create_user('exp_handling_user', 'exphand@example.com')
            
            # Create subscription that expires soon
            near_expiry = datetime.utcnow() + timedelta(hours=1)
            subscription = SubscriptionService.create_subscription(
                'exp_handling_user', 'python', 'active', near_expiry
            )
            
            # Should still have access
            has_access = PaymentGateService.check_subject_access('exp_handling_user', 'python')
            assert has_access == True
            
            # Simulate expiration
            expired_date = datetime.utcnow() - timedelta(hours=1)
            subscription.expires_at = expired_date
            db.session.commit()
            
            # Should no longer have access
            has_access = PaymentGateService.check_subject_access('exp_handling_user', 'python')
            assert has_access == False
            
            # Test renewal
            renewal_result = PaymentGateService.renew_subscription(
                'exp_handling_user', 'python', 'renewal_payment_id'
            )
            assert renewal_result['success'] == True
            
            # Should have access again
            has_access = PaymentGateService.check_subject_access('exp_handling_user', 'python')
            assert has_access == True


class TestBusinessRuleIntegration:
    """Test integration of business rules across services"""
    
    def test_complete_learning_workflow(self, app):
        """Test complete learning workflow business logic"""
        with app.app_context():
            # Step 1: User registration
            user = UserService.create_user('workflow_user', 'workflow@example.com')
            assert user is not None
            
            # Step 2: Check initial access (should be denied)
            has_access = PaymentGateService.check_subject_access('workflow_user', 'python')
            assert has_access == False
            
            # Step 3: Purchase subscription
            purchase_result = PaymentGateService.complete_purchase(
                'workflow_user', 'python', 'workflow_payment_id'
            )
            assert purchase_result['success'] == True
            
            # Step 4: Verify access granted
            has_access = PaymentGateService.check_subject_access('workflow_user', 'python')
            assert has_access == True
            
            # Step 5: Take survey and get results
            survey_result = SurveyResultService.create_survey_result(
                'workflow_user', 'python', 'intermediate'
            )
            assert survey_result.skill_level == 'intermediate'
            
            # Step 6: Generate personalized lessons
            with patch('app.services.survey_analysis_service.SurveyAnalysisService.get_survey_results') as mock_results:
                mock_results.return_value = {
                    'skill_level': 'intermediate',
                    'topic_analysis': {'variables': {'accuracy': 80.0}}
                }
                
                lessons = LessonGenerationService.generate_personalized_lessons(
                    'workflow_user', 'python'
                )
                assert lessons['metadata']['skill_level'] == 'intermediate'
    
    def test_business_rule_violations(self, app):
        """Test that business rule violations are properly handled"""
        with app.app_context():
            # Test accessing lessons without subscription
            with pytest.raises((ValueError, PermissionError)):
                LessonGenerationService.generate_personalized_lessons(
                    'no_sub_user', 'python'
                )
            
            # Test generating lessons without survey
            user = UserService.create_user('no_survey_user', 'nosurvey@example.com')
            subscription = SubscriptionService.create_subscription(
                'no_survey_user', 'python', 'active'
            )
            
            with pytest.raises(FileNotFoundError):
                LessonGenerationService.generate_personalized_lessons(
                    'no_survey_user', 'python'
                )
    
    def test_data_consistency_rules(self, app):
        """Test data consistency business rules"""
        with app.app_context():
            user = UserService.create_user('consistency_user', 'consistency@example.com')
            
            # Create subscription
            subscription = SubscriptionService.create_subscription(
                'consistency_user', 'python', 'active'
            )
            
            # Create survey result
            survey_result = SurveyResultService.create_survey_result(
                'consistency_user', 'python', 'intermediate'
            )
            
            # Verify data consistency
            retrieved_user = UserService.get_user_by_id('consistency_user')
            retrieved_subscription = SubscriptionService.get_subscription('consistency_user', 'python')
            retrieved_survey = SurveyResultService.get_survey_result('consistency_user', 'python')
            
            assert retrieved_user.user_id == 'consistency_user'
            assert retrieved_subscription.user_id == 'consistency_user'
            assert retrieved_survey.user_id == 'consistency_user'
            
            # All should reference the same user
            assert retrieved_subscription.user_id == retrieved_user.user_id
            assert retrieved_survey.user_id == retrieved_user.user_id