```typescript
// FILE: wikipedia-article-verification.cy.ts
/// <reference types="cypress" />

// Test scenario: Wikipedia Article Verification
describe('TC003: Wikipedia Article Verification', () => {
  // Base URL for Wikipedia
  const baseUrl: string = 'https://www.wikipedia.org';

  // Before each test, navigate to the Wikipedia main page
  beforeEach(() => {
    cy.visit(baseUrl);
  });

  // Test case: Navigate to Wikipedia, search for Python programming language, and verify the page title
  it('should search for Python programming language and verify the page title', () => {
    // Step 1: Enter 'Python programming language' in the search field
    // Using robust selector for the search input field
    cy.get('input[name="search"]').type('Python programming language');

    // Step 2: Click the search button to submit the query
    // Using a robust selector for the search button
    cy.get('button[type="submit"]').click();

    // Step 3: Verify that the resulting page title contains the expected text
    // Using Cypress's built-in retry-ability to wait for the page title to be correct
    cy.title().should('contain', 'Python (programming language)');
  });
});
```

This code follows the specified requirements and best practices for writing a Cypress end-to-end test in TypeScript. It includes detailed comments explaining each section and uses robust selectors for interacting with the web page elements.