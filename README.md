# AgenticPOC — AI-Powered Test Script Generator

A **LangChain-based AI agent** that reads test scenario definitions from a JSON file and automatically generates fully working end-to-end test scripts in two frameworks:

- **Selenium WebDriver** (Java) using the **Page Object Model (POM)** design pattern
- **Cypress** (TypeScript) using the standard `describe/it` block structure

---

## End-to-End Execution Flow

Below is a step-by-step walkthrough of exactly what happens when you run the agent against the included `scenarios.json` (using the Amazon laptop search scenario as an example).

### Step 1: Startup and Configuration (`agent.py`)

```
python agent.py
```

1. `load_dotenv()` reads the `.env` file and populates `os.environ` with your API key.
2. `load_config()` validates that the required API key exists (exits with a clear error if not).
3. `create_llm()` instantiates the LLM — either `ChatOpenAI(model="gpt-4o")` or `ChatAnthropic(model="claude-sonnet-4-20250514")` depending on `LLM_PROVIDER`.

### Step 2: Agent Construction (`agent.py → build_agent()`)

4. A `ChatPromptTemplate` is built with three messages:
   - **System message**: instructs the LLM that it is a test automation architect.
   - **Human message**: contains the task instruction (`{input}` placeholder).
   - **Agent scratchpad**: a `MessagesPlaceholder` where LangChain injects tool-call and tool-result messages during the loop.
5. `create_tool_calling_agent()` wires the LLM, tools, and prompt into a runnable.
6. `AgentExecutor` wraps the runnable, adding the think→act→observe loop.

### Step 3: Agent Invocation — The Reasoning Loop

7. `agent_executor.invoke({"input": task})` starts the agent loop.

**Iteration 1 — Read the scenarios:**

8. The LLM reads the task instruction and decides to call `read_scenarios("scenarios.json")`.
9. The `read_scenarios` tool:
   - Opens `scenarios.json` and parses it with `json.load()`.
   - Validates the structure (must be an array, each entry needs `id`, `name`, `steps`).
   - Returns a formatted string: `"Successfully loaded 3 scenario(s): ..."` with full JSON for each scenario.
10. LangChain appends the tool result to the agent scratchpad and sends the updated prompt back to the LLM.

**Iterations 2–7 — Generate tests for each scenario:**

11. The LLM sees three scenarios and decides to process them one by one.
12. For the Amazon Laptop Search scenario, the LLM calls:

    ```
    generate_selenium_test('{"id": "TC001", "name": "Amazon Laptop Search", ...}')
    ```

13. Inside the tool (`tools.py`):
    - The scenario JSON is parsed to extract the name → `"AmazonLaptopSearch"`.
    - The `SELENIUM_PROMPT` template (from `prompts.py`) is rendered with the scenario data.
    - A fresh LLM instance is created via `_get_llm()`.
    - The LLM generates Java code: `AmazonHomePage.java`, `SearchResultsPage.java`, `ProductPage.java`, and `AmazonLaptopSearchTest.java`.
    - `_extract_code_blocks()` parses the Markdown-fenced code blocks from the LLM response.
    - `_save_files()` writes each file to `output/selenium/AmazonLaptopSearch/`.
    - The tool returns: `"Selenium (Java POM) files generated for 'Amazon Laptop Search': ..."`.

14. The LLM then calls:

    ```
    generate_cypress_test('{"id": "TC001", "name": "Amazon Laptop Search", ...}')
    ```

15. Inside the tool:
    - The scenario name is converted to kebab-case → `"amazon-laptop-search"`.
    - The `CYPRESS_PROMPT` template is rendered.
    - The LLM generates a single TypeScript file: `amazon-laptop-search.cy.ts`.
    - The file is saved to `output/cypress/`.

16. Steps 12–15 repeat for the remaining scenarios (Google Search, Wikipedia).

**Final Iteration — Summary:**

17. After all tools return successfully, the LLM produces a final text answer summarizing every file generated and where it was saved.

### Step 4: Output

18. `agent.py` prints the final summary to stdout.
19. Generated files are in the `output/` directory, organized by framework.

---

## Project Structure

```
AgenticPOC/
├── agent.py           ← Main entry point: config, LLM setup, agent construction, execution
├── tools.py           ← Three LangChain tools: read_scenarios, generate_selenium_test, generate_cypress_test
├── prompts.py         ← All prompt templates (system prompt, Selenium prompt, Cypress prompt)
├── scenarios.json     ← Input: array of test scenario definitions
├── requirements.txt   ← Python dependencies with version pins and explanatory comments
├── README.md          ← This file
├── .env               ← (you create this) API keys — never committed to git
└── output/
    ├── selenium/      ← Generated Java POM files, organized by scenario name
    │   ├── AmazonLaptopSearch/
    │   │   ├── AmazonHomePage.java
    │   │   ├── SearchResultsPage.java
    │   │   └── AmazonLaptopSearchTest.java
    │   ├── GoogleSearchAndNavigate/
    │   │   └── ...
    │   └── WikipediaArticleVerification/
    │       └── ...
    └── cypress/       ← Generated TypeScript Cypress specs
        ├── amazon-laptop-search.cy.ts
        ├── google-search-and-navigate.cy.ts
        └── wikipedia-article-verification.cy.ts
```

---

## Setup Instructions

### Prerequisites

- **Python 3.10+** (check with `python --version`)
- An **OpenAI API key** (default) OR an **Anthropic API key**
- **pip** (Python package manager)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AgenticPOC
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

Create a `.env` file in the project root:

```bash
# For OpenAI (default):
OPENAI_API_KEY=sk-your-openai-key-here

# For Anthropic (set LLM_PROVIDER=anthropic to use this instead):
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
# LLM_PROVIDER=anthropic
```

Or export directly in your shell:

```bash
export OPENAI_API_KEY="sk-your-openai-key-here"
```

### 5. Run the Agent

```bash
python agent.py
```

### Configuration Options (Environment Variables)

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | (none) | Required if using OpenAI (the default provider) |
| `ANTHROPIC_API_KEY` | (none) | Required if using Anthropic |
| `LLM_PROVIDER` | `openai` | Set to `anthropic` to use Claude instead of GPT-4o |
| `AGENT_VERBOSE` | `true` | Set to `false` to suppress agent reasoning output |

---

## Output Explanation

After a successful run, the `output/` directory contains:

### `output/selenium/` — Java Page Object Model Files

Each scenario gets its own subdirectory containing:

- **Page Object classes** (`*Page.java`): one per distinct web page in the scenario. Each class encapsulates:
  - Locators (stored as `By` constants)
  - Action methods (e.g., `searchFor(String query)`)
  - A page-load verification method
- **Test class** (`*Test.java`): a TestNG test that chains Page Object calls to execute the scenario. Includes `@BeforeMethod` / `@AfterMethod` for setup/teardown.

### `output/cypress/` — TypeScript Cypress Specs

Each scenario produces a single `*.cy.ts` file containing:

- A top-level `describe` block named after the scenario
- `beforeEach` hook for common setup (e.g., `cy.visit()`)
- `it` blocks for logical test steps
- `.should()` assertions for verification

---

## Error Handling

The agent handles several edge cases:

| Scenario | Behavior |
|---|---|
| `scenarios.json` not found | `read_scenarios` tool returns a clear error; agent reports it |
| Malformed JSON | JSON parse error is caught and reported with details |
| Missing required fields | Validation identifies which scenario and which fields are missing |
| LLM returns unparseable code blocks | Fallback saves the raw LLM response as a single file |
| API key not set | Agent exits immediately with setup instructions |
| LLM produces malformed tool calls | `AgentExecutor` retries with the error message |
