"""Data models for Prioritizer Agent."""
from pydantic import BaseModel
from typing import List
from shared.models import SummarizedEmail


class PrioritizerRequest(BaseModel):
    """Request format for prioritizer agent."""
    emails: List[SummarizedEmail]
