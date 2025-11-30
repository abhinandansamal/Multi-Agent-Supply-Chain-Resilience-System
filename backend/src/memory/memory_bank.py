import json
import os
from typing import List, Dict, Optional
from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger("memory_bank")

class MemoryBank:
    """
    Long-Term Memory System for Autonomous Agents.
    
    Persists 'Learnings' and 'Insights' to a local JSON store. This allows agents
    to retain knowledge across different sessions (e.g., remembering a bad supplier).
    
    Attributes:
        file_path (str): Location of the memory persistence file.
        memories (List[Dict]): In-memory cache of the loaded data.
    """
    
    def __init__(self):
        # We store the memory file in the same data directory as the SQLite DB
        data_dir = os.path.dirname(settings.DATABASE_PATH)
        self.file_path = os.path.join(data_dir, "agent_memory.json")
        self._load_memory()

    def _load_memory(self):
        """Loads existing memories from disk."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    self.memories = json.load(f)
                logger.info(f"🧠 Memory Bank loaded with {len(self.memories)} records.")
            except Exception as e:
                logger.error(f"Failed to load memory file: {e}")
                self.memories = []
        else:
            logger.info("🧠 No existing memory file found. Starting fresh.")
            self.memories = []

    def save_memory(self):
        """Persists current memory state to disk."""
        try:
            with open(self.file_path, "w") as f:
                json.dump(self.memories, f, indent=2)
            logger.debug("Memory persisted to disk.")
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    def add_learning(self, topic: str, insight: str, source: str = "Agent"):
        """
        Stores a new insight into the memory bank.
        
        Args:
            topic (str): The subject (e.g., 'Supplier:TSMC', 'Region:Taiwan').
            insight (str): The learned fact (e.g., 'Reliability score dropped to 0.5').
            source (str): Which agent created this memory.
        """
        entry = {
            "topic": topic,
            "insight": insight,
            "source": source,
            "timestamp": str(os.times().elapsed) # Simple timestamp placeholder
        }
        self.memories.append(entry)
        self.save_memory()
        logger.info(f"🧠 New Learning Stored: [{topic}] -> {insight[:50]}...")

    def recall(self, query: str) -> str:
        """
        Retrieves relevant insights based on a keyword query.
        
        Args:
            query (str): Keyword to search for (e.g., 'Taiwan').
            
        Returns:
            str: A formatted string of relevant past memories.
        """
        # Simple keyword matching logic
        relevant_memories = [
            m for m in self.memories 
            if query.lower() in m["topic"].lower() or query.lower() in m["insight"].lower()
        ]
        
        if not relevant_memories:
            return "No relevant past memories found."
        
        formatted = "\n".join([f"- [{m['topic']}]: {m['insight']}" for m in relevant_memories])
        logger.info(f"🧠 Recalled {len(relevant_memories)} memories for query '{query}'.")
        return f"PAST MEMORIES:\n{formatted}"

if __name__ == "__main__":
    # Manual Test
    bank = MemoryBank()
    bank.add_learning("Supplier:TestCorp", "Rejected orders twice due to stockouts.", "ProcurementAgent")
    print(bank.recall("TestCorp"))