#!/usr/bin/env python3
"""
Check if the bot is working
"""

import os
import requests

# Get token from .env
with open('.env', 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('TELEGRAM_TOKEN='):
            token = line.split('=')[1].strip()
            break

# Test bot
try:
    response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
    data = response.json()

    if data['ok']:
        bot_info = data['result']
        print("=" * 50)
        print("Bot is working!")
        print("=" * 50)
        print(f"Name: {bot_info['first_name']}")
        print(f"Username: @{bot_info['username']}")
        print(f"ID: {bot_info['id']}")
        print("=" * 50)
        print()
        print(f"Telegram Link: https://t.me/{bot_info['username']}")
        print()
        print("Copy the link above and open in browser!")
    else:
        print(f"Bot error: {data.get('description', 'Unknown')}")

except Exception as e:
    print(f"Connection error: {e}")
