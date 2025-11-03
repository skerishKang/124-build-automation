# 🔧 AI 자동화 허브 - 설정 가이드

> 10분 안에 전체 자동화 시스템 구축하기

---

## 📋 체크리스트

### ✅ 필수 설정 (5분)

- [ ] 1. `python -m pip install -r requirements.txt` 실행
- [ ] 2. `.env.example` → `.env` 복사
- [ ] 3. `.env`에 `GEMINI_API_KEY` 설정
- [ ] 4. `.env`에 `TELEGRAM_TOKEN` 설정
- [ ] 5. `.env`에 `OWNER_ID` 설정

### ✅ Google API 설정 (3분)

- [ ] 6. Google Cloud Console 프로젝트 생성
- [ ] 7. Drive/Gmail/Calendar API 활성화
- [ ] 8. 서비스 계정 생성 및 JSON 다운로드
- [ ] 9. OAuth2 클라이언트 생성 및 JSON 다운로드
- [ ] 10. Google Drive 폴더 생성 및 서비스 계정 공유
- [ ] 11. `.env`에 Drive Folder ID 설정

### ✅ 선택 설정 (2분)

- [ ] 12. **Slack** (선택): Bot Token 및 채널 ID 설정
- [ ] 13. **Notion** (선택): Integration Token 및 DB ID 설정
- [ ] 14. **n8n** (선택): Webhook URL 설정

---

## 🚀 단계별 설정

### 1️⃣ Gemini API 키 받기

1. https://makersuite.google.com/app/apikey 접속
2. **"Create API key"** 클릭
3. 키 복사
4. `.env`에 추가:
   ```env
   GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxx
   ```

### 2️⃣ Telegram Bot 생성

1. Telegram에서 @BotFather 대화 시작
2. `/newbot` 명령어 입력
3. 봇 이름 및 사용자명 설정
4. Bot Token 복사
5. `.env`에 추가:
   ```env
   TELEGRAM_TOKEN=1234567890:ABCdefGhijkLMnoPQRstUVwxyz
   ```

### 3️⃣ Telegram User ID 찾기

1. Telegram에서 @userinfobot 대화 시작
2. `/start`发送
3. ID 복사 (예: `123456789`)
4. `.env`에 추가:
   ```env
   OWNER_ID=123456789
   ```

### 4️⃣ Google Cloud 설정

#### 4-1. 프로젝트 생성
1. https://console.cloud.google.com/ 접속
2. **"Select a project"** → **"New Project"**
3. 프로젝트 이름: `AI-Automation-Hub`
4. **"Create"**

#### 4-2. API 활성화
1. **"APIs & Services" > "Library"**
2. 검색하여 각 API 활성화:
   - Google Drive API
   - Gmail API
   - Google Calendar API

#### 4-3. 서비스 계정 생성 (Drive/Calendar용)
1. **"APIs & Services" > "Credentials"**
2. **"Create Credentials" > "Service account"**
3. Name: `drive-calendar-service`
4. **"Create and Continue"**
5. **"Done"**
6. 생성된 계정 클릭 → **"Keys"** 탭
7. **"Add Key" > "Create new key"**
8. **"JSON"** 선택 → 다운로드
9. 파일명을 `service_account.json`로 변경

#### 4-4. OAuth2 클라이언트 생성 (Gmail용)
1. **"Credentials"** 페이지
2. **"Create Credentials" > "OAuth client ID"**
3. Application type: **"Desktop application"**
4. Name: `gmail-client`
5. **"Create"**
6. 다운로드 → `gmail_credentials.json`로 변경

#### 4-5. Drive 폴더 준비
1. Google Drive에서 새 폴더 생성: `AI-Automation-Folder`
2. 폴더 우클릭 → **"Share"**
3. 서비스 계정 이메일 추가 (service_account.json에서 확인 가능)
4. **"Editor"** 권한 부여
5. 폴더 URL에서 Folder ID 복사
   - 예: `https://drive.google.com/drive/folders/1A2B3C4D5E6F7G8H9I0Jabcdef`
   - Folder ID: `1A2B3C4D5E6F7G8H9I0Jabcdef`
6. `.env`에 추가:
   ```env
   GOOGLE_SERVICE_JSON_PATH=service_account.json
   DRIVE_FOLDER_ID=1A2B3C4D5E6F7G8H9I0Jabcdef
   GMAIL_CLIENT_SECRET_PATH=gmail_credentials.json
   GOOGLE_CALENDAR_ID=primary
   ```

### 5️⃣ 테스트 실행

```bash
python main_enhanced.py
```

성공 시 출력:
```
============================================================
🤖 AI 자동화 허브 시작
============================================================
✅ Gemini AI initialized
✅ Google Drive service initialized
✅ Gmail watcher started
✅ Calendar checker started
✅ Slack watcher started
✅ All modules initialized
📡 Starting Telegram bot polling...
============================================================
```

---

## 🔐 선택 연동 설정

### Slack 설정

#### Bot 생성
1. https://api.slack.com/apps 접속
2. **"Create New App"** → **"From scratch"**
3. Name: `AI Automation Hub`
4. 워크스페이스 선택

#### 권한 설정
1. **"OAuth & Permissions"** 탭
2. **"User Token Scopes"** → **"Add an OAuth Scope"**
   - `channels:history`
   - `chat:write`
   - `files:read`
3. **"Bot Token Scopes"** → **"Add an OAuth Scope"**
   - `channels:read`
   - `chat:write`

#### 앱 설치
1. **"Install to Workspace"** 클릭
2. **"Allow"** 클릭
3. **"Bot User OAuth Token"** 복사 (형식: `xoxb-...`)

#### 채널 ID 확인
1. 채널에서 우클릭 → **"Copy link"**
2. URL 형식: `https://app.slack.com/client/T12345678/C123456789`
3. 채널 ID: `C123456789`

#### .env 설정
```env
SLACK_BOT_TOKEN=xoxb-1234567890-ABCDEFGHIJKLMNOP
SLACK_CHANNEL_ID=C1234567890
```

---

### Notion 설정

#### Integration 생성
1. https://www.notion.so/my-integrations 접속
2. **"New integration"** 클릭
3. Name: `AI Automation`
4. **"Submit"**
5. **"Internal Integration Token"** 복사 (형식: `secret_...`)

#### 데이터베이스 생성
1. Notion에서 새 페이지 생성
2. **"/database"** 입력 → **"Database - Table"** 선택
3. Property 추가:
   - **Title** (Title)
   - **Source** (Text)
   - **Date** (Date)
   - **Summary** (Text)

#### Integration 공유
1. 데이터베이스 우클릭 → **"Add a connection"**
2. **"AI Automation"** 선택 → **"Confirm"**

#### DB ID 확인
1. 데이터베이스 URL 형식:
   `https://notion.so/my-workspace/a1b2c3d4e5f6g7h8i9j0`
2. DB ID: `a1b2c3d4e5f6g7h8i9j0`

#### .env 설정
```env
NOTION_TOKEN=secret_abc123xyz789
NOTION_DATABASE_ID=a1b2c3d4e5f6g7h8i9j0
```

---

### n8n 설정

#### Workflow 생성
1. n8n 접속
2. **"New Workflow"**
3. **"Webhook"** 노드 추가
4. **"Webhook URL"** 복사

#### .env 설정
```env
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/ai-summary
```

---

## ✅ 최종 확인

### 1. 필수 파일들
- [ ] `service_account.json` ✓
- [ ] `gmail_credentials.json` ✓
- [ ] `.env` 파일 ✓

### 2. .env 필수 값들
- [ ] GEMINI_API_KEY ✓
- [ ] TELEGRAM_TOKEN ✓
- [ ] OWNER_ID ✓

### 3. 테스트 커맨드
```bash
# 전체 기능 실행
python main_enhanced.py

# 기본 Telegram만 실행
python main.py
```

---

## 🎉 완료!

모든 설정이 완료되었습니다. 이제:

1. **Telegram**에 `/start` 보내기
2. **Drive 폴더**에 파일 업로드
3. **Gmail**에 새 메일 수신
4. **Slack**에서 `@analyze` 메시지 보내기

모든 활동이 AI에 의해 자동 분석되어 결과가 전송됩니다! 🚀

---

## 📞 문제 발생 시

### 로그 확인
```bash
tail -f automation_hub.log
```

### 오류 유형별 해결법

| 오류 | 해결법 |
|------|--------|
| ModuleNotFoundError | `pip install -r requirements.txt` |
| FFmpeg not found | FFmpeg 설치 및 PATH 추가 |
| Gmail auth error | 브라우저에서 Gmail 권한 허용 |
| Drive access denied | 서비스 계정이 폴더에 Editor 권한으로 추가되었는지 확인 |
| Slack token invalid | Bot Token이 정확한지 확인 |
| Notion access denied | Integration이 DB에 연결되었는지 확인 |

더 자세한 문제 해결은 `README_ENHANCED.md`를 참고하세요.
