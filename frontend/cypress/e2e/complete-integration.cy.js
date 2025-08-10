/**
 * Complete Integration Test
 * Tests the entire user workflow from subject selection to lesson viewing
 */

describe('Complete User Integration Workflow', () => {
  const testUserId = `test-user-${Date.now()}`;
  const testSubject = 'python';

  beforeEach(() => {
    // Mock API responses for integration testing
    cy.intercept('GET', '/api/subjects*', {
      statusCode: 200,
      body: {
        subjects: [
          {
            id: 'python',
            name: 'Python Programming',
            description: 'Learn Python from basics to advanced concepts',
            pricing: { monthly: 29.99, yearly: 299.99 },
            available: true,
            locked: false
          },
          {
            id: 'javascript',
            name: 'JavaScript Development',
            description: 'Master JavaScript for web development',
            pricing: { monthly: 29.99, yearly: 299.99 },
            available: true,
            locked: true
          }
        ],
        total_count: 2
      }
    }).as('getSubjects');

    cy.intercept('POST', `/api/users/${testUserId}/subjects/${testSubject}/select`, {
      statusCode: 200,
      body: {
        message: 'Successfully selected Python Programming',
        subject: {
          id: testSubject,
          name: 'Python Programming',
          selected_at: new Date().toISOString()
        }
      }
    }).as('selectSubject');

    cy.intercept('POST', `/api/users/${testUserId}/subjects/${testSubject}/survey/generate`, {
      statusCode: 201,
      body: {
        success: true,
        survey: {
          id: 'survey-123',
          subject: testSubject,
          user_id: testUserId,
          questions: [
            {
              id: 1,
              question: 'What is a Python variable?',
              type: 'multiple_choice',
              options: [
                'A container for storing data',
                'A type of loop',
                'A function',
                'A class'
              ],
              difficulty: 'beginner',
              topic: 'variables'
            },
            {
              id: 2,
              question: 'How do you create a list in Python?',
              type: 'multiple_choice',
              options: [
                'list = []',
                'list = {}',
                'list = ()',
                'list = ""'
              ],
              difficulty: 'beginner',
              topic: 'data_structures'
            }
          ]
        }
      }
    }).as('generateSurvey');

    cy.intercept('POST', `/api/users/${testUserId}/subjects/${testSubject}/survey/submit`, {
      statusCode: 200,
      body: {
        success: true,
        results: {
          user_id: testUserId,
          subject: testSubject,
          skill_level: 'intermediate',
          accuracy: 75,
          total_questions: 2,
          correct_answers: 1,
          topic_analysis: {
            variables: { correct: 1, total: 1, percentage: 100 },
            data_structures: { correct: 0, total: 1, percentage: 0 }
          },
          recommendations: ['Focus on data structures'],
          processed_at: new Date().toISOString()
        }
      }
    }).as('submitSurvey');

    cy.intercept('POST', `/api/users/${testUserId}/subjects/${testSubject}/lessons/generate`, {
      statusCode: 201,
      body: {
        success: true,
        generation_summary: {
          user_id: testUserId,
          subject: testSubject,
          skill_level: 'intermediate',
          total_lessons: 8,
          generated_at: new Date().toISOString()
        }
      }
    }).as('generateLessons');

    cy.intercept('GET', `/api/users/${testUserId}/subjects/${testSubject}/lessons`, {
      statusCode: 200,
      body: {
        success: true,
        lessons: [
          {
            lesson_number: 1,
            title: 'Advanced Variables and Data Types',
            estimated_time: '30 minutes',
            difficulty: 'intermediate',
            topics: ['variables', 'type_hints'],
            file_exists: true
          },
          {
            lesson_number: 2,
            title: 'Working with Lists and Dictionaries',
            estimated_time: '45 minutes',
            difficulty: 'intermediate',
            topics: ['lists', 'dictionaries'],
            file_exists: true
          }
        ],
        summary: {
          total_lessons: 2,
          skill_level: 'intermediate'
        }
      }
    }).as('listLessons');

    cy.intercept('GET', `/api/users/${testUserId}/subjects/${testSubject}/lessons/1`, {
      statusCode: 200,
      body: {
        success: true,
        lesson: {
          lesson_number: 1,
          title: 'Advanced Variables and Data Types',
          estimated_time: '30 minutes',
          difficulty: 'intermediate',
          topics: ['variables', 'type_hints'],
          content: `# Advanced Variables and Data Types

## Introduction
In this lesson, we'll explore advanced variable concepts in Python.

## Variables and Type Hints
Python variables can store different types of data:

\`\`\`python
name: str = "Alice"
age: int = 30
height: float = 5.6
\`\`\`

## Exercise
Create a variable with a type hint for storing a list of numbers.`
        }
      }
    }).as('getLesson');
  });

  it('should complete the entire user workflow successfully', () => {
    // Visit the application
    cy.visit('/');

    // Step 1: Subject Selection
    cy.get('[data-testid="subject-selector"]', { timeout: 10000 }).should('be.visible');
    cy.wait('@getSubjects');
    
    // Verify subjects are loaded
    cy.contains('Python Programming').should('be.visible');
    cy.contains('JavaScript Development').should('be.visible');
    
    // Select Python subject
    cy.contains('Python Programming').click();
    cy.wait('@selectSubject');
    
    // Verify selection confirmation
    cy.contains('Python Programming Selected').should('be.visible');

    // Step 2: Survey Generation and Completion
    cy.get('[data-testid="start-survey-button"]').click();
    cy.wait('@generateSurvey');
    
    // Verify survey is loaded
    cy.contains('What is a Python variable?').should('be.visible');
    
    // Answer first question
    cy.contains('A container for storing data').click();
    cy.get('[data-testid="next-button"]').click();
    
    // Answer second question
    cy.contains('list = []').click();
    cy.get('[data-testid="submit-survey-button"]').click();
    cy.wait('@submitSurvey');
    
    // Verify survey results
    cy.contains('intermediate').should('be.visible');
    cy.contains('75%').should('be.visible'); // accuracy

    // Step 3: Lesson Generation
    cy.get('[data-testid="generate-lessons-button"]').click();
    cy.wait('@generateLessons');
    
    // Verify lesson generation success
    cy.contains('8 personalized lessons').should('be.visible');

    // Step 4: Lesson Viewing
    cy.get('[data-testid="view-lessons-button"]').click();
    cy.wait('@listLessons');
    
    // Verify lesson list
    cy.contains('Advanced Variables and Data Types').should('be.visible');
    cy.contains('Working with Lists and Dictionaries').should('be.visible');
    
    // Open first lesson
    cy.contains('Advanced Variables and Data Types').click();
    cy.wait('@getLesson');
    
    // Verify lesson content
    cy.contains('Advanced Variables and Data Types').should('be.visible');
    cy.contains('In this lesson, we\'ll explore').should('be.visible');
    cy.get('code').should('contain', 'name: str = "Alice"');
    
    // Test lesson navigation
    cy.get('[data-testid="next-lesson-button"]').should('be.visible');
    cy.get('[data-testid="previous-lesson-button"]').should('be.disabled');
    
    // Mark lesson as complete
    cy.get('[data-testid="mark-complete-button"]').click();
    cy.contains('Lesson completed!').should('be.visible');
  });

  it('should handle responsive design across different screen sizes', () => {
    // Test mobile view
    cy.viewport(375, 667); // iPhone SE
    cy.visit('/');
    
    // Verify mobile layout
    cy.get('[data-testid="mobile-subject-dropdown"]').should('be.visible');
    cy.get('[data-testid="desktop-subject-grid"]').should('not.be.visible');
    
    // Test tablet view
    cy.viewport(768, 1024); // iPad
    cy.reload();
    
    // Verify tablet layout
    cy.get('[data-testid="tablet-subject-layout"]').should('be.visible');
    
    // Test desktop view
    cy.viewport(1280, 720); // Desktop
    cy.reload();
    
    // Verify desktop layout
    cy.get('[data-testid="desktop-subject-grid"]').should('be.visible');
    cy.get('[data-testid="sidebar-navigation"]').should('be.visible');
  });

  it('should maintain accessibility standards throughout the workflow', () => {
    cy.visit('/');
    cy.injectAxe();
    
    // Check accessibility on subject selection page
    cy.checkA11y();
    
    // Navigate through workflow and check accessibility at each step
    cy.contains('Python Programming').click();
    cy.checkA11y();
    
    // Check survey accessibility
    cy.get('[data-testid="start-survey-button"]').click();
    cy.wait('@generateSurvey');
    cy.checkA11y();
    
    // Check lesson viewer accessibility
    cy.contains('A container for storing data').click();
    cy.get('[data-testid="next-button"]').click();
    cy.contains('list = []').click();
    cy.get('[data-testid="submit-survey-button"]').click();
    cy.wait('@submitSurvey');
    
    cy.get('[data-testid="generate-lessons-button"]').click();
    cy.wait('@generateLessons');
    
    cy.get('[data-testid="view-lessons-button"]').click();
    cy.wait('@listLessons');
    cy.checkA11y();
    
    cy.contains('Advanced Variables and Data Types').click();
    cy.wait('@getLesson');
    cy.checkA11y();
  });

  it('should handle error scenarios gracefully', () => {
    // Test network error handling
    cy.intercept('GET', '/api/subjects*', {
      statusCode: 500,
      body: { error: { message: 'Server error' } }
    }).as('getSubjectsError');
    
    cy.visit('/');
    cy.wait('@getSubjectsError');
    
    // Verify error handling
    cy.contains('Error loading subjects').should('be.visible');
    cy.get('[data-testid="retry-button"]').should('be.visible');
    
    // Test retry functionality
    cy.intercept('GET', '/api/subjects*', {
      statusCode: 200,
      body: {
        subjects: [
          {
            id: 'python',
            name: 'Python Programming',
            description: 'Learn Python from basics to advanced concepts',
            pricing: { monthly: 29.99 },
            available: true,
            locked: false
          }
        ]
      }
    }).as('getSubjectsRetry');
    
    cy.get('[data-testid="retry-button"]').click();
    cy.wait('@getSubjectsRetry');
    cy.contains('Python Programming').should('be.visible');
  });

  it('should enforce subscription requirements correctly', () => {
    // Mock locked subject response
    cy.intercept('POST', `/api/users/${testUserId}/subjects/javascript/select`, {
      statusCode: 402,
      body: {
        error: {
          code: 'SUBSCRIPTION_REQUIRED',
          message: 'Active subscription required for this subject'
        }
      }
    }).as('selectLockedSubject');
    
    cy.visit('/');
    cy.wait('@getSubjects');
    
    // Try to select locked subject
    cy.contains('JavaScript Development').click();
    cy.wait('@selectLockedSubject');
    
    // Verify payment gate is shown
    cy.contains('Subscription Required').should('be.visible');
    cy.contains('$29.99/month').should('be.visible');
    cy.get('[data-testid="purchase-subscription-button"]').should('be.visible');
  });

  it('should persist user progress across page reloads', () => {
    cy.visit('/');
    
    // Complete subject selection
    cy.wait('@getSubjects');
    cy.contains('Python Programming').click();
    cy.wait('@selectSubject');
    
    // Reload page
    cy.reload();
    
    // Verify state is maintained
    cy.contains('Python Programming Selected').should('be.visible');
    
    // Continue with survey
    cy.get('[data-testid="start-survey-button"]').click();
    cy.wait('@generateSurvey');
    
    // Answer questions
    cy.contains('A container for storing data').click();
    cy.get('[data-testid="next-button"]').click();
    cy.contains('list = []').click();
    cy.get('[data-testid="submit-survey-button"]').click();
    cy.wait('@submitSurvey');
    
    // Reload again
    cy.reload();
    
    // Verify survey results are maintained
    cy.contains('intermediate').should('be.visible');
  });
});

describe('Performance and Load Testing', () => {
  it('should load the application within acceptable time limits', () => {
    const startTime = Date.now();
    
    cy.visit('/');
    cy.get('[data-testid="subject-selector"]').should('be.visible');
    
    cy.then(() => {
      const loadTime = Date.now() - startTime;
      expect(loadTime).to.be.lessThan(3000); // Should load within 3 seconds
    });
  });

  it('should handle concurrent user interactions smoothly', () => {
    cy.visit('/');
    
    // Simulate rapid user interactions
    cy.get('[data-testid="subject-selector"]').should('be.visible');
    
    // Rapid clicking should not break the interface
    for (let i = 0; i < 5; i++) {
      cy.contains('Python Programming').click();
      cy.wait(100);
    }
    
    // Interface should still be responsive
    cy.contains('Python Programming Selected').should('be.visible');
  });
});