"""Prioritizer Agent - FastAPI application."""
import sys
import os
import logging
from fastapi import FastAPI
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.models import AgentResponse
from shared.config import AgentConfig, PRIORITIZER_ENDPOINT
from models import PrioritizerRequest
from prioritizer import PrioritizerAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Prioritizer Agent", description="Email priority classification using Claude"
)

# Initialize agent
agent = PrioritizerAgent()


@app.post(PRIORITIZER_ENDPOINT, response_model=AgentResponse)
async def prioritize_emails(request: PrioritizerRequest):
    """Classify email priorities using OpenAI API."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "="*70)
    print(f"⚙️  PRIORITIZER AGENT RECEIVED REQUEST [{timestamp}]")
    print("="*70)
    print(f"📨 RECEIVED FROM ORCHESTRATOR: {len(request.emails)} summarized emails")
    print(f"   Processing on port {AgentConfig.PRIORITIZER_PORT}")
    logger.info(f"📨 PRIORITIZER AGENT: Received {len(request.emails)} emails from ORCHESTRATOR")
    
    result = agent.process(request.emails)
    
    if result.status == "success":
        print(f"✅ PRIORITIZER AGENT COMPLETED: {len(result.data)} emails prioritized")
        print(f"   📤 Sending response back to ORCHESTRATOR\n")
        logger.info(f"✅ PRIORITIZER AGENT: Completed and returning {len(result.data)} emails")
    else:
        print(f"⚠️  PRIORITIZER AGENT: Partial success ({result.status})")
        print(f"   📤 Sending response back to ORCHESTRATOR\n")
        logger.warning(f"⚠️  PRIORITIZER AGENT: {result.status}")
    
    return result


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "prioritizer"}


if __name__ == "__main__":
    import uvicorn

    logger.info(f"🚀 Starting Prioritizer service on port {AgentConfig.PRIORITIZER_PORT}")
    print(f"🚀 PRIORITIZER AGENT STARTED on port {AgentConfig.PRIORITIZER_PORT}")
    uvicorn.run(app, host="localhost", port=AgentConfig.PRIORITIZER_PORT)
