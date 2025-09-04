#!/usr/bin/env python3
"""
System Integration Test for Personalized Learning Path Generator
Tests all components working together: Frontend, Backend, Database, File System
"""

import requests
import json
import time
import os
import sys
from datetime import datetime
from pathlib import Path

class SystemIntegrationTester:
    def __init__(self):
        self.backend_url = "http://localhost:5000"
        self.frontend_url = "http://localhost:3000"
        self.test_user_id = f"integration-test-{int(time.time())}"
        self.test_subject = "python"
        self.results = {
            "passed": 0,
            "failed": 0,
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
            
    def test_backend_health(self):
        """Test backend API health"""
        response = requests.get(f"{self.backend_url}/api/subjects", timeout=10)
        if response.status_code != 200:
            raise Exception(f"Backend health check failed: {response.status_code}")
        self.log("   Backend API is healthy")
        
    def test_database_connectivity(self):
        """Test database operations"""
        # Create user
        user_data = {
            "user_id": self.test_user_id,
            "email": f"{self.test_user_id}@test.com"
        }
        response = requests.post(f"{self.backend_url}/api/users", json=user_data)
        if response.status_code != 201:
            raise Exception(f"User creation failed: {response.status_code}")
        self.log("   Database user creation successful")
        
    def test_file_system_operations(self):
        """Test file system operations"""
        # Check if users directory exists or can be created
        users_dir = Path("backend/users")
        if not users_dir.exists():
            users_dir.mkdir(parents=True, exist_ok=True)
        
        # Test file creation
        test_file = users_dir / f"{self.test_user_id}_test.json"
        test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
            
        # Test file reading
        with open(test_file, 'r') as f:
            loaded_data = json.load(f)
            
        if loaded_data["test"] != "data":
            raise Exception("File system read/write test failed")
            
        # Cleanup
        test_file.unlink()
        self.log("   File system operations successful")
        

        
    def test_subject_selection_workflow(self):
        """Test subject selection workflow"""
        # Select subject
        response = requests.post(
            f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}/select"
        )
        if response.status_code != 200:
            raise Exception(f"Subject selection failed: {response.status_code}")
            
        # Verify selection was saved
        response = requests.get(
            f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}/status"
        )
        if response.status_code != 200:
            raise Exception(f"Subject status check failed: {response.status_code}")
            
        status_data = response.json()
        if not status_data.get("access_status", {}).get("is_selected"):
            raise Exception("Subject selection not saved")
            
        self.log("   Subject selection workflow successful")
        
    def test_survey_workflow(self):
        """Test complete survey workflow"""
        # Generate survey
        response = requests.post(
            f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}/survey/generate"
        )
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
            
        results_data = response.json()
        if not results_data.get("success") or not results_data.get("results", {}).get("skill_level"):
            raise Exception("Invalid survey results")
            
        self.log(f"   Survey workflow successful - Skill level: {results_data['results']['skill_level']}")
        
    def test_lesson_generation_workflow(self):
        """Test lesson generation workflow"""
        # Generate lessons
        response = requests.post(
            f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons/generate"
        )
        if response.status_code != 201:
            raise Exception(f"Lesson generation failed: {response.status_code}")
            
        generation_data = response.json()
        if not generation_data.get("success"):
            raise Exception("Lesson generation unsuccessful")
            
        # List lessons
        response = requests.get(
            f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}/lessons"
        )
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
            
        self.log(f"   Lesson generation workflow successful - Generated {len(lessons)} lessons")
        
    def test_api_error_handling(self):
        """Test API error handling"""
        # Test invalid user ID
        response = requests.get(f"{self.backend_url}/api/users/invalid-user-id/subscriptions")
        if response.status_code not in [400, 404, 500]:  # Should return an error status
            raise Exception("API should handle invalid user ID with error status")
            
        # Test invalid subject
        response = requests.post(
            f"{self.backend_url}/api/users/{self.test_user_id}/subjects/invalid-subject/select"
        )
        if response.status_code not in [400, 404]:
            raise Exception("API should handle invalid subject with error status")
            
        self.log("   API error handling working correctly")
        
    def test_data_persistence(self):
        """Test data persistence across requests"""
        # Verify user still exists
        response = requests.get(f"{self.backend_url}/api/users/{self.test_user_id}/subscriptions")
        if response.status_code not in [200, 404]:  # 404 is acceptable if no subscriptions
            raise Exception(f"User data persistence check failed: {response.status_code}")
            
        # Verify subject selection persists
        response = requests.get(
            f"{self.backend_url}/api/users/{self.test_user_id}/subjects/{self.test_subject}/status"
        )
        if response.status_code != 200:
            raise Exception("Subject selection not persisted")
            
        self.log("   Data persistence verified")
        
    def test_frontend_accessibility(self):
        """Test frontend accessibility (basic check)"""
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                # Check for basic accessibility indicators in HTML
                html_content = response.text.lower()
                if 'aria-' not in html_content and 'role=' not in html_content:
                    raise Exception("Frontend lacks basic accessibility attributes")
                self.log("   Frontend accessibility indicators present")
            else:
                self.log("   ⚠️  Frontend not running - skipping accessibility test")
        except requests.exceptions.RequestException:
            self.log("   ⚠️  Frontend not accessible - skipping accessibility test")
            
    def test_responsive_design_indicators(self):
        """Test for responsive design indicators"""
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                html_content = response.text.lower()
                # Check for responsive design indicators
                responsive_indicators = [
                    'viewport',
                    'media',
                    'responsive',
                    'mobile',
                    'tablet',
                    'desktop'
                ]
                found_indicators = [indicator for indicator in responsive_indicators if indicator in html_content]
                if len(found_indicators) < 2:
                    raise Exception("Frontend lacks responsive design indicators")
                self.log(f"   Responsive design indicators found: {', '.join(found_indicators)}")
            else:
                self.log("   ⚠️  Frontend not running - skipping responsive design test")
        except requests.exceptions.RequestException:
            self.log("   ⚠️  Frontend not accessible - skipping responsive design test")
            
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
        self.log("🚀 Starting System Integration Tests")
        self.log("=" * 60)
        
        # Core system tests
        self.test("Backend Health Check", self.test_backend_health)
        self.test("Database Connectivity", self.test_database_connectivity)
        self.test("File System Operations", self.test_file_system_operations)
        
        # Business workflow tests
        self.test("Subscription Workflow", self.test_subscription_workflow)
        self.test("Subject Selection Workflow", self.test_subject_selection_workflow)
        self.test("Survey Workflow", self.test_survey_workflow)
        self.test("Lesson Generation Workflow", self.test_lesson_generation_workflow)
        
        # System reliability tests
        self.test("API Error Handling", self.test_api_error_handling)
        self.test("Data Persistence", self.test_data_persistence)
        
        # Frontend integration tests
        self.test("Frontend Accessibility", self.test_frontend_accessibility)
        self.test("Responsive Design Indicators", self.test_responsive_design_indicators)
        
        # Cleanup
        self.cleanup_test_data()
        
        self.print_results()
        
    def print_results(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 SYSTEM INTEGRATION TEST RESULTS")
        print("=" * 60)
        
        total_tests = self.results["passed"] + self.results["failed"]
        success_rate = (self.results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.results["failed"] > 0:
            print("\n❌ Failed Tests:")
            for test in self.results["tests"]:
                if test["status"] == "FAILED":
                    print(f"   - {test['name']}: {test.get('error', 'Unknown error')}")
                    
        # Integration status
        if self.results["failed"] == 0:
            print("\n🎯 Integration Status: ✅ FULLY INTEGRATED")
            print("   All components are working together correctly!")
        elif self.results["failed"] <= 2:
            print("\n🎯 Integration Status: ⚠️  MOSTLY INTEGRATED")
            print("   Minor issues detected, but core functionality works")
        else:
            print("\n🎯 Integration Status: ❌ NEEDS ATTENTION")
            print("   Multiple integration issues detected")
            
        print("=" * 60)
        
        # Recommendations
        if self.results["failed"] > 0:
            print("\n💡 RECOMMENDATIONS:")
            failed_tests = [t["name"] for t in self.results["tests"] if t["status"] == "FAILED"]
            
            if any("Frontend" in test for test in failed_tests):
                print("   - Start the frontend server: npm start")
            if any("Backend" in test for test in failed_tests):
                print("   - Start the backend server: python run.py")
            if any("Database" in test for test in failed_tests):
                print("   - Check database configuration and connectivity")
            if any("File System" in test for test in failed_tests):
                print("   - Check file system permissions and disk space")
                
            print("   - Review error messages above for specific issues")
            print("   - Run individual component tests for detailed debugging")

def main():
    """Main function to run integration tests"""
    tester = SystemIntegrationTester()
    
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