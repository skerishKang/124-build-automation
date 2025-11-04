--- a/modules/gemini_client.py
+++ b/modules/gemini_client.py
@@
-def generate_vision_safe(prompt: str, parts: list, *, temperature: float = 0.2, max_tokens: int = 2048) -> Dict[str, Any]:
+def generate_vision_safe(prompt: str, parts: list, *, temperature: float = 0.2, max_tokens: int = 2048) -> Dict[str, Any]:
@@
-    order = ["gemini-2.5-flash", "gemini-1.5-pro", "gemini-pro-vision"] # gemini-2.5-flash-latest, gemini-1.5-pro-latest
+    order = ["gemini-2.5-flash", "gemini-1.5-pro", "gemini-pro-vision"]  # try multiple capable models
@@
-            resp = model.generate_content(
-                contents,
-                generation_config={"temperature": temperature, "max_output_tokens": max_tokens},
-            )
+            resp = model.generate_content(
+                contents,
+                generation_config={"temperature": temperature, "max_output_tokens": max_tokens},
+            )
             blocked, reason = _is_blocked(resp)
             if blocked:
-                return {"ok": False, "blocked": True, "reason": reason, "text": ""}
-            text = ""
-            try:
-                text = getattr(resp, "text", None) or resp.candidates[0].content.parts[0].text
-            except Exception:
-                text = str(resp)
-            return {"ok": True, "blocked": False, "reason": "", "text": text}
+                return {"ok": False, "blocked": True, "reason": reason, "text": ""}
+
+            # Gracefully handle missing text (finish_reason != SUCCESS)
+            text = getattr(resp, "text", None)
+            if not text:
+                try:
+                    cand0 = resp.candidates[0]
+                    fr = getattr(cand0, "finish_reason", None)
+                    return {"ok": False, "blocked": False, "reason": f"Vision 응답이 중단되었습니다 (finish_reason={fr}). 이미지 크기 축소/크롭 또는 민감요소 제거 후 다시 시도하세요.", "text": ""}
+                except Exception:
+                    return {"ok": False, "blocked": False, "reason": "Vision 응답에 텍스트가 없습니다.", "text": ""}
+            return {"ok": True, "blocked": False, "reason": "", "text": text}
         except Exception as e:
             blocked, reason = _is_blocked(e)
             if blocked:
                 return {"ok": False, "blocked": True, "reason": reason or str(e), "text": ""}
             last_err = e
             continue
     return {"ok": False, "blocked": False, "reason": str(last_err or "unknown"), "text": ""}
