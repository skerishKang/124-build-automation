--- a/SETUP_GUIDE.md
+++ b/SETUP_GUIDE.md
@@
 ## 환경변수(.env)
 
+### 대화 메모리 (Supabase)
+
+```
+CONTEXT_ENABLED=true
+CONTEXT_STORAGE=supabase
+CONTEXT_MAX_MESSAGES=12
+CONTEXT_COMPRESS_THRESHOLD=12000
+
+SUPABASE_URL=your_supabase_url
+SUPABASE_ANON_KEY=your_anon_or_service_key
+# 서버 환경에서는 SERVICE_ROLE_KEY 사용 권장 (노출 주의)
+# SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
+
+# (선택) 테이블명 커스터마이즈
+CONTEXT_TABLE=conversations
+```
+
+### SQL (Supabase)
+
+```
+CREATE TABLE IF NOT EXISTS conversations (
+  id BIGSERIAL PRIMARY KEY,
+  chat_id TEXT NOT NULL,
+  user_id TEXT,
+  role TEXT NOT NULL,              -- 'user' | 'assistant' | 'system'
+  message_type TEXT DEFAULT 'text',-- 'text' | 'voice' | 'image' | 'document'
+  content TEXT NOT NULL,
+  meta JSONB,
+  created_at TIMESTAMPTZ DEFAULT NOW()
+);
+
+CREATE INDEX IF NOT EXISTS idx_conversations_chat_created
+  ON conversations (chat_id, created_at DESC);
+```
+
+### 의존성
+
+```
+pip install -r requirements.txt
+```
+