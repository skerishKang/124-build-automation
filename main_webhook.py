#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot with Webhook (Single Instance)
Avoids conflicts with other bot instances
"""

import os
import logging
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8288922587:AAHUADrjbeLFSTxS_Hx6jEDEbAW88dOzgNY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAP8A5YjpwqOkHo0YLhXUMdzFubYoWSwMk")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

# Flask app
app = Flask(__name__)

# Telegram application
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Add handlers (simplified version)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("AI 자동화 허브 시작! (Webhook 모드)")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        response = model.generate_content(f"요약해주세요:\n\n{user_text}")
        await update.message.reply_text(f"📝 요약:\n\n{response.text}")
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ 오류 발생")

# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming Telegram updates"""
    try:
        update = Update.de_json(request.get_json(), application.bot)
        application.process_update(update)
        return jsonify({'status': 'ok'})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    logger.info("Starting webhook server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)
