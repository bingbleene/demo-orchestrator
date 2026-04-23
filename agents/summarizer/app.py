"""Summarizer Agent - FastAPI application."""
import sys
import os
import logging
from fastapi import FastAPI
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.models import AgentResponse, CleanedEmail
from shared.config import AgentConfig, SUMMARIZER_ENDPOINT
from pydantic import BaseModel
from typing import List
from summarizer import SummarizerAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Summarizer Agent", description="Email summarization using OpenAI")

# Initialize agent
agent = SummarizerAgent()


class SummarizerRequest(BaseModel):
    """Request format for summarizer agent."""
    emails: List[CleanedEmail]


@app.post(SUMMARIZER_ENDPOINT, response_model=AgentResponse)
async def summarize_emails(request: SummarizerRequest):
    """Summarize cleaned emails using OpenAI API."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "="*70)
    print(f"⚙️  SUMMARIZER AGENT RECEIVED REQUEST [{timestamp}]")
    print("="*70)
    print(f"📨 RECEIVED FROM ORCHESTRATOR: {len(request.emails)} cleaned emails")
    print(f"   Processing on port {AgentConfig.SUMMARIZER_PORT}")
    logger.info(f"📨 SUMMARIZER AGENT: Received {len(request.emails)} emails from ORCHESTRATOR")
    
    result = agent.process(request.emails)
    
    if result.status == "success":
        print(f"✅ SUMMARIZER AGENT COMPLETED: {len(result.data)} emails summarized")
        print(f"   📤 Sending response back to ORCHESTRATOR\n")
        logger.info(f"✅ SUMMARIZER AGENT: Completed and returning {len(result.data)} emails")
    else:
        print(f"⚠️  SUMMARIZER AGENT: Partial success ({result.status})")
        print(f"   📤 Sending response back to ORCHESTRATOR\n")
        logger.warning(f"⚠️  SUMMARIZER AGENT: {result.status}")
    
    return result


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "summarizer"}


if __name__ == "__main__":
    import uvicorn

    logger.info(f"🚀 Starting Summarizer service on port {AgentConfig.SUMMARIZER_PORT}")
    print(f"🚀 SUMMARIZER AGENT STARTED on port {AgentConfig.SUMMARIZER_PORT}")
    uvicorn.run(app, host="localhost", port=AgentConfig.SUMMARIZER_PORT)
