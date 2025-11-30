import vertexai
import json
from vertexai.generative_models import (
    GenerativeModel, 
    Tool, 
    Part
)
from src.config import settings
from src.utils.logger import setup_logger
from src.tools.supplier_tool import order_parts_from_supplier, get_price_quote
from src.memory.memory_bank import MemoryBank

# Initialize Agent Logger
logger = setup_logger("agent_procurement")

class ProcurementAgent:
    """
    The Procurement Agent is responsible for executing purchase orders.

    It uses Long-Term Memory to avoid unreliable suppliers.
    
    Architecture:
        - **Role**: Supply Chain Buyer.
        - **Goal**: Secure inventory when risks are detected.
        - **Tools**: Supplier Tool (A2A Protocol).
    
    Attributes:
        project_id (str): Google Cloud Project ID.
        location (str): Google Cloud Region.
        model_name (str): Gemini Model Version.
    """

    def __init__(self):
        """Initializes the Vertex AI model and binds the Supplier Tool."""
        self.project_id = settings.GOOGLE_CLOUD_PROJECT
        self.location = settings.GOOGLE_CLOUD_REGION
        self.model_name = settings.MODEL_NAME

        # Initialize Memory Bank
        self.memory = MemoryBank()
        
        logger.info(f"🤖 Initializing ProcurementAgent with model: {self.model_name}")
        
        vertexai.init(project=self.project_id, location=self.location)
        
        # Define Tools Schema
        self.tools_schema = Tool.from_dict({
            "function_declarations": [
                {
                    "name": "get_price_quote",
                    "description": "Check the price of items before buying.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "part_name": {"type": "string"},
                            "quantity": {"type": "integer"},
                            "urgent": {"type": "boolean"}
                        },
                        "required": ["part_name", "quantity"]
                    }
                },
                {
                    "name": "order_parts_from_supplier",
                    "description": "Execute the final purchase order.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "part_name": {"type": "string"},
                            "quantity": {"type": "integer"},
                            "urgent": {"type": "boolean"}
                        },
                        "required": ["part_name", "quantity"]
                    }
                }
            ]
        })

        # Initialize Model
        self.model = GenerativeModel(
            self.model_name,
            tools=[self.tools_schema],
            system_instruction="""
            You are the Procurement Manager for Sentinell.ai.
            
            CRITICAL PROTOCOL:
            1. CHECK USER APPROVAL FIRST:
               - If the prompt says "USER APPROVAL: APPROVED", you MUST proceed to execute the order immediately. Ignore budget limits.
            
            2. IF NOT APPROVED YET:
               - Use 'get_price_quote' to check the cost.
               - If cost > $5000: STOP immediately. Output exactly: "PAUSED: APPROVAL REQUIRED (Cost: $...)".
               - If cost <= $5000: PROCEED to execute.
            
            3. EXECUTION:
               - Use 'order_parts_from_supplier' to finalize.
            """
        )

    def _execute_tool(self, func_name: str, func_args: dict) -> str:
        """
        Routes tool calls to the underlying Python functions.
        Includes logic to learn from failures (updating Memory Bank).
        """
        try:
            logger.info(f"🔧 Tool Call: {func_name} | Args: {func_args}")
            
            if func_name == "get_price_quote":
                return get_price_quote(
                    part_name=func_args["part_name"],
                    quantity=int(func_args["quantity"]),
                    urgent=bool(func_args.get("urgent", False))
                )
                
            elif func_name == "order_parts_from_supplier":
                result = order_parts_from_supplier(
                    part_name=func_args["part_name"],
                    quantity=int(func_args["quantity"]),
                    urgent=bool(func_args.get("urgent", False))
                )
                
                # Learning Moment: If order failed, verify why and remember it
                if "REJECTED" in result:
                    self.memory.add_learning(
                        topic="Supplier:Global-Chips-Inc", 
                        insight=f"Order rejected. Details: {result}",
                        source="ProcurementAgent"
                    )
                return result
            
            else:
                return f"Error: Unknown tool '{func_name}'"
                
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return f"Tool Error: {str(e)}"

    def create_order(self, part_name: str, quantity: int, risk_level: str, user_approval: bool = False) -> str:
        """
        Executes the procurement workflow.
        
        Args:
            part_name (str): The item to purchase.
            quantity (int): The number of units.
            risk_level (str): Used to determine urgency (CRITICAL = True).
            user_approval (bool): If True, overrides the budget pause for high-value orders.

        Returns:
            str: The final agent report or status message.
        """
        # 1. Recall Memory Context
        memory_context = self.memory.recall("Supplier:Global-Chips-Inc")
        
        # 2. Determine Urgency
        is_urgent = (risk_level.upper() == "CRITICAL")
        approval_status = "APPROVED" if user_approval else "PENDING_APPROVAL"

        prompt = f"""
        TASK: Purchase {quantity} units of {part_name}.
        URGENCY: {is_urgent} (Risk Level: {risk_level}).
        USER APPROVAL: {approval_status}.
        
        MEMORY CONTEXT:
        {memory_context}
        """
        
        logger.info(f"🔄 Starting Procurement Task for {part_name}...")
        chat = self.model.start_chat()
        response = chat.send_message(prompt)
        
        max_turns = 5
        current_turn = 0
        
        while current_turn < max_turns:
            candidate = response.candidates[0]
            function_call = None
            
            # Robust parsing for mixed content (Thought vs Tool)
            for part in candidate.content.parts:
                if part.function_call:
                    function_call = part.function_call
                    continue
                
                # Check for Text output (Thoughts or Pause Signals)
                try:
                    if part.text:
                        text = part.text.strip()
                        logger.info(f"🤔 Procurement Thought: {text[:100]}...")
                        
                        # Check for PAUSE signal
                        if "PAUSED:" in text:
                            logger.warning(f"⏸️ Workflow Paused: {text}")
                            return text 
                except Exception:
                    pass

            if function_call:
                func_name = function_call.name
                func_args = dict(function_call.args)
                
                tool_result = self._execute_tool(func_name, func_args)
                
                response = chat.send_message(
                    Part.from_function_response(
                        name=func_name,
                        response={"content": tool_result}
                    )
                )
                current_turn += 1
            else:
                # Task Complete
                logger.info("✅ Procurement Task Complete.")
                final_text = "".join([p.text for p in candidate.content.parts if p.text])
                return final_text

        return "Error: Procurement Agent timed out."


if __name__ == "__main__":
    # Internal Unit Test
    try:
        agent = ProcurementAgent()
        
        print("\n--- 🛑 TEST 1: High Cost Order (Expect PAUSE) ---")
        # 200 units * $50 = $10,000 > $5,000 Limit
        result_pause = agent.create_order("Expensive-CPU", 200, "LOW", user_approval=False)
        print(f"Result: {result_pause}")
        
        print("\n--- 🟢 TEST 2: Resume with Approval (Expect SUCCESS) ---")
        result_success = agent.create_order("Expensive-CPU", 200, "LOW", user_approval=True)
        print(f"Result: {result_success}")
        
    except Exception as e:
        print(f"❌ Test Failed: {e}")