"""Shared Pydantic models for agent communication."""
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class Email(BaseModel):
    """Raw email structure."""
    sender: str
    subject: str
    body: str
    timestamp: str
    email_id: Optional[str] = None


class CleanedEmail(BaseModel):
    """Email after cleaning by Ingestor."""
    email_id: str
    sender: str
    subject: str
    cleaned_body: str
    timestamp: str


class SummarizedEmail(BaseModel):
    """Email with summary from Summarizer."""
    email_id: str
    sender: str
    subject: str
    cleaned_body: str
    summary: str
    timestamp: str


class PrioritizedEmail(BaseModel):
    """Email with priority classification."""
    email_id: str
    sender: str
    subject: str
    cleaned_body: str
    summary: str
    priority: str  # HIGH, MEDIUM, LOW
    priority_reason: str
    timestamp: str
    reasoning_details: Optional[Dict[str, str]] = None  # Debate/reasoning for each priority level


class AgentResponse(BaseModel):
    """Standard response format for all agents."""
    status: Literal["success", "error", "partial"]
    data: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
