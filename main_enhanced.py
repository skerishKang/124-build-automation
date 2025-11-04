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
import shutil
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
from modules.logging_setup import setup_logger
from modules.env_check import assert_env
try:
    from modules.drive_watcher import poll_drive_once
except Exception:
    poll_drive_once = None

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
        if not shutil.which('ffmpeg'):
            logger.error("ffmpeg not found. Please install ffmpeg and ensure it's in PATH.")
            return False
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

        res = generate_vision_safe(
            "Transcribe this audio to text. Provide only the text without explanations.",
            parts=[{"mime_type": "audio/wav", "data": audio_data}]
        )
        response = res.get("text") if res.get("ok") else "음성 전사에 실패했습니다." 
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
    encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin-1']
    for enc in encodings:
        try:
            with open(txt_path, 'r', encoding=enc, errors='replace') as file:
                return file.read()
        except Exception:
            continue
    return "텍스트 파일 읽기 실패"


def map_reduce_summarize(text: str, max_chunk_size: int = 8000, max_final_summary: int = 1000) -> str:
    """
    긴 텍스트를 Map-Reduce 방식으로 요약
    1. 텍스트를 청크로 나누기
    2. 각 청크 요약 (Map)
    3. 요약 내용 합쳐서 최종 요약 (Reduce)
    """
    if not model:
        return "Gemini client not initialized."

    try:
        # 텍스트가 짧으면 일반 요약
        if len(text) <= max_chunk_size:
            prompt = f"""다음 텍스트를 간결하게 요약해주세요.
핵심 내용만 {max_final_summary}자 이내로 정리해주세요.

텍스트:
{text}

요약:"""
            res = generate_text_safe(prompt, temperature=0.3, max_tokens=max_final_summary)
            return res.get("text", "요약 실패") if res.get("ok") else "요약 실패"

        # 긴 텍스트를 청크로 나누기
        chunks = []
        current_pos = 0
        while current_pos < len(text):
            chunk_end = min(current_pos + max_chunk_size, len(text))
            
            # 문장 경계 찾기
            if chunk_end < len(text):
                last_period = text.rfind('.', current_pos, chunk_end)
                if last_period > current_pos + max_chunk_size // 2:
                    chunk_end = last_period + 1
            
            chunk = text[current_pos:chunk_end].strip()
            if chunk:
                chunks.append(chunk)
            current_pos = chunk_end

        # 각 청크별 요약 (Map)
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            prompt = f"""이 텍스트의 핵심 내용을 간결하게 요약해주세요.
{i+1}/{len(chunks)}번째 부분입니다.

내용:
{chunk}

요약:"""
            res = generate_text_safe(prompt, temperature=0.3, max_tokens=300)
            if res.get("ok"):
                chunk_summaries.append(res["text"])

        # 요약 내용 합치기 (Reduce)
        if chunk_summaries:
            combined_summaries = "\n\n".join([f"- {s}" for s in chunk_summaries])
            final_prompt = f"""다음은 긴 텍스트를 부분별로 요약한 내용입니다.
이를 전체를 아우르는 하나의连贯된 요약으로 정리해주세요.
{max_final_summary}자 이내로 간결하게 정리해주세요.

부분별 요약:
{combined_summaries}

최종 요약:"""
            res = generate_text_safe(final_prompt, temperature=0.3, max_tokens=max_final_summary)
            return res.get("text", "최종 요약 실패") if res.get("ok") else "최종 요약 실패"

        return "요약할 수 있는 내용이 없습니다."

    except Exception as e:
        logger.error(f"Map-reduce 요약 오류: {e}")
        return f"요약 중 오류 발생: {str(e)}"

# Treat common text-like extensions as plain text previewable types
SUPPORTED_TEXT_EXTS = {
    '.txt', '.md', '.markdown', '.json', '.jsonl', '.yaml', '.yml', '.csv', '.log', '.ini', '.cfg', '.conf',
    '.py', '.js', '.ts', '.jsx', '.tsx', '.css', '.html', '.htm', '.xml', '.java', '.rb', '.go', '.rs', '.sh', '.bat', '.ps1', '.toml', '.sql'
}



# === [AUTO-INJECT] telegram commands ===





# =============================================================================
# TELEGRAM BOT HANDLERS
# =============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_message_raw = (
        "🤖 **AI 자동화 허브** 시작합니다! 🚀\n\n"
        "✅ **활성화된 기능:**\n"
        "• 📱 Telegram 메시지 분석 (Gemini가 자동으로 의도 판단)\n"
        "• 🎤 음성 메시지 → 텍스트 변환 및 분석\n"
        "• 🖼️ 이미지 분석 (Gemini Vision)\n"
        "• 📄 문서 분석 (PDF/DOCX/TXT)\n"
        "• 📁 Google Drive 자동 감시\n"
        "• 📧 Gmail 새 메일 분석\n"
        "• 📅 Calendar 리마인더\n"
        "• 💬 Slack 연동\n"
        "• 📝 Notion 자동 기록\n"
        "• 🔗 n8n 워크플로우 연동\n\n"
        "파일이나 Google Drive에 업로드해보세요!\n"
        "AI가 자동으로 분석해서 결과를 알려드립니다."
    )
    formatted_message, parse_mode = format_ai_text(welcome_message_raw)
    await update.message.reply_text(formatted_message, parse_mode=parse_mode)
    logger.info(f"New user started bot: {update.effective_user.id}")








# === [AUTO-INJECT] message routing ===
from modules.gemini_client import generate_text_safe
from modules.telegram_utils import format_ai_text

async def handle_text(update, context):
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()

    if not text:
        formatted_message, parse_mode = format_ai_text("내용이 비어 있어요. 텍스트를 보내주세요.")
        await context.bot.send_message(chat_id, formatted_message, parse_mode=parse_mode)
        return

    # Use Gemini to handle all text inputs, letting it determine the intent
    prompt = f"사용자의 요청: {text}\n\n이 요청에 대해 자연스럽게 대화하거나, 필요한 경우 분석/요약하여 응답해주세요."
    res = generate_text_safe(prompt)
    
    if res.get("ok"):
        formatted_message, parse_mode = format_ai_text(res["text"])
        await context.bot.send_message(chat_id, formatted_message, parse_mode=parse_mode)
    else:
        formatted_message, parse_mode = format_ai_text("요청 처리 중 문제가 발생했습니다. 표현을 조금 바꿔 다시 시도해 주세요.")
        await context.bot.send_message(chat_id, formatted_message, parse_mode=parse_mode)
# === [/AUTO-INJECT] ===


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
            await update.message.reply_text("❌ 음성 변환 실패 (ffmpeg가 설치되어 있는지 확인해 주세요)")
            return

        # Transcribe
        transcription = transcribe_audio(wav_path)
        if transcription == "음성 전사에 실패했습니다.":
            formatted_message, parse_mode = format_ai_text(transcription)
            await update.message.reply_text(formatted_message, parse_mode=parse_mode)
            os.unlink(ogg_path)
            os.unlink(wav_path)
            return

        # Analyze with Gemini
        res = generate_text_safe(f"음성 내용을 분석하고 요약해주세요. 출력은 마크다운 없이 순수 텍스트로 답변하세요.\n\n{transcription}")
        summary = res.get("text") if res.get("ok") else "음성 분석 및 요약에 실패했습니다." 

        message = (
            "🎤 음성 분석 결과:\n\n"
            f"전사:\n{transcription}\n\n"
            f"요약:\n{summary}"
        )
        await update.message.reply_text(message)

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

        res = generate_vision_safe(
            "이미지를 상세히 분석해주세요. 출력은 마크다운 없이 순수 텍스트로 제공하세요.",
            parts=[{"mime_type": "image/jpeg", "data": image_data}]
        )
        analysis = res.get("text") if res.get("ok") else "이미지 분석에 실패했습니다." 
        message = f"🖼️ 이미지 분석 결과:\n\n{analysis}"
        await update.message.reply_text(message)

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

        # Extract content depending on type
        if file_ext == '.pdf':
            text_content = extract_text_from_pdf(doc_path)
            mode = 'summary'
        elif file_ext == '.docx':
            text_content = extract_text_from_docx(doc_path)
            mode = 'summary'
        elif file_ext in SUPPORTED_TEXT_EXTS:
            text_content = extract_text_from_txt(doc_path)
            mode = 'preview'
        else:
            await update.message.reply_text("❌ 지원하지 않는 형식입니다. (.pdf, .docx, .txt, .md, .json, .xml, .html, .css, .js, .py 등 텍스트 파일 지원)")
            if os.path.exists(doc_path):
                os.unlink(doc_path)
            return

        # For text-like files, show a plain text preview; for others, summarize
        if mode == 'preview':
            preview_limit = int(os.getenv('DOC_PREVIEW_LIMIT', '3500'))
            content = (text_content or '')
            if not content:
                content = "텍스트 추출 실패"
            if len(content) > preview_limit:
                preview = content[:preview_limit]
                message = f"📄 파일 내용 (앞부분 {preview_limit}자):\n\n{preview}\n\n… (이하 생략)"
            else:
                message = f"📄 파일 내용:\n\n{content}"
            await update.message.reply_text(message)
        else:
            if text_content and "실패" not in text_content:
                await update.message.reply_text("📄 문서가 길어 Map-Reduce 요약을 수행합니다…")
                summary = map_reduce_summarize(text_content)
            else:
                summary = text_content or "텍스트 추출 실패"
            message = f"📄 문서 분석 결과:\n\n요약:\n{summary}"
            await update.message.reply_text(message)

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
            res = generate_vision_safe(
                "이미지를 상세히 분석해주세요.",
                parts=[{"mime_type": mime_type, "data": data}]
            )
            return res.get("text") if res.get("ok") else "이미지 분석에 실패했습니다." 
        elif mime_type.startswith('audio/'):
            wav_path = file_path.replace(file_ext, '.wav')
            if convert_voice_to_wav(file_path, wav_path):
                transcription = transcribe_audio(wav_path)
                os.unlink(wav_path)
                if model:
                    res = generate_text_safe(f"음성 내용을 분석해주세요. 출력은 마크다운 없이 순수 텍스트로 제공하세요.\n\n{transcription}")
                    summary = res.get("text") if res.get("ok") else "음성 분석에 실패했습니다."
                    return f"전사:\n{transcription}\n\n분석:\n{summary}" 
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
            await bot.send_message(chat_id=OWNER_ID, text=text)
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
                    formatted_file, mode_file = format_ai_text(file_name)
                    formatted_analysis, mode_ana = format_ai_text(analysis)
                    mode = mode_file if mode_file == mode_ana else 'HTML'
                    if mode == 'HTML':
                        message = (
                            f"📂 파일: {formatted_file}\n\n"
                            f"<b>📝 Gemini 분석 결과:</b>\n{formatted_analysis}"
                        )
                    else:
                        message = (
                            f"📂 파일: {formatted_file}\n\n"
                            f"*📝 Gemini 분석 결과:*\n{formatted_analysis}"
                        )

                    # Override to plain text message (no Markdown)
                    message = (
                        f"📂 파일: {file_name}\n\n"
                        f"📝 Gemini 분석 결과:\n{analysis}"
                    )

                    # Send to Telegram
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(application.bot.send_message(chat_id=OWNER_ID, text=message))
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
        await update.effective_message.reply_text("❌ 알 수 없는 오류가 발생했습니다.")


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def build_app() -> Application:
    """Build the Telegram application with enhanced handlers"""
    app: Application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Core handlers
    app.add_handler(CommandHandler("start", start))

    
    # Message handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
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
    # Commands are registered in build_app()


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
