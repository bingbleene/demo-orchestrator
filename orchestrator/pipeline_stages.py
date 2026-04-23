"""Pipeline processing stages for the multi-agent orchestrator."""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests

from shared.utils import clean_email_body, normalize_timestamp, generate_email_id
from shared.config import OrchestratorConfig, SUMMARIZER_ENDPOINT, PRIORITIZER_ENDPOINT

logger = logging.getLogger(__name__)


class PipelineStages:
    """Collection of pipeline processing stages."""

    @staticmethod
    def ingest_emails(
        raw_emails: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Clean and normalize raw emails locally.
        
        Args:
            raw_emails: List of raw email dictionaries
            metadata: Pipeline metadata
            
        Returns:
            Tuple of (cleaned_emails, updated_metadata)
        """
        print("   📋 LOCAL PROCESSING: Cleaning & normalizing...")
        logger.info(f"📋 INGEST: Processing {len(raw_emails)} raw emails locally")

        cleaned_emails = []
        errors = []

        for idx, email in enumerate(raw_emails):
            try:
                # Generate email ID if not present
                email_id = email.get("email_id") or generate_email_id(
                    email["sender"], email["subject"], email["timestamp"]
                )

                # Clean the body
                cleaned_body = clean_email_body(email["body"])

                # Normalize timestamp
                normalized_timestamp = normalize_timestamp(email["timestamp"])

                # Create cleaned email
                cleaned_email = {
                    "email_id": email_id,
                    "sender": email["sender"],
                    "subject": email["subject"],
                    "cleaned_body": cleaned_body,
                    "timestamp": normalized_timestamp,
                }
                cleaned_emails.append(cleaned_email)
                print(f"      ✓ Email {idx+1}: {email.get('subject', 'No Subject')[:50]}")

            except Exception as e:
                errors.append({
                    "index": idx,
                    "error": f"Failed to process email: {str(e)}",
                    "email": email.get("subject", "Unknown"),
                })
                logger.error(f"Error processing email {idx}: {str(e)}")

        metadata["ingestor"] = {
            "status": "success" if not errors else "partial",
            "processed": len(cleaned_emails),
            "errors": len(errors),
        }
        logger.info(f"✅ INGEST: Processed {len(cleaned_emails)} emails locally")

        return cleaned_emails, metadata

    @staticmethod
    def summarize_emails(
        cleaned_emails: List[Dict[str, Any]],
        summarizer_url: str,
        metadata: Dict[str, Any]
    ) -> tuple[Optional[List[Dict[str, Any]]], Dict[str, Any]]:
        """
        Send cleaned emails to summarizer agent.
        
        Args:
            cleaned_emails: List of cleaned email dictionaries
            summarizer_url: Summarizer service URL
            metadata: Pipeline metadata
            
        Returns:
            Tuple of (summarized_emails, updated_metadata)
        """
        if not cleaned_emails:
            logger.warning("No cleaned emails to process")
            return None, metadata

        print("\n   🔗 HTTP REQUEST TO SUMMARIZER AGENT")
        print(f"      URL: POST {summarizer_url}/summarize")
        print(f"      📨 Sending: {len(cleaned_emails)} cleaned emails")
        logger.info(f"🔗 HTTP REQUEST: Sending {len(cleaned_emails)} emails to SUMMARIZER at {summarizer_url}")

        try:
            # Convert raw emails to CleanedEmail format for Summarizer
            formatted_emails = []
            for email in cleaned_emails:
                formatted_emails.append({
                    "email_id": email.get("email_id", ""),
                    "sender": email.get("sender", ""),
                    "subject": email.get("subject", ""),
                    "cleaned_body": email.get("body", email.get("cleaned_body", "")),
                    "timestamp": email.get("timestamp", "")
                })
            
            url = f"{summarizer_url}{SUMMARIZER_ENDPOINT}"
            print(f"      ⏳ Waiting for SUMMARIZER agent response...\n")
            
            response = requests.post(
                url,
                json={"emails": formatted_emails},
                timeout=OrchestratorConfig.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            result = response.json()

            if result["status"] in ["success", "partial"]:
                summarized_emails = result["data"]
                metadata["summarizer"] = {
                    "status": result["status"],
                    "processed": len(summarized_emails),
                    "errors": result.get("metadata", {}).get("total_errors", 0),
                }
                print(f"   ✅ SUMMARIZER AGENT RESPONSE RECEIVED")
                print(f"      Status: {result['status']}")
                print(f"      📤 Returned: {len(summarized_emails)} summarized emails\n")
                logger.info(f"✅ SUMMARIZER: Returned {len(summarized_emails)} summarized emails")
                return summarized_emails, metadata
            else:
                metadata["summarizer"] = {"status": "error", "error": result.get("error")}
                print(f"   ❌ SUMMARIZER AGENT ERROR: {result.get('error')}\n")
                logger.error(f"✗ Summarizer failed: {result.get('error')}")
                return None, metadata

        except Exception as e:
            metadata["summarizer"] = {"status": "error", "error": str(e)}
            print(f"   ❌ HTTP REQUEST FAILED: {str(e)}\n")
            logger.error(f"✗ Summarizer HTTP request failed: {str(e)}")
            return None, metadata

    @staticmethod
    def prioritize_emails(
        summarized_emails: List[Dict[str, Any]],
        prioritizer_url: str,
        metadata: Dict[str, Any]
    ) -> tuple[Optional[List[Dict[str, Any]]], Dict[str, Any]]:
        """
        Send summarized emails to prioritizer agent.
        
        Args:
            summarized_emails: List of summarized email dictionaries
            prioritizer_url: Prioritizer service URL
            metadata: Pipeline metadata
            
        Returns:
            Tuple of (prioritized_emails, updated_metadata)
        """
        if not summarized_emails:
            logger.warning("No summarized emails to process")
            return None, metadata

        print("\n   🔗 HTTP REQUEST TO PRIORITIZER AGENT")
        print(f"      URL: POST {prioritizer_url}/prioritize")
        print(f"      📨 Sending: {len(summarized_emails)} summarized emails")
        logger.info(f"🔗 HTTP REQUEST: Sending {len(summarized_emails)} emails to PRIORITIZER at {prioritizer_url}")

        try:
            # Convert to SummarizedEmail format for Prioritizer
            formatted_emails = []
            for email in summarized_emails:
                formatted_emails.append({
                    "email_id": email.get("email_id", ""),
                    "sender": email.get("sender", ""),
                    "subject": email.get("subject", ""),
                    "cleaned_body": email.get("cleaned_body", email.get("body", "")),
                    "summary": email.get("summary", ""),
                    "timestamp": email.get("timestamp", "")
                })
            
            url = f"{prioritizer_url}{PRIORITIZER_ENDPOINT}"
            print(f"      ⏳ Waiting for PRIORITIZER agent response...\n")
            
            response = requests.post(
                url,
                json={"emails": formatted_emails},
                timeout=OrchestratorConfig.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            result = response.json()

            if result["status"] in ["success", "partial"]:
                prioritized_emails = result["data"]
                metadata["prioritizer"] = {
                    "status": result["status"],
                    "processed": len(prioritized_emails),
                    "errors": result.get("metadata", {}).get("total_errors", 0),
                }
                print(f"   ✅ PRIORITIZER AGENT RESPONSE RECEIVED")
                print(f"      Status: {result['status']}")
                print(f"      📤 Returned: {len(prioritized_emails)} prioritized emails\n")
                logger.info(f"✅ PRIORITIZER: Returned {len(prioritized_emails)} prioritized emails")
                return prioritized_emails, metadata
            else:
                metadata["prioritizer"] = {"status": "error", "error": result.get("error")}
                print(f"   ❌ PRIORITIZER AGENT ERROR: {result.get('error')}\n")
                logger.error(f"✗ Prioritizer failed: {result.get('error')}")
                return None, metadata

        except Exception as e:
            metadata["prioritizer"] = {"status": "error", "error": str(e)}
            print(f"   ❌ HTTP REQUEST FAILED: {str(e)}\n")
            logger.error(f"✗ Prioritizer HTTP request failed: {str(e)}")
            return None, metadata
