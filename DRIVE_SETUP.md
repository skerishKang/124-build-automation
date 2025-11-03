# 📂 Google Drive 연동 설정 가이드

## 1️⃣ Google Cloud Console 설정 (15분)

### Step 1: 프로젝트 생성
1. https://console.cloud.google.com/ 접속
2. "새 프로젝트" 클릭
3. 이름: "AI-Automation-Hub"

### Step 2: API 활성화
"APIs & Services" → "Library" → 검색:
- ✅ Google Drive API
- ✅ Google Gmail API (선택)
- ✅ Google Calendar API (선택)

### Step 3: 서비스 계정 생성
1. "APIs & Services" → "Credentials"
2. "Create Credentials" → "Service account"
3. 이름: "drive-service"
4. "Create and Continue"
5. "Done"

### Step 4: 키 생성
1. 서비스 계정 클릭 → "Keys" 탭
2. "Add Key" → "Create new key"
3. "JSON" 선택 → 다운로드
4. 파일명을 `service_account.json`으로 변경

### Step 5: 폴더 공유
1. Google Drive에서 새 폴더 생성
2. 우클릭 → "Share"
3. 서비스 계정 이메일 추가
4. "Editor" 권한 부여
5. 폴더 URL에서 ID 복사: `https://drive.google.com/drive/folders/여기가_ID`

## 2️⃣ 코드 연동 (15분)

main_enhanced.py의 _fetch_list()와 _handle_file() 구현 필요:

```python
def _fetch_list():
    # TODO: Google Drive API 연동
    return []
```

```python
def _handle_file(f):
    # TODO: 파일 다운로드 → 요약 → 알림/저장
    pass
```

## 3️⃣ .env 설정
```env
DRIVE_FOLDER_ID=실제_FOLDER_ID
GOOGLE_SERVICE_JSON_PATH=service_account.json
```

## 4️⃣ 실행
```bash
python run.py
```
