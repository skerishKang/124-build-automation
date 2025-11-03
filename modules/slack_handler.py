#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Slack Integration Module
Monitors Slack channels and sends analysis results
"""

import os
import logging
import time
from typing import Dict, List

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)

# Environment variables
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "")

def to_slack_ts(value):
    """
    Slack latest/oldest는 '정수.소수' 문자열 형태를 선호.
    숫자면 float 변환 후 문자열로, 문자열 숫자면 그대로 반환.
    ISO8601 등 다른 형식은 여기서 epoch 변환 로직을 추가하세요.
    """
    if isinstance(value, (int, float)):
        return str(float(value))
    if isinstance(value, str) and value.replace(".","",1).isdigit():
        return value
    return None

class SlackHandler:
    def __init__(self):
        if SLACK_BOT_TOKEN:
            self.client = WebClient(token=SLACK_BOT_TOKEN)
            logger.info("Slack client initialized successfully")
        else:
            self.client = None
            logger.warning("Slack bot token not set. Slack functionality disabled.")

    def send_message(self, channel: str, text: str):
        """
        Send message to Slack channel
        """
        if not self.client:
            logger.warning("Slack not configured. Skipping message.")
            return None

        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=text
            )
            logger.info(f"Message sent to Slack channel {channel}")
            return response
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return None

    def send_file_analysis(self, file_name: str, summary: str, channel: str = None):
        """
        Send file analysis result to Slack
        """
        if not channel:
            channel = SLACK_CHANNEL_ID

        message = f"""📂 *File Analysis Complete*

*File:* {file_name}
*Summary:*
{summary}
"""

        return self.send_message(channel, message)

    def send_email_analysis(self, subject: str, sender: str, summary: str, channel: str = None):
        """
        Send email analysis to Slack
        """
        if not channel:
            channel = SLACK_CHANNEL_ID

        message = f"""📧 *Email Analysis*

*Subject:* {subject}
*From:* {sender}
*Summary:*
{summary}
"""

        return self.send_message(channel, message)

    def send_calendar_reminder(self, event_name: str, start_time: str, summary: str, channel: str = None):
        """
        Send calendar reminder to Slack
        """
        if not channel:
            channel = SLACK_CHANNEL_ID

        message = f"""📅 *Meeting Reminder*

*Event:* {event_name}
*Time:* {start_time}
*Brief:*
{summary}
"""

        return self.send_message(channel, message)

    def send_daily_summary(self, summary: str, channel: str = None):
        """
        Send daily summary to Slack
        """
        if not channel:
            channel = SLACK_CHANNEL_ID

        message = f"""📊 *Daily Summary*

{summary}
"""

        return self.send_message(channel, message)

    def get_channel_messages(self, channel: str, limit: int = 10):
        """
        Get recent messages from channel
        """
        if not self.client:
            logger.warning("Slack not configured. Skipping message retrieval.")
            return []

        try:
            result = self.client.conversations_history(
                channel=channel,
                limit=limit
            )
            return result['messages']
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return []


def slack_watcher_thread(gemini_analyzer, telegram_bot=None):
    """
    Background thread to monitor Slack channel
    """
    logger.info("💬 Slack watcher thread started")

    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
        logger.warning("Slack not configured. Exiting watcher thread.")
        return

    slack_handler = SlackHandler()

    # Track processed messages
    processed_messages = set()

    while True:
        try:
            # Get recent messages
            messages = slack_handler.get_channel_messages(SLACK_CHANNEL_ID, limit=5)

            for message in messages:
                msg_id = message.get('ts')
                if msg_id in processed_messages:
                    continue

                # Skip bot messages
                if message.get('bot_id'):
                    processed_messages.add(msg_id)
                    continue

                # Get message text
                text = message.get('text', '')
                if not text:
                    processed_messages.add(msg_id)
                    continue

                # Check if message contains trigger words
                trigger_words = ['@analyze', '分析해줘', '요약', 'summary', '분석']
                if any(word in text.lower() for word in trigger_words):
                    logger.info(f"[Slack] Analyzing message: {text[:50]}")

                    # Analyze with Gemini
                    prompt = f"""
다음 Slack 메시지를 분석하고 요약해주세요:

메시지: {text}

요약时请 다음 형식으로 제공:
1. 메시지의 핵심 내용
2. 요청된 작업이나 질문
3. 권장 응답 또는 액션
"""
                    try:
                        summary = gemini_analyzer.analyze_text(prompt)

                        # Send analysis back to Slack
                        response = f"*Analysis:*\n{summary}"
                        slack_handler.send_message(SLACK_CHANNEL_ID, response)

                        # Also send to Telegram if configured
                        if telegram_bot:
                            import asyncio
                            telegram_msg = f"""💬 **Slack 분석 완료**

**메시지:** {text[:100]}
**분석 결과:**
{summary}
"""
                            asyncio.run(telegram_bot.send_message(
                                chat_id=os.getenv("OWNER_ID"),
                                text=telegram_msg
                            ))
                            logger.info(f"[Telegram] Slack analysis sent")

                    except Exception as e:
                        logger.error(f"Error analyzing Slack message: {e}")

                # Mark as processed
                processed_messages.add(msg_id)

            # Clean old processed messages (keep only last 100)
            if len(processed_messages) > 100:
                processed_messages = set(list(processed_messages)[-100:])

            # Wait before next check (30 seconds)
            time.sleep(30)

        except Exception as e:
            logger.error(f"Error in Slack watcher thread: {e}")
            time.sleep(30)


# Utility functions
def send_to_slack(file_name: str, summary: str):
    """Send file analysis to Slack"""
    slack = SlackHandler()
    return slack.send_file_analysis(file_name, summary)


def send_email_to_slack(subject: str, sender: str, summary: str):
    """Send email analysis to Slack"""
    slack = SlackHandler()
    return slack.send_email_analysis(subject, sender, summary)


def send_reminder_to_slack(event_name: str, start_time: str, summary: str):
    """Send calendar reminder to Slack"""
    slack = SlackHandler()
    return slack.send_calendar_reminder(event_name, start_time, summary)


def send_daily_to_slack(summary: str):
    """Send daily summary to Slack"""
    slack = SlackHandler()
    return slack.send_daily_summary(summary)
