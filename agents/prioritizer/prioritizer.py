"""Prioritizer business logic for email classification."""
import logging
from typing import List, Tuple, Dict
from shared.models import SummarizedEmail, PrioritizedEmail, AgentResponse
from shared.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class PrioritizerAgent(BaseAgent):
    """Business logic for email priority classification using OpenAI."""

    def classify_priority(
        self, sender: str, subject: str, summary: str
    ) -> Tuple[str, str, Dict[str, str]]:
        """
        Classify email priority using OpenAI API with reasoning debate in Vietnamese.

        Args:
            sender: Email sender
            subject: Email subject
            summary: Email summary

        Returns:
            Tuple of (priority_level, reason, reasoning_debate)
        """
        system_prompt = "Bạn là chuyên gia phân loại email. Hãy phân loại mức độ quan trọng của email dựa trên tính khẩn cấp, tầm quan trọng của người gửi, nội dung và các hành động cần thiết. Luôn trả lời bằng định dạng được chỉ định."
        
        prompt = f"""Hãy phân loại mức độ ưu tiên của email này là CAO, TRUNG BÌNH, hoặc THẤP (bằng tiếng Việt).
Xem xét: tính khẩn cấp, mức độ quan trọng của người gửi, độ liên quan của nội dung, các từ khoá hành động.

Từ: {sender}
Tiêu đề: {subject}
Tóm tắt: {summary}

Vui lòng trả lời theo định dạng chính xác:
MỨC ĐỘ: [CAO/TRUNG BÌNH/THẤP]
LÝ DO: [Giải thích ngắn gọn]
LUẬN ĐIỂM_CAO: [Lý do tại sao có thể là ưu tiên CAO]
LUẬN ĐIỂM_TRUNG_BÌNH: [Lý do tại sao có thể là ưu tiên TRUNG BÌNH]
LUẬN ĐIỂM_THẤP: [Lý do tại sao có thể là ưu tiên THẤP]"""

        response_text = self.call_openai(prompt, system_prompt=system_prompt)

        # Parse response
        lines = response_text.split('\n')
        priority = "TRUNG BÌNH"
        reason = "Không thể xác định được mức độ ưu tiên"
        reasoning_debate = {
            "CAO": "Lập luận cho ưu tiên CAO",
            "TRUNG BÌNH": "Lập luận cho ưu tiên TRUNG BÌNH", 
            "THẤP": "Lập luận cho ưu tiên THẤP"
        }

        for line in lines:
            if line.startswith("MỨC ĐỘ:"):
                priority_text = line.replace("MỨC ĐỘ:", "").strip().upper()
                if priority_text in ["CAO", "TRUNG BÌNH", "THẤP"]:
                    priority = priority_text
            elif line.startswith("LÝ DO:"):
                reason = line.replace("LÝ DO:", "").strip()
            elif line.startswith("LUẬN ĐIỂM_CAO:"):
                reasoning_debate["CAO"] = line.replace("LUẬN ĐIỂM_CAO:", "").strip()
            elif line.startswith("LUẬN ĐIỂM_TRUNG_BÌNH:"):
                reasoning_debate["TRUNG BÌNH"] = line.replace("LUẬN ĐIỂM_TRUNG_BÌNH:", "").strip()
            elif line.startswith("LUẬN ĐIỂM_THẤP:"):
                reasoning_debate["THẤP"] = line.replace("LUẬN ĐIỂM_THẤP:", "").strip()

        return priority, reason, reasoning_debate

    def _process_one_email(self, email: SummarizedEmail) -> PrioritizedEmail:
        """Process a single email and return prioritized version."""
        # Classify priority using OpenAI with reasoning debate
        logger.info(f"         🤖 Calling OpenAI API for prioritization...")
        priority, reason, reasoning_debate = self.classify_priority(
            email.sender, email.subject, email.summary
        )

        # Create prioritized email with reasoning details
        return PrioritizedEmail(
            email_id=email.email_id,
            sender=email.sender,
            subject=email.subject,
            cleaned_body=email.cleaned_body,
            summary=email.summary,
            priority=priority,
            priority_reason=reason,
            timestamp=email.timestamp,
            reasoning_details=reasoning_debate,
        )

    def process(self, emails: List[SummarizedEmail]) -> AgentResponse:
        """
        Process summarized emails and return prioritized versions.

        Args:
            emails: List of summarized email objects

        Returns:
            AgentResponse with prioritized emails
        """
        return self.process_batch(emails, self._process_one_email)
