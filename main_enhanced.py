--- a/main_enhanced.py
+++ b/main_enhanced.py
@@
-from modules.gemini_client import generate_text_safe
-from modules.telegram_utils import format_ai_text
+from modules.gemini_client import generate_text_safe
+from modules.telegram_utils import format_ai_text, chunk_text, strip_html_tags
@@
-        res = generate_vision_safe(
-            "이미지를 상세히 분석해주세요. 출력은 마크다운 없이 순수 텍스트로 제공하세요.",
-            parts=[{"mime_type": "image/jpeg", "data": image_data}]
-        )
-        analysis = res.get("text") if res.get("ok") else "이미지 분석에 실패했습니다." 
-        message = f"🖼️ 이미지 분석 결과:\n\n{analysis}"
-        await update.message.reply_text(message)
+        # Increase max tokens and handle finish_reason gracefully inside helper
+        res = generate_vision_safe(
+            "이미지를 상세히 분석해주세요. 핵심 내용과 세부사항을 모두 포함해서 설명해주세요.",
+            parts=[{"mime_type": "image/jpeg", "data": image_data}],
+            max_tokens=int(os.getenv("VISION_MAX_TOKENS", "4096"))
+        )
+        analysis = res.get("text") if res.get("ok") else (res.get("error") or "이미지 분석에 실패했습니다.")
+        # Send chunked if too long
+        for chunk in chunk_text(analysis):
+            await update.message.reply_text(chunk)
@@
-        elif file_ext in SUPPORTED_TEXT_EXTS:
-            text_content = extract_text_from_txt(doc_path)
-            mode = 'preview'
+        elif file_ext in SUPPORTED_TEXT_EXTS:
+            text_content = extract_text_from_txt(doc_path)
+            # Optionally strip HTML for html/htm
+            if file_ext in ('.html', '.htm'):
+                text_content = strip_html_tags(text_content)
+            # Decide summary vs preview by env
+            summary_pref = os.getenv('DOC_TEXT_SUMMARY', 'summary').lower()
+            mode = 'summary' if summary_pref in ("1","true","yes","y","summary") else 'preview'
@@
-        if mode == 'preview':
+        if mode == 'preview':
             preview_limit = int(os.getenv('DOC_PREVIEW_LIMIT', '3500'))
             content = (text_content or '')
             if not content:
                 content = "텍스트 추출 실패"
             if len(content) > preview_limit:
                 preview = content[:preview_limit]
                 message = f"📄 파일 내용 (앞부분 {preview_limit}자):\n\n{preview}\n\n… (이하 생략)"
             else:
                 message = f"📄 파일 내용:\n\n{content}"
-            await update.message.reply_text(message)
+            for chunk in chunk_text(message):
+                await update.message.reply_text(chunk)
         else:
             if text_content and "실패" not in text_content:
-                await update.message.reply_text("📄 문서가 길어 Map-Reduce 요약을 수행합니다…")
-                summary = map_reduce_summarize(text_content)
+                await update.message.reply_text("📄 문서가 길어 Map-Reduce 요약을 수행합니다…")
+                summary = map_reduce_summarize(text_content)
             else:
                 summary = text_content or "텍스트 추출 실패"
             message = f"📄 문서 분석 결과:\n\n요약:\n{summary}"
-            await update.message.reply_text(message)
+            for chunk in chunk_text(message):
+                await update.message.reply_text(chunk)
@@
-                    formatted_file, mode_file = format_ai_text(file_name)
-                    formatted_analysis, mode_ana = format_ai_text(analysis)
-                    mode = mode_file if mode_file == mode_ana else 'HTML'
-                    if mode == 'HTML':
-                        message = (
-                            f"📂 파일: {formatted_file}\n\n"
-                            f"<b>📝 Gemini 분석 결과:</b>\n{formatted_analysis}"
-                        )
-                    else:
-                        message = (
-                            f"📂 파일: {formatted_file}\n\n"
-                            f"*📝 Gemini 분석 결과:*\n{formatted_analysis}"
-                        )
-
-                    # Override to plain text message (no Markdown)
-                    message = (
-                        f"📂 파일: {file_name}\n\n"
-                        f"📝 Gemini 분석 결과:\n{analysis}"
-                    )
+                    formatted_file, mode_file = format_ai_text(file_name)
+                    formatted_analysis, mode_ana = format_ai_text(analysis)
+                    mode = mode_file if mode_file == mode_ana else 'HTML'
+                    if mode == 'HTML':
+                        message = (
+                            f"📂 파일: {formatted_file}\n\n"
+                            f"<b>📝 Gemini 분석 결과:</b>\n{formatted_analysis}"
+                        )
+                    else:
+                        message = (
+                            f"📂 파일: {formatted_file}\n\n"
+                            f"*📝 Gemini 분석 결과:*\n{formatted_analysis}"
+                        )
@@
-                    try:
-                        loop.run_until_complete(application.bot.send_message(chat_id=OWNER_ID, text=message))
+                    try:
+                        if mode == 'HTML':
+                            loop.run_until_complete(application.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode='HTML'))
+                        else:
+                            loop.run_until_complete(application.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode='MarkdownV2'))
                     finally:
                         loop.close()
