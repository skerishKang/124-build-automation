# 🎯 Google Drive 연동 구현 가이드

## 현재 상태
- ✅ Drive 폴링 스레드: 60초 간격
- ✅ poll_drive_once() 유틸: 준비 완료
- ⏳ _fetch_list(): TODO - 실제 Drive API 연동
- ⏳ _handle_file(): TODO - 다운로드+요약 로직

## 구현할 코드 (main_enhanced.py)

### 1. _fetch_list() 구현
```python
def _fetch_list():
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    
    credentials = Credentials.from_service_account_file(
        GOOGLE_SERVICE_JSON_PATH,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    service = build('drive', 'v3', credentials=credentials)
    
    results = service.files().list(
        pageSize=50,
        q=f"'{DRIVE_FOLDER_ID}' in parents",
        fields="nextPageToken, files(id, name, mimeType, modifiedTime)"
    ).execute()
    
    items = results.get('files', [])
    return items
```

### 2. _handle_file() 구현
```python
def _handle_file(f):
    from modules.gemini_client import get_gemini_client
    
    file_id = f['id']
    file_name = f['name']
    mime_type = f['mimeType']
    
    # TODO: 파일 다운로드
    # TODO: 파일 타입별 처리 (PDF, 이미지, 텍스트 등)
    # TODO: Gemini로 요약
    # TODO: Telegram/Slack로 전송
    logger.info(f"Processing file: {file_name}")
```

## 필요한 설정
1. `service_account.json` - Google Cloud Console에서 다운로드
2. `.env`에 `DRIVE_FOLDER_ID=실제_ID`
3. Drive 폴더를 서비스 계정에 공유

## 테스트 방법
```bash
# Drive 폴더에 파일 업로드
# 60초 후 로그 확인: "Processing file: xxx"
# Telegram으로 결과 수신
```
