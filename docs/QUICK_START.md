# 🚀 Quick Start Guide

## ⚡ 5분 설정법

### STEP 1: 필수 API 키 설정
```bash
cp .env.example .env
```

`.env` 파일에서 다음만 설정하면 **즉시 시작 가능**:
- `TELEGRAM_BOT_TOKEN` - BotFather에서 만든 봇 토큰
- `GEMINI_API_KEY` - Google AI Studio에서 받은 키

### STEP 2: 실행
```bash
# Windows
runner.bat

# 또는
python run.py
```

### STEP 3: Telegram 테스트
봇에게 `/start` 메시지 보내기

---

## 📋 다음 단계 (Drive 연동 시)

### 1. Google Drive 연동
```bash
# 1. Google Cloud Console에서 서비스 계정 생성
# 2. JSON 파일을 service_account.json으로 저장
# 3. .env에 설정
DRIVE_FOLDER_ID=실제_폴더_ID
```

### 2. Slack 연동
```bash
# .env에 추가
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ID=C...
```

### 3. n8n 연동
```bash
# .env에 추가
N8N_BASE_URL=https://your-n8n.cloud.app.n8n.cloud
N8N_WEBHOOK_PATH=/webhook/xxx/webhook
```

---

## 🎮 바로 시도해보기

```bash
# 1. 봇만 실행 (Drive/Gmail 제외하고)
python run.py

# 2. Drive 활성화
DRIVE_FOLDER_ID=your-folder-id python run.py

# 3. Webhook 모드
BOT_MODE=webhook python run.py
```
