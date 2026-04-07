// Import Cypress types for better TypeScript support
/// <reference types="cypress" />

// Define the test suite for the Google Search and Navigate scenario
describe('TC002: Google Search and Navigate', () => {
  // Base URL for the tests
  const baseUrl: string = 'https://www.google.com';

  // Before each test, navigate to the Google homepage
  beforeEach(() => {
    cy.visit(baseUrl);
  });

  // Test case: Perform a Google search and visit the first organic result
  it('should perform a Google search and navigate to the first result', () => {
    // Step 1: Type 'OpenAI ChatGPT' into the Google search input
    cy.get('input[name="q"]') // Use the name attribute for the search box
      .type('OpenAI ChatGPT', { delay: 100 }) // Simulate typing with a delay for realism
      .should('have.value', 'OpenAI ChatGPT'); // Assert that the input contains the correct text

    // Step 2: Submit the search query
    cy.get('form').submit(); // Submit the form to trigger the search

    // Step 3: Click the first organic search result link
    cy.get('#search a') // Select the first link in the search results
      .first() // Ensure it's the first result
      .should('be.visible') // Assert that the link is visible
      .click(); // Click the link to navigate

    // Optional: Add assertions to verify navigation to the expected page
    // e.g., cy.url().should('include', 'expected-domain.com');
  });

  // Optional: Handle potential cookie consent / popup dismissals
  // it('should handle cookie consent popup', () => {
  //   cy.get('button').contains('I agree').click();
  // });
});