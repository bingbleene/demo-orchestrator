"""Data models for Summarizer Agent."""
from pydantic import BaseModel
from typing import List
from shared.models import CleanedEmail


class SummarizerRequest(BaseModel):
    """Request format for summarizer agent."""
    emails: List[CleanedEmail]
