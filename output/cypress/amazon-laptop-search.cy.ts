// Import Cypress types for TypeScript support
/// <reference types="cypress" />

// Describe block for the Amazon Laptop Search scenario
describe('Amazon Laptop Search', () => {
  // Base URL for Amazon
  const baseUrl: string = 'https://www.amazon.com';

  // Before each test, navigate to the Amazon homepage
  beforeEach(() => {
    cy.visit(baseUrl);
    // Handle potential cookie consent or popups
    // Assuming there's a button with data-test attribute for dismissing popups
    cy.get('body').then(($body) => {
      if ($body.find('[data-test="cookie-consent-dismiss"]').length) {
        cy.get('[data-test="cookie-consent-dismiss"]').click();
      }
    });
  });

  // Test case for searching laptops and clicking the first result
  it('should search for laptops and click the first result', () => {
    // Step 1: Enter 'laptops' into the main search bar
    // Assuming the search box has an ID or data-test attribute
    cy.get('#twotabsearchtextbox').type('laptops');

    // Step 2: Click the search/submit button
    // Assuming the search button has a type submit or specific selector
    cy.get('#nav-search-submit-button').click();

    // Step 3: Click on the first product in the search results
    // Assuming the first result can be selected with a specific class or data-test attribute
    cy.get('.s-main-slot .s-result-item').first().within(() => {
      cy.get('h2 a').click();
    });

    // Optional: Verify that the product page loads by checking for a common element
    cy.url().should('include', '/dp/');
    cy.get('#productTitle').should('be.visible');
  });
});