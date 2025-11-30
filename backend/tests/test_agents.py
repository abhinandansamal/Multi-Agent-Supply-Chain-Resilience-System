import pytest
import json
import os
from typing import List, Dict, Any
from src.agents.watchtower import WatchtowerAgent

# Define the path to the dataset
# We use abspath to ensure this runs correctly regardless of where pytest is invoked
DATASET_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden_dataset.json")

# Load the Golden Dataset once at module level
with open(DATASET_PATH, "r") as f:
    SCENARIOS: List[Dict[str, Any]] = json.load(f)

@pytest.fixture(scope="module")
def agent() -> WatchtowerAgent:
    """
    Pytest Fixture: Initializes the Watchtower Agent once for the entire test module.
    
    Using scope='module' saves time and money by initializing the Vertex AI model 
    only once, rather than re-loading it for every single test case.

    Returns:
        WatchtowerAgent: An initialized instance of the agent ready for testing.
    """
    print("\n🤖 Initializing Agent for Test Suite...")
    return WatchtowerAgent()

@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_watchtower_scenarios(agent: WatchtowerAgent, scenario: Dict[str, Any]):
    """
    Evaluates the Watchtower Agent against the Golden Dataset scenarios.

    This is a Data-Driven Test. It iterates through every object in `golden_dataset.json`,
    runs the agent with that input, and verifies:
    1. The 'Risk Level' matches the expected severity (e.g., Earthquake -> Critical).
    2. Specific entities (like Part Numbers) appear in the final report.

    Args:
        agent (WatchtowerAgent): The fixture providing the agent instance.
        scenario (Dict): A single test case from the JSON dataset containing 'input', 
                         'expected_risk', and 'expected_entities'.
    
    Raises:
        AssertionError: If the agent's output contradicts the expected results.
    """
    print(f"\n🧪 Testing Scenario: {scenario['description']}")
    
    # 1. Execution Phase
    # We call the agent's main logic loop
    report = agent.scan_region(scenario["input"])
    
    # Normalize report to uppercase for robust string matching
    report_upper = report.upper()
    expected_risk = scenario["expected_risk"].upper()
    
    # 2. Validation Phase: Risk Level
    # We use conditional logic to allow for flexible LLM phrasing
    if expected_risk == "CRITICAL":
        assert "CRITICAL" in report_upper or "HIGH" in report_upper, \
            f"❌ Failure: Expected CRITICAL risk for '{scenario['input']}', but got: {report[:100]}..."
    elif expected_risk == "LOW":
        assert "CRITICAL" not in report_upper, \
            f"❌ Failure: Expected LOW risk for '{scenario['input']}', but Agent flagged it as CRITICAL."
            
    # 3. Validation Phase: Entity Recognition
    # Ensures the agent isn't just hallucinating risk, but finding the specific data points
    for entity in scenario["expected_entities"]:
        assert entity in report, \
            f"❌ Failure: Agent failed to identify the specific impacted part: '{entity}' in report."

    print(f"✅ Scenario '{scenario['id']}' Passed Successfully.")