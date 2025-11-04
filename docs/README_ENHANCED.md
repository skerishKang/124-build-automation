# 🤖 AI 자동화 허브 - 완전 통합版

> **Telegram + Google Drive + Gmail + Calendar + Notion + Slack + n8n + Gemini AI**
>
> 모든 자동화 모듈을 하나의 프로그램으로 통합한 완전 자동화 시스템

---

## ✨ 전체 기능 목록

### 📱 **Telegram Bot**
- ✅ 텍스트 메시지 분석 및 요약
- ✅ 🎤 음성 메시지 → 텍스트 변환 → Gemini 분석
- ✅ 🖼️ 이미지 분석 (Gemini Vision)
- ✅ 📄 문서 처리 (PDF/DOCX/TXT) → 텍스트 추출 → 요약

### 📂 **Google Drive 자동 감시**
- ✅ 지정 폴더를 60초마다 폴링
- ✅ 새 파일 감지 → 자동 다운로드
- ✅ 파일 형식별 자동 분석 (이미지, 오디오, 문서)
- ✅ 중복 처리 방지 (processed_files.json)
- ✅ 분석 결과 → Telegram + Notion + n8n 전송

### 📧 **Gmail 자동 감시**
- ✅ 새 메일 자동 감지
- ✅ 제목, 발신자, 본문 → Gemini 분석
- ✅ 중요 메일 분류 및 요약
- ✅ 결과 → Telegram + Slack + Notion + n8n 전송

### 📅 **Google Calendar 자동 관리**
- ✅ 1시간 내 회의 자동 감지
- ✅ 10분 전 자동 리마인더
- ✅ 회의 정보 → Gemini 브리핑
- ✅ 리마인더 → Telegram + Slack 전송

### 💬 **Slack 연동**
- ✅ 채널 모니터링
- ✅ "@analyze" 트리거 감지
- ✅ 메시지 분석 후 회신
- ✅ 분석 결과 → Telegram + Notion + n8n 전송

### 📝 **Notion 자동 기록**
- ✅ 분석 결과 자동 페이지 생성
- ✅ 소스별 분류 (Gmail, Drive, Calendar, etc.)
- ✅ 메타데이터 자동 기록 (날짜, 발신자, etc.)
- ✅ 데이터베이스 구조에 맞게 저장

### 🔗 **n8n 워크플로우 연동**
- ✅ 모든 분석 결과를 JSON으로 전송
- ✅ 외부 자동화 워크플로우 트리거
- ✅ CRM, ERP 등 외부 시스템 연동

---

## 🏗️ 프로젝트 구조

```
.
├── main_enhanced.py                    # 🎯 메인 실행 파일 (모든 모듈 통합)
├── main.py                            # 📱 기본 Telegram Bot + Drive
├── requirements.txt                   # 📦 모든 의존성 목록
├── .env.example                      # 🔑 환경변수 템플릿
├── .env                              # 💼 실제 환경변수 (직접 생성)
├── README.md                          # 📖 기본 가이드
├── README_ENHANCED.md                 # 📖 이 파일
│
├── modules/                           # 📁 모듈 디렉토리
│   ├── gemini_client.py              # 🧠 중앙 Gemini 클라이언트
│   ├── gmail_watcher.py              # 📧 Gmail 감시 모듈
│   ├── calendar_checker.py           # 📅 Calendar 감시 모듈
│   ├── slack_handler.py              # 💬 Slack 연동 모듈
│   ├── notion_updater.py             # 📝 Notion 기록 모듈
│   └── n8n_connector.py              # 🔗 n8n 연동 모듈
│
└── Generated Files/
    ├── service_account.json          # 🔐 Google 서비스 계정 (다운로드)
    ├── gmail_credentials.json        # 🔐 Gmail OAuth2 (다운로드)
    ├── gmail_token.json              # 🔐 Gmail 토큰 (자동 생성)
    ├── processed_files.json          # 📊 처리된 파일 목록 (자동 생성)
    └── automation_hub.log            # 📜 통합 로그 파일 (자동 생성)
```

---

## 🚀 빠른 시작

### 1️⃣ **의존성 설치**

```bash
pip install -r requirements.txt
```

### 2️⃣ **FFmpeg 설치** (음성 파일 처리용)

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
- https://ffmpeg.org/download.html 에서 다운로드 후 설치

**macOS:**
```bash
brew install ffmpeg
```

### 3️⃣ **환경변수 설정**

```bash
# .env.example을 .env로 복사
cp .env.example .env

# .env 파일 편집
nano .env  # 또는 vim/code/etc.
```

**최소 필수 값:**
```env
GEMINI_API_KEY=your_gemini_api_key
TELEGRAM_TOKEN=your_telegram_token
OWNER_ID=your_telegram_user_id
```

### 4️⃣ **Google API 설정** (옵션)

#### 4-1. Google Cloud Console 프로젝트 생성
1. https://console.cloud.google.com/ 접속
2. 새 프로젝트 생성
3. **APIs & Services > Library** 이동
4. 다음 API 활성화:
   - Google Drive API
   - Gmail API
   - Google Calendar API

#### 4-2. 서비스 계정 생성 (Drive/Calendar용)
1. **APIs & Services > Credentials** 이동
2. **Create Credentials > Service account** 클릭
3. 이름 입력 → **Create** → **Done**
4. 생성된 서비스 계정 클릭 → **Keys** 탭
5. **Add Key > Create new key > JSON** 선택
6. 다운로드 → `service_account.json`으로Rename

#### 4-3. OAuth2 클라이언트 생성 (Gmail용)
1. **Credentials** 페이지에서 **Create Credentials > OAuth client ID**
2. Application type: **Desktop application**
3. 이름 입력 → **Create**
4. 다운로드 → `gmail_credentials.json`으로Rename

#### 4-4. Google Drive 폴더 공유
1. 감시할 폴더 생성
2. 폴더 공유 → 서비스 계정 이메일 추가 (**Editor** 권한)
3. 폴더 URL에서 Folder ID 복사
   - 예: `https://drive.google.com/drive/folders/{FOLDER_ID}`

#### 4-5. .env에 값 설정
```env
GOOGLE_SERVICE_JSON_PATH=service_account.json
DRIVE_FOLDER_ID=your_actual_folder_id
GMAIL_CLIENT_SECRET_PATH=gmail_credentials.json
GOOGLE_CALENDAR_ID=primary  # 또는 calendar ID
```

### 5️⃣ **Slack 설정** (옵션)

1. https://api.slack.com/apps 에서 앱 생성
2. **OAuth & Permissions** 에서 Bot Token Scopes 추가:
   - `channels:history`
   - `chat:write`
   - `files:read`
3. **Bot User OAuth Token** 복사
4. 워크스페이스에 앱 설치
5. 채널 ID 확인 (채널 우클릭 → Copy link → URL에서 ID 추출)
6. .env에 설정:
```env
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_CHANNEL_ID=C1234567890
```

### 6️⃣ **Notion 설정** (옵션)

1. https://www.notion.so/my-integrations 접속
2. **New integration** 클릭
3. 이름 입력 → **Submit**
4. **Internal Integration Token** 복사
5. 데이터베이스 생성 또는 기존 데이터베이스 사용
6. .env에 설정:
```env
NOTION_TOKEN=secret_your_token
NOTION_DATABASE_ID=your_database_id
```

### 7️⃣ **n8n 설정** (옵션)

1. n8n에서 **Webhook Trigger** 노드 생성
2. Webhook URL 복사
3. .env에 설정:
```env
N8N_WEBHOOK_URL=https://your-n8n.com/webhook/ai-summary
N8N_API_KEY=your_api_key  # 필요시
```

---

## 🎯 실행 방법

### 전체 기능 실행 (권장)

```bash
python main_enhanced.py
```

### 기본 Telegram Bot만 실행

```bash
python main.py
```

### 콘솔 출력 확인

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

## 📊 모듈별 자동 실행 로그

### Google Drive
```
[Drive] Found 2 new file(s)
[Drive] New file: quarterly_report.pdf
[Gemini] Analyzing file: quarterly_report.pdf
[Drive] Completed: quarterly_report.pdf
📱 Telegram message sent
```

### Gmail
```
[Gmail] Found 1 new email(s)
[Gmail] Processing email ID: 12345
[Gemini] Analyzing email: Project Update
[Telegram] Email analysis sent
[Slack] Email analysis sent
```

### Calendar
```
[Calendar] Found 1 upcoming meeting(s)
[Calendar] Meeting: Weekly Standup in 5 minutes
[Telegram] Calendar reminder sent
[Slack] Calendar reminder sent
```

### Slack
```
[Slack] Analyzing message: @analyze this report
[Gemini] Analyzing Slack message
[Telegram] Slack analysis sent
```

---

## 🔧 고급 설정

### 폴링 주기 변경

각 모듈의 `time.sleep()` 값 수정:

**gmail_watcher.py:**
```python
time.sleep(120)  # 2분 → 원하는 시간(초)
```

**drive_watcher_thread (main_enhanced.py):**
```python
time.sleep(60)  # 1분 → 원하는 시간(초)
```

**calendar_checker.py:**
```python
time.sleep(300)  # 5분 → 원하는 시간(초)
```

**slack_watcher_thread:**
```python
time.sleep(30)  # 30초 → 원하는 시간(초)
```

### Gemini 모델 변경

`main_enhanced.py`에서:
```python
model = genai.GenerativeModel('gemini-1.5-pro')  # 또는 'gemini-1.5-flash'
```

### 로그 레벨 조정

`main_enhanced.py`에서:
```python
logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR
    ...
)
```

---

## 🐛 문제 해결

### "ModuleNotFoundError"

```bash
pip install -r requirements.txt
```

### "FFmpeg not found"

FFmpeg를 PATH에 추가하거나 설치:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# https://ffmpeg.org/download.html 에서 다운로드 후 PATH 추가
```

### Gmail 인증 오류

1. `gmail_credentials.json` 확인
2. 브라우저가 자동으로 열리고 Gmail 권한 허용
3. `gmail_token.json` 생성 확인

### Google Drive 접근 오류

1. 서비스 계정이 폴더에 **Editor** 권한으로 추가되었는지 확인
2. Folder ID가 정확한지 확인
3. `service_account.json` 경로가 정확한지 확인

### Slack 연동 오류

1. Bot Token이 정확한지 확인
2. 채널 ID가 정확한지 확인
3. Bot이 채널에 추가되었는지 확인

### Notion 연동 오류

1. Integration이 데이터베이스에 접근 권한이 있는지 확인
2. 데이터베이스 ID가 정확한지 확인
3. Property names이 Notion 데이터베이스와 일치하는지 확인

---

## 📈 성능 최적화

### 1. **메모리 사용량 줄이기**

```python
# 큰 파일을 청크로 처리
for chunk in read_large_file_chunks(file_path):
    process_chunk(chunk)
```

### 2. **동시 실행 수 제한**

```python
# ThreadPoolExecutor로 제한
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(process_file, f) for f in files]
    for future in futures:
        future.result()
```

### 3. **캐싱 활용**

```python
#Redis나 메모리 캐시로 중복 API 호출 방지
from functools import lru_cache

@lru_cache(maxsize=100)
def analyze_text_cached(text_hash):
    return analyze_text(text)
```

---

## 🔐 보안 권장사항

1. **민감한 정보는 환경변수로 관리**
   - API 키를 코드에 직접 작성하지 마세요
   - `.env` 파일을 `.gitignore`에 추가

2. **서비스 계정 권한 최소화**
   - 필요한 API만 활성화
   - 서비스 계정에 최소한의 권한만 부여

3. ** secrets 관리**
   - 프로덕션에서는 AWS Secrets Manager, GCP Secret Manager 등 사용
   - Docker secrets 활용

---

## 📝 라이선스

MIT License

---

## 🤝 기여하기

버그 리포트, 기능 제안, PR 등은 언제든 환영합니다!

---

## 📞 지원

문제가 있으시면:
1. `automation_hub.log` 파일 확인
2. GitHub Issues에 문제上报
3.详细的错误信息和重现步骤 제공

---

## 🎉 완성된 자동화 허브

이제 한 번의 실행으로:

✅ **모든 채널 통합** - Telegram, Gmail, Drive, Calendar, Slack
✅ **AI 자동 분석** - Gemini가 모든 콘텐츠 분석
✅ **즉시 알림** - 결과를 즉시推送 (Telegram, Slack)
✅ **자동 기록** - Notion에 체계적으로 저장
✅ **외부 연동** - n8n으로 워크플로우 자동화

**메우 진화된 AI 자동화 시스템이 완성되었습니다!** 🚀
