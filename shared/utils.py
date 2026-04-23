"""Shared utility functions for the multi-agent system."""
import re
from html.parser import HTMLParser
from typing import List


class HTMLStripper(HTMLParser):
    """Remove HTML tags from text."""
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_html(html_text: str) -> str:
    """Remove HTML tags from text."""
    try:
        parser = HTMLStripper()
        parser.feed(html_text)
        return parser.get_data()
    except Exception:
        return html_text


def remove_email_signatures(text: str) -> str:
    """Remove common email signatures."""
    # Remove common signature patterns with better matching
    patterns = [
        r'--\s*\n.*',  # -- separator
        r'_+\s*\n.*',  # ___ separator
        r'(Best regards|Sincerely|Thanks|Regards|Cheers)[\s\S]*$',  # Better ending patterns
        r'Sent from.*',
        r'___+',
    ]

    result = text
    for pattern in patterns:
        result = re.sub(pattern, '', result, flags=re.DOTALL | re.IGNORECASE)

    return result.strip()


def remove_quoted_text(text: str) -> str:
    """Remove quoted/forwarded text (lines starting with >)."""
    lines = text.split('\n')
    filtered = []
    for line in lines:
        # Skip lines that look like quoted text
        if not line.strip().startswith('>') and not line.strip().startswith('|'):
            filtered.append(line)
    return '\n'.join(filtered).strip()


def clean_email_body(body: str) -> str:
    """Comprehensive email body cleaning."""
    # Strip HTML
    text = strip_html(body)

    # Remove quoted text
    text = remove_quoted_text(text)

    # Remove signatures
    text = remove_email_signatures(text)

    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)

    return text.strip()


def normalize_timestamp(timestamp: str) -> str:
    """Normalize timestamp to ISO format."""
    # If already in ISO format, return as is
    if 'T' in timestamp and timestamp.endswith('Z'):
        return timestamp
    # Return as-is if we can't parse it
    return timestamp


def generate_email_id(sender: str, subject: str, timestamp: str) -> str:
    """Generate unique email ID from sender, subject, and timestamp."""
    import hashlib
    content = f"{sender}:{subject}:{timestamp}"
    return hashlib.sha256(content.encode()).hexdigest()[:12]
