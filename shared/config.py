"""Configuration and Constants for Email Digest System."""
import os
from dotenv import load_dotenv

load_dotenv()


# ENDPOINTS
SUMMARIZER_ENDPOINT = "/summarize"
PRIORITIZER_ENDPOINT = "/prioritize"


# AGENT SERVICES CONFIGURATION
class AgentConfig:
    """Configuration for agent service URLs and ports."""
    
    # Load from .env environment variables
    SUMMARIZER_HOST = os.getenv("SUMMARIZER_HOST", "localhost")
    SUMMARIZER_PORT = int(os.getenv("SUMMARIZER_PORT", "8002"))
    
    PRIORITIZER_HOST = os.getenv("PRIORITIZER_HOST", "localhost")
    PRIORITIZER_PORT = int(os.getenv("PRIORITIZER_PORT", "8003"))
    
    # Base URLs for each service
    @classmethod
    def get_summarizer_url(cls) -> str:
        """Get summarizer service base URL."""
        return f"http://{cls.SUMMARIZER_HOST}:{cls.SUMMARIZER_PORT}"
    
    @classmethod
    def get_prioritizer_url(cls) -> str:
        """Get prioritizer service base URL."""
        return f"http://{cls.PRIORITIZER_HOST}:{cls.PRIORITIZER_PORT}"


# ORCHESTRATOR CONFIGURATION
class OrchestratorConfig:
    """Configuration for Orchestrator service."""
    
    HOST = os.getenv("ORCHESTRATOR_HOST", "localhost")
    PORT = int(os.getenv("ORCHESTRATOR_PORT", "8000"))
    REQUEST_TIMEOUT = 60


# LOGGING CONFIGURATION
class LoggingConfig:
    """Configuration for logging."""
    
    LEVEL = os.getenv("LOG_LEVEL", "INFO")


# MODEL CONFIGURATION
class ModelConfig:
    """Configuration for AI models (loaded from .env)."""
    
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))


# OUTPUT CONFIGURATION
class OutputConfig:
    """Configuration for output handling."""
    
    DEFAULT_OUTPUT_DIR = "output"
    SUPPORTED_FORMATS = ["markdown", "text", "html"]
    DEFAULT_FORMAT = "markdown"

