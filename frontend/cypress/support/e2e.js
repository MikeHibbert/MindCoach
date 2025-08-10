// ***********************************************************
// This example support/e2e.js is processed and
// loaded automatically before your test files.
//
// This is a great place to put global configuration and
// behavior that modifies Cypress.
//
// You can change the location of this file or turn off
// automatically serving support files with the
// 'supportFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

// Import commands.js using ES2015 syntax:
import './commands'

// Alternatively you can use CommonJS syntax:
// require('./commands')

// Add accessibility testing support
import 'cypress-axe'

// Add custom commands for testing responsive design
Cypress.Commands.add('setViewport', (size) => {
  const viewports = {
    mobile: [375, 667],
    tablet: [768, 1024],
    desktop: [1280, 720]
  };
  
  if (viewports[size]) {
    cy.viewport(viewports[size][0], viewports[size][1]);
  } else {
    throw new Error(`Unknown viewport size: ${size}`);
  }
});

// Custom command for testing keyboard navigation
Cypress.Commands.add('testKeyboardNavigation', (selector, keys) => {
  cy.get(selector).focus();
  keys.forEach(key => {
    cy.get(selector).type(`{${key}}`);
  });
});

// Custom command for testing screen reader announcements
Cypress.Commands.add('checkAriaLive', (selector, expectedText) => {
  cy.get(selector).should('have.attr', 'aria-live');
  if (expectedText) {
    cy.get(selector).should('contain.text', expectedText);
  }
});

// Mock API responses for testing
Cypress.Commands.add('mockApiResponse', (method, url, response, statusCode = 200) => {
  cy.intercept(method, url, {
    statusCode,
    body: response
  });
});

// Test user journey helpers
Cypress.Commands.add('completeSubjectSelection', (subject = 'python') => {
  cy.mockApiResponse('GET', '/api/subjects*', {
    subjects: [
      { id: 'python', name: 'Python Programming', locked: false },
      { id: 'javascript', name: 'JavaScript', locked: true }
    ]
  });
  
  cy.visit('/');
  cy.get(`[data-testid="subject-card-${subject}"]`).click();
});

Cypress.Commands.add('completeSurvey', (answers = []) => {
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
  
  cy.mockApiResponse('POST', '/api/users/*/subjects/*/survey/submit', {
    success: true,
    skill_level: 'intermediate'
  });
  
  cy.get('[data-testid="survey-question-1"]').within(() => {
    cy.get('input[value="Ordered collection"]').check();
  });
  
  cy.get('[data-testid="submit-survey"]').click();
});

// Accessibility testing helpers
Cypress.Commands.add('checkAccessibility', (context = null, options = {}) => {
  cy.injectAxe();
  cy.checkA11y(context, {
    rules: {
      'color-contrast': { enabled: true },
      'keyboard-navigation': { enabled: true },
      'aria-labels': { enabled: true },
      ...options.rules
    }
  });
});

// Performance testing helpers
Cypress.Commands.add('measurePageLoad', () => {
  cy.window().then((win) => {
    const performance = win.performance;
    const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
    cy.log(`Page load time: ${loadTime}ms`);
    expect(loadTime).to.be.lessThan(3000); // 3 second threshold
  });
});