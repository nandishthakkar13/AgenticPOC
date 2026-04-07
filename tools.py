import json
import os
import re
from pathlib import Path


from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from prompts import SELENIUM_PROMPT, CYPRESS_PROMPT

OUTPUT_DIR = Path("output")


SELENIUM_OUT = OUTPUT_DIR / "selenium"
CYPRESS_OUT = OUTPUT_DIR / "cypress"


# =============================================================================
# Helper: get the configured LLM instance
# =============================================================================
def _get_llm():
    """
    Return a LangChain chat-model instance based on environment configuration.

    Design decision — factory function vs. module-level global:
      We use a factory so that:
        • The LLM is not instantiated at import time (avoids crashes if the
          API key is missing and the user only wants to run tests).
        • Each tool call gets a fresh instance, which avoids shared mutable
          state across concurrent invocations.

    The function checks the LLM_PROVIDER env var:
      - "anthropic" → ChatAnthropic (Claude 3.5 Sonnet)
      - anything else → ChatOpenAI (GPT-4o, the default)

    Why GPT-4o as default?
      At time of writing GPT-4o offers the best balance of speed, cost, and
      code-generation quality in the LangChain ecosystem.  Claude 3.5 Sonnet
      is a strong alternative and is available via the env-var switch.
    """

    provider = os.environ.get("LLM_PROVIDER", "openai").lower()

    if provider == "anthropic":
        return ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0.2,
        )
    else:
        return ChatOpenAI(
            model="gpt-4o",
            temperature=0.2,
        )


# =============================================================================
# Helper: extract code blocks from LLM markdown responses
# =============================================================================
def _extract_code_blocks(text: str) -> list[dict[str, str]]:
    """
    Parse an LLM response and return a list of {filename, code} dicts.

    LLMs typically wrap code in fenced blocks like:

        // FILE: HomePage.java
        ```java
        public class HomePage { ... }
        ```

    This function uses a regex to find every such block and pairs it with
    the filename comment that precedes it.

    Why regex instead of a proper Markdown parser?
      The LLM output is *almost* Markdown but not guaranteed to be valid.
      A regex is more tolerant of minor formatting quirks (extra blank lines,
      inconsistent fence lengths, etc.) and has zero external dependencies.

    Returns:
        A list of dicts, each with 'filename' and 'code' keys.
    """
    # This pattern captures:
    #   Group 1 — the filename from a "// FILE: <name>" comment line (single line only)
    #   Group 2 — everything inside the next fenced code block
    # Filename must not contain newlines to avoid capturing code in the filename
    pattern = r"//\s*FILE:\s*([^\n]+?)\s*\n\s*```[^\n]*\n(.*?)\n\s*```"
    matches = re.findall(pattern, text, re.DOTALL)

    # Build a clean list of filename/code pairs.
    results = []
    for filename, code in matches:
        # Clean up filename: remove quotes, extra whitespace
        filename_clean = filename.strip().strip('"\'')
        code_clean = code.strip()

        # Only add if we have a valid filename
        if filename_clean and not '\n' in filename_clean:
            results.append({
                "filename": filename_clean,
                "code": code_clean,
            })

    return results


# =============================================================================
# Helper: save code files to disk
# =============================================================================
def _save_files(files: list[dict[str, str]], output_dir: Path) -> list[str]:
    """
    Write a list of {filename, code} dicts to the given output directory.

    Creates the output directory (and any parents) if it does not exist.

    Args:
        files:      List of dicts with 'filename' and 'code' keys.
        output_dir: Target directory (e.g., output/selenium).

    Returns:
        List of absolute file paths that were written (for logging/summary).

    Why not return the code content?
      The agent only needs to know *where* files were saved so it can report
      the result.  Returning full code content would bloat the agent's context.
    """
    # Ensure the directory tree exists; exist_ok=True avoids errors if it
    # was already created by a previous tool call.
    os.makedirs(output_dir, exist_ok=True)

    saved_paths = []
    for file_info in files:
        # Validate and clean the filename
        filename = file_info.get("filename", "").strip()
        code = file_info.get("code", "")

        # Skip files with invalid filenames
        if not filename or '\n' in filename or '\r' in filename:
            print(f"⚠️ Skipping invalid filename: {repr(filename)}")
            continue

        # Remove any path traversal attempts
        filename = filename.replace('\\', '/').split('/')[-1]

        # Construct the full path for this file.
        file_path = output_dir / filename

        # Write the code to disk using UTF-8 encoding.
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        # Track the saved path for the summary.
        saved_paths.append(str(file_path))

    return saved_paths


# =============================================================================
# TOOL 1: read_scenarios
# =============================================================================
@tool
def read_scenarios(file_path: str) -> str:
    """
    Read and validate test scenarios from a JSON file.

    This tool is the agent's "eyes" — it loads the scenario definitions so
    the agent can reason about what tests to generate.  It performs basic
    validation (file exists, valid JSON, expected structure) and returns a
    formatted string the agent can include in subsequent LLM calls.

    Args:
        file_path: Path to the JSON file containing test scenarios.

    Returns:
        A formatted string with all scenarios, or an error message.

    Error handling philosophy:
        We catch specific exceptions and return human-readable error messages
        rather than letting raw tracebacks propagate.  This is intentional —
        the LLM agent needs to *understand* what went wrong so it can decide
        whether to retry, ask the user, or abort.  A raw traceback gives it
        no actionable information.
    """
    # --- Guard: file existence ---
    # Check before attempting to open so we can give a clear error message
    # instead of a generic FileNotFoundError traceback.
    if not os.path.exists(file_path):
        return f"ERROR: File '{file_path}' not found. Please ensure the scenarios file exists."

    try:
        # Open and parse the JSON file.
        with open(file_path, "r", encoding="utf-8") as f:
            scenarios = json.load(f)
    except json.JSONDecodeError as e:
        # Return the specific parse error so the agent can report it.
        return f"ERROR: File '{file_path}' contains invalid JSON. Details: {str(e)}"

    # --- Guard: expected structure ---
    # The file must contain a JSON array (list) of scenario objects.
    if not isinstance(scenarios, list):
        return "ERROR: Expected a JSON array of scenarios, but got a different structure."

    # --- Guard: non-empty ---
    if len(scenarios) == 0:
        return "ERROR: The scenarios file is empty (0 scenarios found)."

    # --- Validate each scenario has required fields ---
    required_fields = ["id", "name", "steps"]
    for i, scenario in enumerate(scenarios):
        missing = [f for f in required_fields if f not in scenario]
        if missing:
            return (
                f"ERROR: Scenario at index {i} is missing required fields: "
                f"{', '.join(missing)}. Each scenario needs: {', '.join(required_fields)}."
            )

    # --- Build a human-readable summary for the agent ---
    # We include the full JSON for each scenario because the generation tools
    # need the complete step details.  We also prepend a summary count so the
    # agent knows how many scenarios to process.
    result_parts = [f"Successfully loaded {len(scenarios)} scenario(s):\n"]

    for scenario in scenarios:
        result_parts.append(f"--- Scenario: {scenario['name']} (ID: {scenario['id']}) ---")
        result_parts.append(f"Steps: {len(scenario['steps'])}")
        # Include the full JSON so downstream tools have all the details.
        result_parts.append(json.dumps(scenario, indent=2))
        result_parts.append("")  # blank line between scenarios

    return "\n".join(result_parts)


# =============================================================================
# TOOL 2: generate_selenium_test
# =============================================================================
@tool
def generate_selenium_test(scenario_json: str) -> str:
    """
    Generate Selenium WebDriver test code in Java (Page Object Model) for a single scenario.

    This tool takes the raw JSON string of one scenario, renders it into the
    Selenium prompt template (from prompts.py), sends it to the configured LLM,
    parses the response to extract Java files, and saves them to output/selenium/.

    Args:
        scenario_json: A JSON string representing a single test scenario.

    Returns:
        A summary of files generated, or an error message.

    Why does this tool call the LLM directly instead of returning a prompt?
        In LangChain's tool-use pattern, a tool is expected to *do the work*
        and return the result.  The agent orchestrates which tools to call and
        in what order, but each tool is a self-contained unit of work.  Having
        the tool own the LLM call means:
          • The agent's context window is not bloated with generated code.
          • The tool can retry internally if the LLM produces unparseable output.
          • The tool's input/output contract is simple: JSON in, summary out.
    """
    try:
        # Parse the scenario JSON to extract the name (used for file naming).
        scenario = json.loads(scenario_json)
        # Convert the scenario name to PascalCase for Java class naming.
        # e.g., "Amazon Laptop Search" → "AmazonLaptopSearch"
        scenario_name = scenario.get("name", "UnknownScenario").replace(" ", "")
    except json.JSONDecodeError:
        return "ERROR: Invalid JSON provided for the scenario."

    # Render the prompt template with the scenario data.
    # .format() fills in {scenario_json} and {scenario_name} placeholders.
    prompt_text = SELENIUM_PROMPT.format(
        scenario_json=scenario_json,
        scenario_name=scenario_name,
    )


    llm = _get_llm()

    response = llm.invoke(prompt_text)
    response_text = response.content
    files = _extract_code_blocks(response_text)

    # --- Fallback: if parsing found no files, save the raw response ---
    # This can happen if the LLM uses a slightly different formatting.
    # Saving the raw output ensures we never silently lose generated code.
    if not files:
        files = [{"filename": f"{scenario_name}Test.java", "code": response_text}]

    # Create a scenario-specific subdirectory so files from different
    # scenarios don't collide (e.g., two scenarios might both have a "HomePage.java").
    scenario_dir = SELENIUM_OUT / scenario_name
    saved = _save_files(files, scenario_dir)

    # Return a concise summary for the agent to include in its final report.
    return f"Selenium (Java POM) files generated for '{scenario['name']}':\n" + "\n".join(
        f"  - {path}" for path in saved
    )


# =============================================================================
# TOOL 3: generate_cypress_test
# =============================================================================
@tool
def generate_cypress_test(scenario_json: str) -> str:
    """
    Generate a Cypress end-to-end test in TypeScript for a single scenario.

    This tool mirrors generate_selenium_test but targets the Cypress framework.
    It takes a scenario JSON string, renders the Cypress prompt, calls the LLM,
    extracts the TypeScript code, and saves it to output/cypress/.

    Args:
        scenario_json: A JSON string representing a single test scenario.

    Returns:
        A summary of files generated, or an error message.

    Why separate tools for Selenium and Cypress instead of one parameterized tool?
        Keeping them separate gives the agent maximum flexibility:
          • It can generate Selenium for all scenarios first, then Cypress, or
            alternate between them — whatever the LLM judges most efficient.
          • Each tool has its own prompt template tuned for that framework's
            idioms and best practices.
          • If one framework's generation fails, the other is unaffected.
        A single parameterized tool would be slightly less code but would
        force both frameworks through the same control flow and make error
        handling more complex.
    """
    try:
        # Parse the scenario JSON to extract the name for file naming.
        scenario = json.loads(scenario_json)
        # Convert to kebab-case for Cypress file naming convention.
        # e.g., "Amazon Laptop Search" → "amazon-laptop-search"
        scenario_name = scenario.get("name", "unknown-scenario").replace(" ", "-").lower()
    except json.JSONDecodeError:
        return "ERROR: Invalid JSON provided for the scenario."


    prompt_text = CYPRESS_PROMPT.format(
        scenario_json=scenario_json,
        scenario_name=scenario_name,
    )

    llm = _get_llm()
    response = llm.invoke(prompt_text)
    response_text = response.content
    files = _extract_code_blocks(response_text)

    # Fallback: save raw response if parsing fails.
    if not files:
        files = [{"filename": f"{scenario_name}.cy.ts", "code": response_text}]

    # Save to the Cypress output directory (no subdirectory needed since
    # each scenario produces a single .cy.ts file, and filenames are unique).
    saved = _save_files(files, CYPRESS_OUT)

    # Return a concise summary.
    return f"Cypress (TypeScript) test generated for '{scenario['name']}':\n" + "\n".join(
        f"  - {path}" for path in saved
    )


ALL_TOOLS = [read_scenarios, generate_selenium_test, generate_cypress_test]
