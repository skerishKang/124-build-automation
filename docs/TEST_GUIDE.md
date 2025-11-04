# 🧪 테스트 가이드

## 1️⃣ 기본 기능 테스트

### Telegram Bot
```bash
python run.py
```

1. Telegram에서 봇에게 `/start` 전송
2. 텍스트 메시지 → AI 분석 결과 수신
3. 이미지 전송 → Gemini Vision 분석
4. 음성 메시지 → 텍스트 변환 + 요약

### Drive 모니터링
```bash
# Drive 폴더 ID 설정 후
DRIVE_FOLDER_ID=your_folder_id python run.py
```

1. Drive 폴더에 파일 업로드
2. 60초 후 자동 분석 시작
3. Telegram으로 결과 전송

### Slack 연동
```bash
# Slack 설정 후
python run.py
```

1. Slack 채널에 "@analyze 메시지" 입력
2. AI가 메시지 분석 후 응답

## 2️⃣ 운영 안정성 테스트

### 중복 실행 방지
```bash
# 터미널 1
python run.py

# 터미널 2 (即 종료됨)
python run.py
```

### 로그 로테이션
```bash
# 크기 모니터링
tail -f automation_hub.log

# 5MB 초과 시 자동 압축 확인
ls -lh automation_hub.log*
```

## 3️⃣ 오류 시 확인사항

### 로그 확인
```bash
tail -f automation_hub.log | grep -i error
```

### 프로세스 상태 확인
```bash
ps aux | grep python
```

### 락 파일 제거 (강제 종료 시)
```bash
rm -f automation_hub.lock
```
