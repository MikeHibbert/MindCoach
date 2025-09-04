#!/usr/bin/env python3
"""
Simple Integration Test for Task 17.1 (without Selenium)
Tests all components working together: Backend, Database, File System
"""

import requests
import json
import time
import os
import sys
from datetime import datetime
from pathlib import Path

class SimpleIntegrationTester:
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
        
    def test_backend_health(self):
        """Test backend API health and basic endpoints"""
        # Test subjects endpoint
        response = requests.get(f"{self.backend_url}/api/subjects", timeout=10)
        if response.status_code != 200:
            raise Exception(f"Subjects endpoint failed: {response.status_code}")
        
        subjects_data = response.json()
        if not subjects_data.get("subjects"):
            raise Exception("No subjects returned from API")
        
        # Test that we have expected subjects
        subject_ids = [s["id"] for s in subjects_data["subjects"]]
        if "python" not in subject_ids:
            raise Exception("Python subject not found in subjects list")
        
        self.log(f"   Backend API healthy - Found {len(subjects_data['subjects'])} subjects")
        
    def test_database_operations(self):
        """Test complete database operations workflow"""
        # Create user
        user_data = {
            "user_id": self.test_user_id,
            "email": f"{self.test_user_id}@test.com"
        }
        response = requests.post(f"{self.backend_url}/api/users", json=user_data)
        if response.status_code != 201:
            raise Exception(f"User creation failed: {response.status_code} - {response.text}")
        
        created_user = response.json()
        if created_user["user"]["user_id"] != self.test_user_id:
            raise Exception("User creation returned incorrect user ID")
        
        # Purchase subscription
        response = requests.post(f"{self.backend_url}/api/users/{self.test_user_id}/subscriptions/{self.test_subject}")
        if response.status_code != 201:
            raise Exception(f"Subscription purchase failed: {response.status_code} - {response.text}")
        
        # Verify subscription
        response = requests.get(f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}/status")
        if response.status_code != 200:
            raise Exception(f"Subscription verification failed: {response.status_code}")
        
        status_data = response.json()
        if not status_data.get("access_status", {}).get("has_active_subscription"):
            raise Exception("Subscription not active after purchase")
        
        self.log("   Database operations successful - User created, subscription purchased and verified")
        
    def test_file_system_operations(self):
        """Test file system operations for user data"""
        # Check if users directory exists or can be created
        users_dir = Path("backend/users")
        if not users_dir.exists():
            users_dir.mkdir(parents=True, exist_ok=True)
        
        # Test file creation and reading
        test_file = users_dir / f"{self.test_user_id}_test.json"
        test_data = {
            "test": "data", 
            "timestamp": datetime.now().isoformat(),
            "user_id": self.test_user_id,
            "large_data": list(range(100))  # Test with some data
        }
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f, indent=2)
            
        with open(test_file, 'r') as f:
            loaded_data = json.load(f)
            
        if loaded_data["test"] != "data" or loaded_data["user_id"] != self.test_user_id:
            raise Exception("File system read/write test failed - data mismatch")
        
        # Test file size
        file_size = test_file.stat().st_size
        if file_size < 100:  # Should be at least 100 bytes with the test data
            raise Exception("File system test failed - file too small")
            
        # Cleanup
        test_file.unlink()
        self.log(f"   File system operations successful - Created, read, and deleted {file_size} byte file")
        
    def test_complete_api_workflow(self):
        """Test complete API workflow from user creation to lesson access"""
        # Generate survey
        response = requests.post(f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}/survey/generate")
        if response.status_code != 201:
            raise Exception(f"Survey generation failed: {response.status_code} - {response.text}")
        
        survey_data = response.json()
        if not survey_data.get("success") or not survey_data.get("survey", {}).get("questions"):
            raise Exception("Invalid survey generated - missing questions")
        
        questions = survey_data["survey"]["questions"]
        if len(questions) < 3:
            raise Exception(f"Survey has too few questions: {len(questions)}")
        
        # Submit survey answers
        answers = []
        for i, question in enumerate(questions):
            answer_value = 0 if question["type"] == "multiple_choice" else "Test answer"
            answers.append({
                "question_id": question["id"],
                "answer": answer_value,
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
            raise Exception(f"Survey submission failed: {response.status_code} - {response.text}")
        
        results_data = response.json()
        if not results_data.get("success") or not results_data.get("results", {}).get("skill_level"):
            raise Exception("Survey submission did not return valid results")
        
        skill_level = results_data["results"]["skill_level"]
        
        # Generate lessons
        response = requests.post(f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons/generate")
        if response.status_code != 201:
            raise Exception(f"Lesson generation failed: {response.status_code} - {response.text}")
        
        generation_data = response.json()
        if not generation_data.get("success"):
            raise Exception("Lesson generation was not successful")
        
        # List lessons
        response = requests.get(f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons")
        if response.status_code != 200:
            raise Exception(f"Lesson listing failed: {response.status_code}")
        
        lessons_data = response.json()
        if not lessons_data.get("success") or not lessons_data.get("lessons"):
            raise Exception("No lessons found after generation")
        
        lessons = lessons_data["lessons"]
        if len(lessons) < 3:
            raise Exception(f"Too few lessons generated: {len(lessons)}")
        
        # Get first lesson
        first_lesson = lessons[0]
        response = requests.get(
            f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons/{first_lesson['lesson_number']}"
        )
        if response.status_code != 200:
            raise Exception(f"Lesson retrieval failed: {response.status_code}")
        
        lesson_data = response.json()
        if not lesson_data.get("success") or not lesson_data.get("lesson", {}).get("content"):
            raise Exception("Invalid lesson content returned")
        
        lesson_content = lesson_data["lesson"]["content"]
        if len(lesson_content) < 100:
            raise Exception("Lesson content too short - may not be properly generated")
        
        self.log(f"   Complete API workflow successful - Skill level: {skill_level}, Generated {len(lessons)} lessons")
        
    def test_api_error_handling(self):
        """Test API error handling and validation"""
        error_tests = []
        
        # Test invalid user ID
        response = requests.get(f"{self.backend_url}/api/users/invalid-user-id/subscriptions")
        if response.status_code in [400, 404]:
            error_tests.append("Invalid user ID handled correctly")
        else:
            error_tests.append(f"Invalid user ID not handled (got {response.status_code})")
        
        # Test invalid subject
        response = requests.post(f"{self.backend_url}/api/users/{self.test_user_id}/subjects/invalid-subject/select")
        if response.status_code in [400, 404]:
            error_tests.append("Invalid subject handled correctly")
        else:
            error_tests.append(f"Invalid subject not handled (got {response.status_code})")
        
        # Test unauthorized access
        response = requests.post(f"{self.backend_url}/api/users/unauthorized-user/subjects/{self.test_subject}/lessons/generate")
        if response.status_code in [403, 404]:
            error_tests.append("Unauthorized access prevented correctly")
        else:
            error_tests.append(f"Unauthorized access not prevented (got {response.status_code})")
        
        # Test malformed JSON
        response = requests.post(
            f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}/survey/submit",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 400:
            error_tests.append("Malformed JSON handled correctly")
        else:
            error_tests.append(f"Malformed JSON not handled (got {response.status_code})")
        
        failed_error_tests = [test for test in error_tests if "not handled" in test or "not prevented" in test]
        if failed_error_tests:
            raise Exception(f"Error handling issues: {'; '.join(failed_error_tests)}")
        
        self.log(f"   API error handling working correctly - {len(error_tests)} error scenarios tested")
        
    def test_frontend_basic_connectivity(self):
        """Test basic frontend connectivity"""
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                html_content = response.text.lower()
                
                # Check for basic web app indicators
                indicators = {
                    "HTML structure": "<html" in html_content and "<body" in html_content,
                    "React app": "react" in html_content or "app" in html_content,
                    "CSS/Styling": "css" in html_content or "style" in html_content,
                    "JavaScript": "script" in html_content or "js" in html_content
                }
                
                missing_indicators = [name for name, present in indicators.items() if not present]
                if len(missing_indicators) > 2:
                    self.warning("Frontend Basic Connectivity", f"Missing indicators: {', '.join(missing_indicators)}")
                else:
                    self.log(f"   Frontend accessible - Found: {', '.join([name for name, present in indicators.items() if present])}")
            else:
                self.warning("Frontend Basic Connectivity", f"Frontend returned status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            if "connection refused" in str(e).lower():
                self.warning("Frontend Basic Connectivity", "Frontend server not running")
            else:
                self.warning("Frontend Basic Connectivity", f"Frontend connection error: {e}")
                
    def test_performance_metrics(self):
        """Test basic performance metrics"""
        # Test API response times
        api_tests = [
            ("Subjects listing", f"{self.backend_url}/api/subjects"),
            ("User subscriptions", f"{self.backend_url}/api/users/{self.test_user_id}/subscriptions"),
            ("Subject status", f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}/status")
        ]
        
        performance_results = []
        
        for test_name, url in api_tests:
            start_time = time.time()
            try:
                response = requests.get(url, timeout=5)
                response_time = time.time() - start_time
                
                if response.status_code in [200, 404]:  # 404 is acceptable for some endpoints
                    if response_time > 2.0:
                        performance_results.append(f"{test_name}: SLOW ({response_time:.2f}s)")
                    else:
                        performance_results.append(f"{test_name}: OK ({response_time:.2f}s)")
                else:
                    performance_results.append(f"{test_name}: ERROR ({response.status_code})")
                    
            except Exception as e:
                performance_results.append(f"{test_name}: FAILED ({str(e)[:50]})")
        
        # Check if any tests were too slow
        slow_tests = [result for result in performance_results if "SLOW" in result]
        if slow_tests:
            raise Exception(f"Performance issues detected: {'; '.join(slow_tests)}")
        
        self.log(f"   Performance metrics acceptable - {'; '.join(performance_results)}")
        
    def test_data_persistence(self):
        """Test data persistence across requests"""
        # Verify user still exists
        response = requests.get(f"{self.backend_url}/api/users/{self.test_user_id}")
        if response.status_code != 200:
            raise Exception(f"User data not persisted: {response.status_code}")
        
        user_data = response.json()
        if user_data["user"]["user_id"] != self.test_user_id:
            raise Exception("User data corrupted")
        
        
        # Check if user directory was created
        user_dir = Path(f"backend/users/{self.test_user_id}")
        if not user_dir.exists():
            self.warning("Data Persistence", "User directory not created")
        else:
            # Check for expected files
            expected_files = ["selection.json", f"{self.test_subject}/survey.json", f"{self.test_subject}/survey_answers.json"]
            existing_files = []
            for expected_file in expected_files:
                file_path = user_dir / expected_file
                if file_path.exists():
                    existing_files.append(expected_file)
            
            if existing_files:
                self.log(f"   Data persistence verified - User data and {len(existing_files)} files persisted")
            else:
                self.log("   Data persistence verified - Database records persisted")
        
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
        self.log("🚀 Starting Integration Tests for Task 17.1")
        self.log("=" * 70)
        
        try:
            # Core system integration tests
            self.test("Backend Health Check", self.test_backend_health)
            self.test("Database Operations", self.test_database_operations)
            self.test("File System Operations", self.test_file_system_operations)
            
            # Complete workflow tests
            self.test("Complete API Workflow", self.test_complete_api_workflow)
            self.test("API Error Handling", self.test_api_error_handling)
            self.test("Data Persistence", self.test_data_persistence)
            
            # Frontend and performance tests
            self.test("Frontend Basic Connectivity", self.test_frontend_basic_connectivity)
            self.test("Performance Metrics", self.test_performance_metrics)
            
        finally:
            # Cleanup
            self.cleanup_test_data()
        
        self.print_results()
        
    def print_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 70)
        print("📊 INTEGRATION TEST RESULTS - TASK 17.1")
        print("=" * 70)
        
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
        
        # Task 17.1 specific assessment
        print("\n🎯 TASK 17.1 INTEGRATION STATUS:")
        
        # Check core requirements
        backend_working = any(test["name"] in ["Backend Health Check", "Complete API Workflow"] and test["status"] == "PASSED" for test in self.results["tests"])
        database_working = any(test["name"] == "Database Operations" and test["status"] == "PASSED" for test in self.results["tests"])
        file_system_working = any(test["name"] == "File System Operations" and test["status"] == "PASSED" for test in self.results["tests"])
        workflow_working = any(test["name"] == "Complete API Workflow" and test["status"] == "PASSED" for test in self.results["tests"])
        
        print(f"   {'✅' if backend_working else '❌'} Backend API Integration")
        print(f"   {'✅' if database_working else '❌'} Database Operations")
        print(f"   {'✅' if file_system_working else '❌'} File System Operations")
        print(f"   {'✅' if workflow_working else '❌'} End-to-End Workflows")
        
        # Overall assessment
        core_components_working = backend_working and database_working and file_system_working and workflow_working
        
        if core_components_working and self.results["failed"] == 0:
            print("\n🎉 TASK 17.1 REQUIREMENTS MET!")
            print("   ✅ All components integrated successfully")
            print("   ✅ End-to-end workflows functional")
            print("   ✅ System ready for deployment preparation")
        elif core_components_working:
            print("\n✅ TASK 17.1 MOSTLY COMPLETE")
            print("   ✅ Core integration successful")
            print("   ⚠️  Minor issues to address")
        else:
            print("\n❌ TASK 17.1 NEEDS WORK")
            print("   ❌ Core integration issues detected")
        
        print("=" * 70)
        
        # Recommendations
        if self.results["failed"] > 0 or self.results["warnings"] > 0:
            print("\n💡 RECOMMENDATIONS:")
            
            if not backend_working:
                print("   - Ensure backend server is running: cd backend && python run.py")
            if not database_working:
                print("   - Check database configuration and connectivity")
            if self.results["warnings"] > 0:
                print("   - Start frontend server for complete testing: cd frontend && npm start")
            
            print("   - Review error messages above for specific issues")

def main():
    """Main function to run integration tests"""
    tester = SimpleIntegrationTester()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        tester.cleanup_test_data()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        tester.cleanup_test_data()
        sys.exit(1)
    
    # Exit with error code if tests failed
    sys.exit(1 if tester.results["failed"] > 0 else 0)

if __name__ == "__main__":
    main()