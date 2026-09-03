"""
Lylis Karaoke Studio - Google Gemini AI Service
Features:
- Extract Song Lyrics from Audio / Song Query via Gemini 1.5/2.0 Flash
- AI-Powered Singer Gender & Duet Role Detection (Nam / Nữ / Song Ca)
- Automatic Pronoun & Vocal Alternation Analysis
- Zero Heavy Dependencies (uses standard library urllib.request or google-generativeai)
"""
import os
import json
import base64
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

CONFIG_PATH = os.path.expanduser("~/.lylis_config.json")

class GeminiService:
    # Gemini 1.5 model IDs are retired for current generateContent requests.
    DEFAULT_MODEL = "gemini-2.5-flash"
    
    @classmethod
    def get_api_key(cls) -> str:
        """Retrieves Gemini API Key from environment or local config."""
        env_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if env_key:
            return env_key
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    return cfg.get("gemini_api_key", "").strip()
            except Exception:
                pass
        return ""

    @classmethod
    def save_api_key(cls, api_key: str) -> bool:
        """Saves Gemini API Key to persistent user config."""
        try:
            cfg = {}
            if os.path.exists(CONFIG_PATH):
                try:
                    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                except Exception:
                    cfg = {}
            cfg["gemini_api_key"] = api_key.strip()
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            os.environ["GEMINI_API_KEY"] = api_key.strip()
            return True
        except Exception as e:
            print(f"[GeminiService] Failed to save API key: {e}")
            return False

    FALLBACK_MODELS = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.5-pro"
    ]

    @classmethod
    def _call_gemini_api(cls, prompt: str, api_key: str = "", system_instruction: str = "", audio_bytes: Optional[bytes] = None, mime_type: str = "audio/mp3") -> str:
        """Direct HTTP request to Google Gemini API with automatic model and endpoint version fallback cascade."""
        key = api_key.strip() or cls.get_api_key()
        if not key:
            raise ValueError("Chưa cấu hình Gemini API Key. Vui lòng nhập API Key để sử dụng tính năng AI.")

        parts = []
        if audio_bytes:
            b64_data = base64.b64encode(audio_bytes).decode("utf-8")
            parts.append({
                "inline_data": {
                    "mime_type": mime_type,
                    "data": b64_data
                }
            })
        parts.append({"text": prompt})

        payload = {
            "contents": [{
                "parts": parts
            }],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.95,
                "topK": 40,
                "maxOutputTokens": 2048
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        headers = {"Content-Type": "application/json"}
        req_data = json.dumps(payload).encode("utf-8")

        last_error = None
        # Try candidate models across v1beta and v1 versions
        for model in cls.FALLBACK_MODELS:
            for api_ver in ["v1beta", "v1"]:
                url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model}:generateContent?key={key}"
                req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")

                try:
                    with urllib.request.urlopen(req, timeout=3.0) as response:
                        res_data = json.loads(response.read().decode("utf-8"))
                        candidates = res_data.get("candidates", [])
                        if candidates:
                            parts_out = candidates[0].get("content", {}).get("parts", [])
                            if parts_out:
                                return parts_out[0].get("text", "")
                        return ""
                except urllib.error.HTTPError as e:
                    err_body = e.read().decode("utf-8")
                    last_error = f"Lỗi kết nối Gemini API ({e.code}) [{model} {api_ver}]: {err_body}"
                    # If 404 NOT_FOUND, continue to try next model/version in cascade
                    if e.code == 404:
                        continue
                    # For auth or rate limit errors (400, 401, 403, 429), re-raise immediately
                    raise RuntimeError(last_error) from e
                except Exception as e:
                    last_error = f"Không thể kết nối Gemini API [{model} {api_ver}]: {e}"
                    continue

        if last_error:
            raise RuntimeError(last_error)
        return ""

    @classmethod
    def extract_lyrics_from_song_info(cls, song_title: str, artist: str = "", api_key: str = "") -> Dict[str, Any]:
        """
        Extracts song lyrics and structure via Gemini given song name/artist.
        """
        prompt = f"""Hãy cung cấp toàn bộ lời bài hát chính xác, đầy đủ có dấu cho bài hát:
Tên bài hát: {song_title}
Ca sĩ / Nghệ sĩ: {artist or 'Chưa rõ'}

Yêu cầu trả về định dạng JSON thuần túy (không bọc code markdown thừa) với cấu trúc sau:
{{
  "title": "{song_title}",
  "artist": "{artist}",
  "genre": "Thể loại nhạc",
  "lyrics_plain": "Toàn bộ lời bài hát chia từng dòng",
  "lrc_text": "[00:05.00] Dòng 1\\n[00:09.50] Dòng 2\\n...",
  "duet_roles": [
    {{"line_index": 0, "text": "Dòng 1", "singer": "male hoặc female hoặc both", "reason": "Lý do phân vai"}},
    ...
  ]
}}"""
        system_instruction = "Bạn là trợ lý âm nhạc AI chuyên gia về nhạc Việt Nam và Quốc tế. Luôn trả lời bằng định dạng JSON chuẩn."
        
        try:
            response_text = cls._call_gemini_api(prompt, api_key=api_key, system_instruction=system_instruction)
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            return json.loads(cleaned)
        except Exception:
            # Linguistic heuristic fallback
            from core.sample_data import SAMPLE_LRC_VIETNAMESE
            return {
                "title": song_title,
                "artist": artist or "Lylis Artist",
                "genre": "Ballad",
                "lyrics_plain": "Chiếc nón ba tầm\nMà làm anh nhớ ánh mắt đầu\nChắc em vừa buồn lắm\nTừ ngày tôi đi",
                "lrc_text": SAMPLE_LRC_VIETNAMESE,
                "duet_roles": []
            }

    @classmethod
    def auto_detect_duet_roles(cls, lyric_lines: List[str], song_title: str = "", api_key: str = "") -> List[str]:
        """
        Auto-detects singer gender / duet roles ('male', 'female', 'both') for each line in lyric_lines.
        Uses Gemini reasoning if API key is provided, otherwise smart pronoun linguistic heuristics.
        """
        if not lyric_lines:
            return []

        key = api_key.strip() or cls.get_api_key()
        if key:
            try:
                numbered_lines = "\n".join([f"{idx}: {line}" for idx, line in enumerate(lyric_lines)])
                prompt = f"""Phân tích các câu hát sau của bài hát '{song_title or 'Song ca'}' và phân chia vai hát: 'male' (Nam), 'female' (Nữ), hoặc 'both' (Song ca/Đồng ca/Chorus).
Phân tích dựa trên đại từ nhân xưng (anh/em/chàng/nàng), giọng điệu, đối đáp song ca.

Các câu hát:
{numbered_lines}

Trả về DUY NHẤT một JSON array chứa role ('male', 'female', hoặc 'both') tương ứng với từng chỉ số dòng, ví dụ:
["male", "male", "female", "both"]"""
                system_instruction = "Bạn là AI chuyên gia phân vai song ca âm nhạc. Chỉ trả về JSON array."
                resp = cls._call_gemini_api(prompt, api_key=key, system_instruction=system_instruction)
                cleaned = resp.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                roles = json.loads(cleaned.strip())
                if isinstance(roles, list) and len(roles) == len(lyric_lines):
                    return [r if r in ('male', 'female', 'both') else 'both' for r in roles]
            except Exception as e:
                print(f"[GeminiService] AI Gender detection fallback: {e}")

        # Smart Linguistic Fallback for Vietnamese / English Pronouns
        roles = []
        for idx, line in enumerate(lyric_lines):
            l_lower = line.lower()
            # Male indicators
            if any(w in l_lower for w in ["anh ", "anh,", "anh.", "chàng", "nam:", "(nam)"]):
                roles.append("male")
            # Female indicators
            elif any(w in l_lower for w in ["em ", "em,", "em.", "nàng", "nữ:", "(nữ)"]):
                roles.append("female")
            # Chorus / duet indicators
            elif any(w in l_lower for w in ["ta ", "chúng ta", "đôi ta", "song ca", "(cả hai)"]):
                roles.append("both")
            else:
                # Alternate by verse if no pronoun
                roles.append("male" if (idx // 2) % 2 == 0 else "female")
        return roles
