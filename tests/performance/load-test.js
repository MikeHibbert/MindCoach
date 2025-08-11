// K6 Load Testing Script for MindCoach
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('error_rate');
const responseTime = new Trend('response_time');
const requestCount = new Counter('request_count');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp up to 10 users
    { duration: '5m', target: 10 },   // Stay at 10 users
    { duration: '2m', target: 20 },   // Ramp up to 20 users
    { duration: '5m', target: 20 },   // Stay at 20 users
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '5m', target: 50 },   // Stay at 50 users
    { duration: '2m', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
    http_req_failed: ['rate<0.05'],   // Error rate must be below 5%
    error_rate: ['rate<0.05'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost';
const API_URL = `${BASE_URL}/api`;

// Test data
const testUsers = [
  { id: 'test-user-1', subject: 'python' },
  { id: 'test-user-2', subject: 'javascript' },
  { id: 'test-user-3', subject: 'react' },
  { id: 'test-user-4', subject: 'nodejs' },
  { id: 'test-user-5', subject: 'python' },
];

const surveyAnswers = [
  { question_id: 1, answer: 'A' },
  { question_id: 2, answer: 'B' },
  { question_id: 3, answer: 'C' },
  { question_id: 4, answer: 'A' },
  { question_id: 5, answer: 'B' },
];

export function setup() {
  console.log('Starting load test setup...');
  
  // Health check
  const healthResponse = http.get(`${API_URL}/health`);
  check(healthResponse, {
    'health check status is 200': (r) => r.status === 200,
  });
  
  if (healthResponse.status !== 200) {
    throw new Error('Application is not healthy, aborting test');
  }
  
  console.log('Setup completed successfully');
  return { baseUrl: BASE_URL, apiUrl: API_URL };
}

export default function (data) {
  const user = testUsers[Math.floor(Math.random() * testUsers.length)];
  
  // Test scenario: Complete user journey
  testCompleteUserJourney(user, data.apiUrl);
  
  sleep(1);
}

function testCompleteUserJourney(user, apiUrl) {
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  // 1. Create user
  let response = http.post(
    `${apiUrl}/users`,
    JSON.stringify({ user_id: user.id }),
    params
  );
  
  check(response, {
    'create user status is 200 or 409': (r) => r.status === 200 || r.status === 409,
  });
  
  requestCount.add(1);
  responseTime.add(response.timings.duration);
  errorRate.add(response.status >= 400);
  
  // 2. Select subject
  response = http.post(
    `${apiUrl}/users/${user.id}/subjects/${user.subject}/select`,
    '{}',
    params
  );
  
  check(response, {
    'select subject status is 200': (r) => r.status === 200,
  });
  
  requestCount.add(1);
  responseTime.add(response.timings.duration);
  errorRate.add(response.status >= 400);
  
  // 3. Get survey
  response = http.get(`${apiUrl}/users/${user.id}/subjects/${user.subject}/survey`);
  
  check(response, {
    'get survey status is 200': (r) => r.status === 200,
    'survey has questions': (r) => {
      try {
        const survey = JSON.parse(r.body);
        return survey.questions && survey.questions.length > 0;
      } catch (e) {
        return false;
      }
    },
  });
  
  requestCount.add(1);
  responseTime.add(response.timings.duration);
  errorRate.add(response.status >= 400);
  
  // 4. Submit survey answers
  response = http.post(
    `${apiUrl}/users/${user.id}/subjects/${user.subject}/survey/submit`,
    JSON.stringify({ answers: surveyAnswers }),
    params
  );
  
  check(response, {
    'submit survey status is 200': (r) => r.status === 200,
  });
  
  requestCount.add(1);
  responseTime.add(response.timings.duration);
  errorRate.add(response.status >= 400);
  
  // 5. Start content generation
  response = http.post(
    `${apiUrl}/users/${user.id}/subjects/${user.subject}/content/generate`,
    '{}',
    params
  );
  
  check(response, {
    'start content generation status is 200 or 202': (r) => r.status === 200 || r.status === 202,
  });
  
  requestCount.add(1);
  responseTime.add(response.timings.duration);
  errorRate.add(response.status >= 400);
  
  // 6. Check generation status (simulate polling)
  for (let i = 0; i < 3; i++) {
    sleep(2);
    
    response = http.get(`${apiUrl}/users/${user.id}/subjects/${user.subject}/content/status`);
    
    check(response, {
      'content status check is 200': (r) => r.status === 200,
    });
    
    requestCount.add(1);
    responseTime.add(response.timings.duration);
    errorRate.add(response.status >= 400);
    
    if (response.status === 200) {
      try {
        const status = JSON.parse(response.body);
        if (status.state === 'SUCCESS') {
          break;
        }
      } catch (e) {
        // Continue polling
      }
    }
  }
  
  // 7. Get lessons list
  response = http.get(`${apiUrl}/users/${user.id}/subjects/${user.subject}/lessons`);
  
  check(response, {
    'get lessons status is 200': (r) => r.status === 200,
  });
  
  requestCount.add(1);
  responseTime.add(response.timings.duration);
  errorRate.add(response.status >= 400);
  
  // 8. Get individual lesson
  response = http.get(`${apiUrl}/users/${user.id}/subjects/${user.subject}/lessons/1`);
  
  check(response, {
    'get lesson status is 200': (r) => r.status === 200,
  });
  
  requestCount.add(1);
  responseTime.add(response.timings.duration);
  errorRate.add(response.status >= 400);
}

export function teardown(data) {
  console.log('Load test completed');
  
  // Final health check
  const healthResponse = http.get(`${data.apiUrl}/health`);
  check(healthResponse, {
    'final health check status is 200': (r) => r.status === 200,
  });
}