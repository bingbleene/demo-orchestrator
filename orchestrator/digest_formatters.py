"""Digest formatting utilities for multiple output formats."""
from typing import List, Dict


def format_markdown(emails: List[Dict], date: str) -> str:
    """Format emails as markdown digest."""
    digest = f"# Daily Email Digest - {date}\n\n"

    # Count by priority
    high = [e for e in emails if e.get("priority") == "HIGH"]
    medium = [e for e in emails if e.get("priority") == "MEDIUM"]
    low = [e for e in emails if e.get("priority") == "LOW"]

    digest += f"**Summary**: {len(emails)} emails | 🔴 {len(high)} High | 🟡 {len(medium)} Medium | 🟢 {len(low)} Low\n\n"

    # High priority section
    if high:
        digest += "## 🔴 High Priority\n\n"
        for email in high:
            digest += f"### {email.get('subject', 'No Subject')}\n"
            digest += f"**From**: {email.get('sender', 'Unknown')}  \n"
            digest += f"**Summary**: {email.get('summary', 'N/A')}  \n"
            digest += f"**Reason**: {email.get('priority_reason', 'N/A')}  \n"
            digest += f"**Time**: {email.get('timestamp', 'N/A')}  \n\n"

    # Medium priority section
    if medium:
        digest += "## 🟡 Medium Priority\n\n"
        for email in medium:
            digest += f"### {email.get('subject', 'No Subject')}\n"
            digest += f"**From**: {email.get('sender', 'Unknown')}  \n"
            digest += f"**Summary**: {email.get('summary', 'N/A')}  \n"
            digest += f"**Reason**: {email.get('priority_reason', 'N/A')}  \n"
            digest += f"**Time**: {email.get('timestamp', 'N/A')}  \n\n"

    # Low priority section
    if low:
        digest += "## 🟢 Low Priority\n\n"
        for email in low:
            digest += f"### {email.get('subject', 'No Subject')}\n"
            digest += f"**From**: {email.get('sender', 'Unknown')}  \n"
            digest += f"**Summary**: {email.get('summary', 'N/A')}  \n"
            digest += f"**Reason**: {email.get('priority_reason', 'N/A')}  \n"
            digest += f"**Time**: {email.get('timestamp', 'N/A')}  \n\n"

    digest += f"---\n*Generated on {date}*"
    return digest


def format_html(emails: List[Dict], date: str) -> str:
    """Format emails as HTML digest."""
    html = f"""<html>
<head>
    <title>Daily Email Digest - {date}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background-color: #f0f0f0; padding: 10px; margin-bottom: 20px; }}
        .high {{ background-color: #ffcccc; padding: 10px; margin: 10px 0; border-left: 4px solid #ff0000; }}
        .medium {{ background-color: #ffffcc; padding: 10px; margin: 10px 0; border-left: 4px solid #ffaa00; }}
        .low {{ background-color: #ccffcc; padding: 10px; margin: 10px 0; border-left: 4px solid #00aa00; }}
        .email {{ margin: 10px 0; }}
        .subject {{ font-weight: bold; font-size: 14px; }}
        .sender {{ color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <h1>Daily Email Digest</h1>
    <div class="summary">
        <p>{date}</p>
    </div>
"""
    high = [e for e in emails if e.get("priority") == "HIGH"]
    medium = [e for e in emails if e.get("priority") == "MEDIUM"]
    low = [e for e in emails if e.get("priority") == "LOW"]

    for section_name, section_emails, css_class in [
        ("High Priority", high, "high"),
        ("Medium Priority", medium, "medium"),
        ("Low Priority", low, "low"),
    ]:
        if section_emails:
            html += f"<h2>{section_name}</h2>"
            for email in section_emails:
                html += f"""<div class="{css_class} email">
    <div class="subject">{email.get('subject', 'No Subject')}</div>
    <div class="sender">From: {email.get('sender', 'Unknown')}</div>
    <div>{email.get('summary', 'N/A')}</div>
    <small>Reason: {email.get('priority_reason', 'N/A')}</small>
</div>"""

    html += """
</body>
</html>"""
    return html


def format_text(emails: List[Dict], date: str) -> str:
    """Format emails as plain text digest."""
    digest = f"DAILY EMAIL DIGEST - {date}\n"
    digest += "=" * 50 + "\n\n"

    high = [e for e in emails if e.get("priority") == "HIGH"]
    medium = [e for e in emails if e.get("priority") == "MEDIUM"]
    low = [e for e in emails if e.get("priority") == "LOW"]

    for section_name, section_emails in [
        ("HIGH PRIORITY", high),
        ("MEDIUM PRIORITY", medium),
        ("LOW PRIORITY", low),
    ]:
        if section_emails:
            digest += f"{section_name}\n"
            digest += "-" * 30 + "\n"
            for email in section_emails:
                digest += f"Subject: {email.get('subject', 'No Subject')}\n"
                digest += f"From: {email.get('sender', 'Unknown')}\n"
                digest += f"Summary: {email.get('summary', 'N/A')}\n"
                digest += f"Reason: {email.get('priority_reason', 'N/A')}\n"
                digest += f"Time: {email.get('timestamp', 'N/A')}\n\n"

    digest += "=" * 50 + f"\nGenerated on {date}"
    return digest
