# 🤖 Telegram Bot with Gemini AI + Google Drive Integration

텔레그램 메시지, 음성, 이미지, 문서를 Gemini AI로 분석하고, **Google Drive 폴더를 자동으로 감시하여 새 파일을 분석**하는 봇입니다.

## ✨ 주요 기능

### 📱 Telegram Bot 기능
- **텍스트 메시지** → Gemini로 분석 및 요약
- **🎤 음성 메시지** → STT 변환 → Gemini 요약
- **🖼️ 이미지** → Gemini Vision으로 상세 분석
- **📄 문서** (PDF/DOCX/TXT) → 텍스트 추출 → Gemini 요약

### 📂 Google Drive 자동 감시 기능
- 지정된 Google Drive 폴더를 **60초마다 폴링**
- 새 파일 감지 시 **자동 다운로드** 및 분석
- **중복 처리 방지** (processed_files.json로 추적)
- 분석 결과를 **즉시 Telegram으로 전송**

## 🚀 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. FFmpeg 설치 (음성 파일 처리용)

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

### 3. 환경변수 설정

`.env.example` 파일을 `.env`로 복사하고 값을 수정:

```bash
cp .env.example .env
```

`.env` 파일 내용:
```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
OWNER_ID=your_telegram_user_id_here
GOOGLE_SERVICE_JSON_PATH=service_account.json
DRIVE_FOLDER_ID=your_google_drive_folder_id_here
```

### 4. Google Drive API 설정

#### 4-1. Google Cloud Console에서 서비스 계정 생성

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. **"APIs & Services" > "Library"** 이동
4. **"Google Drive API"** 검색 후 **"ENABLE"**
5. **"APIs & Services" > "Credentials"** 이동
6. **"Create Credentials" > "Service account"** 클릭
7. 서비스 계정 이름 입력 후 **"Create"**
8. **"Skip (optional)"** 선택 → **"Done"**
9. 생성된 서비스 계정 클릭 → **"Keys"** 탭 → **"Add Key" > "Create new key"**
10. **JSON** 선택 → 다운로드 (service_account.json)

#### 4-2. 서비스 계정 JSON 파일 배치

다운로드한 JSON 파일을 프로젝트 루트에 `service_account.json`으로 저장

#### 4-3. Google Drive 폴더 공유

1. Google Drive에서 감시할 폴더 생성
2. 폴더를 **공유** → 서비스 계정 이메일 추가
3. **"Editor"** 권한 부여
4. 폴더 URL에서 folder ID 복사
   - 예: `https://drive.google.com/drive/folders/{FOLDER_ID}`
   - `{FOLDER_ID}` 부분이 실제 Folder ID

#### 4-4. .env에 값 설정

```env
GOOGLE_SERVICE_JSON_PATH=service_account.json
DRIVE_FOLDER_ID=1A2B3C4D5E6F7G8H9I0J  # 실제 folder ID
```

## 📖 실행 방법

### Bot만 실행 (Telegram 전용)

```bash
python main.py
```

Drive 감시를 비활성화하려면:
- `.env`에서 `DRIVE_FOLDER_ID`를 비워두거나 삭제

### 전체 기능 실행 (Telegram + Drive)

```bash
python main.py
```

실행 시 콘솔 출력:
```
🤖 Telegram Bot started...
📡 Bot is polling for messages...
🔍 Google Drive watcher thread started
```

## 🎯 사용법

### Telegram에서

1. 봇에게 `/start` 명령어 전송
2. 파일 전송 (텍스트/음성/이미지/문서)
3. AI 분석 결과 수신

### Google Drive에서

1. 설정된 폴더에 파일 업로드
2. 1분 내 분석 완료
3. Telegram으로 결과 수신

**지원 파일 형식:**
- 📄 PDF, DOCX, TXT
- 🖼️ JPG, PNG, GIF
- 🎤 MP3, WAV, OGG

## 🔧 주요 파일 구조

```
.
├── main.py                    # 메인 봇 프로그램
├── requirements.txt           # 의존성 목록
├── .env.example              # 환경변수 예시
├── .env                      # 실제 환경변수 (미리 만들기)
├── service_account.json      # Google 서비스 계정 JSON (다운로드 필요)
├── processed_files.json      # 처리된 파일 목록 (자동 생성)
└── README.md                 # 이 파일
```

## 📝 로그 및 모니터링

실시간 콘솔 로그:
- `[Drive Watcher] New file detected: {filename}` - 새 파일 감지
- `[Gemini] Analyzing file: {filename}` - AI 분석 시작
- `[Telegram] Message sent for: {filename}` - 결과 전송 완료

## ⚙️ 설정 옵션

### 폴링 주기 변경

`main.py`의 `drive_watcher_thread()` 함수에서:
```python
time.sleep(60)  # 60초 → 원하는 초수로 변경
```

### 파일 크기 제한

Gemini API 토큰 제한으로 대용량 파일은 자동으로 제한됩니다.

## 🐛 문제 해결

### "Google Drive libraries not installed" 경고

```bash
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
```

### "FFmpeg not found" 오류

FFmpeg를 설치하거나 PATH에 추가하세요.

### Drive 폴더 접근 오류

1. 서비스 계정이 폴더에 **Editor** 권한으로 추가되었는지 확인
2. Folder ID가 정확한지 확인
3. `service_account.json`이 올바른 위치에 있는지 확인

## 📄 라이선스

MIT License

## 🙏 기여

개선 제안이나 버그 리포트는 언제든 환영합니다!
