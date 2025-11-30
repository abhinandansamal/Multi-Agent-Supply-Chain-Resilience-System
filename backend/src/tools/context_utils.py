import vertexai
from vertexai.generative_models import GenerativeModel
from src.config import settings
from src.utils.logger import setup_logger

# Initialize Logger
logger = setup_logger("tool_context_utils")

def compact_context(raw_text: str, max_words: int = 150) -> str:
    """
    Context Compaction Strategy.
    
    Uses a lightweight, high-speed model (Gemini Flash) to compress large text inputs
    into high-density summaries. This reduces token usage and noise for the main
    reasoning agents.

    Args:
        raw_text (str): The noisy input text (e.g., raw search results).
        max_words (int): The target length for the summary.

    Returns:
        str: A concise summary focusing strictly on supply chain risks.
    """
    if not raw_text or len(raw_text) < 200:
        # If text is already short, don't waste an API call
        return raw_text

    try:
        # We use the same model defined in settings (Flash-Lite) for efficiency
        model = GenerativeModel(settings.MODEL_NAME)
        
        prompt = f"""
        TASK: Compress the following text into a concise summary of exactly {max_words} words.
        FOCUS: Supply chain disruptions, disasters, strikes, and delays.
        IGNORE: General news, marketing fluff, or irrelevant details.
        
        INPUT TEXT:
        {raw_text}
        """
        
        logger.debug(f"Compacting context of size {len(raw_text)} chars...")
        response = model.generate_content(prompt)
        summary = response.text.strip()
        
        logger.info(f"✅ Context compacted: {len(raw_text)} -> {len(summary)} chars.")
        return summary

    except Exception as e:
        logger.warning(f"Context compaction failed (using raw text fallback): {e}")
        # Fallback: Return truncated raw text to prevent crashing
        return raw_text[:2000]