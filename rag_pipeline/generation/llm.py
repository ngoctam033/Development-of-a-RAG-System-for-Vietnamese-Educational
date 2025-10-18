# rag_pipeline/generation/llm.py
import os
import google.generativeai as genai
from google.api_core.exceptions import NotFound

# ------------------------------------------------------------
# Chọn model ứng viên (ưu tiên 2.5 theo list_models() của bạn)
# ------------------------------------------------------------
def _candidate_models():
    """
    Trả về danh sách tên model theo thứ tự ưu tiên.
    - Ưu tiên lấy từ ENV GEMINI_MODEL_NAME nếu có.
    - Sau đó là các model chắc chắn có trong list_models() bạn vừa in:
      models/gemini-2.5-flash, models/gemini-2.5-pro, models/gemini-2.0-flash, models/gemini-pro-latest
    - Thêm một vài fallback phổ biến.
    """
    env = os.getenv("GEMINI_MODEL_NAME")
    base = [
        "models/gemini-2.5-flash",
        "models/gemini-2.5-pro",
        "models/gemini-2.0-flash",
        "models/gemini-pro-latest",
        "models/gemini-2.0-flash-001",
        "models/gemini-2.0-pro-exp",
        "models/gemini-pro",              # fallback cuối
    ]
    if env:
        # đưa ENV lên đầu, giữ lại thứ tự phần còn lại
        return [env] + [m for m in base if m != env]
    return base


# ------------------------------------------------------------
# Tạo safety_settings:
# - Thử typed (SDK v1)
# - Nếu không có types thì dùng dict
# - Nếu lúc generate lỗi do safety -> sẽ retry không safety
# ------------------------------------------------------------
def _build_safety_typed_or_dict():
    try:
        from google.generativeai.types import HarmCategory, SafetySetting, HarmBlockThreshold  # type: ignore
        return [
            SafetySetting(category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_HARASSMENT,        threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,       threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_SEXUAL_CONTENT,    threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_VIOLENCE,          threshold=HarmBlockThreshold.BLOCK_NONE),
        ]
    except Exception:
        # Một số bản SDK cũ chấp nhận dict; nếu không chấp nhận, generate_answer sẽ tự retry không safety
        return [
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT",        "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH",       "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUAL_CONTENT",    "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_VIOLENCE",          "threshold": "BLOCK_NONE"},
        ]


class GeminiGenerator:
    """
    Trình bao cho Google Generative AI:
    - Tự chọn model hợp lệ (ưu tiên 2.5 theo list_models)
    - Gọi generate_content với/không với safety tùy SDK
    - Thuộc tính self.model_name để CLI in debug
    """
    def __init__(self, api_key: str = None, model_name: str = None):
        api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY/GOOGLE_API_KEY chưa được thiết lập.")
        genai.configure(api_key=api_key)

        self._gen_cfg = dict(
            temperature=0.2,
            top_p=0.9,
            max_output_tokens=1024,
        )
        self._safety_settings = _build_safety_typed_or_dict()

        # Chọn model
        self.model = None
        self.model_name = None
        candidates = [model_name] if model_name else _candidate_models()

        last_err = None
        for name in candidates:
            try:
                m = genai.GenerativeModel(name)
                # xác nhận nhanh model hợp lệ bằng request nhẹ
                _ = m.generate_content("ping")
                self.model = m
                self.model_name = name
                break
            except NotFound as e:
                last_err = e
                continue
            except Exception as e:
                # Một số SDK có thể lỗi ở ping, nhưng model vẫn hợp lệ khi dùng thật.
                # Ta vẫn chấp nhận name này, để generate_answer lo retry.
                self.model = genai.GenerativeModel(name)
                self.model_name = name
                last_err = e
                break

        if not self.model:
            raise RuntimeError(f"Không tìm được model Gemini khả dụng. Lỗi cuối: {last_err}")

    def generate_answer(self, prompt: str) -> str:
        """
        Trả về text; nếu SDK/safety gây lỗi key/format -> retry không safety.
        Ghi rõ thông báo nếu empty / lỗi khác.
        """
        # 1) Thử với safety_settings (typed hoặc dict)
        try:
            resp = self.model.generate_content(
                prompt,
                generation_config=self._gen_cfg,
                safety_settings=self._safety_settings,
            )
            text = getattr(resp, "text", None)
            if not text:
                details = getattr(resp, "prompt_feedback", None) or getattr(resp, "candidates", None)
                return f"[LLM empty] Không nhận được text. Chi tiết: {details}"
            return text.strip()

        # 2) Nếu safety settings không hợp (KeyError/TypeError/ValueError) -> gọi lại không safety
        except (KeyError, TypeError, ValueError):
            try:
                resp = self.model.generate_content(
                    prompt,
                    generation_config=self._gen_cfg,  # KHÔNG truyền safety_settings
                )
                text = getattr(resp, "text", None)
                if not text:
                    details = getattr(resp, "prompt_feedback", None) or getattr(resp, "candidates", None)
                    return f"[LLM empty] Không nhận được text (retry no safety). Chi tiết: {details}"
                return text.strip()
            except NotFound as e:
                return f"[LLM error] NotFound: {e}"
            except Exception as e:
                return f"[LLM error] {type(e).__name__}: {e}"

        # 3) Các lỗi khác (bao gồm NotFound nếu phát sinh ở lần gọi đầu)
        except NotFound as e:
            return f"[LLM error] NotFound: {e}"
        except Exception as e:
            return f"[LLM error] {type(e).__name__}: {e}"
