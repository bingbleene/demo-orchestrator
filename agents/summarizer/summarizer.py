"""Summarizer business logic for email summarization."""
import logging
from typing import List
from shared.models import CleanedEmail, SummarizedEmail, AgentResponse
from shared.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SummarizerAgent(BaseAgent):
    """Business logic for email summarization using OpenAI."""

    def summarize_email(self, cleaned_body: str, subject: str) -> str:
        """
        Summarize email content using OpenAI API in Vietnamese.

        Args:
            cleaned_body: Cleaned email body
            subject: Email subject

        Returns:
            Summary text in Vietnamese (2-3 sentences, max 150 chars)
        """
        system_prompt = "Bạn là chuyên gia tóm tắt email. Hãy tạo các tóm tắt ngắn gọn, rõ ràng bằng tiếng Việt, nắm bắt các điểm chính và các hành động cần thiết."
        
        prompt = f"""Hãy tóm tắt email sau bằng tiếng Việt trong 2-3 câu ngắn gọn, tối đa 150 ký tự.
Tập trung vào các hành động chính, quyết định hoặc thông tin quan trọng.

Tiêu đề: {subject}

Nội dung email:
{cleaned_body}

Tóm tắt:"""

        return self.call_openai(prompt, system_prompt=system_prompt)

    def _process_one_email(self, email: CleanedEmail) -> SummarizedEmail:
        """Process a single email and return summarized version."""
        # Generate summary using OpenAI
        logger.info(f"         🤖 Calling OpenAI API for summary...")
        summary = self.summarize_email(email.cleaned_body, email.subject)

        # Truncate summary to max 150 chars
        summary = summary[:150].strip()

        # Create summarized email
        return SummarizedEmail(
            email_id=email.email_id,
            sender=email.sender,
            subject=email.subject,
            cleaned_body=email.cleaned_body,
            summary=summary,
            timestamp=email.timestamp,
        )

    def process(self, emails: List[CleanedEmail]) -> AgentResponse:
        """
        Process cleaned emails and return summarized versions.

        Args:
            emails: List of cleaned email objects

        Returns:
            AgentResponse with summarized emails
        """
        return self.process_batch(emails, self._process_one_email)
