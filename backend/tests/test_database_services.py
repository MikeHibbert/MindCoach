"""
Unit tests for database services
"""

import unittest
import tempfile
import os
from app import create_app, db
from app.services.user_service import UserService
from app.services.survey_result_service import SurveyResultService
from app.services.database_service import DatabaseService

class TestDatabaseServices(unittest.TestCase):
    """Test cases for database services"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Create test app with in-memory database
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create tables
        db.create_all()
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_user_service_crud(self):
        """Test UserService CRUD operations"""
        # Test create user
        user = UserService.create_user('test_user_1', 'test@example.com')
        self.assertIsNotNone(user)
        self.assertEqual(user.user_id, 'test_user_1')
        self.assertEqual(user.email, 'test@example.com')
        
        # Test get user by id
        retrieved_user = UserService.get_user_by_id('test_user_1')
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.user_id, 'test_user_1')
        
        # Test user exists
        self.assertTrue(UserService.user_exists('test_user_1'))
        self.assertFalse(UserService.user_exists('nonexistent_user'))
        
        # Test update user
        updated_user = UserService.update_user('test_user_1', email='updated@example.com')
        self.assertIsNotNone(updated_user)
        self.assertEqual(updated_user.email, 'updated@example.com')
        
        # Test get all users
        all_users = UserService.get_all_users()
        self.assertEqual(len(all_users), 1)
        
        # Test delete user
        result = UserService.delete_user('test_user_1')
        self.assertTrue(result)
        self.assertFalse(UserService.user_exists('test_user_1'))
    

    def test_survey_result_service_crud(self):
        """Test SurveyResultService CRUD operations"""
        # Create a user first
        user = UserService.create_user('test_user_4', 'test4@example.com')
        
        # Test create survey result
        survey_result = SurveyResultService.create_survey_result(
            'test_user_4', 'python', 'intermediate'
        )
        self.assertIsNotNone(survey_result)
        self.assertEqual(survey_result.user_id, 'test_user_4')
        self.assertEqual(survey_result.subject, 'python')
        self.assertEqual(survey_result.skill_level, 'intermediate')
        
        # Test get survey result
        retrieved_result = SurveyResultService.get_survey_result('test_user_4', 'python')
        self.assertIsNotNone(retrieved_result)
        self.assertEqual(retrieved_result.skill_level, 'intermediate')
        
        # Test update survey result (should update existing)
        updated_result = SurveyResultService.create_survey_result(
            'test_user_4', 'python', 'advanced'
        )
        self.assertEqual(updated_result.skill_level, 'advanced')
        
        # Test get user survey results
        user_results = SurveyResultService.get_user_survey_results('test_user_4')
        self.assertEqual(len(user_results), 1)
        
        # Test get results by skill level
        skill_results = SurveyResultService.get_results_by_skill_level('advanced')
        self.assertEqual(len(skill_results), 1)
        
        # Test get results by subject
        subject_results = SurveyResultService.get_results_by_subject('python')
        self.assertEqual(len(subject_results), 1)
        
        # Test delete survey result
        result = SurveyResultService.delete_survey_result('test_user_4', 'python')
        self.assertTrue(result)
        
        # Verify deletion
        deleted_result = SurveyResultService.get_survey_result('test_user_4', 'python')
        self.assertIsNone(deleted_result)
    
    def test_database_transaction_handling(self):
        """Test database transaction handling"""
        # Test successful transaction
        with DatabaseService.transaction() as session:
            user = UserService.create_user('transaction_user', 'trans@example.com')
            self.assertIsNotNone(user)
        
        # Verify user was created
        self.assertTrue(UserService.user_exists('transaction_user'))
        
        # Test safe commit
        result = DatabaseService.safe_commit()
        self.assertTrue(result)
        
        # Test safe rollback
        DatabaseService.safe_rollback()  # Should not raise error

if __name__ == '__main__':
    unittest.main()