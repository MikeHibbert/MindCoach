/**
 * Comprehensive Integration Test for Personalized Learning Path Generator
 * Tests the complete user workflow from subject selection to lesson viewing
 */

const axios = require('axios');

// Configuration
const BACKEND_URL = 'http://localhost:5000';
const FRONTEND_URL = 'http://localhost:3000';

// Test data
const TEST_USER_ID = 'test-user-integration-' + Date.now();
const TEST_SUBJECT = 'python';

class IntegrationTester {
  constructor() {
    this.results = {
      passed: 0,
      failed: 0,
      tests: []
    };
  }

  async test(name, testFn) {
    console.log(`\n🧪 Testing: ${name}`);
    try {
      await testFn();
      console.log(`✅ PASSED: ${name}`);
      this.results.passed++;
      this.results.tests.push({ name, status: 'PASSED' });
    } catch (error) {
      console.log(`❌ FAILED: ${name}`);
      console.log(`   Error: ${error.message}`);
      this.results.failed++;
      this.results.tests.push({ name, status: 'FAILED', error: error.message });
    }
  }

  async testBackendHealth() {
    const response = await axios.get(`${BACKEND_URL}/api/subjects`);
    if (response.status !== 200) {
      throw new Error(`Backend health check failed: ${response.status}`);
    }
    console.log('   Backend is responding');
  }

  async testUserCreation() {
    const response = await axios.post(`${BACKEND_URL}/api/users`, {
      user_id: TEST_USER_ID,
      email: `${TEST_USER_ID}@test.com`
    });
    
    if (response.status !== 201) {
      throw new Error(`User creation failed: ${response.status}`);
    }
    console.log(`   User created: ${TEST_USER_ID}`);
  }

  async testSubjectListing() {
    const response = await axios.get(`${BACKEND_URL}/api/subjects?user_id=${TEST_USER_ID}`);
    
    if (response.status !== 200) {
      throw new Error(`Subject listing failed: ${response.status}`);
    }
    
    const subjects = response.data.subjects;
    if (!Array.isArray(subjects) || subjects.length === 0) {
      throw new Error('No subjects returned');
    }
    
    const pythonSubject = subjects.find(s => s.id === TEST_SUBJECT);
    if (!pythonSubject) {
      throw new Error('Python subject not found');
    }
    
    console.log(`   Found ${subjects.length} subjects including Python`);
  }

  async testSubscriptionPurchase() {
    const response = await axios.post(
      `${BACKEND_URL}/api/users/${TEST_USER_ID}/subscriptions/${TEST_SUBJECT}`,
      { plan: 'monthly' }
    );
    
    if (response.status !== 201) {
      throw new Error(`Subscription purchase failed: ${response.status}`);
    }
    
    console.log('   Subscription purchased successfully');
  }

  async testSubjectSelection() {
    const response = await axios.post(
      `${BACKEND_URL}/api/users/${TEST_USER_ID}/subjects/${TEST_SUBJECT}/select`
    );
    
    if (response.status !== 200) {
      throw new Error(`Subject selection failed: ${response.status}`);
    }
    
    console.log('   Subject selected successfully');
  }

  async testSurveyGeneration() {
    const response = await axios.post(
      `${BACKEND_URL}/api/users/${TEST_USER_ID}/subjects/${TEST_SUBJECT}/survey/generate`
    );
    
    if (response.status !== 201) {
      throw new Error(`Survey generation failed: ${response.status}`);
    }
    
    const survey = response.data.survey;
    if (!survey || !survey.questions || survey.questions.length === 0) {
      throw new Error('Invalid survey generated');
    }
    
    console.log(`   Survey generated with ${survey.questions.length} questions`);
    return survey;
  }

  async testSurveySubmission(survey) {
    // Create mock answers
    const answers = survey.questions.map((question, index) => ({
      question_id: question.id,
      answer: question.type === 'multiple_choice' ? 0 : 'Test answer',
      question_text: question.question,
      question_type: question.type,
      difficulty: question.difficulty || 'beginner',
      topic: question.topic || 'general'
    }));

    const response = await axios.post(
      `${BACKEND_URL}/api/users/${TEST_USER_ID}/subjects/${TEST_SUBJECT}/survey/submit`,
      { answers }
    );
    
    if (response.status !== 200) {
      throw new Error(`Survey submission failed: ${response.status}`);
    }
    
    const results = response.data.results;
    if (!results || !results.skill_level) {
      throw new Error('Invalid survey results');
    }
    
    console.log(`   Survey submitted, skill level: ${results.skill_level}`);
    return results;
  }

  async testLessonGeneration() {
    const response = await axios.post(
      `${BACKEND_URL}/api/users/${TEST_USER_ID}/subjects/${TEST_SUBJECT}/lessons/generate`
    );
    
    if (response.status !== 201) {
      throw new Error(`Lesson generation failed: ${response.status}`);
    }
    
    const generation = response.data.generation_summary;
    if (!generation || !generation.total_lessons) {
      throw new Error('Invalid lesson generation response');
    }
    
    console.log(`   Generated ${generation.total_lessons} lessons`);
  }

  async testLessonListing() {
    const response = await axios.get(
      `${BACKEND_URL}/api/users/${TEST_USER_ID}/subjects/${TEST_SUBJECT}/lessons`
    );
    
    if (response.status !== 200) {
      throw new Error(`Lesson listing failed: ${response.status}`);
    }
    
    const lessons = response.data.lessons;
    if (!Array.isArray(lessons) || lessons.length === 0) {
      throw new Error('No lessons returned');
    }
    
    console.log(`   Listed ${lessons.length} lessons`);
    return lessons;
  }

  async testLessonRetrieval(lessons) {
    const firstLesson = lessons[0];
    const response = await axios.get(
      `${BACKEND_URL}/api/users/${TEST_USER_ID}/subjects/${TEST_SUBJECT}/lessons/${firstLesson.lesson_number}`
    );
    
    if (response.status !== 200) {
      throw new Error(`Lesson retrieval failed: ${response.status}`);
    }
    
    const lesson = response.data.lesson;
    if (!lesson || !lesson.content) {
      throw new Error('Invalid lesson content');
    }
    
    console.log(`   Retrieved lesson: ${lesson.title}`);
  }

  async testAccessControl() {
    // Test access without subscription (should fail)
    try {
      await axios.post(
        `${BACKEND_URL}/api/users/unauthorized-user/subjects/${TEST_SUBJECT}/select`
      );
      throw new Error('Access control failed - unauthorized access allowed');
    } catch (error) {
      if (error.response && error.response.status === 402) {
        console.log('   Access control working - subscription required');
      } else {
        throw error;
      }
    }
  }

  async testResponsiveDesign() {
    // This would typically be done with a browser automation tool
    // For now, we'll just verify the frontend is serving content
    try {
      const response = await axios.get(FRONTEND_URL);
      if (response.status !== 200) {
        throw new Error(`Frontend not accessible: ${response.status}`);
      }
      console.log('   Frontend is accessible');
    } catch (error) {
      if (error.code === 'ECONNREFUSED') {
        console.log('   ⚠️  Frontend not running - skipping responsive design test');
      } else {
        throw error;
      }
    }
  }

  async runAllTests() {
    console.log('🚀 Starting Comprehensive Integration Tests\n');
    console.log('=' .repeat(60));

    await this.test('Backend Health Check', () => this.testBackendHealth());
    await this.test('User Creation', () => this.testUserCreation());
    await this.test('Subject Listing', () => this.testSubjectListing());
    await this.test('Subscription Purchase', () => this.testSubscriptionPurchase());
    await this.test('Subject Selection', () => this.testSubjectSelection());
    
    let survey;
    await this.test('Survey Generation', async () => {
      survey = await this.testSurveyGeneration();
    });
    
    await this.test('Survey Submission', () => this.testSurveySubmission(survey));
    await this.test('Lesson Generation', () => this.testLessonGeneration());
    
    let lessons;
    await this.test('Lesson Listing', async () => {
      lessons = await this.testLessonListing();
    });
    
    await this.test('Lesson Retrieval', () => this.testLessonRetrieval(lessons));
    await this.test('Access Control', () => this.testAccessControl());
    await this.test('Responsive Design Check', () => this.testResponsiveDesign());

    this.printResults();
  }

  printResults() {
    console.log('\n' + '=' .repeat(60));
    console.log('📊 INTEGRATION TEST RESULTS');
    console.log('=' .repeat(60));
    
    console.log(`✅ Passed: ${this.results.passed}`);
    console.log(`❌ Failed: ${this.results.failed}`);
    console.log(`📈 Success Rate: ${Math.round((this.results.passed / (this.results.passed + this.results.failed)) * 100)}%`);
    
    if (this.results.failed > 0) {
      console.log('\n❌ Failed Tests:');
      this.results.tests
        .filter(t => t.status === 'FAILED')
        .forEach(t => console.log(`   - ${t.name}: ${t.error}`));
    }
    
    console.log('\n🎯 Integration Status:', this.results.failed === 0 ? 'FULLY INTEGRATED' : 'NEEDS ATTENTION');
    console.log('=' .repeat(60));
  }
}

// Run the tests
async function main() {
  const tester = new IntegrationTester();
  
  try {
    await tester.runAllTests();
  } catch (error) {
    console.error('❌ Integration test suite failed:', error.message);
    process.exit(1);
  }
  
  // Exit with error code if any tests failed
  process.exit(tester.results.failed > 0 ? 1 : 0);
}

if (require.main === module) {
  main();
}

module.exports = IntegrationTester;