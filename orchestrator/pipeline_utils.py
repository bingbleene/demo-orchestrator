"""Utility functions for pipeline execution and output management."""
import os
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


def print_pipeline_summary(state: Dict[str, Any], duration: float) -> None:
    """
    Print formatted summary of pipeline execution.
    
    Args:
        state: Final pipeline state
        duration: Total execution time in seconds
    """
    summary = f"""
{'='*70}
                    ✅ PIPELINE EXECUTION COMPLETE
{'='*70}

📊 WORKFLOW SUMMARY:
  
  📬 ORCHESTRATOR ─→ receives {len(state.get('raw_emails') or [])} raw emails
                      │
                      ├─→ 🔄 STAGE 1: INGEST (local)
                      │   └─→ cleaned {len(state.get('cleaned_emails') or [])} emails
                      │
                      ├─→ 📨 STAGE 2: SEND TO SUMMARIZER AGENT
                      │   ├─→ 🚀 Sending {len(state.get('cleaned_emails') or [])} emails
                      │   ├─→ ⚙️  Agent processes
                      │   └─→ 📤 Returning {len(state.get('summarized_emails') or [])} summarized emails
                      │
                      ├─→ 📨 STAGE 3: SEND TO PRIORITIZER AGENT  
                      │   ├─→ 🚀 Sending {len(state.get('summarized_emails') or [])} emails
                      │   ├─→ ⚙️  Agent processes
                      │   └─→ 📤 Returning {len(state.get('prioritized_emails') or [])} prioritized emails
                      │
                      └─→ 🔄 STAGE 4: FORMAT (local)
                          └─→ generated digest

📈 PROCESSING RESULTS:
  ✓ Ingest:     {len(state.get('cleaned_emails') or [])} emails cleaned
  ✓ Summarize:  {len(state.get('summarized_emails') or [])} emails summarized
  ✓ Prioritize: {len(state.get('prioritized_emails') or [])} emails prioritized
  ✓ Format:     Digest generated

🎯 PRIORITY BREAKDOWN:
"""
    if state.get("prioritized_emails"):
        high = len([e for e in state["prioritized_emails"] if e.get("priority") == "HIGH"])
        medium = len([e for e in state["prioritized_emails"] if e.get("priority") == "MEDIUM"])
        low = len([e for e in state["prioritized_emails"] if e.get("priority") == "LOW"])
        summary += f"  🔴 HIGH:   {high}\n  🟡 MEDIUM: {medium}\n  🟢 LOW:    {low}\n"

    summary += f"""
⏱️  TIMING:
  Duration:      {duration:.2f}s
  Start:         {state['metadata']['start_time']}
  End:           {state['metadata']['end_time']}
  Format:        {state.get('output_format', 'markdown')}

{'='*70}
"""
    print(summary)


def save_digest(
    state: Dict[str, Any],
    output_dir: str = "output"
) -> str:
    """
    Save digest and state metadata to files.
    
    Args:
        state: Final pipeline state
        output_dir: Output directory path
        
    Returns:
        Path to saved digest file
    """
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"digest_{timestamp}.md"
    filepath = os.path.join(output_dir, filename)

    # Also save state as JSON for reference
    state_filename = f"state_{timestamp}.json"
    state_filepath = os.path.join(output_dir, state_filename)

    try:
        # Save digest
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(state.get("digest") or "No digest generated")

        # Save state metadata
        with open(state_filepath, "w", encoding="utf-8") as f:
            state_dict = {
                "raw_emails_count": len(state.get("raw_emails", [])),
                "cleaned_emails_count": len(state.get("cleaned_emails", [])) if state.get("cleaned_emails") else 0,
                "summarized_emails_count": len(state.get("summarized_emails", [])) if state.get("summarized_emails") else 0,
                "prioritized_emails_count": len(state.get("prioritized_emails", [])) if state.get("prioritized_emails") else 0,
                "metadata": state.get("metadata", {}),
            }
            json.dump(state_dict, f, indent=2)

        print(f"\n[ORCHESTRATOR] 📁 Digest saved to: {filepath}")
        print(f"[ORCHESTRATOR] 📁 State saved to: {state_filepath}")

        return filepath

    except Exception as e:
        logger.error(f"Error saving digest: {str(e)}")
        print(f"[ORCHESTRATOR] ❌ Error saving digest: {str(e)}")
        return ""
