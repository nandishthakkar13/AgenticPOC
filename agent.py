
import os
import sys

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from tools import ALL_TOOLS
from prompts import SYSTEM_PROMPT


# =============================================================================
# Configuration Loader
# =============================================================================
def load_config():
    """
    Load environment variables and validate that required API keys are present.

    This function is called once at startup.  It:
      1. Loads .env file if present (for local development).
      2. Checks that the required API key for the selected LLM provider exists.
      3. Exits with a clear error message if configuration is missing.

    Design decision — fail fast:
        We validate configuration *before* building the agent so the user
        gets an immediate, actionable error ("set OPENAI_API_KEY") rather
        than a cryptic 401 error three tool calls deep.

    Returns:
        A dict with configuration values: {"provider": str, "verbose": bool}
    """

    load_dotenv(override=False)


    provider = os.environ.get("LLM_PROVIDER", "openai").lower()

    # Validate that the appropriate API key is present.
    if provider == "anthropic":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
            print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
            print("Or add it to a .env file in the project root.")
            sys.exit(1)
    else:
        if not os.environ.get("OPENAI_API_KEY"):
            print("ERROR: OPENAI_API_KEY environment variable is not set.")
            print("Set it with: export OPENAI_API_KEY='your-key-here'")
            print("Or add it to a .env file in the project root.")
            sys.exit(1)

    verbose = os.environ.get("AGENT_VERBOSE", "true").lower() == "true"

    return {"provider": provider, "verbose": verbose}


# =============================================================================
# LLM Factory
# =============================================================================
def create_llm(provider: str):
    """
    Instantiate the appropriate LangChain chat model based on the provider.

    Args:
        provider: Either "openai" or "anthropic".

    Returns:
        A LangChain ChatModel instance (ChatOpenAI or ChatAnthropic).

    Why a factory function instead of a global?
        • Testability — tests can call create_llm("openai") without touching env vars.
        • Clarity — the caller explicitly chooses the provider.
        • Avoids import-time side effects (network calls, API key validation).

    Why temperature=0?
        We want deterministic, reproducible output.  Code generation benefits
        from low temperature because creative variation in code structure makes
        the output harder to validate and less consistent across runs.
        (The tools in tools.py use 0.2 for the code-generation calls to allow
        slight variation in comments and naming; the agent's own reasoning
        uses 0 for maximum reliability.)
    """
    if provider == "anthropic":
        return ChatAnthropic(
            model="claude-sonnet-4-20250514",  # Claude 3.5 Sonnet — fast, capable
            temperature=0,                # deterministic agent reasoning
        )
    else:
        return ChatOpenAI(
            model="gpt-4o",              # GPT-4o — best speed/quality ratio
            temperature=0,                # deterministic agent reasoning
        )


# =============================================================================
# Agent Builder
# =============================================================================
def build_agent(llm, tools, verbose: bool = True):
    """
    Construct the LangChain tool-calling agent and its executor.

    This function:
      1. Builds a ChatPromptTemplate with system message, user input, and
         an agent_scratchpad placeholder for intermediate tool call/result
         messages.
      2. Creates a tool-calling agent runnable using create_tool_calling_agent.
      3. Wraps it in an AgentExecutor that manages the tool-call loop.

    Args:
        llm:     A LangChain ChatModel (ChatOpenAI or ChatAnthropic).
        tools:   List of LangChain Tool objects the agent can invoke.
        verbose: If True, print agent reasoning to stdout.

    Returns:
        An AgentExecutor instance ready to be invoked.

    Architecture notes:
    -------------------
    The AgentExecutor runs a loop:
      1. Send the prompt (system + user message + scratchpad) to the LLM.
      2. The LLM returns either a final answer OR one or more tool calls.
      3. If tool calls: execute them, append results to scratchpad, go to 1.
      4. If final answer: return it to the caller.

    max_iterations=25:
        Safety limit to prevent infinite loops.  With 3 scenarios × 2 tools
        per scenario + 1 read call = 7 tool calls, so 25 is generous.

    handle_parsing_errors=True:
        If the LLM produces malformed tool calls (rare with native tool
        calling, but possible), the executor will send the error back to the
        LLM and let it retry instead of crashing.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(
        llm=llm,
        tools=tools,
        prompt=prompt,
    )

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,            # Print reasoning steps to stdout
        max_iterations=25,          # Safety net against infinite loops
        handle_parsing_errors=True, # Recover from malformed LLM output
    )

    return executor


# =============================================================================
# Main — Entry Point
# =============================================================================
def main():
    """
    Top-level function that ties everything together.

    Execution flow:
      1. Load and validate configuration (API keys, provider choice).
      2. Instantiate the LLM.
      3. Build the agent with all tools.
      4. Invoke the agent with the task instruction.
      5. Print the agent's final output.

    Why a main() function instead of top-level code?
        • Keeps the module importable without side effects (important for testing).
        • Follows the standard Python entry-point pattern.
        • Makes the execution flow explicit and easy to follow.
    """

    print("=" * 70)
    print("  AgenticPOC — AI-Powered Test Script Generator")
    print("=" * 70)
    print()

    config = load_config()
    print(f"LLM Provider: {config['provider']}")
    print(f"Verbose mode: {config['verbose']}")
    print()

    llm = create_llm(config["provider"])
    print(f"LLM initialized: {llm.__class__.__name__}")


    agent_executor = build_agent(
        llm=llm,
        tools=ALL_TOOLS,
        verbose=config["verbose"],
    )
    print(f"Agent built with {len(ALL_TOOLS)} tools: "
          f"{', '.join(t.name for t in ALL_TOOLS)}")
    print()

    task = (
        "Process the file 'scenarios.json' in the current directory. "
        "For each scenario in the file:\n"
        "1. First, use the read_scenarios tool to load and validate the scenarios.\n"
        "2. Then, for each scenario, generate BOTH a Selenium WebDriver test "
        "(Java POM) and a Cypress test (TypeScript).\n"
        "3. Pass each scenario's COMPLETE JSON as a string to the generation tools.\n"
        "4. After processing all scenarios, provide a summary of all generated files."
    )

    print("Sending task to agent...")
    print("-" * 70)
    print()

    result = agent_executor.invoke({"input": task})

    print()
    print("=" * 70)
    print("  AGENT COMPLETED — Final Summary")
    print("=" * 70)
    # The result dict has an "output" key with the agent's final text answer.
    print(result["output"])
    print()

if __name__ == "__main__":
    main()
