"""Orchestrator FastAPI Application."""
import sys
import os
import logging
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from hashlib import md5
from shared.models import Email
from orchestrator import EmailDigestOrchestrator
from shared.config import AgentConfig, OrchestratorConfig

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Email Digest Orchestrator (LangGraph)",
    description="Multi-agent email processing pipeline using LangGraph"
)

# Initialize orchestrator with configuration (no ingestor/formatter URLs)
orchestrator = EmailDigestOrchestrator(
    summarizer_url=AgentConfig.get_summarizer_url(),
    prioritizer_url=AgentConfig.get_prioritizer_url(),
)


class DigestRequest(BaseModel):
    """Request to process emails and generate digest."""
    emails: List[Email]
    output_format: str = "markdown"
    save_to_file: bool = True


class DigestResponse(BaseModel):
    """Response with generated digest."""
    status: str
    digest: Optional[str]
    stats: dict
    errors: List[dict]
    output_file: Optional[str]
    reasoning_data: Optional[List[dict]] = None  # Reasoning & debate details


@app.post("/process", response_model=DigestResponse)
async def process_emails(request: DigestRequest):
    """Process emails and generate daily digest using LangGraph pipeline."""
    try:
        # Run pipeline using LangGraph
        state = orchestrator.run_pipeline(request.emails, request.output_format)

        # Save to file if requested
        output_file = None
        if request.save_to_file:
            output_file = orchestrator.save_digest(state)

        # Calculate stats
        stats = {
            "raw_emails": len(state.get("raw_emails", [])),
            "summarized_emails": len(state.get("summarized_emails", [])) if state.get("summarized_emails") else 0,
            "prioritized_emails": len(state.get("prioritized_emails", [])) if state.get("prioritized_emails") else 0,
            "priority_breakdown": {},
        }

        if state.get("prioritized_emails"):
            for email in state["prioritized_emails"]:
                priority = email.get("priority")
                stats["priority_breakdown"][priority] = (
                    stats["priority_breakdown"].get(priority, 0) + 1
                )

        # Check for errors in metadata
        errors = state.get("metadata", {}).get("errors", [])

        # Extract reasoning data for UI display
        reasoning_data = []
        if state.get("prioritized_emails"):
            # Create summary lookup by subject
            summary_lookup = {}
            if state.get("summarized_emails"):
                for email in state["summarized_emails"]:
                    summary_lookup[email.get("subject")] = email.get("summary", "No summary")
            
            for email in state["prioritized_emails"]:
                summary = summary_lookup.get(email.get("subject"), "No summary")
                reasoning_data.append({
                    "subject": email.get("subject"),
                    "sender": email.get("sender"),
                    "summary": summary,
                    "priority": email.get("priority"),
                    "priority_reason": email.get("priority_reason"),
                    "reasoning_details": email.get("reasoning_details") or {}
                })

        return DigestResponse(
            status="success" if not errors else "partial",
            digest=state.get("digest"),
            stats=stats,
            errors=errors,
            output_file=output_file,
            reasoning_data=reasoning_data if reasoning_data else None,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "orchestrator",
        "type": "langgraph",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/graph")
async def get_graph_visualization():
    """Get ASCII visualization of the LangGraph pipeline."""
    return {
        "graph": orchestrator.get_graph_visualization()
    }


@app.post("/process/stream")
async def process_emails_stream(request: DigestRequest):
    """
    Process emails with real-time streaming progress updates.
    Returns Server-Sent Events (JSON lines format).
    """
    
    async def event_generator():
        """Generate progress events as JSON lines."""
        
        # Emit start event
        yield json.dumps({
            "event": "start",
            "timestamp": datetime.utcnow().isoformat(),
            "total_emails": len(request.emails),
            "message": f"Starting pipeline with {len(request.emails)} emails"
        }) + "\n"
        
        try:
            # Convert Pydantic Email models to dicts and add email_id
            emails_data = []
            for email in request.emails:
                email_dict = email.dict() if hasattr(email, 'dict') else email
                if "email_id" not in email_dict or not email_dict.get("email_id"):
                    # Generate deterministic email_id from content
                    content = f"{email_dict.get('sender', '')}{email_dict.get('subject', '')}{email_dict.get('timestamp', '')}".encode()
                    email_dict["email_id"] = md5(content).hexdigest()[:12]
                emails_data.append(Email(**email_dict))
            
            # Run pipeline
            state = orchestrator.run_pipeline(emails_data, request.output_format)
            
            # Emit stage complete events based on state
            stats = {
                "raw_emails": len(state.get("raw_emails", [])),
                "summarized_emails": len(state.get("summarized_emails", [])) if state.get("summarized_emails") else 0,
                "prioritized_emails": len(state.get("prioritized_emails", [])) if state.get("prioritized_emails") else 0,
            }
            
            # Stage 1: Summarizer
            yield json.dumps({
                "event": "stage_start",
                "stage": "summarizer",
                "agent": "Summarizer Agent",
                "action": "xử lý",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Đang tóm tắt emails..."
            }) + "\n"
            
            yield json.dumps({
                "event": "stage_complete",
                "stage": "summarizer",
                "agent": "Summarizer Agent",
                "status": "complete",
                "count": stats["summarized_emails"],
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"✓ Tóm tắt {stats['summarized_emails']} emails"
            }) + "\n"
            
            # Stage 2: Prioritizer
            yield json.dumps({
                "event": "stage_start",
                "stage": "prioritizer",
                "agent": "Prioritizer Agent",
                "action": "xử lý",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Đang ưu tiên hóa emails..."
            }) + "\n"
            
            yield json.dumps({
                "event": "stage_complete",
                "stage": "prioritizer",
                "agent": "Prioritizer Agent",
                "status": "complete",
                "count": stats["prioritized_emails"],
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"✓ Ưu tiên hóa {stats['prioritized_emails']} emails"
            }) + "\n"
            
            # Stage 3: Formatter
            yield json.dumps({
                "event": "stage_start",
                "stage": "format",
                "agent": "Orchestrator",
                "action": "định dạng",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Đang tạo JSON digest..."
            }) + "\n"
            
            yield json.dumps({
                "event": "stage_complete",
                "stage": "format",
                "agent": "Orchestrator",
                "status": "complete",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "✓ Tạo JSON digest thành công"
            }) + "\n"
            
            # Save to file if requested
            output_file = None
            if request.save_to_file:
                output_file = orchestrator.save_digest(state)
            
            # Calculate priority breakdown
            priority_breakdown = {}
            if state.get("prioritized_emails"):
                for email in state["prioritized_emails"]:
                    priority = email.get("priority")
                    priority_breakdown[priority] = priority_breakdown.get(priority, 0) + 1
            
            stats["priority_breakdown"] = priority_breakdown
            
            # Extract reasoning data
            reasoning_data = []
            if state.get("prioritized_emails"):
                # Create summary lookup by subject
                summary_lookup = {}
                if state.get("summarized_emails"):
                    for email in state["summarized_emails"]:
                        summary_lookup[email.get("subject")] = email.get("summary", "No summary")
                
                for email in state["prioritized_emails"]:
                    summary = summary_lookup.get(email.get("subject"), "No summary")
                    reasoning_data.append({
                        "subject": email.get("subject"),
                        "sender": email.get("sender"),
                        "summary": summary,
                        "priority": email.get("priority"),
                        "priority_reason": email.get("priority_reason"),
                        "reasoning_details": email.get("reasoning_details") or {}
                    })
            
            # Emit completion event with full data
            yield json.dumps({
                "event": "complete",
                "status": "success",
                "timestamp": datetime.utcnow().isoformat(),
                "stats": stats,
                "output_file": output_file,
                "reasoning_data": reasoning_data,
                "digest": state.get("digest"),
                "errors": state.get("metadata", {}).get("errors", [])
            }) + "\n"
            
        except Exception as e:
            yield json.dumps({
                "event": "error",
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "message": str(e)
            }) + "\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="application/x-ndjson"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
