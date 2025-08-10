// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************

// Custom command for login (if authentication is added later)
Cypress.Commands.add('login', (userId = 'test-user-123') => {
  cy.window().then((win) => {
    win.localStorage.setItem('userId', userId);
  });
});

// Custom command for clearing all data
Cypress.Commands.add('clearAppData', () => {
  cy.window().then((win) => {
    win.localStorage.clear();
    win.sessionStorage.clear();
  });
});

// Custom command for waiting for API calls to complete
Cypress.Commands.add('waitForApiCalls', () => {
  cy.intercept('GET', '/api/**').as('apiGet');
  cy.intercept('POST', '/api/**').as('apiPost');
  cy.intercept('PUT', '/api/**').as('apiPut');
  cy.intercept('DELETE', '/api/**').as('apiDelete');
});

// Custom command for testing responsive breakpoints
Cypress.Commands.add('testResponsiveBreakpoints', (callback) => {
  const breakpoints = [
    { name: 'mobile', width: 375, height: 667 },
    { name: 'tablet', width: 768, height: 1024 },
    { name: 'desktop', width: 1280, height: 720 }
  ];
  
  breakpoints.forEach(breakpoint => {
    cy.viewport(breakpoint.width, breakpoint.height);
    cy.log(`Testing ${breakpoint.name} breakpoint`);
    callback(breakpoint);
  });
});