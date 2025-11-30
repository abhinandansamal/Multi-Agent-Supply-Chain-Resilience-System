import vertexai
from vertexai.generative_models import (
    GenerativeModel, 
    Tool, 
    Part, 
    ChatSession
)
from src.config import settings
from src.utils.logger import setup_logger
from src.tools.database_tool import query_inventory_by_region
from src.tools.search_tool import search_news
from src.tools.context_utils import compact_context

# Initialize Agent Logger
logger = setup_logger("agent_watchtower")

class WatchtowerAgent:
    """
    The Watchtower Agent implements a Proactive Monitoring Loop using the ReAct pattern.
    
    Architecture:
        - **Role**: Supply Chain Risk Analyst.
        - **Pattern**: Sequential Loop (Observation -> Thought -> Action -> Observation).
        - **Model**: Gemini (Vertex AI).
        - **Tools**: External Search (News) + Internal Database (Inventory).
        - **Optimization**: Uses Context Compaction to summarize large search results.
    
    Attributes:
        project_id (str): Google Cloud Project ID.
        location (str): Google Cloud Region (e.g., us-central1).
        model_name (str): The specific Gemini model version.
    """

    def __init__(self):
        """
        Initializes the Vertex AI environment, binds tools, and configures the Generative Model.
        """
        self.project_id = settings.GOOGLE_CLOUD_PROJECT
        self.location = settings.GOOGLE_CLOUD_REGION
        self.model_name = settings.MODEL_NAME
        
        logger.info(f"🤖 Initializing WatchtowerAgent with model: {self.model_name}")
        
        # 1. Initialize Vertex AI SDK
        vertexai.init(project=self.project_id, location=self.location)
        
        # 2. Define Tools Schema
        # This tells the LLM exactly when and how to call our Python functions.
        self.tools_schema = Tool.from_dict({
            "function_declarations": [
                {
                    "name": "search_news",
                    "description": "Search for current events, disasters, or news in a specific region.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search keywords (e.g., 'Taiwan earthquake')"}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "query_inventory_by_region",
                    "description": "Check inventory levels for a specific region.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "region": {"type": "string", "description": "Region name (e.g., 'Taiwan')"}
                        },
                        "required": ["region"]
                    }
                }
            ]
        })

        # 3. Initialize Model with System Instructions
        self.model = GenerativeModel(
            self.model_name,
            tools=[self.tools_schema],
            system_instruction="""
            You are Sentinell, an Autonomous Supply Chain Risk Monitor.
            
            PROTOCOL:
            1. You will be given a Region to monitor.
            2. First, SEARCH NEWS for that region.
            3. If the news contains risks (Earthquakes, Strikes), IMMEDIATELY query inventory for that region.
            4. If the news is safe, report "NO RISK".
            
            IMPORTANT:
            - You can think out loud before calling a tool.
            - Always use the tools provided to verify facts.
            """
        )

    def _execute_tool(self, func_name: str, func_args: dict) -> str:
        """
        Routes tool calls to the actual Python functions with error handling.

        Args:
            func_name (str): The name of the function called by the LLM.
            func_args (dict): The dictionary of arguments provided by the LLM.

        Returns:
            str: The output of the tool execution.
        """
        try:
            logger.info(f"🛠️ Executing Tool: {func_name} with args: {func_args}")
            
            if func_name == "search_news":
                # context compaction logic
                raw_news = search_news(func_args["query"])

                # We compress the news before giving it to the reasoning agent.
                # This saves tokens and focuses the agent on "Risks" only.
                compacted_news = compact_context(raw_news, max_words=100)
                
                logger.debug(f"Passing compacted context to agent: {compacted_news[:50]}...")
                
                return compacted_news
            
            elif func_name == "query_inventory_by_region":
                return query_inventory_by_region(func_args["region"])
            else:
                logger.warning(f"Attempted to call unknown tool: {func_name}")
                return f"Error: Unknown tool '{func_name}'"
                
        except Exception as e:
            logger.error(f"Tool execution failed for {func_name}: {e}")
            return f"Tool Error: {str(e)}"

    def scan_region(self, region: str) -> str:
        """
        Executes the monitoring loop for a specific region.
        
        This method handles the "Turn-Taking" between the Agent and the Tools,
        managing multi-part responses where the Agent thinks before acting.

        Args:
            region (str): The region to scan (e.g., "Taiwan").
            
        Returns:
            str: The final risk assessment report.
        """
        logger.info(f"🔄 Starting Watchtower Scan for: {region}")
        chat = self.model.start_chat()
        
        # The Trigger Prompt
        prompt = f"Monitor supply chain risks for: {region}"
        response = chat.send_message(prompt)
        
        # --- The Agentic Loop ---
        max_turns = 5
        current_turn = 0
        
        while current_turn < max_turns:
            candidate = response.candidates[0]
            function_call = None
            
            # --- ROBUST PART HANDLING ---
            # Vertex AI responses can contain (Text) OR (FunctionCall) OR (Text + FunctionCall)
            for part in candidate.content.parts:
                if part.function_call:
                    function_call = part.function_call
                    continue
                
                # If we are here, it is NOT a function call, so we try reading text
                try:
                    text_content = part.text
                    if text_content:
                        logger.info(f"🤔 Agent Thought: {text_content.strip()[:100]}...")
                except Exception:
                    pass 

            # Decision Logic
            if function_call:
                # 1. Parse Arguments
                func_name = function_call.name
                func_args = dict(function_call.args)
                
                # 2. Execute Tool
                tool_result = self._execute_tool(func_name, func_args)
                
                # 3. Feed Result back to Model
                response = chat.send_message(
                    Part.from_function_response(
                        name=func_name,
                        response={"content": tool_result}
                    )
                )
                current_turn += 1
            else:
                # No function call found -> The agent has finished its job
                logger.info("✅ Agent Scan Complete.")
                
                # Extract final text safely
                final_text = ""
                for part in candidate.content.parts:
                    try:
                        if part.text:
                            final_text += part.text
                    except Exception:
                        pass
                return final_text

        logger.warning("Agent exceeded maximum loop turns.")
        return "Error: Agent exceeded maximum loop turns."

if __name__ == "__main__":
    # Internal Manual Test
    try:
        agent = WatchtowerAgent()
        
        # We start with the critical test case
        print("\n--- 🚨 TEST 1: Scanning Taiwan (Expect CRITICAL Risk) ---")
        report = agent.scan_region("Taiwan")
        print("\n📝 AGENT REPORT:\n" + report)
        
    except Exception as e:
        print(f"❌ Test Failed: {e}")