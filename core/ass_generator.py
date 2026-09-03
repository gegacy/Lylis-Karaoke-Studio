r"""
Lylis Karaoke Studio - Advanced SubStation Alpha (.ass) Progressive Karaoke Generator
Generates {\kf<duration>} tags with dual-line staggered top/bottom layout
"""
from typing import List
from core.lrc_engine import LyricLine

class AssGenerator:
    @staticmethod
    def format_ass_timestamp(seconds: float) -> str:
        """Converts seconds into ASS timestamp format: H:MM:SS.cc (centiseconds)."""
        if seconds < 0:
            seconds = 0
        total_cs = max(0, int(round(float(seconds) * 100.0)))
        hours, remainder = divmod(total_cs, 360000)
        mins, remainder = divmod(remainder, 6000)
        secs, cs = divmod(remainder, 100)
        return f"{hours:d}:{mins:02d}:{secs:02d}.{cs:02d}"

    @classmethod
    def generate_ass(
        cls, 
        lines: List[LyricLine], 
        font_name: str = "Montserrat", 
        font_size: int = 54,
        primary_color: str = "&H00FFFFFF",  # Base white
        secondary_color: str = "&H00FFD200",# Active Cyan
        outline_color: str = "&H00000000",  # Black stroke
        aspect_ratio: str = "16:9"
    ) -> str:
        res_x, res_y = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)

        ass_header = f"""[Script Info]
Title: Lylis Karaoke Studio Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: {res_x}
PlayResY: {res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: KaraokeTop,{font_name},{font_size},{primary_color},{secondary_color},{outline_color},&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,60,60,{int(res_y * 0.22)},1
Style: KaraokeBottom,{font_name},{font_size},{primary_color},{secondary_color},{outline_color},&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,60,60,{int(res_y * 0.10)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        for idx, line in enumerate(lines):
            style_name = "KaraokeTop" if idx % 2 == 0 else "KaraokeBottom"
            start_ts = cls.format_ass_timestamp(line.line_start)
            end_ts = cls.format_ass_timestamp(line.line_end)

            kf_words = []
            for w in line.words:
                dur_cs = max(5, int(round((w.end_time - w.start_time) * 100)))
                kf_words.append(f"{{\\kf{dur_cs}}}{w.text}")

            line_text = "".join(kf_words)
            events.append(f"Dialogue: 0,{start_ts},{end_ts},{style_name},,0,0,0,,{line_text}")

        return ass_header + "\n".join(events) + "\n"
