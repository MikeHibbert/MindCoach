describe('Responsive Design Tests', () => {
  beforeEach(() => {
    cy.clearAppData();
    cy.login('test-user-123');
    
    // Mock basic API responses
    cy.mockApiResponse('GET', '/api/subjects*', {
      subjects: [
        { id: 'python', name: 'Python Programming', locked: false },
        { id: 'javascript', name: 'JavaScript', locked: true },
        { id: 'react', name: 'React', locked: false }
      ]
    });
  });

  describe('Mobile Layout (375px)', () => {
    beforeEach(() => {
      cy.setViewport('mobile');
    });

    it('displays mobile-optimized subject selection', () => {
      cy.visit('/');
      
      // Check mobile layout structure
      cy.get('[data-testid="mobile-layout"]').should('be.visible');
      cy.get('[data-testid="sidebar"]').should('not.be.visible');
      
      // Check subject grid is single column
      cy.get('[data-testid="subject-grid"]').should('have.class', 'grid-cols-1');
      
      // Check touch targets are large enough (minimum 44px)
      cy.get('[data-testid^="subject-card-"]').each($card => {
        cy.wrap($card).then($el => {
          const height = $el.height();
          expect(height).to.be.at.least(44);
        });
      });
      
      // Test mobile navigation
      cy.get('[data-testid="mobile-menu-button"]').should('be.visible');
      cy.get('[data-testid="mobile-menu-button"]').click();
      cy.get('[data-testid="mobile-menu"]').should('be.visible');
    });

    it('handles mobile survey interface', () => {
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

      cy.visit('/');
      cy.get('[data-testid="subject-card-python"]').click();
      cy.get('[data-testid="start-survey"]').click();
      
      // Check mobile survey layout
      cy.get('[data-testid="survey-container"]').should('have.class', 'mobile:px-4');
      
      // Check radio buttons have large touch targets
      cy.get('input[type="radio"]').each($radio => {
        cy.wrap($radio).parent().then($label => {
          const height = $label.height();
          expect(height).to.be.at.least(44);
        });
      });
      
      // Test mobile form submission
      cy.get('input[value="Ordered collection"]').check();
      cy.get('[data-testid="submit-survey"]').should('be.visible');
      cy.get('[data-testid="submit-survey"]').click();
    });

    it('displays mobile-optimized lesson viewer', () => {
      cy.mockApiResponse('GET', '/api/users/*/subjects/*/lessons/1', {
        success: true,
        lesson: {
          lesson_number: 1,
          title: 'Advanced Python Data Structures',
          content: '# Advanced Python Data Structures\n\nThis lesson covers...',
          estimated_time: '45 minutes'
        }
      });

      cy.visit('/lessons/python/1');
      
      // Check mobile lesson layout
      cy.get('[data-testid="lesson-viewer"]').should('have.class', 'mobile:px-4');
      
      // Check mobile navigation buttons
      cy.get('[data-testid="mobile-lesson-nav"]').should('be.visible');
      cy.get('[data-testid="prev-lesson-mobile"]').should('have.css', 'min-height', '44px');
      cy.get('[data-testid="next-lesson-mobile"]').should('have.css', 'min-height', '44px');
    });
  });

  describe('Tablet Layout (768px)', () => {
    beforeEach(() => {
      cy.setViewport('tablet');
    });

    it('displays tablet-optimized subject selection', () => {
      cy.visit('/');
      
      // Check tablet layout structure
      cy.get('[data-testid="tablet-layout"]').should('be.visible');
      
      // Check subject grid is two columns
      cy.get('[data-testid="subject-grid"]').should('have.class', 'tablet:grid-cols-2');
      
      // Check stacked navigation
      cy.get('[data-testid="tablet-nav"]').should('be.visible');
      
      // Test tablet touch targets
      cy.get('[data-testid^="subject-card-"]').each($card => {
        cy.wrap($card).then($el => {
          const height = $el.height();
          expect(height).to.be.at.least(44);
        });
      });
    });

    it('handles tablet survey interface', () => {
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

      cy.visit('/');
      cy.get('[data-testid="subject-card-python"]').click();
      cy.get('[data-testid="start-survey"]').click();
      
      // Check tablet survey layout
      cy.get('[data-testid="survey-container"]').should('have.class', 'tablet:px-6');
      
      // Check tablet form layout
      cy.get('[data-testid="survey-form"]').should('have.class', 'tablet:max-w-2xl');
    });

    it('displays tablet-optimized payment interface', () => {
      cy.mockApiResponse('GET', '/api/users/*/subjects/*/status', {
        access_status: {
          has_active_subscription: false,
          subscription_required: true
        }
      });

      cy.visit('/');
      cy.get('[data-testid="subject-card-javascript"]').click();
      
      // Check tablet payment layout
      cy.get('[data-testid="payment-gate"]').should('be.visible');
      cy.get('[data-testid="plan-selection"]').should('have.class', 'tablet:grid-cols-2');
      
      // Test tablet plan selection
      cy.get('[data-testid="plan-yearly"]').should('have.css', 'min-height', '44px');
    });
  });

  describe('Desktop Layout (1280px)', () => {
    beforeEach(() => {
      cy.setViewport('desktop');
    });

    it('displays desktop-optimized subject selection', () => {
      cy.visit('/');
      
      // Check desktop layout structure
      cy.get('[data-testid="desktop-layout"]').should('be.visible');
      cy.get('[data-testid="sidebar"]').should('be.visible');
      
      // Check subject grid is three columns
      cy.get('[data-testid="subject-grid"]').should('have.class', 'desktop:grid-cols-3');
      
      // Check sidebar navigation
      cy.get('[data-testid="sidebar-nav"]').should('be.visible');
      cy.get('[data-testid="sidebar-nav"]').within(() => {
        cy.get('a').should('have.length.at.least', 3);
      });
    });

    it('handles desktop survey interface', () => {
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

      cy.visit('/');
      cy.get('[data-testid="subject-card-python"]').click();
      cy.get('[data-testid="start-survey"]').click();
      
      // Check desktop survey layout
      cy.get('[data-testid="survey-container"]').should('have.class', 'desktop:px-8');
      
      // Check desktop form layout with sidebar
      cy.get('[data-testid="main-content"]').should('have.class', 'desktop:ml-64');
    });

    it('displays desktop-optimized lesson viewer', () => {
      cy.mockApiResponse('GET', '/api/users/*/subjects/*/lessons/1', {
        success: true,
        lesson: {
          lesson_number: 1,
          title: 'Advanced Python Data Structures',
          content: '# Advanced Python Data Structures\n\nThis lesson covers...',
          estimated_time: '45 minutes'
        }
      });

      cy.visit('/lessons/python/1');
      
      // Check desktop lesson layout
      cy.get('[data-testid="lesson-viewer"]').should('have.class', 'desktop:max-w-4xl');
      
      // Check desktop navigation
      cy.get('[data-testid="desktop-lesson-nav"]').should('be.visible');
      cy.get('[data-testid="lesson-sidebar"]').should('be.visible');
    });
  });

  describe('Responsive Breakpoint Transitions', () => {
    it('smoothly transitions between breakpoints', () => {
      cy.visit('/');
      
      // Start at desktop
      cy.setViewport('desktop');
      cy.get('[data-testid="desktop-layout"]').should('be.visible');
      
      // Transition to tablet
      cy.setViewport('tablet');
      cy.get('[data-testid="tablet-layout"]').should('be.visible');
      cy.get('[data-testid="desktop-layout"]').should('not.be.visible');
      
      // Transition to mobile
      cy.setViewport('mobile');
      cy.get('[data-testid="mobile-layout"]').should('be.visible');
      cy.get('[data-testid="tablet-layout"]').should('not.be.visible');
      
      // Transition back to desktop
      cy.setViewport('desktop');
      cy.get('[data-testid="desktop-layout"]').should('be.visible');
      cy.get('[data-testid="mobile-layout"]').should('not.be.visible');
    });

    it('maintains functionality across all breakpoints', () => {
      const testFunctionality = () => {
        // Test subject selection works
        cy.get('[data-testid="subject-card-python"]').click();
        cy.get('[data-testid="selected-subject"]').should('contain', 'Python');
        
        // Reset for next breakpoint
        cy.reload();
      };

      // Test on each breakpoint
      cy.setViewport('mobile');
      testFunctionality();
      
      cy.setViewport('tablet');
      testFunctionality();
      
      cy.setViewport('desktop');
      testFunctionality();
    });
  });

  describe('Touch Target Accessibility', () => {
    it('ensures all interactive elements meet touch target requirements', () => {
      const breakpoints = ['mobile', 'tablet'];
      
      breakpoints.forEach(breakpoint => {
        cy.setViewport(breakpoint);
        cy.visit('/');
        
        // Test subject cards
        cy.get('[data-testid^="subject-card-"]').each($card => {
          cy.wrap($card).then($el => {
            const rect = $el[0].getBoundingClientRect();
            expect(Math.min(rect.width, rect.height)).to.be.at.least(44);
          });
        });
        
        // Test buttons
        cy.get('button').each($button => {
          cy.wrap($button).then($el => {
            const rect = $el[0].getBoundingClientRect();
            expect(Math.min(rect.width, rect.height)).to.be.at.least(44);
          });
        });
      });
    });
  });

  describe('Content Overflow and Scrolling', () => {
    it('handles content overflow properly on small screens', () => {
      cy.setViewport('mobile');
      
      // Mock lesson with long content
      cy.mockApiResponse('GET', '/api/users/*/subjects/*/lessons/1', {
        success: true,
        lesson: {
          lesson_number: 1,
          title: 'Very Long Lesson Title That Should Wrap Properly on Mobile Devices',
          content: '# Very Long Content\n\n' + 'This is a very long lesson content that should scroll properly on mobile devices. '.repeat(100),
          estimated_time: '45 minutes'
        }
      });

      cy.visit('/lessons/python/1');
      
      // Check that content is scrollable
      cy.get('[data-testid="lesson-content"]').should('be.visible');
      cy.get('[data-testid="lesson-content"]').scrollTo('bottom');
      cy.get('[data-testid="lesson-content"]').scrollTo('top');
      
      // Check that title wraps properly
      cy.get('[data-testid="lesson-title"]').should('be.visible');
    });

    it('maintains proper spacing and margins across breakpoints', () => {
      const checkSpacing = (breakpoint) => {
        cy.setViewport(breakpoint);
        cy.visit('/');
        
        // Check container margins
        cy.get('[data-testid="main-container"]').should('have.css', 'margin-left');
        cy.get('[data-testid="main-container"]').should('have.css', 'margin-right');
        
        // Check content padding
        cy.get('[data-testid="content-area"]').should('have.css', 'padding');
      };

      ['mobile', 'tablet', 'desktop'].forEach(checkSpacing);
    });
  });
});