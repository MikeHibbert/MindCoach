describe('Complete User Journey', () => {
  beforeEach(() => {
    cy.clearAppData();
    cy.login('test-user-123');
  });

  it('completes full learning path from subject selection to lesson viewing', () => {
    // Mock API responses for the complete journey
    cy.mockApiResponse('GET', '/api/subjects*', {
      subjects: [
        { 
          id: 'python', 
          name: 'Python Programming', 
          locked: false,
          description: 'Learn Python programming from basics to advanced'
        },
        { 
          id: 'javascript', 
          name: 'JavaScript', 
          locked: true,
          description: 'Master JavaScript for web development'
        }
      ]
    });

    cy.mockApiResponse('POST', '/api/users/*/subjects/*/select', {
      success: true,
      message: 'Subject selected successfully'
    });

    cy.mockApiResponse('GET', '/api/users/*/subjects/*/survey', {
      questions: [
        {
          id: 1,
          question: 'What is a Python list?',
          type: 'multiple_choice',
          options: ['Array', 'Dictionary', 'Ordered collection', 'Function'],
          difficulty: 'beginner'
        },
        {
          id: 2,
          question: 'How do you define a function in Python?',
          type: 'multiple_choice',
          options: ['function myFunc()', 'def myFunc():', 'func myFunc()', 'define myFunc()'],
          difficulty: 'intermediate'
        }
      ]
    });

    cy.mockApiResponse('POST', '/api/users/*/subjects/*/survey/submit', {
      success: true,
      skill_level: 'intermediate',
      analysis: {
        correct_answers: 2,
        total_questions: 2,
        percentage: 100
      }
    });

    cy.mockApiResponse('POST', '/api/users/*/subjects/*/lessons/generate', {
      success: true,
      generation_summary: {
        user_id: 'test-user-123',
        subject: 'python',
        skill_level: 'intermediate',
        total_lessons: 10,
        generated_at: '2024-01-15T10:00:00Z'
      }
    });

    cy.mockApiResponse('GET', '/api/users/*/subjects/*/lessons', {
      success: true,
      lessons: [
        {
          lesson_number: 1,
          title: 'Advanced Python Data Structures',
          estimated_time: '45 minutes',
          difficulty: 'intermediate'
        },
        {
          lesson_number: 2,
          title: 'Object-Oriented Programming',
          estimated_time: '60 minutes',
          difficulty: 'intermediate'
        }
      ]
    });

    cy.mockApiResponse('GET', '/api/users/*/subjects/*/lessons/1', {
      success: true,
      lesson: {
        lesson_number: 1,
        title: 'Advanced Python Data Structures',
        content: '# Advanced Python Data Structures\n\nThis lesson covers dictionaries, sets, and tuples...',
        estimated_time: '45 minutes',
        difficulty: 'intermediate'
      }
    });

    // Start the journey
    cy.visit('/');
    
    // Step 1: Subject Selection
    cy.get('[data-testid="subject-card-python"]').should('be.visible');
    cy.get('[data-testid="subject-card-python"]').click();
    
    // Verify subject selection was saved
    cy.get('[data-testid="selected-subject"]').should('contain', 'Python Programming');
    
    // Step 2: Take Survey
    cy.get('[data-testid="start-survey"]').click();
    
    // Answer survey questions
    cy.get('[data-testid="survey-question-1"]').within(() => {
      cy.get('input[value="Ordered collection"]').check();
    });
    
    cy.get('[data-testid="survey-question-2"]').within(() => {
      cy.get('input[value="def myFunc():"]').check();
    });
    
    cy.get('[data-testid="submit-survey"]').click();
    
    // Verify survey results
    cy.get('[data-testid="survey-results"]').should('contain', 'intermediate');
    
    // Step 3: Generate Lessons
    cy.get('[data-testid="generate-lessons"]').click();
    
    // Wait for lesson generation to complete
    cy.get('[data-testid="generation-complete"]', { timeout: 10000 }).should('be.visible');
    
    // Step 4: View Lessons
    cy.get('[data-testid="lesson-list"]').should('be.visible');
    cy.get('[data-testid="lesson-1"]').click();
    
    // Verify lesson content is displayed
    cy.get('[data-testid="lesson-content"]').should('contain', 'Advanced Python Data Structures');
    cy.get('[data-testid="lesson-title"]').should('contain', 'Advanced Python Data Structures');
    
    // Test lesson navigation
    cy.get('[data-testid="next-lesson"]').should('be.visible');
    cy.get('[data-testid="lesson-progress"]').should('be.visible');
  });

  it('handles subscription required flow', () => {
    // Mock locked subject
    cy.mockApiResponse('GET', '/api/subjects*', {
      subjects: [
        { 
          id: 'javascript', 
          name: 'JavaScript', 
          locked: true,
          description: 'Master JavaScript for web development'
        }
      ]
    });

    cy.mockApiResponse('GET', '/api/users/*/subjects/*/status', {
      access_status: {
        has_active_subscription: false,
        subscription_required: true
      }
    });

    cy.visit('/');
    
    // Try to select locked subject
    cy.get('[data-testid="subject-card-javascript"]').click();
    
    // Should show payment gate
    cy.get('[data-testid="payment-gate"]').should('be.visible');
    cy.get('[data-testid="subscription-required"]').should('contain', 'Subscription Required');
    
    // Test plan selection
    cy.get('[data-testid="plan-yearly"]').check();
    cy.get('[data-testid="selected-plan"]').should('contain', 'yearly');
    
    // Mock successful subscription
    cy.mockApiResponse('POST', '/api/users/*/subscriptions/*', {
      success: true,
      subscription: {
        status: 'active',
        expires_at: '2024-12-31T23:59:59Z'
      }
    });
    
    cy.get('[data-testid="purchase-subscription"]').click();
    
    // Should proceed to survey after successful subscription
    cy.get('[data-testid="subscription-active"]').should('be.visible');
  });

  it('tests responsive design across all breakpoints', () => {
    cy.mockApiResponse('GET', '/api/subjects*', {
      subjects: [
        { id: 'python', name: 'Python Programming', locked: false }
      ]
    });

    cy.testResponsiveBreakpoints((breakpoint) => {
      cy.visit('/');
      
      if (breakpoint.name === 'mobile') {
        // Mobile-specific tests
        cy.get('[data-testid="mobile-menu"]').should('be.visible');
        cy.get('[data-testid="subject-grid"]').should('have.class', 'grid-cols-1');
      } else if (breakpoint.name === 'tablet') {
        // Tablet-specific tests
        cy.get('[data-testid="subject-grid"]').should('have.class', 'tablet:grid-cols-2');
      } else if (breakpoint.name === 'desktop') {
        // Desktop-specific tests
        cy.get('[data-testid="sidebar"]').should('be.visible');
        cy.get('[data-testid="subject-grid"]').should('have.class', 'desktop:grid-cols-3');
      }
      
      // Test touch targets are appropriate for each breakpoint
      cy.get('[data-testid="subject-card-python"]').then($el => {
        const height = $el.height();
        if (breakpoint.name === 'mobile') {
          expect(height).to.be.at.least(44); // Minimum touch target
        }
      });
    });
  });

  it('tests accessibility compliance throughout the journey', () => {
    cy.mockApiResponse('GET', '/api/subjects*', {
      subjects: [
        { id: 'python', name: 'Python Programming', locked: false }
      ]
    });

    cy.visit('/');
    
    // Test initial page accessibility
    cy.checkAccessibility();
    
    // Test keyboard navigation
    cy.get('body').tab();
    cy.focused().should('have.attr', 'data-testid', 'subject-card-python');
    
    // Test screen reader announcements
    cy.get('[data-testid="subject-card-python"]').click();
    cy.checkAriaLive('[data-testid="status-announcement"]', 'Python Programming selected');
    
    // Test form accessibility
    cy.mockApiResponse('GET', '/api/users/*/subjects/*/survey', {
      questions: [
        {
          id: 1,
          question: 'What is a Python list?',
          type: 'multiple_choice',
          options: ['Array', 'Dictionary', 'Ordered collection', 'Function']
        }
      ]
    });
    
    cy.get('[data-testid="start-survey"]').click();
    
    // Check form has proper labels and fieldsets
    cy.get('fieldset').should('exist');
    cy.get('legend').should('exist');
    cy.get('input[type="radio"]').each($input => {
      cy.wrap($input).should('have.attr', 'aria-describedby');
    });
    
    // Test accessibility after form submission
    cy.get('input[value="Ordered collection"]').check();
    cy.get('[data-testid="submit-survey"]').click();
    
    cy.checkAccessibility();
  });

  it('handles error states gracefully', () => {
    // Test network error
    cy.mockApiResponse('GET', '/api/subjects*', {}, 500);
    
    cy.visit('/');
    
    cy.get('[data-testid="error-message"]').should('be.visible');
    cy.get('[data-testid="retry-button"]').should('be.visible');
    
    // Test retry functionality
    cy.mockApiResponse('GET', '/api/subjects*', {
      subjects: [
        { id: 'python', name: 'Python Programming', locked: false }
      ]
    });
    
    cy.get('[data-testid="retry-button"]').click();
    cy.get('[data-testid="subject-card-python"]').should('be.visible');
    
    // Test survey submission error
    cy.mockApiResponse('GET', '/api/users/*/subjects/*/survey', {
      questions: [
        {
          id: 1,
          question: 'What is a Python list?',
          type: 'multiple_choice',
          options: ['Array', 'Dictionary', 'Ordered collection', 'Function']
        }
      ]
    });
    
    cy.mockApiResponse('POST', '/api/users/*/subjects/*/survey/submit', {}, 400);
    
    cy.get('[data-testid="subject-card-python"]').click();
    cy.get('[data-testid="start-survey"]').click();
    cy.get('input[value="Ordered collection"]').check();
    cy.get('[data-testid="submit-survey"]').click();
    
    cy.get('[data-testid="survey-error"]').should('be.visible');
    cy.get('[data-testid="retry-survey"]').should('be.visible');
  });

  it('measures and validates performance', () => {
    cy.mockApiResponse('GET', '/api/subjects*', {
      subjects: [
        { id: 'python', name: 'Python Programming', locked: false }
      ]
    });

    cy.visit('/');
    
    // Measure initial page load
    cy.measurePageLoad();
    
    // Test that interactions are responsive
    cy.get('[data-testid="subject-card-python"]').click();
    
    // Measure time to interactive elements
    cy.get('[data-testid="start-survey"]').should('be.visible');
    
    // Test that large content loads efficiently
    cy.mockApiResponse('GET', '/api/users/*/subjects/*/lessons/1', {
      success: true,
      lesson: {
        lesson_number: 1,
        title: 'Advanced Python Data Structures',
        content: '# Advanced Python Data Structures\n\n' + 'Large content here...'.repeat(1000),
        estimated_time: '45 minutes',
        difficulty: 'intermediate'
      }
    });
    
    const startTime = Date.now();
    cy.get('[data-testid="view-lesson-1"]').click();
    cy.get('[data-testid="lesson-content"]').should('be.visible').then(() => {
      const loadTime = Date.now() - startTime;
      expect(loadTime).to.be.lessThan(2000); // 2 second threshold for content loading
    });
  });
});