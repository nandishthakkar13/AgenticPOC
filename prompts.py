
from langchain_core.prompts import PromptTemplate

SYSTEM_PROMPT = """You are a senior test automation architect.  Your job is to:
1. Read test scenario definitions from a JSON file.
2. For each scenario, generate TWO test scripts:
   a) A Selenium WebDriver test in Java using the Page Object Model (POM).
   b) A Cypress test in TypeScript using describe/it blocks.
3. Save every generated script to the appropriate output folder.

Rules you MUST follow:
- Always read the scenarios file first before generating any code.
- Generate Selenium and Cypress scripts for EVERY scenario in the file.
- Selenium output MUST follow POM: separate Page classes and a Test class.
- Cypress output MUST use TypeScript and follow describe/it structure.
- Include meaningful comments in all generated code.
- After processing all scenarios, report a summary of what was generated."""


SELENIUM_PROMPT = PromptTemplate(
    # input_variables tells LangChain which placeholders to expect.
    input_variables=["scenario_json", "scenario_name"],
    template="""Generate a complete Selenium WebDriver test in Java using the Page Object Model (POM) design pattern for the following test scenario.

SCENARIO:
{scenario_json}

REQUIREMENTS:
1. Create Page Object classes for each distinct page involved in the scenario.
   - Each Page class must:
     • Be in a file named <PageName>Page.java
     • Store all locators as private static final By fields at the top of the class
     • Accept a WebDriver instance via the constructor
     • Expose public action methods (e.g., searchFor, clickFirstResult) that return
       either void or the next Page object for fluent chaining
     • Include a method to verify the page is loaded (e.g., isLoaded)
2. Create a Test class named {scenario_name}Test.java that:
   - Uses TestNG annotations (@BeforeMethod, @Test, @AfterMethod)
   - Instantiates ChromeDriver in setup and quits in teardown
   - Calls Page Object methods to execute the scenario steps
   - Includes at least one assertion per scenario step where applicable
3. Add detailed comments explaining each section of the code.
4. Use explicit waits (WebDriverWait) instead of Thread.sleep.
5. Import all necessary packages.

IMPORTANT: Return the code in the following format — one code block per file,
each preceded by a comment line with the filename:

// FILE: <filename>.java
```java
<code>
```

Generate ALL required files now.""",
)



CYPRESS_PROMPT = PromptTemplate(
    input_variables=["scenario_json", "scenario_name"],
    template="""Generate a complete Cypress end-to-end test in TypeScript for the following test scenario.

SCENARIO:
{scenario_json}

REQUIREMENTS:
1. Use the describe/it block structure (Mocha BDD style).
2. The test file must be named {scenario_name}.cy.ts
3. Use Cypress best practices:
   - cy.visit() for navigation
   - cy.get() with robust selectors (data-test attributes preferred, fall back to CSS/ID)
   - cy.contains() for text-based element selection where appropriate
   - .should() assertions to verify expected outcomes
   - No cy.wait() with arbitrary timeouts — use Cypress's built-in retry-ability instead
4. Structure the spec as:
   - A top-level describe block named after the scenario
   - A beforeEach hook that handles common setup (e.g., visiting the base URL)
   - Individual it blocks for logical groupings of steps
5. Add detailed comments explaining each section.
6. Include proper TypeScript typing where applicable.
7. Handle potential cookie consent / popup dismissals if relevant to the site.

IMPORTANT: Return the code in exactly this format:

// FILE: {scenario_name}.cy.ts
```typescript
<code>
```

Generate the complete test file now.""",
)

