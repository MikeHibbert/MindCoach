#!/usr/bin/env python3
"""
Docker System Validation Script
Validates the containerized system functionality with proper error handling
"""

import os
import sys
import time
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
import logging
from datetime import datetime

# Configure logging without Unicode characters for Windows compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('docker_validation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DockerSystemValidator:
    """Validates Docker containerized system functionality"""
    
    def __init__(self):
        self.test_results = {}
        self.temp_dirs = []
        self.test_start_time = datetime.now()
        
    def setup_test_environment(self):
        """Set up test environment"""
        logger.info("Setting up test environment...")
        
        # Create temporary directories for test data
        self.test_data_dir = tempfile.mkdtemp(prefix="docker_validation_")
        self.temp_dirs.append(self.test_data_dir)
        
        logger.info(f"Test data directory: {self.test_data_dir}")
        
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
            ], check=False, capture_output=True, shell=True, timeout=60)
        except Exception as e:
            logger.warning(f"Error during container cleanup: {e}")
            
        logger.info("Test environment cleanup completed")
        
    def validate_docker_environment(self):
        """Validate Docker environment is ready"""
        logger.info("Validating Docker environment...")
        
        try:
            # Check Docker is running
            result = subprocess.run([
                "docker", "info"
            ], capture_output=True, text=True, shell=True, timeout=30)
            
            if result.returncode != 0:
                logger.error("Docker daemon is not running")
                return False
                
            # Check Docker Compose is available
            result = subprocess.run([
                "docker-compose", "--version"
            ], capture_output=True, text=True, shell=True, timeout=30)
            
            if result.returncode != 0:
                logger.error("Docker Compose is not available")
                return False
                
            logger.info("Docker environment validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Docker environment validation failed: {e}")
            return False        
    
    def validate_container_startup(self):
        """Validate that containers start successfully"""
        logger.info("Validating container startup...")
        
        try:
            # Start test infrastructure
            logger.info("Starting test containers...")
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.test.yml",
                "up", "-d", "test-db", "test-redis", "mock-api"
            ], capture_output=True, text=True, shell=True, timeout=120)
            
            if result.returncode != 0:
                logger.error(f"Failed to start containers: {result.stderr}")
                return False
                
            # Wait for services to be ready
            logger.info("Waiting for services to be ready...")
            time.sleep(45)
            
            # Check container status
            result = subprocess.run([
                "docker", "ps", "--filter", "name=mindcoach-test", "--format", "{{.Names}}\t{{.Status}}"
            ], capture_output=True, text=True, shell=True, timeout=30)
            
            if result.returncode != 0:
                logger.error("Failed to check container status")
                return False
                
            running_containers = result.stdout.count("Up")
            logger.info(f"Found {running_containers} running containers")
            
            self.test_results['container_startup'] = {
                'status': 'passed' if running_containers >= 3 else 'failed',
                'running_containers': running_containers,
                'container_details': result.stdout
            }
            
            return running_containers >= 3
            
        except Exception as e:
            logger.error(f"Container startup validation failed: {e}")
            self.test_results['container_startup'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
            
    def validate_database_connectivity(self):
        """Validate database connectivity and basic operations"""
        logger.info("Validating database connectivity...")
        
        try:
            # Test database connection
            for attempt in range(10):
                result = subprocess.run([
                    "docker", "exec", "mindcoach-test-db", 
                    "pg_isready", "-U", "test_user", "-d", "mindcoach_test"
                ], capture_output=True, text=True, shell=True, timeout=30)
                
                if result.returncode == 0:
                    logger.info("Database connection successful")
                    break
                    
                if attempt < 9:
                    logger.info(f"Database not ready, attempt {attempt + 1}/10")
                    time.sleep(5)
                else:
                    logger.error("Database connection failed after 10 attempts")
                    return False
                    
            # Test basic database operations
            logger.info("Testing basic database operations...")
            
            # Create a test table
            result = subprocess.run([
                "docker", "exec", "mindcoach-test-db",
                "psql", "-U", "test_user", "-d", "mindcoach_test", "-c",
                "CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, name VARCHAR(100));"
            ], capture_output=True, text=True, shell=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"Failed to create test table: {result.stderr}")
                return False
                
            # Insert test data
            result = subprocess.run([
                "docker", "exec", "mindcoach-test-db",
                "psql", "-U", "test_user", "-d", "mindcoach_test", "-c",
                "INSERT INTO test_table (name) VALUES ('test_data');"
            ], capture_output=True, text=True, shell=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"Failed to insert test data: {result.stderr}")
                return False
                
            # Query test data
            result = subprocess.run([
                "docker", "exec", "mindcoach-test-db",
                "psql", "-U", "test_user", "-d", "mindcoach_test", "-t", "-c",
                "SELECT name FROM test_table WHERE name = 'test_data';"
            ], capture_output=True, text=True, shell=True, timeout=30)
            
            if result.returncode != 0 or "test_data" not in result.stdout:
                logger.error("Failed to query test data")
                return False
                
            logger.info("Database connectivity validation passed")
            self.test_results['database_connectivity'] = {
                'status': 'passed',
                'connection_test': True,
                'basic_operations': True
            }
            return True
            
        except Exception as e:
            logger.error(f"Database connectivity validation failed: {e}")
            self.test_results['database_connectivity'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False 
           
    def validate_redis_connectivity(self):
        """Validate Redis connectivity and basic operations"""
        logger.info("Validating Redis connectivity...")
        
        try:
            # Test Redis connection
            for attempt in range(10):
                result = subprocess.run([
                    "docker", "exec", "mindcoach-test-redis", 
                    "redis-cli", "ping"
                ], capture_output=True, text=True, shell=True, timeout=30)
                
                if result.returncode == 0 and "PONG" in result.stdout:
                    logger.info("Redis connection successful")
                    break
                    
                if attempt < 9:
                    logger.info(f"Redis not ready, attempt {attempt + 1}/10")
                    time.sleep(5)
                else:
                    logger.error("Redis connection failed after 10 attempts")
                    return False
                    
            # Test basic Redis operations
            logger.info("Testing basic Redis operations...")
            
            # Set a test key
            result = subprocess.run([
                "docker", "exec", "mindcoach-test-redis",
                "redis-cli", "set", "test_key", "test_value"
            ], capture_output=True, text=True, shell=True, timeout=30)
            
            if result.returncode != 0:
                logger.error("Failed to set Redis key")
                return False
                
            # Get the test key
            result = subprocess.run([
                "docker", "exec", "mindcoach-test-redis",
                "redis-cli", "get", "test_key"
            ], capture_output=True, text=True, shell=True, timeout=30)
            
            if result.returncode != 0 or "test_value" not in result.stdout:
                logger.error("Failed to get Redis key")
                return False
                
            # Delete the test key
            result = subprocess.run([
                "docker", "exec", "mindcoach-test-redis",
                "redis-cli", "del", "test_key"
            ], capture_output=True, text=True, shell=True, timeout=30)
            
            if result.returncode != 0:
                logger.error("Failed to delete Redis key")
                return False
                
            logger.info("Redis connectivity validation passed")
            self.test_results['redis_connectivity'] = {
                'status': 'passed',
                'connection_test': True,
                'basic_operations': True
            }
            return True
            
        except Exception as e:
            logger.error(f"Redis connectivity validation failed: {e}")
            self.test_results['redis_connectivity'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
            
    def validate_data_persistence(self):
        """Validate data persistence across container restarts"""
        logger.info("Validating data persistence...")
        
        try:
            # Create persistent test data
            logger.info("Creating persistent test data...")
            
            # Create database data
            result = subprocess.run([
                "docker", "exec", "mindcoach-test-db",
                "psql", "-U", "test_user", "-d", "mindcoach_test", "-c",
                "CREATE TABLE IF NOT EXISTS persistence_test (id SERIAL PRIMARY KEY, data VARCHAR(100)); INSERT INTO persistence_test (data) VALUES ('persistent_data');"
            ], capture_output=True, text=True, shell=True, timeout=30)
            
            if result.returncode != 0:
                logger.error("Failed to create persistent database data")
                return False
                
            # Create Redis data
            result = subprocess.run([
                "docker", "exec", "mindcoach-test-redis",
                "redis-cli", "set", "persistent_key", "persistent_value"
            ], capture_output=True, text=True, shell=True, timeout=30)
            
            if result.returncode != 0:
                logger.error("Failed to create persistent Redis data")
                return False
                
            # Restart containers
            logger.info("Restarting containers to test persistence...")
            
            subprocess.run([
                "docker-compose", "-f", "docker-compose.test.yml",
                "restart", "test-db", "test-redis"
            ], capture_output=True, shell=True, timeout=60)
            
            # Wait for services to be ready after restart
            time.sleep(30)
            
            # Verify database data persistence
            result = subprocess.run([
                "docker", "exec", "mindcoach-test-db",
                "psql", "-U", "test_user", "-d", "mindcoach_test", "-t", "-c",
                "SELECT data FROM persistence_test WHERE data = 'persistent_data';"
            ], capture_output=True, text=True, shell=True, timeout=30)
            
            db_data_persisted = result.returncode == 0 and "persistent_data" in result.stdout
            
            # Verify Redis data persistence
            result = subprocess.run([
                "docker", "exec", "mindcoach-test-redis",
                "redis-cli", "get", "persistent_key"
            ], capture_output=True, text=True, shell=True, timeout=30)
            
            redis_data_persisted = result.returncode == 0 and "persistent_value" in result.stdout
            
            persistence_passed = db_data_persisted and redis_data_persisted
            
            if persistence_passed:
                logger.info("Data persistence validation passed")
            else:
                logger.error(f"Data persistence validation failed - DB: {db_data_persisted}, Redis: {redis_data_persisted}")
                
            self.test_results['data_persistence'] = {
                'status': 'passed' if persistence_passed else 'failed',
                'database_persistence': db_data_persisted,
                'redis_persistence': redis_data_persisted
            }
            
            return persistence_passed
            
        except Exception as e:
            logger.error(f"Data persistence validation failed: {e}")
            self.test_results['data_persistence'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False     
       
    def validate_container_networking(self):
        """Validate container networking and inter-service communication"""
        logger.info("Validating container networking...")
        
        try:
            # Test network connectivity between containers
            logger.info("Testing network connectivity between containers...")
            
            # Test database connectivity from Redis container
            result = subprocess.run([
                "docker", "exec", "mindcoach-test-redis",
                "nc", "-z", "test-db", "5432"
            ], capture_output=True, text=True, shell=True, timeout=30)
            
            db_network_test = result.returncode == 0
            
            # Test Redis connectivity from database container
            result = subprocess.run([
                "docker", "exec", "mindcoach-test-db",
                "nc", "-z", "test-redis", "6379"
            ], capture_output=True, text=True, shell=True, timeout=30)
            
            redis_network_test = result.returncode == 0
            
            # Test mock API connectivity
            result = subprocess.run([
                "docker", "exec", "mindcoach-test-redis",
                "nc", "-z", "mock-api", "8080"
            ], capture_output=True, text=True, shell=True, timeout=30)
            
            api_network_test = result.returncode == 0
            
            networking_passed = db_network_test and redis_network_test and api_network_test
            
            if networking_passed:
                logger.info("Container networking validation passed")
            else:
                logger.error(f"Container networking validation failed - DB: {db_network_test}, Redis: {redis_network_test}, API: {api_network_test}")
                
            self.test_results['container_networking'] = {
                'status': 'passed' if networking_passed else 'failed',
                'database_network': db_network_test,
                'redis_network': redis_network_test,
                'api_network': api_network_test
            }
            
            return networking_passed
            
        except Exception as e:
            logger.error(f"Container networking validation failed: {e}")
            self.test_results['container_networking'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
            
    def validate_environment_configuration(self):
        """Validate environment variable configuration"""
        logger.info("Validating environment configuration...")
        
        try:
            # Check environment variables in test database
            result = subprocess.run([
                "docker", "exec", "mindcoach-test-db",
                "env"
            ], capture_output=True, text=True, shell=True, timeout=30)
            
            if result.returncode != 0:
                logger.error("Failed to check database environment variables")
                return False
                
            db_env_vars = result.stdout
            required_db_vars = ["POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]
            db_vars_present = all(var in db_env_vars for var in required_db_vars)
            
            # Check environment variables in Redis
            result = subprocess.run([
                "docker", "exec", "mindcoach-test-redis",
                "env"
            ], capture_output=True, text=True, shell=True, timeout=30)
            
            redis_env_check = result.returncode == 0
            
            # Check that secrets are not exposed in container processes
            result = subprocess.run([
                "docker", "exec", "mindcoach-test-db",
                "ps", "aux"
            ], capture_output=True, text=True, shell=True, timeout=30)
            
            # Check that password is not visible in process list
            secrets_secure = "test_password" not in result.stdout
            
            env_config_passed = db_vars_present and redis_env_check and secrets_secure
            
            if env_config_passed:
                logger.info("Environment configuration validation passed")
            else:
                logger.error(f"Environment configuration validation failed - DB vars: {db_vars_present}, Redis: {redis_env_check}, Secrets: {secrets_secure}")
                
            self.test_results['environment_configuration'] = {
                'status': 'passed' if env_config_passed else 'failed',
                'database_env_vars': db_vars_present,
                'redis_env_check': redis_env_check,
                'secrets_secure': secrets_secure
            }
            
            return env_config_passed
            
        except Exception as e:
            logger.error(f"Environment configuration validation failed: {e}")
            self.test_results['environment_configuration'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False       
     
    def generate_validation_report(self):
        """Generate comprehensive validation report"""
        logger.info("Generating validation report...")
        
        test_duration = datetime.now() - self.test_start_time
        
        report = {
            'validation_summary': {
                'start_time': self.test_start_time.isoformat(),
                'duration_seconds': test_duration.total_seconds(),
                'total_validations': len(self.test_results),
                'passed_validations': len([r for r in self.test_results.values() if r['status'] == 'passed']),
                'failed_validations': len([r for r in self.test_results.values() if r['status'] == 'failed'])
            },
            'validation_results': self.test_results,
            'environment': {
                'docker_version': self._get_docker_version(),
                'compose_version': self._get_compose_version(),
                'python_version': sys.version,
                'test_data_dir': self.test_data_dir
            },
            'recommendations': self._generate_recommendations()
        }
        
        # Write JSON report
        with open('docker_validation_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
            
        # Write markdown report
        self._write_markdown_report(report)
        
        logger.info("Validation report generated: docker_validation_report.json")
        logger.info("Markdown report generated: docker_validation_report.md")
        
        return report
        
    def _get_docker_version(self):
        """Get Docker version"""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True, shell=True)
            return result.stdout.strip()
        except:
            return "Unknown"
            
    def _get_compose_version(self):
        """Get Docker Compose version"""
        try:
            result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True, shell=True)
            return result.stdout.strip()
        except:
            return "Unknown"
            
    def _generate_recommendations(self):
        """Generate recommendations based on validation results"""
        recommendations = []
        
        for test_name, result in self.test_results.items():
            if result['status'] == 'failed':
                if test_name == 'container_startup':
                    recommendations.append("Check Docker daemon status and container resource limits")
                elif test_name == 'database_connectivity':
                    recommendations.append("Verify database configuration and network connectivity")
                elif test_name == 'redis_connectivity':
                    recommendations.append("Check Redis configuration and memory limits")
                elif test_name == 'data_persistence':
                    recommendations.append("Verify volume mounts and storage configuration")
                elif test_name == 'container_networking':
                    recommendations.append("Check Docker network configuration and firewall settings")
                elif test_name == 'environment_configuration':
                    recommendations.append("Review environment variable configuration and secrets management")
                    
        if not recommendations:
            recommendations.append("All validations passed - system is ready for deployment")
            
        return recommendations
        
    def _write_markdown_report(self, report):
        """Write markdown validation report"""
        with open('docker_validation_report.md', 'w', encoding='utf-8') as f:
            f.write("# Docker Containerized System Validation Report\n\n")
            
            # Summary
            f.write("## Validation Summary\n\n")
            f.write(f"- **Start Time**: {report['validation_summary']['start_time']}\n")
            f.write(f"- **Duration**: {report['validation_summary']['duration_seconds']:.2f} seconds\n")
            f.write(f"- **Total Validations**: {report['validation_summary']['total_validations']}\n")
            f.write(f"- **Passed**: {report['validation_summary']['passed_validations']}\n")
            f.write(f"- **Failed**: {report['validation_summary']['failed_validations']}\n\n")
            
            # Validation Results
            f.write("## Validation Results\n\n")
            for test_name, result in report['validation_results'].items():
                status_icon = "PASS" if result['status'] == 'passed' else "FAIL"
                f.write(f"### [{status_icon}] {test_name.replace('_', ' ').title()}\n\n")
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
            f.write(f"- **Test Data Directory**: {report['environment']['test_data_dir']}\n\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            for i, recommendation in enumerate(report['recommendations'], 1):
                f.write(f"{i}. {recommendation}\n")
            f.write("\n")     
       
    def run_all_validations(self):
        """Run all containerized system validations"""
        logger.info("Starting comprehensive Docker containerized system validation...")
        
        self.setup_test_environment()
        
        try:
            # Check Docker environment first
            if not self.validate_docker_environment():
                logger.error("Docker environment validation failed - cannot proceed")
                return False
                
            # Run all validations
            validations = [
                ('container_startup', self.validate_container_startup),
                ('database_connectivity', self.validate_database_connectivity),
                ('redis_connectivity', self.validate_redis_connectivity),
                ('data_persistence', self.validate_data_persistence),
                ('container_networking', self.validate_container_networking),
                ('environment_configuration', self.validate_environment_configuration)
            ]
            
            passed_validations = 0
            total_validations = len(validations)
            
            for validation_name, validation_func in validations:
                logger.info(f"Running {validation_name} validation...")
                try:
                    if validation_func():
                        passed_validations += 1
                        logger.info(f"[PASS] {validation_name} validation PASSED")
                    else:
                        logger.error(f"[FAIL] {validation_name} validation FAILED")
                except Exception as e:
                    logger.error(f"[FAIL] {validation_name} validation FAILED with exception: {e}")
                    
            # Generate report
            report = self.generate_validation_report()
            
            # Print summary
            logger.info(f"\nDocker System Validation Summary:")
            logger.info(f"Total Validations: {total_validations}")
            logger.info(f"Passed: {passed_validations}")
            logger.info(f"Failed: {total_validations - passed_validations}")
            
            if passed_validations == total_validations:
                logger.info("All validations passed! System is ready for deployment.")
                return True
            else:
                logger.error("Some validations failed. Check the reports for details.")
                return False
                
        finally:
            self.cleanup_test_environment()

if __name__ == "__main__":
    validator = DockerSystemValidator()
    success = validator.run_all_validations()
    sys.exit(0 if success else 1)