# 🚀 지금 바로 실행 테스트

## 즉시 실행 가능 (모든 API 키 준비됨!)
```bash
python run.py
```

## 테스트할 수 있는 기능들
1. **Telegram Bot** ✅
   - `/start` 명령어
   - 텍스트 메시지 → AI 분석
   - 이미지 → Gemini Vision 분석
   - 음성 메시지 → STT + 요약
   - PDF/DOCX → 텍스트 추출 + 요약

2. **Slack 연동** ✅
   - 채널에 "@analyze 메시지" 입력
   - 자동 AI 분석 결과 응답

3. **운영 안정성** ✅
   - 중복 실행 방지
   - 로그 로테이션 (5MB)
   - 60초 Drive 폴링 (폴더 ID 설정 시)

## 사용법 예시
```
Telegram에서:
"안녕하세요" → Gemini AI가 분석해서 요약해줌
"팀 회의 자료 요약해줘" → 음성 파일을 텍스트로 변환 후 요약
이미지 전송 → "이 이미지에서 중요한 정보를 요약해주세요"
```

## 확인 방법
```bash
# 로그 모니터링
tail -f automation_hub.log

# 프로세스 상태
ps aux | grep run.py
```
