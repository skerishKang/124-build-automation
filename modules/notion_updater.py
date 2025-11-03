#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion Updater Module
Records Gemini analysis results to Notion database
"""

import os
import logging
from datetime import datetime

try:
    from notion_client import Client
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Notion client not installed. Notion functionality will be disabled.")

logger = logging.getLogger(__name__)

# Environment variables
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")


class NotionUpdater:
    def __init__(self):
        if NOTION_TOKEN:
            self.client = Client(auth=NOTION_TOKEN)
            logger.info("Notion client initialized successfully")
        else:
            self.client = None
            logger.warning("Notion token not set. Notion functionality disabled.")

    def create_summary_page(self, title: str, summary: str, source: str, metadata: dict = None):
        """
        Create a new summary page in Notion database
        """
        if not self.client or not NOTION_DATABASE_ID:
            logger.warning("Notion not configured. Skipping page creation.")
            return None

        try:
            # Create properties based on database schema
            # Adjust property names according to your Notion database structure
            properties = {
                "Title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                },
                "Source": {
                    "rich_text": [
                        {
                            "text": {
                                "content": source
                            }
                        }
                    ]
                },
                "Date": {
                    "date": {
                        "start": datetime.now().isoformat()
                    }
                }
            }

            # Add metadata as separate property if needed
            if metadata:
                for key, value in metadata.items():
                    if isinstance(value, str) and len(value) < 100:
                        properties[key] = {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": str(value)
                                    }
                                }
                            ]
                        }

            # Create page
            page = self.client.pages.create(
                parent={"database_id": NOTION_DATABASE_ID},
                properties=properties,
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": summary
                                    }
                                }
                            ]
                        }
                    }
                ]
            )

            logger.info(f"Notion page created: {title}")
            return page

        except Exception as e:
            logger.error(f"Error creating Notion page: {e}")
            return None

    def update_existing_page(self, page_id: str, summary: str):
        """
        Update an existing Notion page
        """
        if not self.client:
            logger.warning("Notion not configured. Skipping page update.")
            return None

        try:
            # Add new content block
            blocks = self.client.blocks.children.append(
                block_id=page_id,
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": summary
                                    }
                                }
                            ]
                        }
                    }
                ]
            )

            logger.info(f"Notion page updated: {page_id}")
            return blocks

        except Exception as e:
            logger.error(f"Error updating Notion page: {e}")
            return None


def save_email_to_notion(email_data: dict, summary: str):
    """
    Save email analysis to Notion
    """
    from modules.notion_updater import NotionUpdater

    notion = NotionUpdater()
    title = f"Email: {email_data['subject'][:50]}"

    metadata = {
        "Sender": email_data['sender'][:50],
        "EmailID": email_data['id']
    }

    return notion.create_summary_page(
        title=title,
        summary=summary,
        source="Gmail",
        metadata=metadata
    )


def save_file_to_notion(file_name: str, summary: str, file_type: str):
    """
    Save file analysis to Notion
    """
    from modules.notion_updater import NotionUpdater

    notion = NotionUpdater()
    title = f"File: {file_name}"

    metadata = {
        "Type": file_type,
        "Source": "Google Drive"
    }

    return notion.create_summary_page(
        title=title,
        summary=summary,
        source="Google Drive",
        metadata=metadata
    )


def save_meeting_to_notion(event: dict, summary: str):
    """
    Save meeting analysis to Notion
    """
    from modules.notion_updater import NotionUpdater

    notion = NotionUpdater()
    title = f"Meeting: {event.get('summary', 'Untitled')}"

    start = event['start'].get('dateTime', event['start'].get('date'))
    metadata = {
        "DateTime": start,
        "Location": event.get('location', 'N/A'),
        "Source": "Google Calendar"
    }

    return notion.create_summary_page(
        title=title,
        summary=summary,
        source="Google Calendar",
        metadata=metadata
    )


def save_transcript_to_notion(source_type: str, title: str, transcript: str, summary: str):
    """
    Save transcript analysis to Notion
    """
    from modules.notion_updater import NotionUpdater

    notion = NotionUpdater()

    metadata = {
        "Source": source_type,
        "Length": len(transcript)
    }

    # Combine transcript and summary
    content = f"""전사 내용:
{transcript}

요약:
{summary}"""

    return notion.create_summary_page(
        title=title,
        summary=content,
        source=source_type,
        metadata=metadata
    )
