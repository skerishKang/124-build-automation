#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot with Gemini AI Integration
Receives text, voice, images, and documents, analyzes them with Gemini AI, and sends summaries back.
"""

import os
import logging
import tempfile
import subprocess
import threading
import time
import json
import asyncio
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import google.generativeai as genai
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables (loaded from .env file or environment)
# WARNING: Never commit hardcoded API keys to version control
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OWNER_ID = os.getenv("OWNER_ID")

# Google Drive settings
GOOGLE_SERVICE_JSON_PATH = os.getenv("GOOGLE_SERVICE_JSON_PATH", "service_account.json")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "")

# Processed files tracking
PROCESSED_FILES_DB = "processed_files.json"

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')


def convert_voice_to_wav(input_path: str, output_path: str) -> bool:
    """
    Convert voice file (ogg/mp3) to wav format using ffmpeg
    """
    try:
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            output_path,
            '-y'
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        logger.error(f"Error converting voice to wav: {e}")
        return False


def transcribe_audio(wav_path: str) -> str:
    """
    Transcribe audio file to text using Gemini
    """
    try:
        with open(wav_path, 'rb') as audio_file:
            audio_data = audio_file.read()

        # Send audio to Gemini for transcription
        response = model.generate_content([
            "Transcribe this audio to text. Provide only the text without any explanations.",
            {"mime_type": "audio/wav", "data": audio_data}
        ])

        return response.text.strip()
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return "음성 转文字에 실패했습니다."


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF file
    """
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return "PDF 텍스트 추출에 실패했습니다."


def extract_text_from_docx(docx_path: str) -> str:
    """
    Extract text from DOCX file
    """
    try:
        from docx import Document
        doc = Document(docx_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}")
        return "DOCX 텍스트 추출에 실패했습니다."


def extract_text_from_txt(txt_path: str) -> str:
    """
    Extract text from TXT file
    """
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error reading TXT file: {e}")
        return "TXT 파일 읽기에 실패했습니다."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command
    """
    welcome_message = """
🤖 안녕하세요! Gemini AI 통합 텔레그램 봇입니다!

📨 다음 유형의 파일을 전송해보세요:
• 텍스트 메시지 - 직접 분석 및 요약
• 🎤 음성 메시지 - 텍스트 변환 후 요약
• 🖼️ 이미지 - Gemini Vision으로 분석
• 📄 문서 (PDF/DOCX/TXT) - 텍스트 추출 후 요약

AI가 전송해드린 내용을 분석하여 요약해드립니다! 🚀
"""
    await update.message.reply_text(welcome_message)
    logger.info(f"New user started bot: {update.effective_user.id}")


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle text messages
    """
    user_text = update.message.text
    user_id = update.effective_user.id

    logger.info(f"Received text message from user {user_id}")

    try:
        # Send to Gemini for analysis
        response = model.generate_content(f"다음 텍스트를 분석하고 핵심 내용을 요약해주세요:\n\n{user_text}")
        summary = response.text

        await update.message.reply_text(f"📝 **요약 결과:**\n\n{summary}")
        logger.info(f"Sent summary to user {user_id}")

    except Exception as e:
        logger.error(f"Error processing text message: {e}")
        await update.message.reply_text("❌ 텍스트 분석 중 오류가 발생했습니다.")


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle voice messages
    """
    user_id = update.effective_user.id
    voice = update.message.voice

    logger.info(f"Received voice message from user {user_id}")

    try:
        # Download voice file
        file = await context.bot.get_file(voice.file_id)
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as ogg_file:
            await file.download_to_drive(ogg_file.name)
            ogg_path = ogg_file.name

        # Convert to wav
        wav_path = ogg_path.replace('.ogg', '.wav')
        if not convert_voice_to_wav(ogg_path, wav_path):
            await update.message.reply_text("❌ 음성 파일 변환에 실패했습니다.")
            return

        # Transcribe audio
        transcription = transcribe_audio(wav_path)

        if transcription == "음성 转文字에 실패했습니다.":
            await update.message.reply_text(transcription)
            return

        # Analyze transcription with Gemini
        response = model.generate_content(f"다음 음성 내용을 분석하고 핵심 요약을 제공해주세요:\n\n{transcription}")
        summary = response.text

        await update.message.reply_text(f"🎤 **음성 분석 결과:**\n\n**📄 변환된 텍스트:**\n{transcription}\n\n**📝 요약:**\n{summary}")

        # Clean up temp files
        os.unlink(ogg_path)
        os.unlink(wav_path)

        logger.info(f"Sent voice analysis to user {user_id}")

    except Exception as e:
        logger.error(f"Error processing voice message: {e}")
        await update.message.reply_text("❌ 음성 메시지 처리 중 오류가 발생했습니다.")


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle image messages
    """
    user_id = update.effective_user.id
    photo = update.message.photo[-1]  # Get highest resolution

    logger.info(f"Received image from user {user_id}")

    try:
        # Download image file
        file = await context.bot.get_file(photo.file_id)
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as img_file:
            await file.download_to_drive(img_file.name)
            img_path = img_file.name

        # Send to Gemini Vision
        with open(img_path, 'rb') as image_file:
            image_data = image_file.read()

        response = model.generate_content([
            "이미지를 분석하고 자세히 설명해주세요. 주요 내용, 텍스트, 객체를 포함하여 설명해주세요.",
            {"mime_type": "image/jpeg", "data": image_data}
        ])

        analysis = response.text

        await update.message.reply_text(f"🖼️ **이미지 분석 결과:**\n\n{analysis}")

        # Clean up temp file
        os.unlink(img_path)

        logger.info(f"Sent image analysis to user {user_id}")

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text("❌ 이미지 분석 중 오류가 발생했습니다.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle document messages (PDF, DOCX, TXT)
    """
    user_id = update.effective_user.id
    document = update.message.document

    logger.info(f"Received document from user {user_id}: {document.file_name}")

    try:
        # Download document
        file = await context.bot.get_file(document.file_id)
        file_extension = os.path.splitext(document.file_name)[1].lower()
        temp_file = tempfile.NamedTemporaryFile(suffix=file_extension, delete=False)
        await file.download_to_drive(temp_file.name)
        doc_path = temp_file.name

        # Extract text based on file type
        text_content = ""

        if file_extension == '.pdf':
            text_content = extract_text_from_pdf(doc_path)
        elif file_extension == '.docx':
            text_content = extract_text_from_docx(doc_path)
        elif file_extension == '.txt':
            text_content = extract_text_from_txt(doc_path)
        else:
            await update.message.reply_text("❌ 지원하지 않는 문서 형식입니다. PDF, DOCX, TXT 파일만 지원됩니다.")
            os.unlink(doc_path)
            return

        # Analyze text with Gemini
        response = model.generate_content(
            f"다음 문서 내용을 분석하고 핵심 내용을 요약해주세요:\n\n{text_content[:8000]}"  # Limit to avoid token limits
        )
        summary = response.text

        await update.message.reply_text(f"📄 **문서 분석 결과:**\n\n**📝 요약:**\n{summary}")

        # Clean up temp file
        os.unlink(doc_path)

        logger.info(f"Sent document analysis to user {user_id}")

    except Exception as e:
        logger.error(f"Error processing document: {e}")
        await update.message.reply_text("❌ 문서 분석 중 오류가 발생했습니다.")


# Google Drive utilities
def load_processed_files():
    """Load list of already processed files"""
    try:
        if os.path.exists(PROCESSED_FILES_DB):
            with open(PROCESSED_FILES_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading processed files: {e}")
        return []


def save_processed_files(processed_list):
    """Save list of processed files"""
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
        logger.info("Google Drive service initialized successfully")
        return service
    except Exception as e:
        logger.error(f"Error initializing Google Drive service: {e}")
        return None


def get_new_files_from_drive(service, processed_files):
    """Get new files from Google Drive folder"""
    try:
        results = service.files().list(
            q=f"'{DRIVE_FOLDER_ID}' in parents and trashed=false",
            pageSize=100,
            fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime)"
        ).execute()

        items = results.get('files', [])
        new_files = []

        for item in items:
            file_id = item['id']
            if file_id not in processed_files:
                new_files.append(item)

        return new_files
    except Exception as e:
        logger.error(f"Error getting files from Drive: {e}")
        return []


def download_file_from_drive(service, file_id, file_name):
    """Download file from Google Drive"""
    try:
        request = service.files().get_media(fileId=file_id)
        file_path = os.path.join(tempfile.gettempdir(), file_name)

        with open(file_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()

        logger.info(f"Downloaded file: {file_name}")
        return file_path
    except Exception as e:
        logger.error(f"Error downloading file {file_name}: {e}")
        return None


async def send_telegram_message(bot, text):
    """Send message to owner"""
    try:
        if OWNER_ID:
            await bot.send_message(chat_id=OWNER_ID, text=text)
            logger.info(f"Sent message to owner {OWNER_ID}")
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")


def analyze_drive_file_with_gemini(file_path, mime_type):
    """Analyze file from Drive with Gemini"""
    try:
        file_extension = os.path.splitext(file_path)[1].lower()

        # Handle different file types
        if mime_type == 'application/pdf' or file_extension == '.pdf':
            text_content = extract_text_from_pdf(file_path)
            prompt = "다음 문서 내용을 분석하고 핵심 내용을 요약해주세요:\n\n"
        elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or file_extension == '.docx':
            text_content = extract_text_from_docx(file_path)
            prompt = "다음 문서 내용을 분석하고 핵심 내용을 요약해주세요:\n\n"
        elif mime_type == 'text/plain' or file_extension == '.txt':
            text_content = extract_text_from_txt(file_path)
            prompt = "다음 문서 내용을 분석하고 핵심 내용을 요약해주세요:\n\n"
        elif mime_type.startswith('image/'):
            # Image analysis
            with open(file_path, 'rb') as image_file:
                image_data = image_file.read()
            response = model.generate_content([
                "이미지를 분석하고 자세히 설명해주세요. 주요 내용, 텍스트, 객체를 포함하여 설명해주세요.",
                {"mime_type": mime_type, "data": image_data}
            ])
            return response.text.strip()
        elif mime_type.startswith('audio/'):
            # Audio transcription and analysis
            wav_path = file_path.replace(file_extension, '.wav')
            if not convert_voice_to_wav(file_path, wav_path):
                return "음성 파일 변환에 실패했습니다."
            transcription = transcribe_audio(wav_path)
            os.unlink(wav_path)
            response = model.generate_content(f"다음 음성 내용을 분석하고 핵심 요약을 제공해주세요:\n\n{transcription}")
            return f"**음성 변환:**\n{transcription}\n\n**요약:**\n{response.text}"
        else:
            return "지원하지 않는 파일 형식입니다."

        # Text-based analysis
        if text_content and not text_content.endswith("실패했습니다."):
            response = model.generate_content(prompt + text_content[:8000])
            return response.text.strip()
        else:
            return text_content

    except Exception as e:
        logger.error(f"Error analyzing file with Gemini: {e}")
        return "파일 분석 중 오류가 발생했습니다."


def drive_watcher_thread(application):
    """Background thread to monitor Google Drive folder"""
    logger.info("🔍 Google Drive watcher thread started")

    # Initialize Drive service
    service = initialize_drive_service()
    if not service:
        logger.error("Failed to initialize Drive service. Exiting watcher thread.")
        return

    # Load already processed files
    processed_files = load_processed_files()

    while True:
        try:
            # Get new files
            new_files = get_new_files_from_drive(service, processed_files)

            if new_files:
                logger.info(f"[Drive Watcher] Found {len(new_files)} new file(s)")

                # Process each new file
                for file_info in new_files:
                    file_id = file_info['id']
                    file_name = file_info['name']
                    mime_type = file_info['mimeType']

                    logger.info(f"[Drive Watcher] New file detected: {file_name}")

                    # Download file
                    file_path = download_file_from_drive(service, file_id, file_name)
                    if not file_path:
                        continue

                    # Analyze with Gemini
                    logger.info(f"[Gemini] Analyzing file: {file_name}")
                    analysis = analyze_drive_file_with_gemini(file_path, mime_type)

                    # Format message for Telegram
                    message = f"📂 [{file_name}]\n\nGemini 분석 결과:\n{analysis}"

                    # Send to Telegram using asyncio
                    asyncio.run(send_telegram_message(application.bot, message))
                    logger.info(f"[Telegram] Message sent for: {file_name}")

                    # Clean up temp file
                    os.unlink(file_path)

                    # Mark as processed
                    processed_files.append(file_id)
                    save_processed_files(processed_files)

                    logger.info(f"[Drive Watcher] Completed processing: {file_name}")

            # Wait before next check (60 seconds)
            time.sleep(60)

        except Exception as e:
            logger.error(f"Error in drive watcher thread: {e}")
            time.sleep(60)  # Wait before retrying


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle errors
    """
    logger.warning(f'Update "{update}" caused error "{context.error}"')
    if update and update.effective_message:
        update.effective_message.reply_text("❌ 알 수 없는 오류가 발생했습니다.")


def main():
    """
    Main function to start the bot
    """
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Add error handler
    application.add_error_handler(error_handler)

    # Start Google Drive watcher thread
    if DRIVE_FOLDER_ID:
        drive_thread = threading.Thread(target=drive_watcher_thread, args=(application,), daemon=True)
        drive_thread.start()
        logger.info("🔍 Google Drive watcher thread started")
    else:
        logger.info("⚠️ DRIVE_FOLDER_ID not set. Google Drive monitoring disabled.")

    # Start polling
    logger.info("🤖 Telegram Bot started...")
    logger.info("📡 Bot is polling for messages...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()