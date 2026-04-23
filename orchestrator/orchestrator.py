"""LangGraph Orchestrator - Coordinates multi-agent pipeline using LangGraph."""
import sys
import os
import logging
import json
from typing import List, Any, Dict
from datetime import datetime
from dotenv import load_dotenv
from langgraph.graph import StateGraph
from typing import TypedDict, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

from shared.models import Email
from shared.config import AgentConfig

from digest_formatters import format_markdown, format_html, format_text
from pipeline_stages import PipelineStages
from pipeline_utils import print_pipeline_summary, save_digest

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# Define LangGraph State
class PipelineState(TypedDict):
    """State for the email processing pipeline."""
    raw_emails: List[Dict[str, Any]]
    summarized_emails: Optional[List[Dict[str, Any]]]
    prioritized_emails: Optional[List[Dict[str, Any]]]
    digest: Optional[str]
    metadata: Dict[str, Any]
    output_format: str


class EmailDigestOrchestrator:
    """Orchestrates the multi-agent pipeline for email processing using LangGraph."""

    def __init__(
        self,
        summarizer_url: str = None,
        prioritizer_url: str = None,
    ):
        """Initialize orchestrator with agent URLs."""
        self.summarizer_url = summarizer_url or AgentConfig.get_summarizer_url()
        self.prioritizer_url = prioritizer_url or AgentConfig.get_prioritizer_url()
        self.graph = self._build_graph()

    def _summarize_node(self, state: PipelineState) -> PipelineState:
        """LangGraph node for summarization stage."""
        print("\n" + "="*70)
        print("📬 ORCHESTRATOR → STAGE 1: SUMMARIZER AGENT")
        print("="*70)
        raw_count = len(state.get("raw_emails") or [])
        print(f"🚀 SENDING TO SUMMARIZER: {raw_count} emails")
        print(f"   Endpoint: {self.summarizer_url}")
        logger.info(f"🚀 ORCHESTRATOR: Sending {raw_count} emails to SUMMARIZER agent")
        
        summarized_emails, metadata = PipelineStages.summarize_emails(
            state.get("raw_emails") or [],
            self.summarizer_url,
            state["metadata"]
        )
        state["summarized_emails"] = summarized_emails
        state["metadata"] = metadata
        
        if summarized_emails:
            print(f"📨 ORCHESTRATOR RECEIVED FROM SUMMARIZER: {len(summarized_emails)} emails")
            logger.info(f"📨 ORCHESTRATOR: Received {len(summarized_emails)} summarized emails from SUMMARIZER\n")
        return state

    def _prioritize_node(self, state: PipelineState) -> PipelineState:
        """LangGraph node for prioritization stage."""
        print("\n" + "="*70)
        print("📬 ORCHESTRATOR → STAGE 2: PRIORITIZER AGENT")
        print("="*70)
        summarized_count = len(state.get("summarized_emails") or [])
        print(f"🚀 SENDING TO PRIORITIZER: {summarized_count} summarized emails")
        print(f"   Endpoint: {self.prioritizer_url}")
        logger.info(f"🚀 ORCHESTRATOR: Sending {summarized_count} emails to PRIORITIZER agent")
        
        prioritized_emails, metadata = PipelineStages.prioritize_emails(
            state.get("summarized_emails") or [],
            self.prioritizer_url,
            state["metadata"]
        )
        state["prioritized_emails"] = prioritized_emails
        state["metadata"] = metadata
        
        if prioritized_emails:
            print(f"📨 ORCHESTRATOR RECEIVED FROM PRIORITIZER: {len(prioritized_emails)} emails")
            logger.info(f"📨 ORCHESTRATOR: Received {len(prioritized_emails)} prioritized emails from PRIORITIZER\n")
        return state

    def _format_node(self, state: PipelineState) -> PipelineState:
        """LangGraph node for formatting stage."""
        print("\n" + "="*70)
        print("📬 ORCHESTRATOR → STAGE 3: FORMATTER (JSON Output)")
        print("="*70)
        prioritized_count = len(state.get("prioritized_emails") or [])
        print(f"⚙️  FORMATTING: {prioritized_count} prioritized emails")
        logger.info(f"⚙️  FORMATTER STAGE: Formatting {prioritized_count} emails")
        
        if not state.get("prioritized_emails"):
            logger.warning("No prioritized emails to process")
            return state

        try:
            output_format = state.get("output_format", "json")
            date = datetime.utcnow().strftime("%Y-%m-%d")

            if output_format == "json":
                # Format as JSON digest
                digest = json.dumps({
                    "date": date,
                    "total_emails": len(state["prioritized_emails"]),
                    "emails": state["prioritized_emails"]
                }, ensure_ascii=False, indent=2)
            else:
                # Fallback to text format
                digest = format_text(state["prioritized_emails"], date)

            state["digest"] = digest
            state["metadata"]["formatter"] = {
                "status": "success",
                "format": output_format,
            }
            logger.info("✓ Formatter: Generated digest")
            print(f"✅ FORMATTER COMPLETE: JSON digest generated ({len(digest)} chars)\n")

        except Exception as e:
            state["metadata"]["formatter"] = {"status": "error", "error": str(e)}
            logger.error(f"✗ Formatter failed: {str(e)}")
            print(f"❌ FORMAT FAILED: {str(e)}\n")

        return state

    def _build_graph(self) -> Any:
        """Build the LangGraph workflow graph."""
        workflow = StateGraph(PipelineState)

        # Add nodes for each stage
        workflow.add_node("summarize", self._summarize_node)
        workflow.add_node("prioritize", self._prioritize_node)
        workflow.add_node("format", self._format_node)

        # Add edges to connect stages
        workflow.set_entry_point("summarize")
        workflow.add_edge("summarize", "prioritize")
        workflow.add_edge("prioritize", "format")
        workflow.set_finish_point("format")

        # Compile the graph
        return workflow.compile()

    def run_pipeline(self, raw_emails: List[Email], output_format: str = "markdown") -> PipelineState:
        """
        Execute the complete email processing pipeline using LangGraph.

        Args:
            raw_emails: List of raw email objects
            output_format: Format for final digest (markdown, text, html)

        Returns:
            Final pipeline state with all processing results
        """
        logger.info(f"🚀 Starting email processing pipeline using LangGraph...")
        logger.info(f"📧 Input: {len(raw_emails)} emails | Format: {output_format}")
        print("\n" + "🚀 " + "="*70)
        print("       📬 MULTI-AGENT EMAIL PROCESSING PIPELINE START")
        print("="*70)
        print(f"📨 ORCHESTRATOR RECEIVED: {len(raw_emails)} emails")
        print(f"   Format: {output_format}")
        print("="*70 + "\n")
        
        start_time = datetime.utcnow()

        # Initialize state
        initial_state: PipelineState = {
            "raw_emails": [e.model_dump() for e in raw_emails],
            "summarized_emails": None,
            "prioritized_emails": None,
            "digest": None,
            "output_format": output_format,
            "metadata": {
                "start_time": start_time.isoformat(),
                "pipeline_stages": [],
                "errors": [],
            },
        }

        # Run the graph
        final_state = self.graph.invoke(initial_state)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        final_state["metadata"]["end_time"] = end_time.isoformat()
        final_state["metadata"]["total_emails"] = len(raw_emails)
        final_state["metadata"]["duration_seconds"] = duration

        # Print summary
        print_pipeline_summary(final_state, duration)

        logger.info("✅ Pipeline completed successfully!")

        return final_state

    def save_digest(self, state: PipelineState, output_dir: str = "output") -> str:
        """
        Save digest to file.

        Args:
            state: Final pipeline state
            output_dir: Output directory path

        Returns:
            Path to saved file
        """
        return save_digest(state, output_dir)

    def get_graph_visualization(self) -> str:
        """Get ASCII representation of the graph."""
        return self.graph.get_graph().draw_ascii()


if __name__ == "__main__":
    print("LangGraph Orchestrator - Email Digest System")
    print("Run with: python orchestrator.py or integrate with FastAPI app")

