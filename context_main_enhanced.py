--- a/main_enhanced.py
+++ b/main_enhanced.py
@@
-from modules.telegram_utils import format_ai_text, chunk_text, strip_html_tags
+from modules.telegram_utils import format_ai_text, chunk_text, strip_html_tags
+from modules.context_manager import ContextManager, build_prompt_with_context
@@
 logger = logging.getLogger(__name__)
@@
+# Conversation context manager (Supabase-backed)
+ctx_mgr = ContextManager()
+
@@
 async def handle_text(update, context):
     chat_id = update.effective_chat.id
     text = (update.message.text or "").strip()
 
     if not text:
         formatted_message, parse_mode = format_ai_text("내용이 비어 있어요. 텍스트를 보내주세요.")
         await context.bot.send_message(chat_id, formatted_message, parse_mode=parse_mode)
         return
 
-    # Use Gemini to handle all text inputs, letting it determine the intent
-    prompt = f"사용자의 요청: {text}\n\n이 요청에 대해 자연스럽게 대화하거나, 필요한 경우 분석/요약하여 응답해주세요."
+    # Save user message
+    try:
+        user_id = update.effective_user.id
+    except Exception:
+        user_id = None
+    ctx_mgr.add(chat_id, user_id, "user", text, "text")
+
+    # Build prompt with recent context
+    prompt = build_prompt_with_context(ctx_mgr, chat_id, text)
     res = generate_text_safe(prompt)
     
     if res.get("ok"):
-        formatted_message, parse_mode = format_ai_text(res["text"])
+        answer = res["text"]
+        # Save assistant answer and maybe compress
+        ctx_mgr.add(chat_id, user_id, "assistant", answer, "text")
+        ctx_mgr.compress_if_needed(chat_id)
+        formatted_message, parse_mode = format_ai_text(answer)
         await context.bot.send_message(chat_id, formatted_message, parse_mode=parse_mode)
     else:
         formatted_message, parse_mode = format_ai_text("요청 처리 중 문제가 발생했습니다. 표현을 조금 바꿔 다시 시도해 주세요.")
         await context.bot.send_message(chat_id, formatted_message, parse_mode=parse_mode)
@@
 async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
@@
-        # Transcribe
+        # Transcribe
         transcription = transcribe_audio(wav_path)
         if transcription == "음성 전사에 실패했습니다.":
             formatted_message, parse_mode = format_ai_text(transcription)
             await update.message.reply_text(formatted_message, parse_mode=parse_mode)
             os.unlink(ogg_path)
             os.unlink(wav_path)
             return
 
-        # Analyze with Gemini
-        res = generate_text_safe(f"음성 내용을 분석하고 요약해주세요. 출력은 마크다운 없이 순수 텍스트로 답변하세요.\n\n{transcription}")
+        # Store user voice transcript
+        try:
+            user_id = update.effective_user.id
+        except Exception:
+            user_id = None
+        ctx_mgr.add(chat_id, user_id, "user", f"[음성 전사]\n{transcription}", "voice")
+
+        # Analyze with Gemini with context
+        prompt = build_prompt_with_context(ctx_mgr, chat_id, f"음성 내용을 분석하고 요약:\n{transcription}")
+        res = generate_text_safe(prompt)
         summary = res.get("text") if res.get("ok") else "음성 분석 및 요약에 실패했습니다." 
 
         message = (
             "🎤 음성 분석 결과:\n\n"
             f"전사:\n{transcription}\n\n"
             f"요약:\n{summary}"
         )
         await update.message.reply_text(message)
+
+        # Save assistant answer
+        ctx_mgr.add(chat_id, user_id, "assistant", summary, "voice")
+        ctx_mgr.compress_if_needed(chat_id)
@@
 async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
@@
-        analysis = res.get("text") if res.get("ok") else (res.get("error") or "이미지 분석에 실패했습니다.")
+        analysis = res.get("text") if res.get("ok") else (res.get("error") or "이미지 분석에 실패했습니다.")
         # Send chunked if too long
         for chunk in chunk_text(analysis):
             await update.message.reply_text(chunk)
+
+        # Add to context as assistant message for future reference
+        try:
+            user_id = update.effective_user.id
+        except Exception:
+            user_id = None
+        ctx_mgr.add(chat_id, user_id, "assistant", f"[이미지 분석]\n{analysis}", "image")
+        ctx_mgr.compress_if_needed(chat_id)
