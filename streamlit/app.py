import json
import os
import sys
from pathlib import Path

import requests
import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.config import AgentConfig

# Priority level mapping (Vietnamese to English)
PRIORITY_VN_TO_EN = {
    "CAO": "HIGH",
    "TRUNG BÌNH": "MEDIUM",
    "THẤP": "LOW",
    "HIGH": "HIGH",
    "MEDIUM": "MEDIUM",
    "LOW": "LOW"
}

PRIORITY_EN_TO_VN = {
    "HIGH": "CAO",
    "MEDIUM": "TRUNG BÌNH",
    "LOW": "THẤP",
    "CAO": "CAO",
    "TRUNG BÌNH": "TRUNG BÌNH",
    "THẤP": "THẤP"
}

def get_priority_display_name(priority_level: str) -> str:
    """Convert priority level to display name."""
    return PRIORITY_EN_TO_VN.get(priority_level, priority_level)

def get_priority_en(priority_level: str) -> str:
    """Convert Vietnamese priority to English."""
    return PRIORITY_VN_TO_EN.get(priority_level, priority_level)

st.set_page_config(page_title="Email Digest Tester", page_icon="📬", layout="wide")

# Custom CSS for beautiful email cards
st.markdown("""
<style>
    .email-card {
        background: white;
        border-left: 5px solid #667eea;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        transition: all 0.3s;
    }
    .email-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
        transform: translateY(-2px);
    }
    .email-card.high {
        border-left-color: #dc3545;
        background-color: #fff5f5;
    }
    .email-card.medium {
        border-left-color: #ffc107;
        background-color: #fffbf0;
    }
    .email-card.low {
        border-left-color: #28a745;
        background-color: #f5fff5;
    }
    .email-subject {
        font-size: 16px;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 8px;
    }
    .email-meta {
        font-size: 13px;
        color: #666;
        margin: 4px 0;
    }
    .email-sender {
        font-weight: 500;
        color: #667eea;
    }
    .email-body {
        font-size: 13px;
        color: #555;
        background: rgba(0,0,0,0.02);
        padding: 8px;
        border-radius: 4px;
        margin-top: 8px;
        max-height: 80px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

st.title("📬 Email Digest Processor")
st.caption("Real-time email processing with AI-powered prioritization")

orchestrator_base_url = st.sidebar.text_input(
    "Orchestrator base URL",
    value=os.getenv("ORCHESTRATOR_URL", "http://localhost:8000"),
)
request_timeout = st.sidebar.slider("Request timeout (seconds)", 10, 120, 45)

sample_path = Path("data/sample_emails.json")
if sample_path.exists():
    sample_json = sample_path.read_text(encoding="utf-8")
else:
    sample_json = "[]"

st.subheader("📧 Input: Select Emails to Process")

emails_json = st.text_area(
    "Paste emails (JSON array)",
    value=sample_json,
    height=250,
    help="Each email must have: sender, subject, body, timestamp",
    label_visibility="collapsed",
    key="json_input"
)

# Validate JSON
if emails_json:
    try:
        emails_data_test = json.loads(emails_json)
        if isinstance(emails_data_test, list):
            st.success(f"✓ Valid JSON with {len(emails_data_test)} emails")
        else:
            st.error("❌ JSON must be a list")
    except:
        st.error("❌ Invalid JSON format")

# Preview button
if st.button("👁️ Show Email Preview", use_container_width=False):
    try:
        preview_emails = json.loads(emails_json) if emails_json else []
        if isinstance(preview_emails, list) and preview_emails:
            st.subheader(f"📋 Email List ({len(preview_emails)} emails)")
            for idx, email in enumerate(preview_emails, 1):
                st.write(f"**#{idx}** {email.get('subject', 'No subject')} — **From:** {email.get('sender', 'Unknown')}")
                st.caption(f"{email.get('body', '')[:100]}...")
    except Exception as e:
        st.error(f"Cannot parse emails: {e}")

st.divider()

# ============ SECTION 2: PROCESS & PROGRESS ============

if st.button("🚀 Process Emails", type="primary", use_container_width=True):
    # Use parsed emails if available, otherwise parse from JSON
    if st.session_state.get("parsed_emails"):
        emails_data = st.session_state.get("parsed_emails")
    else:
        try:
            emails_data = json.loads(emails_json) if emails_json else []
            if not isinstance(emails_data, list):
                st.error("❌ Emails JSON must be a list.")
                st.stop()
        except json.JSONDecodeError as exc:
            st.error(f"❌ Invalid JSON: {exc}")
            st.stop()

    if not emails_data:
        st.error("❌ No emails to process. Please parse or provide emails first.")
        st.stop()

    payload = {
        "emails": emails_data,
    }

    # Streaming processing with real-time UI updates
    st.subheader("⚡ Processing")
    
    # Container for stage status
    stage_containers = {
        "ingest": st.container(),
        "summarizer": st.container(),
        "prioritizer": st.container(),
        "format": st.container(),
    }
    
    final_data = None
    current_stage = None
    stage_status = {}  # Track stage status
    
    try:
        response = requests.post(
            f"{orchestrator_base_url.rstrip('/')}/process/stream",
            json=payload,
            timeout=request_timeout,
            stream=True
        )
        response.raise_for_status()
        
        # Process streaming response
        for line in response.iter_lines():
            if line:
                event = json.loads(line)
                event_type = event.get("event")
                
                if event_type == "start":
                    st.info(f"🚀 {event.get('message')}")
                    
                elif event_type == "stage_start":
                    stage = event.get("stage")
                    agent = event.get("agent", "Unknown")
                    action = event.get("action", "processing")
                    
                    stage_status[stage] = "running"
                    
                    with stage_containers[stage]:
                        if stage == "ingest":
                            st.info(f"🔄 **STAGE 0: INGEST** - {agent} đang {action}")
                        elif stage == "summarizer":
                            st.info(f"🔄 **STAGE 1: SUMMARIZER** - {agent} đang {action}")
                        elif stage == "prioritizer":
                            st.info(f"🔄 **STAGE 2: PRIORITIZER** - {agent} đang {action}")
                        elif stage == "format":
                            st.info(f"🔄 **STAGE 3: FORMAT** - {agent} đang {action}")
                    
                elif event_type == "stage_complete":
                    stage = event.get("stage")
                    agent = event.get("agent", "Unknown")
                    status_msg = event.get("message", "Complete")
                    count = event.get("count", 0)
                    
                    stage_status[stage] = "complete"
                    
                    with stage_containers[stage]:
                        if stage == "ingest":
                            st.success(f"✅ **STAGE 0: INGEST** - {status_msg}")
                            st.caption(f"📋 {count} emails cleaned by {agent}")
                        elif stage == "summarizer":
                            st.success(f"✅ **STAGE 1: SUMMARIZER** - {status_msg}")
                            st.caption(f"⚙️ {count} emails summarized by {agent}")
                        elif stage == "prioritizer":
                            st.success(f"✅ **STAGE 2: PRIORITIZER** - {status_msg}")
                            st.caption(f"⭐ {count} emails prioritized by {agent}")
                        elif stage == "format":
                            st.success(f"✅ **STAGE 3: FORMAT** - {status_msg}")
                            st.caption(f"📄 Digest generated by {agent}")
                
                elif event_type == "complete":
                    st.success("✅ Tất cả pipeline hoàn tất!")
                    final_data = event
                    break
                    
                elif event_type == "error":
                    st.error(f"❌ Lỗi pipeline: {event.get('message')}")
                    st.stop()
        
    except requests.RequestException as exc:
        st.error(f"❌ Không thể kết nối đến orchestrator: {exc}")
        st.stop()
    
    if final_data:
        st.divider()
        data = final_data
        

        # ====== RESULTS SECTION ======
        st.subheader("📊 Processing Results")
        
        stats = data.get("stats", {})
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📧 Raw Emails", stats.get("raw_emails", 0))
        with col2:
            st.metric("✏️ Summarized", stats.get("summarized_emails", 0))
        with col3:
            st.metric("⭐ Prioritized", stats.get("prioritized_emails", 0))
        with col4:
            st.metric("❌ Errors", len(data.get("errors", [])))
        
        # Priority breakdown
        st.subheader("Priority Distribution")
        priority_data = stats.get("priority_breakdown", {})
        if priority_data:
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                st.metric("🔴 CAO", priority_data.get("CAO", 0))
            with col_p2:
                st.metric("🟡 TRUNG BÌNH", priority_data.get("TRUNG BÌNH", 0))
            with col_p3:
                st.metric("🟢 THẤP", priority_data.get("THẤP", 0))

        # Agent reasoning details with summaries
        st.subheader("🤔 Email Analysis & Agent Reasoning")
        
        reasoning_data = data.get("reasoning_data", [])
        if reasoning_data:
            for idx, email_reasoning in enumerate(reasoning_data, 1):
                priority_display = get_priority_display_name(
                    email_reasoning.get("priority", "UNKNOWN")
                )
                
                # Color code by priority
                if email_reasoning.get("priority") == "CAO":
                    emoji = "🔴"
                elif email_reasoning.get("priority") == "TRUNG BÌNH":
                    emoji = "🟡"
                else:
                    emoji = "🟢"
                
                with st.expander(
                    f"{emoji} **{email_reasoning.get('subject', 'No subject')}** — {priority_display}"
                ):
                    # Summary section
                    st.markdown("**📝 Summary:**")
                    summary = email_reasoning.get("summary", "No summary")
                    st.markdown(f"> {summary}")
                    
                    st.divider()
                    
                    # Reasoning section
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.markdown("**Email Info:**")
                        st.write(f"From: {email_reasoning.get('sender', 'Unknown')}")
                        st.write(f"Priority: **{priority_display}**")
                        st.write(f"Reason: {email_reasoning.get('priority_reason', 'N/A')}")
                    
                    with col2:
                        st.markdown("**Priority Arguments:**")
                        reasoning_details = email_reasoning.get("reasoning_details", {})
                        
                        for priority_level in ["CAO", "TRUNG BÌNH", "THẤP"]:
                            argument = reasoning_details.get(priority_level, "No argument")
                            
                            if priority_level == "CAO":
                                emoji_p, color = "🔴", "#dc3545"
                            elif priority_level == "TRUNG BÌNH":
                                emoji_p, color = "🟡", "#ffc107"
                            else:
                                emoji_p, color = "🟢", "#28a745"
                            
                            is_selected = priority_level == email_reasoning.get("priority")
                            if is_selected:
                                st.markdown(
                                    f"<div style='background-color: {color}22; padding: 10px; border-left: 4px solid {color}; border-radius: 4px; margin: 8px 0;'><strong>{emoji_p} {priority_level} ✓</strong><br/>{argument}</div>",
                                    unsafe_allow_html=True
                                )
                            else:
                                st.markdown(
                                    f"<div style='padding: 8px; border-left: 2px solid #ddd; margin: 8px 0;'>{emoji_p} {priority_level}<br/><small>{argument}</small></div>",
                                    unsafe_allow_html=True
                                )

        # Errors
        if data.get("errors"):
            st.subheader("⚠️ Processing Errors")
            for error in data.get("errors"):
                st.error(f"• {error}")
