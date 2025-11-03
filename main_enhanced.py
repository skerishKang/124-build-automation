#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 AI 자동화 허브 - 통합 버전
Telegram + Google Drive + Gmail + Calendar + Notion + Slack + n8n + Gemini AI

모든 자동화 모듈을 하나의 프로그램으로 통합 실행
"""

import os
import logging
import tempfile
import subprocess
import threading
import time
import json
import re
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo



import google.generativeai as genai
# === [AUTO-INJECT] base utils ===
from modules.logging_setup import setup_logger
from modules.env_check import assert_env
try:
    from modules.drive_watcher import poll_drive_once
except Exception:
    poll_drive_once = None
# === [/AUTO-INJECT] ===

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ApplicationBuilder

# Google Drive API imports
try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import io
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Google Drive libraries not installed. Drive functionality will be disabled.")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('automation_hub.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Reduce httpx logging noise
logging.getLogger("httpx").setLevel(logging.WARNING)

# =============================================================================
# ENVIRONMENT VARIABLES
# =============================================================================

# Core settings
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8288922587:AAHUADrjbeLFSTxS_Hx6jEDEbAW88dOzgNY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAP8A5YjpwqOkHo0YLhXUMdzFubYoWSwMk")
OWNER_ID = os.getenv("OWNER_ID", "5833561465")

# Google Drive settings
GOOGLE_SERVICE_JSON_PATH = os.getenv("GOOGLE_SERVICE_JSON_PATH", "service_account.json")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "")

# Gmail settings
GMAIL_CLIENT_SECRET_PATH = os.getenv("GMAIL_CLIENT_SECRET_PATH", "gmail_credentials.json")
GMAIL_TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "gmail_token.json")

# Calendar settings
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")

# Notion settings
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")

# Slack settings
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "")

# n8n settings
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")

# Processed files tracking
PROCESSED_FILES_DB = "processed_files.json"

# =============================================================================
# GEMINI AI SETUP
# =============================================================================

try:
    genai.configure(api_key=GEMINI_API_KEY)
    # Enhanced generation config for stability and performance
    generation_config = {
        "temperature": float(os.getenv("GEN_TEMPERATURE", "0.2")),
        "top_p": 0.9,
        "max_output_tokens": int(os.getenv("GEN_MAX_OUTPUT_TOKENS", "1024")),
    }
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    model = genai.GenerativeModel(
        'gemini-2.5-pro',
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    logger.info("✅ Gemini AI initialized (gemini-2.5-flash with enhanced config)")
except Exception as e:
    logger.error(f"❌ Failed to initialize Gemini: {e}")
    model = None

# =============================================================================
# ENHANCED UTILITIES
# =============================================================================



# =============================================================================
# FILE PROCESSING UTILITIES
# =============================================================================

def convert_voice_to_wav(input_path: str, output_path: str) -> bool:
    """Convert voice file (ogg/mp3) to wav format"""
    try:
        cmd = ['ffmpeg', '-i', input_path, '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', output_path, '-y']
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        logger.error(f"Error converting voice: {e}")
        return False


def transcribe_audio(wav_path: str) -> str:
    """Transcribe audio to text using Gemini"""
    if not model:
        return "Gemini client not initialized."

    try:
        with open(wav_path, 'rb') as audio_file:
            audio_data = audio_file.read()

        response = safe_generate(
            "Transcribe this audio to text. Provide only the text without explanations.",
            parts=[{"mime_type": "audio/wav", "data": audio_data}]
        )
        return response.strip() if response else "음성 전사에 실패했습니다."
    except Exception as e:
        logger.error(f"Error transcribing: {e}")
        return "음성 전사에 실패했습니다."


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF"""
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = "".join([page.extract_text() + "\n" for page in reader.pages])
        return text
    except Exception as e:
        logger.error(f"Error extracting PDF: {e}")
        return "PDF 텍스트 추출 실패"


def extract_text_from_docx(docx_path: str) -> str:
    """Extract text from DOCX"""
    try:
        from docx import Document
        doc = Document(docx_path)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        logger.error(f"Error extracting DOCX: {e}")
        return "DOCX 텍스트 추출 실패"


def extract_text_from_txt(txt_path: str) -> str:
    """Extract text from TXT"""
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error reading TXT: {e}")
        return "TXT 파일 읽기 실패"

# === [AUTO-INJECT] convo mode state ===
from collections import defaultdict
from modules.intent_router import detect_intent

# 채팅방/사용자별 모드 상태: 'chat' | 'analyze' | 'auto'
_CONVO_MODE = defaultdict(lambda: "chat")  # 기본은 'chat'

def set_mode(chat_id: int, mode: str):
    mode = (mode or "chat").lower()
    if mode not in ("chat", "analyze", "auto"):
        mode = "chat"
    _CONVO_MODE[chat_id] = mode
    return mode

def get_mode(chat_id: int):
    return _CONVO_MODE[chat_id]
# === [/AUTO-INJECT] ===

# === [AUTO-INJECT] telegram commands ===
async def cmd_chat(update, context):
    m = set_mode(update.effective_chat.id, "chat")
    await context.bot.send_message(update.effective_chat.id, "모드를 '대화(chat)'로 전환했습니다. 짧은 문장은 요약하지 않습니다.")

async def cmd_analyze(update, context):
    m = set_mode(update.effective_chat.id, "analyze")
    await context.bot.send_message(update.effective_chat.id, "모드를 '분석(analyze)'로 전환했습니다. 긴/짧은 문서도 분석합니다.")

async def cmd_auto(update, context):
    m = set_mode(update.effective_chat.id, "auto")
    await context.bot.send_message(update.effective_chat.id, "모드를 '자동(auto)'로 전환했습니다. 내용에 따라 대화/분석을 자동 선택합니다.")

def register_mode_commands(app):
    from telegram.ext import CommandHandler
    app.add_handler(CommandHandler("chat", cmd_chat))
    app.add_handler(CommandHandler("analyze", cmd_analyze))
    app.add_handler(CommandHandler("auto", cmd_auto))
# === [/AUTO-INJECT] ===

# === [AUTO-INJECT] convo mode state ===
from collections import defaultdict
from modules.intent_router import detect_intent

# 채팅방/사용자별 모드 상태: 'chat' | 'analyze' | 'auto'
_CONVO_MODE = defaultdict(lambda: "chat")  # 기본은 'chat'

def set_mode(chat_id: int, mode: str):
    mode = (mode or "chat").lower()
    if mode not in ("chat", "analyze", "auto"):
        mode = "chat"
    _CONVO_MODE[chat_id] = mode
    return mode

def get_mode(chat_id: int):
    return _CONVO_MODE[chat_id]
# === [/AUTO-INJECT] ===

# === [AUTO-INJECT] telegram commands ===
async def cmd_chat(update, context):
    m = set_mode(update.effective_chat.id, "chat")
    await context.bot.send_message(update.effective_chat.id, "모드를 '대화(chat)'로 전환했습니다. 짧은 문장은 요약하지 않습니다.")

async def cmd_analyze(update, context):
    m = set_mode(update.effective_chat.id, "analyze")
    await context.bot.send_message(update.effective_chat.id, "모드를 '분석(analyze)'로 전환했습니다. 긴/짧은 문서도 분석합니다.")

async def cmd_auto(update, context):
    m = set_mode(update.effective_chat.id, "auto")
    await context.bot.send_message(update.effective_chat.id, "모드를 '자동(auto)'로 전환했습니다. 내용에 따라 대화/분석을 자동 선택합니다.")

def register_mode_commands(app):
    from telegram.ext import CommandHandler
    app.add_handler(CommandHandler("chat", cmd_chat))
    app.add_handler(CommandHandler("analyze", cmd_analyze))
    app.add_handler(CommandHandler("auto", cmd_auto))
# === [/AUTO-INJECT] ===

# =============================================================================
# TELEGRAM BOT HANDLERS
# =============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    mode = context.user_data.get("mode", "auto")
    welcome_message = f"""
🤖 **AI 자동화 허브** 시작합니다! 🚀

현재 모드: [{mode}]

✅ **활성화된 기능:**
• 📱 Telegram 메시지 분석 (개선된 의도 분류)
• 🎤 음성 메시지 → 텍스트 변환
• 🖼️ 이미지 분석 (Gemini Vision)
• 📄 문서 분석 (PDF/DOCX/TXT)
• 📁 Google Drive 자동 감시
• 📧 Gmail 새 메일 분석
• 📅 Calendar 리마인더
• 💬 Slack 연동
• 📝 Notion 자동 기록
• 🔗 n8n 워크플로우 연동

💡 `/mode chat | analyze | auto` 로 모드 전환 가능!

파일이나 Google Drive에 업로드해보세요!
AI가 자동으로 분석해서 결과를 알려드립니다.
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')
    logger.info(f"New user started bot: {update.effective_user.id}")


async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mode command to toggle response mode"""
    user_id = update.effective_user.id

    if not context.args:
        # Show current mode
        current_mode = context.user_data.get('mode', 'auto')
        mode_descriptions = {
            'auto': '자동 (의도에 따라 응답)',
            'chat': '대화 모드 (모든 입력을 자연스러운 대화로 처리)',
            'analyze': '분석 모드 (모든 입력을 요약/분석)'
        }
        description = mode_descriptions.get(current_mode, current_mode)
        await update.message.reply_text(f"현재 모드: {description}\n\n사용법: /mode auto|chat|analyze")
        return

    new_mode = context.args[0].lower()
    if new_mode in ['auto', 'chat', 'analyze']:
        context.user_data['mode'] = new_mode
        mode_descriptions = {
            'auto': '자동 (의도에 따라 응답)',
            'chat': '대화 모드 (모든 입력을 자연스러운 대화로 처리)',
            'analyze': '분석 모드 (모든 입력을 요약/분석)'
        }
        description = mode_descriptions.get(new_mode, new_mode)
        await update.message.reply_text(f"✅ 모드가 {description}로 변경되었습니다.")
        logger.info(f"User {user_id} changed mode to {new_mode}")
    else:
        await update.message.reply_text("❌ 잘못된 모드입니다. 사용법: /mode auto|chat|analyze")


# === [AUTO-INJECT] telegram short-circuit ===
def _is_smalltalk(text: str) -> bool:
    t = (text or "").strip().lower()
    return t in {"hi", "hello", "안녕", "ㅎㅇ", "하이"} or (len(t) <= 5 and any(k in t for k in ["안녕","hi","ㅎㅇ","하이"]))

def handle_incoming_text(text: str) -> str:
    """
    기존 파이프라인 진입 전, 짧은 인삿말/단문은 직접 응답으로 처리.
    """
    if not text or not text.strip():
        return "내용이 비어 있어요. 분석할 텍스트를 보내주세요."
    if _is_smalltalk(text):
        return "안녕하세요! 무엇을 도와드릴까요? 😊"
    # 길면 기존 Map-Reduce/요약 파이프라인으로
    return None  # None이면 이후 요약 로직으로 진행
# === [/AUTO-INJECT] ===


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages with improved intent classification and error handling."""
    user_text = update.message.text or ""
    user_id = update.effective_user.id
    logger.info(f"Received text from user {user_id}: {user_text[:50]}...")

    try:
        # 1. Use the short-circuit function for small talk
        quick_response = handle_incoming_text(user_text)
        if quick_response is not None:
            await update.message.reply_text(quick_response)
            return

        # 2. For longer text, use the robust pipeline
        from modules.gemini_client import generate_text_safe
        
        await update.message.reply_text("📝 텍스트를 분석 중입니다. 잠시만 기다려주세요...")

        prompt = f"다음 텍스트를 분석하고, 내용을 요약한 뒤, 핵심 액션 아이템을 1~3개 제안해주세요.\n\n---\n{user_text}"
        result = generate_text_safe(prompt)

        if result["ok"]:
            response_text = result["text"]
        elif result.get("blocked"):
            # 2nd-pass with a safer prompt
            safe_prompt = f"규칙: 민감한 표현은 [REDACTED]로 치환하고, 핵심 요지만 중립적으로 요약해주세요.\n\n---\n{user_text}"
            result2 = generate_text_safe(safe_prompt)
            if result2["ok"]:
                response_text = "해당 내용은 일부 민감할 수 있는 표현을 제외하고 중립적으로 요약했습니다.\n\n" + result2["text"]
            else:
                response_text = "요청을 처리할 수 없었습니다. 내용에 민감한 부분이 포함되어 있을 수 있습니다. 다른 표현으로 다시 시도해 주세요."
        else:  # General error
            response_text = "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
            logger.error(f"General error from generate_text_safe: {result.get('reason')}")

        await update.message.reply_text(response_text)

    except Exception as e:
        logger.exception(f"Error in handle_text_message: {e}")
        await update.message.reply_text("메시지 처리 중 예기치 않은 오류가 발생했습니다.")


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages"""
    user_id = update.effective_user.id
    voice = update.message.voice

    logger.info(f"Received voice from user {user_id}")

    try:
        # Download and convert
        file = await context.bot.get_file(voice.file_id)
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as ogg_file:
            await file.download_to_drive(ogg_file.name)
            ogg_path = ogg_file.name

        wav_path = ogg_path.replace('.ogg', '.wav')
        if not convert_voice_to_wav(ogg_path, wav_path):
            await update.message.reply_text("❌ 음성 변환 실패")
            return

        # Transcribe
        transcription = transcribe_audio(wav_path)
        if transcription == "음성 전사에 실패했습니다.":
            await update.message.reply_text(transcription)
            os.unlink(ogg_path)
            os.unlink(wav_path)
            return

        # Analyze with Gemini
        summary = safe_generate(f"음성 내용을 분석하고 요약해주세요:\n\n{transcription}")

        message = f"🎤 **음성 분석 결과:**\n\n**📄 전사:**\n{transcription}\n\n**📝 요약:**\n{summary}"
        await update.message.reply_text(message, parse_mode='Markdown')

        # Save to Notion
        if NOTION_TOKEN:
            try:
                from modules.notion_updater import save_transcript_to_notion
                save_transcript_to_notion("Telegram Voice", f"User {user_id}", transcription, summary)
            except Exception as e:
                logger.error(f"Notion save error: {e}")

        # Send to n8n
        if N8N_WEBHOOK_URL:
            from modules.n8n_connector import send_transcript_to_n8n
            send_transcript_to_n8n("Telegram Voice", transcription, summary)

        os.unlink(ogg_path)
        os.unlink(wav_path)
        logger.info(f"Sent voice analysis to user {user_id}")

    except Exception as e:
        logger.error(f"Error processing voice: {e}")
        await update.message.reply_text("❌ 음성 처리 중 오류 발생")


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle images"""
    user_id = update.effective_user.id
    photo = update.message.photo[-1]

    logger.info(f"Received image from user {user_id}")

    if not model:
        await update.message.reply_text("❌ Gemini AI가 초기화되지 않았습니다.")
        return

    try:
        file = await context.bot.get_file(photo.file_id)
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as img_file:
            await file.download_to_drive(img_file.name)
            img_path = img_file.name

        with open(img_path, 'rb') as image_file:
            image_data = image_file.read()

        analysis = safe_generate(
            "이미지를 상세히 분석해주세요.",
            parts=[{"mime_type": "image/jpeg", "data": image_data}]
        )

        message = f"🖼️ **이미지 분석 결과:**\n\n{analysis}"
        await update.message.reply_text(message, parse_mode='Markdown')

        # Save to Notion
        if NOTION_TOKEN:
            try:
                from modules.notion_updater import save_file_to_notion
                save_file_to_notion(f"Image_{user_id}.jpg", analysis, "Image")
            except Exception as e:
                logger.error(f"Notion save error: {e}")

        os.unlink(img_path)
        logger.info(f"Sent image analysis to user {user_id}")

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text("❌ 이미지 분석 중 오류 발생")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle documents with improved processing"""
    user_id = update.effective_user.id
    document = update.message.document

    logger.info(f"Received document from user {user_id}: {document.file_name}")

    try:
        file = await context.bot.get_file(document.file_id)
        file_ext = os.path.splitext(document.file_name)[1].lower()
        temp_file = tempfile.NamedTemporaryFile(suffix=file_ext, delete=False)
        await file.download_to_drive(temp_file.name)
        temp_file.close()  # Close file handle explicitly
        doc_path = temp_file.name

        # Extract text
        if file_ext == '.pdf':
            text_content = extract_text_from_pdf(doc_path)
        elif file_ext == '.docx':
            text_content = extract_text_from_docx(doc_path)
        elif file_ext in ['.txt', '.md', '.markdown']:
            text_content = extract_text_from_txt(doc_path)
        elif file_ext == '.json':
            text_content = extract_text_from_txt(doc_path)
        else:
            await update.message.reply_text("❌ 지원하지 않는 형식입니다. (.pdf, .docx, .txt, .md, .json만 지원)")
            if os.path.exists(doc_path):
                os.unlink(doc_path)
            return

        # Use map_reduce_summarize for all document processing
        if text_content and "실패" not in text_content:
            await update.message.reply_text("📄 문서가 길어 Map-Reduce 요약을 수행합니다…")
            summary = map_reduce_summarize(text_content)
        else:
            summary = text_content or "텍스트 추출 실패"

        message = f"📄 **문서 분석 결과:**\n\n**📝 요약:**\n{summary}"
        await update.message.reply_text(message, parse_mode='Markdown')

        # Save to Notion
        if NOTION_TOKEN:
            try:
                from modules.notion_updater import save_file_to_notion
                save_file_to_notion(document.file_name, summary, "Document")
            except Exception as e:
                logger.error(f"Notion save error: {e}")

        # Send to n8n
        if N8N_WEBHOOK_URL:
            from modules.n8n_connector import send_file_to_n8n
            send_file_to_n8n(document.file_name, summary)

        if os.path.exists(doc_path):
            os.unlink(doc_path)
        logger.info(f"Sent document analysis to user {user_id}")

    except Exception as e:
        logger.error(f"Error processing document: {e}")
        await update.message.reply_text("❌ 문서 처리 중 오류 발생")


# =============================================================================
# GOOGLE DRIVE WATCHER
# =============================================================================

def load_processed_files():
    """Load processed files list"""
    try:
        if os.path.exists(PROCESSED_FILES_DB):
            with open(PROCESSED_FILES_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading processed files: {e}")
        return []


def save_processed_files(processed_list):
    """Save processed files list"""
    try:
        with open(PROCESSED_FILES_DB, 'w', encoding='utf-8') as f:
            json.dump(processed_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving processed files: {e}")


def initialize_drive_service():
    """Initialize Google Drive API service"""
    try:
        credentials = Credentials.from_service_account_file(
            GOOGLE_SERVICE_JSON_PATH,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        service = build('drive', 'v3', credentials=credentials)
        logger.info("✅ Google Drive service initialized")
        return service
    except Exception as e:
        logger.error(f"❌ Drive service error: {e}")
        return None


def get_new_files_from_drive(service, processed_files):
    """Get new files from Drive"""
    try:
        results = service.files().list(
            q=f"'{DRIVE_FOLDER_ID}' in parents and trashed=false",
            pageSize=100,
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        items = results.get('files', [])
        return [item for item in items if item['id'] not in processed_files]
    except Exception as e:
        logger.error(f"Error getting Drive files: {e}")
        return []


def download_file_from_drive(service, file_id, file_name):
    """Download file from Drive"""
    try:
        request = service.files().get_media(fileId=file_id)
        file_path = os.path.join(tempfile.gettempdir(), file_name)

        with open(file_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

        return file_path
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None


def analyze_drive_file(file_path, mime_type):
    """Analyze file from Drive with improved long text handling"""
    try:
        file_ext = os.path.splitext(file_path)[1].lower()

        if mime_type == 'application/pdf' or file_ext == '.pdf':
            text = extract_text_from_pdf(file_path)
        elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or file_ext == '.docx':
            text = extract_text_from_docx(file_path)
        elif mime_type == 'text/plain' or file_ext == '.txt':
            text = extract_text_from_txt(file_path)
        elif mime_type == 'text/markdown' or file_ext == '.md':
            text = extract_text_from_txt(file_path)
        elif mime_type.startswith('image/'):
            with open(file_path, 'rb') as f:
                data = f.read()
            return safe_generate(
                "이미지를 상세히 분석해주세요.",
                parts=[{"mime_type": mime_type, "data": data}]
            )
        elif mime_type.startswith('audio/'):
            wav_path = file_path.replace(file_ext, '.wav')
            if convert_voice_to_wav(file_path, wav_path):
                transcription = transcribe_audio(wav_path)
                os.unlink(wav_path)
                if model:
                    summary = safe_generate(f"음성 내용을 분석해주세요:\n\n{transcription}")
                    return f"**전사:**\n{transcription}\n\n**분석:**\n{summary}"
                return transcription
            return "음성 변환 실패"
        else:
            return "지원하지 않는 형식입니다."

        if model and text and "실패" not in text:
            return map_reduce_summarize(text)
        return text

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return "파일 분석 오류"


async def send_telegram_message(bot, text):
    """Send message to Telegram"""
    try:
        if OWNER_ID:
            await bot.send_message(chat_id=OWNER_ID, text=text, parse_mode='Markdown')
            logger.info(f"📱 Telegram message sent")
    except Exception as e:
        logger.error(f"Telegram send error: {e}")


def drive_watcher_thread(application):
    """Monitor Google Drive folder"""
    logger.info("🔍 Google Drive watcher started")

    service = initialize_drive_service()
    if not service:
        logger.error("❌ Drive service failed. Exiting.")
        return

    processed_files = load_processed_files()

    while True:
        try:
            new_files = get_new_files_from_drive(service, processed_files)

            if new_files:
                logger.info(f"[Drive] Found {len(new_files)} new file(s)")

                for file_info in new_files:
                    file_id = file_info['id']
                    file_name = file_info['name']
                    mime_type = file_info['mimeType']

                    logger.info(f"[Drive] New file: {file_name}")

                    file_path = download_file_from_drive(service, file_id, file_name)
                    if not file_path:
                        continue

                    analysis = analyze_drive_file(file_path, mime_type)
                    message = f"📂 [{file_name}]\n\n📝 **Gemini 분석 결과:**\n{analysis}"

                    # Send to Telegram using asyncio.create_task
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(send_telegram_message(application.bot, message))
                    finally:
                        loop.close()

                    # Save to Notion
                    if NOTION_TOKEN:
                        try:
                            from modules.notion_updater import save_file_to_notion
                            save_file_to_notion(file_name, analysis, "Drive File")
                        except Exception as e:
                            logger.error(f"Notion error: {e}")

                    # Send to n8n
                    if N8N_WEBHOOK_URL:
                        from modules.n8n_connector import send_file_to_n8n
                        send_file_to_n8n(file_name, analysis)

                    os.unlink(file_path)
                    processed_files.append(file_id)
                    save_processed_files(processed_files)
                    logger.info(f"[Drive] Completed: {file_name}")

            time.sleep(60)

        except Exception as e:
            logger.error(f"Drive watcher error: {e}")
            time.sleep(60)


# =============================================================================
# ERROR HANDLER
# =============================================================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.warning(f'Error: {context.error}')
    if update and update.effective_message:
        update.effective_message.reply_text("❌ 알 수 없는 오류가 발생했습니다.")


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def build_app() -> Application:
    """Build the Telegram application with enhanced handlers"""
    app: Application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Core handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mode", set_mode))
    
    # Message handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    return app


def main():
    """
    Start all automation modules with enhanced configuration
    """
    logger.info("=" * 60)

    # === [AUTO-INJECT] boot ===
    setup_logger("app")
    assert_env()
    # === [/AUTO-INJECT] ===

    logger.info("🤖 AI 자동화 허브 시작 (개선된 버전)")
    logger.info("=" * 60)

    # Create Telegram application
    application = build_app()

    # === [AUTO-INJECT] register commands ===
    try:
        register_mode_commands(application)  # application은 기존 Telegram Application 인스턴스
    except Exception:
        pass
    # === [/AUTO-INJECT] ===

    # === [AUTO-INJECT] register commands ===
    try:
        register_mode_commands(application)  # application은 기존 Telegram Application 인스턴스
    except Exception:
        pass
    # === [/AUTO-INJECT] ===

    # === [AUTO-INJECT] drive schedule ===
    import os, threading, time

    def _fetch_list():
        # TODO: Google Drive API 연동 함수로 교체 (list: [{id,name,mimeType}, ...])
        return []

    def _handle_file(f):
        # TODO: 파일 다운로드 → 요약 → 알림/저장 로직
        pass

    def _drive_loop():
        while True:
            try:
                if poll_drive_once:
                    poll_drive_once(_fetch_list, _handle_file)
            except Exception as e:
                logger.exception(f"[drive] {e}")
            time.sleep(60)

    if os.getenv("DRIVE_FOLDER_ID") and poll_drive_once and "AUTO_DRIVE_LOOP" not in globals():
        AUTO_DRIVE_LOOP = True
        threading.Thread(target=_drive_loop, daemon=True).start()
        logger.info("Drive watcher thread started.")
    # === [/AUTO-INJECT] ===


    # Start Google Drive watcher
    if DRIVE_FOLDER_ID:
        drive_thread = threading.Thread(target=drive_watcher_thread, args=(application,), daemon=True)
        drive_thread.start()
        logger.info("✅ Google Drive watcher started")
    else:
        logger.info("⚠️ Drive monitoring disabled")

    # Start Gmail watcher
    if os.getenv("GMAIL_CLIENT_SECRET_PATH"):
        try:
            import asyncio
            from modules.gmail_watcher import gmail_watcher_thread
            from modules.gemini_client import get_gemini_client

            gmail_thread = threading.Thread(
                target=gmail_watcher_thread,
                args=(get_gemini_client(), application.bot),
                daemon=True
            )
            gmail_thread.start()
            logger.info("✅ Gmail watcher started")
        except Exception as e:
            logger.error(f"❌ Gmail watcher failed: {e}")
    else:
        logger.info("⚠️ Gmail monitoring disabled")

    # Start Calendar checker
    if os.getenv("GMAIL_CLIENT_SECRET_PATH"):
        try:
            from modules.calendar_checker import calendar_checker_thread
            from modules.gemini_client import get_gemini_client

            calendar_thread = threading.Thread(
                target=calendar_checker_thread,
                args=(get_gemini_client(), application.bot),
                daemon=True
            )
            calendar_thread.start()
            logger.info("✅ Calendar checker started")
        except Exception as e:
            logger.error(f"❌ Calendar checker failed: {e}")
    else:
        logger.info("⚠️ Calendar monitoring disabled")

    # Start Slack watcher
    if SLACK_BOT_TOKEN:
        try:
            from modules.slack_handler import slack_watcher_thread
            from modules.gemini_client import get_gemini_client

            slack_thread = threading.Thread(
                target=slack_watcher_thread,
                args=(get_gemini_client(), application.bot),
                daemon=True
            )
            slack_thread.start()
            logger.info("✅ Slack watcher started")
        except Exception as e:
            logger.error(f"❌ Slack watcher failed: {e}")
    else:
        logger.info("⚠️ Slack integration disabled")

    # Start polling
    logger.info("✅ 모든 모듈 초기화 완료")
    logger.info("📡 Telegram 봇 폴링 시작...")
    logger.info("=" * 60)
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == '__main__':
    main()
