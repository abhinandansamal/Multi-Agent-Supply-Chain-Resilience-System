import vertexai
from vertexai.generative_models import (
    GenerativeModel, 
    Tool, 
    Part, 
    ChatSession
)
from src.config import settings
from src.utils.logger import setup_logger
from src.tools.supplier_tool import order_parts_from_supplier
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
                    "name": "order_parts_from_supplier",
                    "description": "Send a purchase order to the external supplier.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "part_name": {"type": "string", "description": "The SKU to buy (e.g., 'Logic-Core-CPU-X1')"},
                            "quantity": {"type": "integer", "description": "Number of units"},
                            "urgent": {"type": "boolean", "description": "True if critical risk, False otherwise"}
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
            
            YOUR MISSION:
            1. Receive a buying task.
            2. CHECK MEMORY CONTEXT provided in the prompt for any past issues with suppliers.
            3. If memory says the supplier is 'Unreliable' or 'Blocked', ABORT the order.
            4. Otherwise, use 'order_parts_from_supplier' to execute.
            5. If the order fails, REPORT the failure clearly.
            """
        )

    def _execute_tool(self, func_name: str, func_args: dict) -> str:
        """Executes the mapped tool function."""
        try:
            logger.info(f"🛒 Procurement Action: {func_name} | Args: {func_args}")
            if func_name == "order_parts_from_supplier":
                return order_parts_from_supplier(
                    part_name=func_args["part_name"],
                    quantity=int(func_args["quantity"]),
                    urgent=bool(func_args.get("urgent", False))
                )
            
                # --- MEMORY LEARNING MOMENT ---
                # If an order fails, we should remember it!
                if "REJECTED" in result:
                    self.memory.add_learning(
                        topic="Supplier:Global-Chips-Inc", 
                        insight=f"Order rejected for {func_args['part_name']}. Reason: {result}",
                        source="ProcurementAgent"
                    )
                return result
            else:
                return f"Error: Unknown tool '{func_name}'"
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return f"Tool Error: {str(e)}"

    def create_order(self, part_name: str, quantity: int, risk_level: str) -> str:
        """
        Triggers the agent to place an order.
        
        Recall Memory
        We assume for this demo the main supplier is "Global-Chips-Inc"
        In a real app, we'd look up the supplier for the part first.

        Args:
            part_name (str): Item to buy.
            quantity (int): How many.
            risk_level (str): If 'CRITICAL', marks order as urgent.
        """
        memory_context = self.memory.recall("Supplier:Global-Chips-Inc")
        
        logger.info(f"🧠 Memory Context retrieved: {memory_context[:100]}...")

        prompt = f"""
        TASK: Purchase {quantity} units of {part_name}. Risk level is {risk_level}.
        
        MEMORY CONTEXT ABOUT SUPPLIER:
        {memory_context}
        
        INSTRUCTION:
        If the memory indicates recent severe failures, you may choose to warn the user instead of ordering.
        Otherwise, proceed with the order.
        """
        
        logger.info(f"🔄 Starting Procurement Task...")
        chat = self.model.start_chat()
        response = chat.send_message(prompt)
        
        # --- ReAct Loop ---
        # Similar logic to Watchtower, but focused on buying
        max_turns = 3
        current_turn = 0
        
        while current_turn < max_turns:
            candidate = response.candidates[0]
            function_call = None
            
            # Check for function call
            for part in candidate.content.parts:
                if part.function_call:
                    function_call = part.function_call
                    continue # Skip text check for this part
                
                try:
                    if part.text:
                        logger.info(f"🤔 Procurement Thought: {part.text.strip()[:100]}...")
                except:
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
                logger.info("✅ Procurement Task Complete.")
                
                final_text = ""
                for part in candidate.content.parts:
                    try:
                        if part.text: final_text += part.text
                    except: pass
                return final_text

        return "Error: Procurement Agent timed out."

if __name__ == "__main__":
    # MANUAL TEST
    # 1. Ensure 'python src/a2a/mock_supplier.py' is running in another terminal!
    try:
        agent = ProcurementAgent()
        print("\n--- 🛒 TEST: Buying 50 CPUs (Urgent) ---")
        report = agent.create_order("Logic-Core-CPU-X1", 50, "CRITICAL")
        print("\n📝 AGENT REPORT:\n" + report)
    except Exception as e:
        print(f"❌ Test Failed: {e}")