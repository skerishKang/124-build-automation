#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Calendar Checker Module
Monitors Google Calendar for today's events and sends reminders
"""

import os
import logging
import time
import datetime
from datetime import timedelta

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

# Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Environment variables
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
GMAIL_CLIENT_SECRET_PATH = os.getenv("GMAIL_CLIENT_SECRET_PATH", "gmail_credentials.json")
GMAIL_TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "gmail_token.json")


def get_calendar_service():
    """
    Get authenticated Calendar service
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
        service = build('calendar', 'v3', credentials=creds)
        logger.info("Google Calendar service initialized successfully")
        return service
    except Exception as e:
        logger.error(f"Error initializing Calendar service: {e}")
        return None


def get_today_events(service):
    """
    Get today's calendar events
    """
    try:
        now = datetime.datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        result = service.events().list(
            calendarId=GOOGLE_CALENDAR_ID,
            timeMin=start_of_day.isoformat() + 'Z',
            timeMax=end_of_day.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = result.get('items', [])
        return events
    except HttpError as error:
        logger.error(f"Calendar API error: {error}")
        return []


def format_event_time(event):
    """
    Format event start time
    """
    start = event['start'].get('dateTime', event['start'].get('date'))
    if start:
        try:
            dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
            return dt.strftime('%H:%M')
        except:
            return "All day"
    return "Unknown"


def check_upcoming_meetings(service):
    """
    Check for meetings starting in the next hour
    """
    try:
        now = datetime.datetime.now()
        in_one_hour = now + timedelta(hours=1)

        result = service.events().list(
            calendarId=GOOGLE_CALENDAR_ID,
            timeMin=now.isoformat() + 'Z',
            timeMax=in_one_hour.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = result.get('items', [])
        upcoming = []

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            if start:
                try:
                    event_time = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                    if event_time > now:  # Future event
                        upcoming.append(event)
                except:
                    pass

        return upcoming
    except HttpError as error:
        logger.error(f"Calendar API error: {error}")
        return []


def calendar_checker_thread(gemini_analyzer, telegram_bot=None):
    """
    Background thread to check Calendar
    """
    logger.info("📅 Google Calendar checker thread started")

    service = get_calendar_service()
    if not service:
        logger.error("Failed to initialize Calendar service. Exiting checker thread.")
        return

    sent_reminders = set()

    while True:
        try:
            # Check for upcoming meetings (within 1 hour)
            upcoming_meetings = check_upcoming_meetings(service)

            if upcoming_meetings:
                logger.info(f"[Calendar] Found {len(upcoming_meetings)} upcoming meeting(s)")

                for event in upcoming_meetings:
                    event_id = event['id']

                    # Skip if already sent reminder
                    if event_id in sent_reminders:
                        continue

                    # Check if meeting is within 10 minutes
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    if start:
                        try:
                            event_time = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                            time_until = (event_time - datetime.datetime.now()).total_seconds() / 60

                            if 0 < time_until < 10:  # Between 0 and 10 minutes
                                # Analyze event with Gemini
                                attendees = event.get('attendees', [])
                                attendees_list = [a.get('email', '') for a in attendees]

                                prompt = f"""
다음 회의 일정을 분석하고 핵심 정보를 요약해주세요:

회의명: {event.get('summary', 'N/A')}
시간: {format_event_time(event)}
장소: {event.get('location', 'N/A')}
참석자: {', '.join(attendees_list)}

요약时请 다음 형식으로 제공:
1. 회의 목적 및 주요 안건
2. 핵심 논의 포인트
3. 준비물이나 사전 준비사항 (있다면)
"""
                                try:
                                    summary = gemini_analyzer.analyze_text(prompt)

                                    # Format reminder message
                                    message = f"""📅 **회의 리마인더** ⏰

**회의명:** {event.get('summary', 'N/A')}
**시간:** {format_event_time(event)}
**장소:** {event.get('location', 'N/A')}
**참석자:** {len(attendees_list)}명

**📝 미팅 브리프:**
{summary}
"""

                                    # Send to Telegram
                                    if telegram_bot:
                                        import asyncio
                                        asyncio.run(telegram_bot.send_message(
                                            chat_id=os.getenv("OWNER_ID"),
                                            text=message
                                        ))
                                        logger.info(f"[Telegram] Calendar reminder sent for: {event.get('summary', 'N/A')}")

                                    # Mark as reminded
                                    sent_reminders.add(event_id)

                                except Exception as e:
                                    logger.error(f"Error analyzing calendar event: {e}")

                        except Exception as e:
                            logger.error(f"Error processing calendar event: {e}")

            # Wait before next check (300 seconds = 5 minutes)
            time.sleep(300)

        except Exception as e:
            logger.error(f"Error in Calendar checker thread: {e}")
            time.sleep(300)


def send_daily_schedule(service, gemini_analyzer, telegram_bot):
    """
    Send daily schedule summary
    """
    try:
        events = get_today_events(service)

        if not events:
            message = """📅 **오늘의 일정**

오늘은 예정된 일정이 없습니다.
"""
        else:
            event_list = []
            for event in events:
                time_str = format_event_time(event)
                event_list.append(f"• {time_str} - {event.get('summary', 'N/A')}")

            prompt = f"""
다음 오늘의 일정들을 분석하고 요약해주세요:

일정 목록:
{chr(10).join([f"{i+1}. {e.get('summary', 'N/A')} at {format_event_time(e)}" for i, e in enumerate(events)])}

요약时请 다음 형식으로 제공:
1. 오늘의 주요 업무 포인트
2. 시간대별 일정 요약
3. 주의사항이나 권장사항
"""
            try:
                summary = gemini_analyzer.analyze_text(prompt)
                message = f"""📅 **오늘의 일정 요약**

{chr(10).join(event_list)}

**📊 AI 요약:**
{summary}
"""
            except Exception as e:
                logger.error(f"Error analyzing schedule: {e}")
                message = f"""📅 **오늘의 일정**

총 {len(events)}개의 일정이 예정되어 있습니다.
"""

        # Send to Telegram
        import asyncio
        asyncio.run(telegram_bot.send_message(
            chat_id=os.getenv("OWNER_ID"),
            text=message
        ))
        logger.info("[Telegram] Daily schedule sent")

    except Exception as e:
        logger.error(f"Error sending daily schedule: {e}")
