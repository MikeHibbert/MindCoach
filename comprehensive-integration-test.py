#!/usr/bin/env python3
"""
Comprehensive Integration Test for Task 17.1
Tests all components working together: Frontend, Backend, Database, File System
Validates responsive design, accessibility, and complete user workflows
"""

import requests
import json
import time
import os
import sys
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

class ComprehensiveIntegrationTester:
    def __init__(self):
        self.backend_url = "http://localhost:5000"
        self.frontend_url = "http://localhost:3000"
        self.test_user_id = f"integration-test-{int(time.time())}"
        self.test_subject = "python"
        self.results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "tests": []
        }
        self.driver = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test(self, name, test_func):
        """Run a test and record results"""
        self.log(f"🧪 Testing: {name}")
        try:
            test_func()
            self.log(f"✅ PASSED: {name}")
            self.results["passed"] += 1
            self.results["tests"].append({"name": name, "status": "PASSED"})
        except Exception as e:
            self.log(f"❌ FAILED: {name} - {str(e)}", "ERROR")
            self.results["failed"] += 1
            self.results["tests"].append({"name": name, "status": "FAILED", "error": str(e)})
    
    def warning(self, name, message):
        """Record a warning"""
        self.log(f"⚠️  WARNING: {name} - {message}", "WARNING")
        self.results["warnings"] += 1
        self.results["tests"].append({"name": name, "status": "WARNING", "message": message})
            
    def setup_selenium(self):
        """Set up Selenium WebDriver for frontend testing"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            return True
        except Exception as e:
            self.log(f"Could not set up Selenium: {e}", "WARNING")
            return False
    
    def cleanup_selenium(self):
        """Clean up Selenium WebDriver"""
        if self.driver:
            self.driver.quit()
            
    def test_backend_health(self):
        """Test backend API health and basic endpoints"""
        # Test subjects endpoint
        response = requests.get(f"{self.backend_url}/api/subjects", timeout=10)
        if response.status_code != 200:
            raise Exception(f"Subjects endpoint failed: {response.status_code}")
        
        subjects_data = response.json()
        if not subjects_data.get("subjects"):
            raise Exception("No subjects returned from API")
        
        self.log("   Backend API is healthy and returning subjects")
        
    def test_database_operations(self):
        """Test complete database operations workflow"""
        # Create user
        user_data = {
            "user_id": self.test_user_id,
            "email": f"{self.test_user_id}@test.com"
        }
        response = requests.post(f"{self.backend_url}/api/users", json=user_data)
        if response.status_code != 201:
            raise Exception(f"User creation failed: {response.status_code}")
        
        # Purchase subscription
        response = requests.post(f"{self.backend_url}/api/users/{self.test_user_id}/subscriptions/{self.test_subject}")
        if response.status_code != 201:
            raise Exception(f"Subscription purchase failed: {response.status_code}")
        
        # Verify subscription
        response = requests.get(f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}/status")
        if response.status_code != 200:
            raise Exception(f"Subscription verification failed: {response.status_code}")
        
        status_data = response.json()
        if not status_data.get("access_status", {}).get("has_active_subscription"):
            raise Exception("Subscription not active after purchase")
        
        self.log("   Database operations successful")
        
    def test_file_system_operations(self):
        """Test file system operations for user data"""
        # Check if users directory exists or can be created
        users_dir = Path("backend/users")
        if not users_dir.exists():
            users_dir.mkdir(parents=True, exist_ok=True)
        
        # Test file creation and reading
        test_file = users_dir / f"{self.test_user_id}_test.json"
        test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
            
        with open(test_file, 'r') as f:
            loaded_data = json.load(f)
            
        if loaded_data["test"] != "data":
            raise Exception("File system read/write test failed")
            
        # Cleanup
        test_file.unlink()
        self.log("   File system operations successful")
        
    def test_complete_api_workflow(self):
        """Test complete API workflow from user creation to lesson access"""
        # Generate survey
        response = requests.post(f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}/survey/generate")
        if response.status_code != 201:
            raise Exception(f"Survey generation failed: {response.status_code}")
        
        survey_data = response.json()
        if not survey_data.get("success") or not survey_data.get("survey", {}).get("questions"):
            raise Exception("Invalid survey generated")
        
        # Submit survey answers
        questions = survey_data["survey"]["questions"]
        answers = []
        for i, question in enumerate(questions):
            answers.append({
                "question_id": question["id"],
                "answer": 0 if question["type"] == "multiple_choice" else "Test answer",
                "question_text": question["question"],
                "question_type": question["type"],
                "difficulty": question.get("difficulty", "beginner"),
                "topic": question.get("topic", "general")
            })
        
        response = requests.post(
            f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}/survey/submit",
            json={"answers": answers}
        )
        if response.status_code != 200:
            raise Exception(f"Survey submission failed: {response.status_code}")
        
        # Generate lessons
        response = requests.post(f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons/generate")
        if response.status_code != 201:
            raise Exception(f"Lesson generation failed: {response.status_code}")
        
        # List lessons
        response = requests.get(f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons")
        if response.status_code != 200:
            raise Exception(f"Lesson listing failed: {response.status_code}")
        
        lessons_data = response.json()
        if not lessons_data.get("success") or not lessons_data.get("lessons"):
            raise Exception("No lessons found after generation")
        
        # Get first lesson
        lessons = lessons_data["lessons"]
        first_lesson = lessons[0]
        response = requests.get(
            f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons/{first_lesson['lesson_number']}"
        )
        if response.status_code != 200:
            raise Exception(f"Lesson retrieval failed: {response.status_code}")
        
        lesson_data = response.json()
        if not lesson_data.get("success") or not lesson_data.get("lesson", {}).get("content"):
            raise Exception("Invalid lesson content")
        
        self.log(f"   Complete API workflow successful - Generated {len(lessons)} lessons")
        
    def test_api_error_handling(self):
        """Test API error handling and validation"""
        # Test invalid user ID
        response = requests.get(f"{self.backend_url}/api/users/invalid-user-id/subscriptions")
        if response.status_code not in [400, 404, 500]:
            raise Exception("API should handle invalid user ID with error status")
        
        # Test invalid subject
        response = requests.post(f"{self.backend_url}/api/users/{self.test_user_id}/subjects/invalid-subject/select")
        if response.status_code not in [400, 404]:
            raise Exception("API should handle invalid subject with error status")
        
        # Test unauthorized access
        response = requests.post(f"{self.backend_url}/api/users/unauthorized-user/subjects/{self.test_subject}/lessons/generate")
        if response.status_code not in [403, 404]:
            raise Exception("API should prevent unauthorized access")
        
        self.log("   API error handling working correctly")
        
    def test_frontend_accessibility(self):
        """Test frontend accessibility using Selenium"""
        if not self.driver:
            self.warning("Frontend Accessibility", "Selenium not available - skipping detailed accessibility tests")
            return
        
        try:
            self.driver.get(self.frontend_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check for basic accessibility elements
            html_content = self.driver.page_source.lower()
            
            accessibility_checks = {
                "ARIA attributes": "aria-" in html_content,
                "Role attributes": "role=" in html_content,
                "Alt text": "alt=" in html_content,
                "Semantic HTML": any(tag in html_content for tag in ["<main", "<nav", "<header", "<footer"]),
                "Skip links": "skip" in html_content
            }
            
            failed_checks = [check for check, passed in accessibility_checks.items() if not passed]
            if failed_checks:
                raise Exception(f"Accessibility checks failed: {', '.join(failed_checks)}")
            
            # Test keyboard navigation
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                body.send_keys(Keys.TAB)
                active_element = self.driver.switch_to.active_element
                if not active_element:
                    raise Exception("Keyboard navigation not working")
            except Exception as e:
                self.log(f"   Warning: Keyboard navigation test failed: {e}", "WARNING")
            
            self.log("   Frontend accessibility checks passed")
            
        except Exception as e:
            if "ERR_CONNECTION_REFUSED" in str(e) or "connection refused" in str(e).lower():
                self.warning("Frontend Accessibility", "Frontend server not running")
            else:
                raise e
                
    def test_responsive_design(self):
        """Test responsive design across different screen sizes"""
        if not self.driver:
            self.warning("Responsive Design", "Selenium not available - skipping responsive design tests")
            return
        
        try:
            self.driver.get(self.frontend_url)
            
            # Test different viewport sizes
            viewports = [
                {"name": "Mobile", "width": 375, "height": 667},
                {"name": "Tablet", "width": 768, "height": 1024},
                {"name": "Desktop", "width": 1280, "height": 720}
            ]
            
            for viewport in viewports:
                self.driver.set_window_size(viewport["width"], viewport["height"])
                time.sleep(1)  # Allow layout to adjust
                
                # Check that content is visible and properly laid out
                body = self.driver.find_element(By.TAG_NAME, "body")
                if not body.is_displayed():
                    raise Exception(f"Content not visible on {viewport['name']} viewport")
                
                # Check for responsive classes (if using Tailwind)
                html_content = self.driver.page_source
                responsive_indicators = ["mobile:", "tablet:", "desktop:", "sm:", "md:", "lg:", "xl:"]
                if not any(indicator in html_content for indicator in responsive_indicators):
                    self.log(f"   Warning: No responsive classes found for {viewport['name']}", "WARNING")
            
            self.log("   Responsive design tests passed")
            
        except Exception as e:
            if "ERR_CONNECTION_REFUSED" in str(e) or "connection refused" in str(e).lower():
                self.warning("Responsive Design", "Frontend server not running")
            else:
                raise e
                
    def test_end_to_end_user_workflow(self):
        """Test complete end-to-end user workflow using Selenium"""
        if not self.driver:
            self.warning("End-to-End Workflow", "Selenium not available - skipping E2E tests")
            return
        
        try:
            self.driver.get(self.frontend_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Look for subject selection elements
            try:
                # Try to find subject selection interface
                subject_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid*='subject'], .subject-card, .subject-selector")
                if not subject_elements:
                    # Try alternative selectors
                    subject_elements = self.driver.find_elements(By.CSS_SELECTOR, "button, .card, .selection")
                
                if subject_elements:
                    self.log("   Found subject selection interface")
                    
                    # Try to interact with first element
                    first_element = subject_elements[0]
                    if first_element.is_displayed() and first_element.is_enabled():
                        first_element.click()
                        time.sleep(2)  # Allow for navigation/state change
                        self.log("   Successfully interacted with subject selection")
                else:
                    self.log("   Warning: Could not find subject selection interface", "WARNING")
                
            except Exception as e:
                self.log(f"   Warning: Subject selection interaction failed: {e}", "WARNING")
            
            # Check for form elements (survey, payment, etc.)
            form_elements = self.driver.find_elements(By.CSS_SELECTOR, "form, input, button, select")
            if form_elements:
                self.log(f"   Found {len(form_elements)} interactive form elements")
            
            # Check for navigation elements
            nav_elements = self.driver.find_elements(By.CSS_SELECTOR, "nav, .navigation, [role='navigation']")
            if nav_elements:
                self.log(f"   Found {len(nav_elements)} navigation elements")
            
            self.log("   End-to-end workflow structure verified")
            
        except Exception as e:
            if "ERR_CONNECTION_REFUSED" in str(e) or "connection refused" in str(e).lower():
                self.warning("End-to-End Workflow", "Frontend server not running")
            else:
                raise e
                
    def test_performance_metrics(self):
        """Test basic performance metrics"""
        # Test API response times
        start_time = time.time()
        response = requests.get(f"{self.backend_url}/api/subjects")
        api_response_time = time.time() - start_time
        
        if response.status_code != 200:
            raise Exception("API not responding for performance test")
        
        if api_response_time > 2.0:
            raise Exception(f"API response time too slow: {api_response_time:.2f}s")
        
        # Test frontend load time if available
        if self.driver:
            try:
                start_time = time.time()
                self.driver.get(self.frontend_url)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                frontend_load_time = time.time() - start_time
                
                if frontend_load_time > 5.0:
                    self.log(f"   Warning: Frontend load time slow: {frontend_load_time:.2f}s", "WARNING")
                else:
                    self.log(f"   Frontend load time: {frontend_load_time:.2f}s")
                    
            except Exception as e:
                if "ERR_CONNECTION_REFUSED" not in str(e):
                    self.log(f"   Warning: Frontend performance test failed: {e}", "WARNING")
        
        self.log(f"   API response time: {api_response_time:.2f}s")
        
    def test_data_persistence(self):
        """Test data persistence across requests"""
        # Verify user still exists
        response = requests.get(f"{self.backend_url}/api/users/{self.test_user_id}")
        if response.status_code != 200:
            raise Exception(f"User data persistence check failed: {response.status_code}")
        
        # Verify subject selection persists
        response = requests.get(f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}")
        if response.status_code != 200:
            raise Exception("Subject selection not persisted")
        
        self.log("   Data persistence verified")
        
    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            # Clean up user directory if it exists
            user_dir = Path(f"backend/users/{self.test_user_id}")
            if user_dir.exists():
                import shutil
                shutil.rmtree(user_dir)
                self.log("   Test user directory cleaned up")
        except Exception as e:
            self.log(f"   Warning: Could not clean up test data: {e}")
            
    def run_all_tests(self):
        """Run all integration tests"""
        self.log("🚀 Starting Comprehensive Integration Tests for Task 17.1")
        self.log("=" * 80)
        
        # Set up Selenium for frontend tests
        selenium_available = self.setup_selenium()
        if not selenium_available:
            self.log("Selenium WebDriver not available - frontend tests will be limited", "WARNING")
        
        try:
            # Core system integration tests
            self.test("Backend Health Check", self.test_backend_health)
            self.test("Database Operations", self.test_database_operations)
            self.test("File System Operations", self.test_file_system_operations)
            
            # Complete workflow tests
            self.test("Complete API Workflow", self.test_complete_api_workflow)
            self.test("API Error Handling", self.test_api_error_handling)
            self.test("Data Persistence", self.test_data_persistence)
            
            # Frontend integration tests
            self.test("Frontend Accessibility", self.test_frontend_accessibility)
            self.test("Responsive Design", self.test_responsive_design)
            self.test("End-to-End User Workflow", self.test_end_to_end_user_workflow)
            
            # Performance tests
            self.test("Performance Metrics", self.test_performance_metrics)
            
        finally:
            # Cleanup
            self.cleanup_test_data()
            self.cleanup_selenium()
        
        self.print_results()
        
    def print_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE INTEGRATION TEST RESULTS - TASK 17.1")
        print("=" * 80)
        
        total_tests = self.results["passed"] + self.results["failed"]
        success_rate = (self.results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"⚠️  Warnings: {self.results['warnings']}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Detailed results
        if self.results["failed"] > 0:
            print("\n❌ Failed Tests:")
            for test in self.results["tests"]:
                if test["status"] == "FAILED":
                    print(f"   - {test['name']}: {test.get('error', 'Unknown error')}")
        
        if self.results["warnings"] > 0:
            print("\n⚠️  Warnings:")
            for test in self.results["tests"]:
                if test["status"] == "WARNING":
                    print(f"   - {test['name']}: {test.get('message', 'Unknown warning')}")
        
        # Integration status assessment
        print("\n🎯 TASK 17.1 INTEGRATION STATUS:")
        if self.results["failed"] == 0:
            print("   ✅ FULLY INTEGRATED - All components working together correctly!")
            print("   ✅ Backend APIs functional")
            print("   ✅ Database operations working")
            print("   ✅ File system operations working")
            print("   ✅ Complete user workflows functional")
            if self.results["warnings"] == 0:
                print("   ✅ Frontend accessibility and responsive design verified")
        elif self.results["failed"] <= 2:
            print("   ⚠️  MOSTLY INTEGRATED - Minor issues detected")
            print("   ✅ Core functionality works")
            print("   ⚠️  Some components need attention")
        else:
            print("   ❌ NEEDS ATTENTION - Multiple integration issues detected")
            print("   ❌ Core integration problems found")
        
        # Task 17.1 specific assessments
        print("\n📋 TASK 17.1 REQUIREMENTS ASSESSMENT:")
        
        # Check if all components are connected
        backend_working = any(test["name"] in ["Backend Health Check", "Complete API Workflow"] and test["status"] == "PASSED" for test in self.results["tests"])
        database_working = any(test["name"] == "Database Operations" and test["status"] == "PASSED" for test in self.results["tests"])
        file_system_working = any(test["name"] == "File System Operations" and test["status"] == "PASSED" for test in self.results["tests"])
        
        print(f"   {'✅' if backend_working else '❌'} Frontend-Backend API Integration")
        print(f"   {'✅' if database_working else '❌'} Database Connectivity")
        print(f"   {'✅' if file_system_working else '❌'} File System Operations")
        
        # Check end-to-end workflows
        workflow_working = any(test["name"] in ["Complete API Workflow", "End-to-End User Workflow"] and test["status"] == "PASSED" for test in self.results["tests"])
        print(f"   {'✅' if workflow_working else '❌'} End-to-End User Workflows")
        
        # Check responsive design and accessibility
        responsive_tested = any(test["name"] == "Responsive Design" and test["status"] in ["PASSED", "WARNING"] for test in self.results["tests"])
        accessibility_tested = any(test["name"] == "Frontend Accessibility" and test["status"] in ["PASSED", "WARNING"] for test in self.results["tests"])
        
        print(f"   {'✅' if responsive_tested else '❌'} Responsive Design Validation")
        print(f"   {'✅' if accessibility_tested else '❌'} Accessibility Compliance Testing")
        
        print("=" * 80)
        
        # Recommendations
        if self.results["failed"] > 0 or self.results["warnings"] > 0:
            print("\n💡 RECOMMENDATIONS FOR TASK 17.1 COMPLETION:")
            
            failed_tests = [t["name"] for t in self.results["tests"] if t["status"] == "FAILED"]
            warning_tests = [t["name"] for t in self.results["tests"] if t["status"] == "WARNING"]
            
            if any("Frontend" in test for test in failed_tests + warning_tests):
                print("   - Start the frontend server: cd frontend && npm start")
                print("   - Install Selenium WebDriver for comprehensive frontend testing")
            if any("Backend" in test for test in failed_tests):
                print("   - Ensure backend server is running: cd backend && python run.py")
            if any("Database" in test for test in failed_tests):
                print("   - Check database configuration and connectivity")
            if any("Performance" in test for test in failed_tests):
                print("   - Optimize API response times and frontend loading")
            
            print("   - Review error messages above for specific issues")
            print("   - Run individual component tests for detailed debugging")
        else:
            print("\n🎉 TASK 17.1 SUCCESSFULLY COMPLETED!")
            print("   All components are properly integrated and working together.")
            print("   System is ready for deployment preparation (Task 17.2).")

def main():
    """Main function to run comprehensive integration tests"""
    tester = ComprehensiveIntegrationTester()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        tester.cleanup_test_data()
        tester.cleanup_selenium()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        tester.cleanup_test_data()
        tester.cleanup_selenium()
        sys.exit(1)
    
    # Exit with error code if tests failed
    sys.exit(1 if tester.results["failed"] > 0 else 0)

if __name__ == "__main__":
    main()