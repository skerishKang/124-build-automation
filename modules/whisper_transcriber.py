import os
from typing import Optional


class WhisperTranscriber:
    def __init__(self):
        impl = (os.getenv("WHISPER_IMPL", "faster") or "faster").lower()
        self.language = os.getenv("WHISPER_LANGUAGE", "ko") or None
        self.model_size = os.getenv("WHISPER_MODEL", "base")
        self.impl = impl

        if impl == "faster":
            try:
                from faster_whisper import WhisperModel  # type: ignore
            except Exception as e:
                raise RuntimeError(
                    "faster-whisper not installed. Run `pip install faster-whisper`."
                ) from e

            device = os.getenv("WHISPER_DEVICE", "cpu")
            compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
            self._model = WhisperModel(self.model_size, device=device, compute_type=compute_type)
            self._impl = "faster"

        else:
            # Fallback to openai-whisper if requested
            try:
                import whisper  # type: ignore
            except Exception as e:
                raise RuntimeError(
                    "openai-whisper not installed. Run `pip install openai-whisper`."
                ) from e
            self._model = whisper.load_model(self.model_size)
            self._impl = "openai"

    def transcribe(self, audio_path: str) -> str:
        try:
            if self._impl == "faster":
                segments, info = self._model.transcribe(audio_path, language=self.language)
                text = " ".join([seg.text for seg in segments])
                return (text or "").strip()
            else:
                result = self._model.transcribe(audio_path, language=self.language)
                return (result.get("text") or "").strip()
        except Exception as e:
            return f"전사 실패: {str(e)}"

