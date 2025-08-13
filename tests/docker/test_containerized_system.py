#!/usr/bin/env python3
"""
Comprehensive Docker containerized system tests
Tests end-to-end functionality, data persistence, networking, and environment configuration
"""

import os
import sys
import time
import json
import requests
import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest
import docker
import redis
import psycopg2
from psycopg2 import sql
import logging
from datetime import datetime
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('docker_system_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DockerSystemTester:
    """Test suite for complete containerized system"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.test_results = {}
        self.temp_dirs = []
        self.test_start_time = datetime.now()
        
    def setup_test_environment(self):
        """Set up test environment with temporary directories and configurations"""
        logger.info("Setting up test environment...")
        
        # Create temporary directories for test data
        self.test_data_dir = tempfile.mkdtemp(prefix="docker_test_data_")
        self.test_users_dir = tempfile.mkdtemp(prefix="docker_test_users_")
        self.test_logs_dir = tempfile.mkdtemp(prefix="docker_test_logs_")
        
        self.temp_dirs.extend([self.test_data_dir, self.test_users_dir, self.test_logs_dir])
        
        # Create test environment file
        self.test_env_file = os.path.join(self.test_data_dir, ".env.test")
        with open(self.test_env_file, 'w') as f:
            f.write("""
# Test environment configuration
FLASK_ENV=testing
SECRET_KEY=test-secret-key-for-docker-testing
DATABASE_URL=postgresql://test_user:test_password@postgres-test:5432/mindcoach_test
REDIS_URL=redis://redis-test:6379/0
CELERY_BROKER_URL=redis://redis-test:6379/0
CELERY_RESULT_BACKEND=redis://redis-test:6379/0
XAI_API_KEY=test-api-key
GROK_API_URL=http://mock-api-test:8000
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
LOG_LEVEL=DEBUG
PYTHONUNBUFFERED=1
""")
        
        logger.info(f"Test environment setup completed")
        logger.info(f"Test data directory: {self.test_data_dir}")
        logger.info(f"Test users directory: {self.test_users_dir}")
        logger.info(f"Test logs directory: {self.test_logs_dir}")
        
    def cleanup_test_environment(self):
        """Clean up test environment"""
        logger.info("Cleaning up test environment...")
        
        # Remove temporary directories
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        # Stop and remove test containers
        try:
            subprocess.run([
                "docker-compose", "-f", "docker-compose.test.yml", 
                "down", "-v", "--remove-orphans"
            ], check=False, capture_output=True)
        except Exception as e:
            logger.warning(f"Error during container cleanup: {e}")
            
        logger.info("Test environment cleanup completed")
        
    def test_container_startup(self):
        """Test that all containers start successfully"""
        logger.info("Testing container startup...")
        
        try:
            # Start test infrastructure
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.test.yml",
                "up", "-d", "test-db", "test-redis", "mock-api"
            ], check=True, capture_output=True, text=True)
            
            logger.info("Test infrastructure containers started")
            
            # Wait for services to be ready
            time.sleep(30)
            
            # Check container health
            containers = self.docker_client.containers.list(
                filters={"label": "com.docker.compose.project=mindcoach"}
            )
            
            healthy_containers = 0
            for container in containers:
                if container.status == "running":
                    healthy_containers += 1
                    logger.info(f"Container {container.name} is running")
                else:
                    logger.error(f"Container {container.name} status: {container.status}")
                    
            self.test_results['container_startup'] = {
                'status': 'passed' if healthy_containers >= 3 else 'failed',
                'healthy_containers': healthy_containers,
                'total_containers': len(containers)
            }
            
            return healthy_containers >= 3
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Container startup failed: {e.stderr}")
            self.test_results['container_startup'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
            
    def test_container_networking(self):
        """Test container networking and service communication"""
        logger.info("Testing container networking...")
        
        try:
            # Test database connectivity
            db_test = self._test_database_connection()
            
            # Test Redis connectivity
            redis_test = self._test_redis_connection()
            
            # Test inter-service communication
            service_comm_test = self._test_service_communication()
            
            networking_passed = db_test and redis_test and service_comm_test
            
            self.test_results['container_networking'] = {
                'status': 'passed' if networking_passed else 'failed',
                'database_connection': db_test,
                'redis_connection': redis_test,
                'service_communication': service_comm_test
            }
            
            return networking_passed
            
        except Exception as e:
            logger.error(f"Container networking test failed: {e}")
            self.test_results['container_networking'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
            
    def _test_database_connection(self):
        """Test PostgreSQL database connection"""
        try:
            # Wait for database to be ready
            for attempt in range(10):
                try:
                    conn = psycopg2.connect(
                        host="localhost",
                        port="5433",
                        database="mindcoach_test",
                        user="test_user",
                        password="test_password"
                    )
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    cursor.close()
                    conn.close()
                    
                    logger.info("Database connection test passed")
                    return True
                    
                except psycopg2.OperationalError:
                    if attempt < 9:
                        logger.info(f"Database not ready, attempt {attempt + 1}/10")
                        time.sleep(5)
                    else:
                        raise
                        
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
            
    def _test_redis_connection(self):
        """Test Redis connection"""
        try:
            # Wait for Redis to be ready
            for attempt in range(10):
                try:
                    r = redis.Redis(host='localhost', port=6380, db=0)
                    r.ping()
                    r.set('test_key', 'test_value')
                    value = r.get('test_key')
                    r.delete('test_key')
                    
                    if value.decode() == 'test_value':
                        logger.info("Redis connection test passed")
                        return True
                    else:
                        raise Exception("Redis value mismatch")
                        
                except (redis.ConnectionError, redis.TimeoutError):
                    if attempt < 9:
                        logger.info(f"Redis not ready, attempt {attempt + 1}/10")
                        time.sleep(5)
                    else:
                        raise
                        
        except Exception as e:
            logger.error(f"Redis connection test failed: {e}")
            return False
            
    def _test_service_communication(self):
        """Test communication between services"""
        try:
            # Start backend service
            subprocess.run([
                "docker-compose", "-f", "docker-compose.test.yml",
                "up", "-d", "backend-test"
            ], check=True, capture_output=True)
            
            # Wait for backend to be ready
            time.sleep(30)
            
            # Test API endpoint
            for attempt in range(10):
                try:
                    response = requests.get("http://localhost:5000/api/health", timeout=10)
                    if response.status_code == 200:
                        logger.info("Service communication test passed")
                        return True
                except requests.RequestException:
                    if attempt < 9:
                        logger.info(f"Backend not ready, attempt {attempt + 1}/10")
                        time.sleep(5)
                    else:
                        raise
                        
            return False
            
        except Exception as e:
            logger.error(f"Service communication test failed: {e}")
            return False
            
    def test_data_persistence(self):
        """Test data persistence across container restarts"""
        logger.info("Testing data persistence...")
        
        try:
            # Create test data
            test_data_created = self._create_test_data()
            if not test_data_created:
                return False
                
            # Restart containers
            restart_success = self._restart_containers()
            if not restart_success:
                return False
                
            # Verify data persistence
            data_persisted = self._verify_data_persistence()
            
            self.test_results['data_persistence'] = {
                'status': 'passed' if data_persisted else 'failed',
                'test_data_created': test_data_created,
                'restart_success': restart_success,
                'data_persisted': data_persisted
            }
            
            return data_persisted
            
        except Exception as e:
            logger.error(f"Data persistence test failed: {e}")
            self.test_results['data_persistence'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
            
    def _create_test_data(self):
        """Create test data in database and file system"""
        try:
            # Create database test data
            conn = psycopg2.connect(
                host="localhost",
                port="5433",
                database="mindcoach_test",
                user="test_user",
                password="test_password"
            )
            cursor = conn.cursor()
            
            # Create test user
            cursor.execute("""
                INSERT INTO users (user_id, email) 
                VALUES ('test-persistence-user', 'test@persistence.com')
                ON CONFLICT (user_id) DO NOTHING
            """)
            
            # Create test subscription
            cursor.execute("""
                INSERT INTO subscriptions (user_id, subject, status) 
                VALUES ('test-persistence-user', 'python', 'active')
                ON CONFLICT (user_id, subject) DO NOTHING
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Create file system test data
            user_dir = os.path.join(self.test_users_dir, "test-persistence-user", "python")
            os.makedirs(user_dir, exist_ok=True)
            
            # Create test files
            with open(os.path.join(user_dir, "selection.json"), 'w') as f:
                json.dump({"selected_subject": "python", "selected_at": "2024-01-01T00:00:00Z"}, f)
                
            with open(os.path.join(user_dir, "lesson_1.md"), 'w') as f:
                f.write("# Test Lesson 1\n\nThis is a test lesson for persistence testing.")
                
            logger.info("Test data created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create test data: {e}")
            return False
            
    def _restart_containers(self):
        """Restart containers to test persistence"""
        try:
            logger.info("Restarting containers...")
            
            # Stop containers
            subprocess.run([
                "docker-compose", "-f", "docker-compose.test.yml",
                "stop"
            ], check=True, capture_output=True)
            
            time.sleep(10)
            
            # Start containers again
            subprocess.run([
                "docker-compose", "-f", "docker-compose.test.yml",
                "up", "-d", "test-db", "test-redis"
            ], check=True, capture_output=True)
            
            time.sleep(30)
            
            logger.info("Containers restarted successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restart containers: {e}")
            return False
            
    def _verify_data_persistence(self):
        """Verify that data persisted after restart"""
        try:
            # Check database data
            conn = psycopg2.connect(
                host="localhost",
                port="5433",
                database="mindcoach_test",
                user="test_user",
                password="test_password"
            )
            cursor = conn.cursor()
            
            # Check user exists
            cursor.execute("SELECT user_id FROM users WHERE user_id = 'test-persistence-user'")
            user_result = cursor.fetchone()
            
            # Check subscription exists
            cursor.execute("""
                SELECT user_id, subject FROM subscriptions 
                WHERE user_id = 'test-persistence-user' AND subject = 'python'
            """)
            subscription_result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            # Check file system data
            user_dir = os.path.join(self.test_users_dir, "test-persistence-user", "python")
            selection_file = os.path.join(user_dir, "selection.json")
            lesson_file = os.path.join(user_dir, "lesson_1.md")
            
            files_exist = os.path.exists(selection_file) and os.path.exists(lesson_file)
            
            data_persisted = (user_result is not None and 
                            subscription_result is not None and 
                            files_exist)
            
            if data_persisted:
                logger.info("Data persistence verification passed")
            else:
                logger.error("Data persistence verification failed")
                logger.error(f"User result: {user_result}")
                logger.error(f"Subscription result: {subscription_result}")
                logger.error(f"Files exist: {files_exist}")
                
            return data_persisted
            
        except Exception as e:
            logger.error(f"Failed to verify data persistence: {e}")
            return False
            
    def test_environment_variables(self):
        """Test environment variable configuration and secrets management"""
        logger.info("Testing environment variables...")
        
        try:
            # Start backend with test environment
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.test.yml",
                "run", "--rm", "backend-test",
                "python", "-c", """
import os
import json

env_vars = {
    'FLASK_ENV': os.getenv('FLASK_ENV'),
    'SECRET_KEY': os.getenv('SECRET_KEY'),
    'DATABASE_URL': os.getenv('DATABASE_URL'),
    'REDIS_URL': os.getenv('REDIS_URL'),
    'XAI_API_KEY': os.getenv('XAI_API_KEY'),
    'GROK_API_URL': os.getenv('GROK_API_URL'),
    'LOG_LEVEL': os.getenv('LOG_LEVEL')
}

# Check required variables are set
required_vars = ['FLASK_ENV', 'SECRET_KEY', 'DATABASE_URL', 'REDIS_URL']
missing_vars = [var for var in required_vars if not env_vars[var]]

result = {
    'env_vars': env_vars,
    'missing_vars': missing_vars,
    'all_required_set': len(missing_vars) == 0
}

print(json.dumps(result))
"""
            ], capture_output=True, text=True, check=True)
            
            env_test_result = json.loads(result.stdout.strip())
            
            # Test secrets are not exposed in logs
            secrets_secure = self._test_secrets_security()
            
            env_vars_passed = (env_test_result['all_required_set'] and secrets_secure)
            
            self.test_results['environment_variables'] = {
                'status': 'passed' if env_vars_passed else 'failed',
                'required_vars_set': env_test_result['all_required_set'],
                'missing_vars': env_test_result['missing_vars'],
                'secrets_secure': secrets_secure
            }
            
            logger.info(f"Environment variables test: {'passed' if env_vars_passed else 'failed'}")
            return env_vars_passed
            
        except Exception as e:
            logger.error(f"Environment variables test failed: {e}")
            self.test_results['environment_variables'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
            
    def _test_secrets_security(self):
        """Test that secrets are not exposed in container logs or processes"""
        try:
            # Check container logs don't contain secrets
            containers = self.docker_client.containers.list(
                filters={"label": "com.docker.compose.project=mindcoach"}
            )
            
            for container in containers:
                logs = container.logs().decode('utf-8', errors='ignore')
                
                # Check for common secret patterns
                secret_patterns = [
                    'SECRET_KEY=',
                    'PASSWORD=',
                    'API_KEY=',
                    'test-secret-key',
                    'test_password'
                ]
                
                for pattern in secret_patterns:
                    if pattern in logs:
                        logger.warning(f"Potential secret exposure in {container.name} logs: {pattern}")
                        return False
                        
            logger.info("Secrets security test passed")
            return True
            
        except Exception as e:
            logger.error(f"Secrets security test failed: {e}")
            return False
            
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow in containerized environment"""
        logger.info("Testing end-to-end workflow...")
        
        try:
            # Start full application stack
            subprocess.run([
                "docker-compose", "-f", "docker-compose.test.yml",
                "up", "-d", "backend-test", "test-db", "test-redis", "mock-api"
            ], check=True, capture_output=True)
            
            time.sleep(45)  # Wait for all services to be ready
            
            # Test workflow steps
            workflow_steps = [
                self._test_user_creation(),
                self._test_subject_selection(),
                self._test_survey_generation(),
                self._test_lesson_generation()
            ]
            
            workflow_passed = all(workflow_steps)
            
            self.test_results['end_to_end_workflow'] = {
                'status': 'passed' if workflow_passed else 'failed',
                'user_creation': workflow_steps[0],
                'subject_selection': workflow_steps[1],
                'survey_generation': workflow_steps[2],
                'lesson_generation': workflow_steps[3]
            }
            
            logger.info(f"End-to-end workflow test: {'passed' if workflow_passed else 'failed'}")
            return workflow_passed
            
        except Exception as e:
            logger.error(f"End-to-end workflow test failed: {e}")
            self.test_results['end_to_end_workflow'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
            
    def _test_user_creation(self):
        """Test user creation via API"""
        try:
            response = requests.post(
                "http://localhost:5000/api/users",
                json={"user_id": "test-e2e-user", "email": "test@e2e.com"},
                timeout=10
            )
            
            success = response.status_code in [200, 201]
            if success:
                logger.info("User creation test passed")
            else:
                logger.error(f"User creation failed: {response.status_code} - {response.text}")
                
            return success
            
        except Exception as e:
            logger.error(f"User creation test failed: {e}")
            return False
            
    def _test_subject_selection(self):
        """Test subject selection via API"""
        try:
            response = requests.post(
                "http://localhost:5000/api/users/test-e2e-user/subjects/python/select",
                timeout=10
            )
            
            success = response.status_code in [200, 201]
            if success:
                logger.info("Subject selection test passed")
            else:
                logger.error(f"Subject selection failed: {response.status_code} - {response.text}")
                
            return success
            
        except Exception as e:
            logger.error(f"Subject selection test failed: {e}")
            return False
            
    def _test_survey_generation(self):
        """Test survey generation via API"""
        try:
            response = requests.post(
                "http://localhost:5000/api/users/test-e2e-user/subjects/python/survey/generate",
                timeout=30
            )
            
            success = response.status_code in [200, 201, 202]
            if success:
                logger.info("Survey generation test passed")
            else:
                logger.error(f"Survey generation failed: {response.status_code} - {response.text}")
                
            return success
            
        except Exception as e:
            logger.error(f"Survey generation test failed: {e}")
            return False
            
    def _test_lesson_generation(self):
        """Test lesson generation via API"""
        try:
            # First submit survey answers
            survey_answers = {
                "answers": [
                    {"question_id": 1, "answer": "A", "correct": True},
                    {"question_id": 2, "answer": "B", "correct": False}
                ]
            }
            
            response = requests.post(
                "http://localhost:5000/api/users/test-e2e-user/subjects/python/survey/submit",
                json=survey_answers,
                timeout=10
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"Survey submission failed: {response.status_code}")
                return False
                
            # Then test lesson generation
            response = requests.post(
                "http://localhost:5000/api/users/test-e2e-user/subjects/python/content/generate",
                timeout=60
            )
            
            success = response.status_code in [200, 201, 202]
            if success:
                logger.info("Lesson generation test passed")
            else:
                logger.error(f"Lesson generation failed: {response.status_code} - {response.text}")
                
            return success
            
        except Exception as e:
            logger.error(f"Lesson generation test failed: {e}")
            return False
            
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("Generating test report...")
        
        test_duration = datetime.now() - self.test_start_time
        
        report = {
            'test_summary': {
                'start_time': self.test_start_time.isoformat(),
                'duration_seconds': test_duration.total_seconds(),
                'total_tests': len(self.test_results),
                'passed_tests': len([r for r in self.test_results.values() if r['status'] == 'passed']),
                'failed_tests': len([r for r in self.test_results.values() if r['status'] == 'failed'])
            },
            'test_results': self.test_results,
            'environment': {
                'docker_version': self._get_docker_version(),
                'compose_version': self._get_compose_version(),
                'python_version': sys.version,
                'test_data_dir': self.test_data_dir,
                'test_users_dir': self.test_users_dir
            }
        }
        
        # Write JSON report
        with open('docker_system_test_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        # Write markdown report
        self._write_markdown_report(report)
        
        logger.info("Test report generated: docker_system_test_report.json")
        logger.info("Markdown report generated: docker_system_test_report.md")
        
        return report
        
    def _get_docker_version(self):
        """Get Docker version"""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return "Unknown"
            
    def _get_compose_version(self):
        """Get Docker Compose version"""
        try:
            result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return "Unknown"
            
    def _write_markdown_report(self, report):
        """Write markdown test report"""
        with open('docker_system_test_report.md', 'w') as f:
            f.write("# Docker Containerized System Test Report\n\n")
            
            # Summary
            f.write("## Test Summary\n\n")
            f.write(f"- **Start Time**: {report['test_summary']['start_time']}\n")
            f.write(f"- **Duration**: {report['test_summary']['duration_seconds']:.2f} seconds\n")
            f.write(f"- **Total Tests**: {report['test_summary']['total_tests']}\n")
            f.write(f"- **Passed**: {report['test_summary']['passed_tests']}\n")
            f.write(f"- **Failed**: {report['test_summary']['failed_tests']}\n\n")
            
            # Test Results
            f.write("## Test Results\n\n")
            for test_name, result in report['test_results'].items():
                status_icon = "✅" if result['status'] == 'passed' else "❌"
                f.write(f"### {status_icon} {test_name.replace('_', ' ').title()}\n\n")
                f.write(f"**Status**: {result['status'].upper()}\n\n")
                
                if 'error' in result:
                    f.write(f"**Error**: {result['error']}\n\n")
                else:
                    for key, value in result.items():
                        if key != 'status':
                            f.write(f"- **{key.replace('_', ' ').title()}**: {value}\n")
                    f.write("\n")
                    
            # Environment
            f.write("## Environment Information\n\n")
            f.write(f"- **Docker Version**: {report['environment']['docker_version']}\n")
            f.write(f"- **Docker Compose Version**: {report['environment']['compose_version']}\n")
            f.write(f"- **Python Version**: {report['environment']['python_version']}\n")
            f.write(f"- **Test Data Directory**: {report['environment']['test_data_dir']}\n")
            f.write(f"- **Test Users Directory**: {report['environment']['test_users_dir']}\n\n")
            
    def run_all_tests(self):
        """Run all containerized system tests"""
        logger.info("Starting comprehensive Docker containerized system tests...")
        
        try:
            self.setup_test_environment()
            
            # Run all tests
            tests = [
                ('container_startup', self.test_container_startup),
                ('container_networking', self.test_container_networking),
                ('data_persistence', self.test_data_persistence),
                ('environment_variables', self.test_environment_variables),
                ('end_to_end_workflow', self.test_end_to_end_workflow)
            ]
            
            for test_name, test_func in tests:
                logger.info(f"Running {test_name} test...")
                try:
                    test_func()
                except Exception as e:
                    logger.error(f"Test {test_name} failed with exception: {e}")
                    self.test_results[test_name] = {
                        'status': 'failed',
                        'error': str(e)
                    }
                    
            # Generate report
            report = self.generate_test_report()
            
            # Print summary
            passed = report['test_summary']['passed_tests']
            total = report['test_summary']['total_tests']
            
            if passed == total:
                logger.info(f"🎉 All tests passed! ({passed}/{total})")
                return True
            else:
                logger.error(f"❌ {total - passed} tests failed. ({passed}/{total} passed)")
                return False
                
        finally:
            self.cleanup_test_environment()


def main():
    """Main test execution function"""
    tester = DockerSystemTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test execution interrupted by user")
        tester.cleanup_test_environment()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        tester.cleanup_test_environment()
        sys.exit(1)


if __name__ == "__main__":
    main()