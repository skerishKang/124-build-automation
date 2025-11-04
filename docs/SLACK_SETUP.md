# 💬 Slack 연동 설정

## 1️⃣ Slack App 생성 (5분)

1. https://api.slack.com/apps 접속
2. "Create New App" → "From scratch"
3. 이름: "AI Automation Hub"

### 권한 설정
"Bot Token Scopes"에 추가:
- `channels:read`
- `chat:write`

"Install to Workspace" 클릭 → "Allow"

## 2️⃣ 채널 ID 확인
1. 채널에서 우클릭 → "Copy link"
2. URL: `https://app.slack.com/client/T123/C123456789`
3. 채널 ID: `C123456789`

## 3️⃣ .env 설정
```env
SLACK_BOT_TOKEN=xoxb-1234567890-...
SLACK_CHANNEL_ID=C1234567890
```

## 4️⃣ 실행
```bash
python run.py
```

## 사용법
Slack 채널에서 `@analyze` 또는 `요약` 입력하면 자동 분석
