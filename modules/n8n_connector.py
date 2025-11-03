#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
n8n Webhook Connector Module
Sends Gemini analysis results to n8n workflows
"""

import os
import logging
import requests
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Environment variables
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")


class N8NConnector:
    def __init__(self):
        if N8N_WEBHOOK_URL:
            self.webhook_url = N8N_WEBHOOK_URL
            logger.info("n8n connector initialized successfully")
        else:
            self.webhook_url = None
            logger.warning("n8n webhook URL not set. n8n functionality disabled.")

    def send_data(self, payload: dict):
        """
        Send data to n8n webhook
        """
        if not self.webhook_url:
            logger.warning("n8n not configured. Skipping data send.")
            return None

        try:
            headers = {
                'Content-Type': 'application/json'
            }

            # Add API key if available
            if N8N_API_KEY:
                headers['Authorization'] = f'Bearer {N8N_API_KEY}'

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                logger.info("Data sent to n8n successfully")
                return response.json()
            else:
                logger.error(f"n8n webhook error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error sending data to n8n: {e}")
            return None

    def send_file_analysis(self, file_name: str, summary: str, source: str = "google_drive"):
        """
        Send file analysis result to n8n
        """
        payload = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "type": "file_analysis",
            "data": {
                "file_name": file_name,
                "summary": summary
            }
        }

        return self.send_data(payload)

    def send_email_analysis(self, subject: str, sender: str, summary: str, email_id: str):
        """
        Send email analysis result to n8n
        """
        payload = {
            "timestamp": datetime.now().isoformat(),
            "source": "gmail",
            "type": "email_analysis",
            "data": {
                "email_id": email_id,
                "subject": subject,
                "sender": sender,
                "summary": summary
            }
        }

        return self.send_data(payload)

    def send_calendar_event(self, event_name: str, start_time: str, summary: str, location: str = None):
        """
        Send calendar event to n8n
        """
        payload = {
            "timestamp": datetime.now().isoformat(),
            "source": "google_calendar",
            "type": "calendar_event",
            "data": {
                "event_name": event_name,
                "start_time": start_time,
                "location": location,
                "summary": summary
            }
        }

        return self.send_data(payload)

    def send_slack_message(self, channel: str, message: str, summary: str):
        """
        Send Slack message analysis to n8n
        """
        payload = {
            "timestamp": datetime.now().isoformat(),
            "source": "slack",
            "type": "message_analysis",
            "data": {
                "channel": channel,
                "original_message": message,
                "summary": summary
            }
        }

        return self.send_data(payload)

    def send_transcript(self, source_type: str, transcript: str, summary: str):
        """
        Send transcript analysis to n8n
        """
        payload = {
            "timestamp": datetime.now().isoformat(),
            "source": source_type,
            "type": "transcript_analysis",
            "data": {
                "transcript": transcript,
                "summary": summary
            }
        }

        return self.send_data(payload)

    def trigger_workflow(self, workflow_name: str, data: dict):
        """
        Trigger a specific n8n workflow
        """
        payload = {
            "timestamp": datetime.now().isoformat(),
            "trigger": workflow_name,
            "data": data
        }

        return self.send_data(payload)


# Utility functions
def send_file_to_n8n(file_name: str, summary: str):
    """Send file analysis to n8n"""
    connector = N8NConnector()
    return connector.send_file_analysis(file_name, summary)


def send_email_to_n8n(subject: str, sender: str, summary: str, email_id: str):
    """Send email analysis to n8n"""
    connector = N8NConnector()
    return connector.send_email_analysis(subject, sender, summary, email_id)


def send_event_to_n8n(event_name: str, start_time: str, summary: str, location: str = None):
    """Send calendar event to n8n"""
    connector = N8NConnector()
    return connector.send_calendar_event(event_name, start_time, summary, location)


def send_message_to_n8n(channel: str, message: str, summary: str):
    """Send Slack message to n8n"""
    connector = N8NConnector()
    return connector.send_slack_message(channel, message, summary)


def send_transcript_to_n8n(source_type: str, transcript: str, summary: str):
    """Send transcript to n8n"""
    connector = N8NConnector()
    return connector.send_transcript(source_type, transcript, summary)


def trigger_custom_workflow(workflow_name: str, data: dict):
    """Trigger custom workflow"""
    connector = N8NConnector()
    return connector.trigger_workflow(workflow_name, data)
