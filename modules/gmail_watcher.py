#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail Watcher Module
Monitors Gmail for new emails and analyzes them with Gemini AI
"""

import os
import logging
import time
import base64
from email.mime.text import MIMEText
from typing import List, Dict

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.send']

# Environment variables
GMAIL_CLIENT_SECRET_PATH = os.getenv("GMAIL_CLIENT_SECRET_PATH", "gmail_credentials.json")
GMAIL_TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "gmail_token.json")


def get_gmail_service():
    """
    Get authenticated Gmail service
    """
    creds = None

    # Load existing token
    if os.path.exists(GMAIL_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, SCOPES)

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GMAIL_CLIENT_SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open(GMAIL_TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail service initialized successfully")
        return service
    except Exception as e:
        logger.error(f"Error initializing Gmail service: {e}")
        return None


def get_new_emails(service, processed_emails: set) -> List[Dict]:
    """
    Get new unread emails
    """
    try:
        result = service.users().messages().list(
            userId='me',
            q='is:unread',
            maxResults=10
        ).execute()

        messages = result.get('messages', [])
        new_emails = []

        for message in messages:
            msg_id = message['id']
            if msg_id not in processed_emails:
                new_emails.append(msg_id)

        return new_emails
    except HttpError as error:
        logger.error(f"Gmail API error: {error}")
        return []


def get_email_details(service, msg_id: str) -> Dict:
    """
    Get detailed email information
    """
    try:
        message = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='full'
        ).execute()

        headers = message['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')

        # Extract body
        body = ""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part.get('mimeType') == 'text/plain' and 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')

        return {
            'id': msg_id,
            'subject': subject,
            'sender': sender,
            'date': date,
            'body': body[:2000]  # Limit body size
        }
    except Exception as e:
        logger.error(f"Error getting email details: {e}")
        return {}


def mark_as_read(service, msg_id: str):
    """
    Mark email as read
    """
    try:
        service.users().messages().modify(
            userId='me',
            id=msg_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
    except HttpError as error:
        logger.error(f"Error marking email as read: {error}")


def gmail_watcher_thread(gemini_analyzer, telegram_bot=None, slack_bot=None):
    """
    Background thread to monitor Gmail
    """
    logger.info("📧 Gmail watcher thread started")

    service = get_gmail_service()
    if not service:
        logger.error("Failed to initialize Gmail service. Exiting watcher thread.")
        return

    processed_emails = set()

    while True:
        try:
            # Get new emails
            new_email_ids = get_new_emails(service, processed_emails)

            if new_email_ids:
                logger.info(f"[Gmail] Found {len(new_email_ids)} new email(s)")

                for email_id in new_email_ids:
                    logger.info(f"[Gmail] Processing email ID: {email_id}")

                    # Get email details
                    email = get_email_details(service, email_id)
                    if not email:
                        continue

                    # Mark as read
                    mark_as_read(service, email_id)

                    # Analyze with Gemini
                    logger.info(f"[Gemini] Analyzing email: {email['subject']}")
                    prompt = f"""
다음 이메일 내용을 분석하고 핵심 내용을 요약해주세요:

제목: {email['subject']}
발신자: {email['sender']}
날짜: {email['date']}

내용:
{email['body']}

요약时请 다음 형식으로 제공:
1. 메일의 주요 내용 (3-5줄)
2. 필요한 액션이 있다면 명시
3. 우선순위 (높음/중간/낮음)
"""
                    try:
                        summary = gemini_analyzer.analyze_text(prompt)

                        # Format message
                        message = f"""📧 **새 메일 분석 완료**

**제목:** {email['subject']}
**발신자:** {email['sender']}

**📝 Gemini 분석 결과:**
{summary}
"""

                        # Send to Telegram
                        if telegram_bot:
                            import asyncio
                            asyncio.run(telegram_bot.send_message(
                                chat_id=os.getenv("OWNER_ID"),
                                text=message
                            ))
                            logger.info(f"[Telegram] Email analysis sent")

                        # Send to Slack
                        if slack_bot:
                            from slack_sdk import WebClient
                            client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
                            client.chat_postMessage(
                                channel=os.getenv("SLACK_CHANNEL_ID"),
                                text=message
                            )
                            logger.info(f"[Slack] Email analysis sent")

                        # Mark as processed
                        processed_emails.add(email_id)

                    except Exception as e:
                        logger.error(f"Error analyzing email: {e}")

            # Wait before next check (120 seconds)
            time.sleep(120)

        except Exception as e:
            logger.error(f"Error in Gmail watcher thread: {e}")
            time.sleep(120)
