"""
Lylis Karaoke Studio - Enhanced Word-by-Word LRC Engine
Exact parser and serializer matching Lylis.app specifications with Voice Gender support.
"""
import re
from dataclasses import dataclass, field
from typing import List

@dataclass
class WordSyllable:
    text: str
    start_time: float
    end_time: float
    
    @property
    def duration(self) -> float:
        return max(0.05, self.end_time - self.start_time)

@dataclass
class LyricLine:
    line_start: float
    line_end: float
    words: List[WordSyllable] = field(default_factory=list)
    raw_text: str = ""
    singer: str = "both"  # "male" | "female" | "both"

    @property
    def full_text(self) -> str:
        return "".join([w.text for w in self.words]).strip() or self.raw_text

class LrcEngine:
    @staticmethod
    def parse_timestamp(ts_str: str) -> float:
        """Parses mm:ss.xx into seconds."""
        ts_str = ts_str.strip('[]()<> ')
        parts = ts_str.split(':')
        if len(parts) == 2:
            try:
                mins = float(parts[0])
                secs = float(parts[1])
                return mins * 60.0 + secs
            except ValueError:
                return 0.0
        return 0.0

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """Formats seconds into mm:ss.xx."""
        total_cs = max(0, int(round(float(seconds) * 100.0)))
        mins, centiseconds = divmod(total_cs, 6000)
        secs, cs = divmod(centiseconds, 100)
        return f"{mins:02d}:{secs:02d}.{cs:02d}"

    @classmethod
    def parse(cls, lrc_text: str) -> List[LyricLine]:
        """
        Parses word-by-word LRC text matching Lylis.app format:
        [00:28.84](00:28.84)Chiếc (00:29.12)nón (00:29.42)ba (00:29.79)tầm...
        or standard line LRC:
        [00:28.84]Chiếc nón ba tầm
        Supports singer tags: (Nam), (Nữ), (Song ca), {singer:male}
        """
        if not lrc_text or not lrc_text.strip():
            return []

        timestamp = r'(\d{1,3}):(\d{2})(?:[\.:](\d{1,3}))?'
        line_regex = re.compile(r'^\[' + timestamp + r'\]')
        word_regex = re.compile(r'[\(\<]' + timestamp + r'[\)\>]\s*([^\(\<]+)')
        singer_tag_regex = re.compile(r'\{(?:singer|voice):([a-zA-Z]+)\}', re.IGNORECASE)
        
        output_lines = []
        raw_lines = lrc_text.strip().splitlines()

        for raw_line in raw_lines:
            raw_line = raw_line.strip()
            if not raw_line or raw_line.startswith('#'):
                continue

            line_match = line_regex.search(raw_line)
            if not line_match:
                continue

            # Compute line start time
            l_min = int(line_match.group(1))
            l_sec = int(line_match.group(2))
            fraction = line_match.group(3) or "0"
            line_start = l_min * 60.0 + l_sec + int(fraction) / (10 ** len(fraction))

            content = raw_line[line_match.end():].strip()
            
            # Detect singer tag
            singer = "both"
            singer_m = singer_tag_regex.search(content)
            if singer_m:
                s_val = singer_m.group(1).lower()
                singer = s_val if s_val in ["male", "female", "both"] else "both"
                content = singer_tag_regex.sub("", content).strip()
            elif "(nam)" in content.lower() or "[nam]" in content.lower():
                singer = "male"
            elif "(nữ)" in content.lower() or "[nữ]" in content.lower() or "(nu)" in content.lower():
                singer = "female"
            elif "(song ca)" in content.lower() or "[song ca]" in content.lower():
                singer = "both"
            elif content.lower().startswith("anh ") or " chàng " in content.lower():
                singer = "male"
            elif content.lower().startswith("em ") or " nàng " in content.lower():
                singer = "female"

            # Human-readable role markers are metadata, not lyric content.
            content = re.sub(
                r'\s*[\(\[]\s*(?:nam|nữ|nu|song ca)\s*[\)\]]\s*',
                ' ', content, flags=re.IGNORECASE
            ).strip()

            # Find word-by-word timestamps
            word_matches = list(word_regex.finditer(content))
            words_list = []

            if word_matches:
                for w_m in word_matches:
                    w_min = int(w_m.group(1))
                    w_sec = int(w_m.group(2))
                    w_fraction = w_m.group(3) or "0"
                    w_start = w_min * 60.0 + w_sec + int(w_fraction) / (10 ** len(w_fraction))
                    w_text = w_m.group(4)

                    words_list.append(WordSyllable(
                        text=w_text,
                        start_time=w_start,
                        end_time=w_start + 0.5  # placeholder
                    ))

                # Calculate word end times
                for i in range(len(words_list) - 1):
                    words_list[i].end_time = max(words_list[i].start_time + 0.05, words_list[i + 1].start_time)
                if words_list:
                    words_list[-1].end_time = words_list[-1].start_time + 0.8
                
                line_end = words_list[-1].end_time if words_list else line_start + 3.0
            else:
                # Fallback: line without word timestamps
                words_raw = content.split()
                dur_per_word = 2.5 / max(1, len(words_raw))
                for i, w in enumerate(words_raw):
                    w_s = line_start + i * dur_per_word
                    words_list.append(WordSyllable(
                        text=w + " ",
                        start_time=w_s,
                        end_time=w_s + dur_per_word
                    ))
                line_end = line_start + 2.5

            output_lines.append(LyricLine(
                line_start=line_start,
                line_end=line_end,
                words=words_list,
                raw_text=content,
                singer=singer
            ))

        # Imported LRC files are not always ordered; normalize before deriving ends.
        output_lines.sort(key=lambda line: line.line_start)

        # Adjust line_end if consecutive lines overlap
        for i in range(len(output_lines) - 1):
            if output_lines[i].line_end > output_lines[i + 1].line_start:
                output_lines[i].line_end = max(output_lines[i].line_start + 0.1, output_lines[i + 1].line_start)
                if output_lines[i].words:
                    output_lines[i].words[-1].end_time = output_lines[i].line_end

        return output_lines

    @classmethod
    def export_lrc(cls, lines: List[LyricLine], include_singer: bool = True) -> str:
        """Exports LyricLines back to standard word-synced LRC text."""
        result = []
        for line in lines:
            line_ts = cls.format_timestamp(line.line_start)
            if line.words:
                words_str = " ".join([f"({cls.format_timestamp(w.start_time)}){w.text.strip()}" for w in line.words if w.text.strip()])
            else:
                words_str = line.raw_text.strip()
            singer_tag = f" {{singer:{line.singer}}}" if include_singer and line.singer != "both" else ""
            result.append(f"[{line_ts}]{words_str}{singer_tag}")
        return "\n".join(result)

    @classmethod
    def export_srt(cls, lines: List[LyricLine]) -> str:
        """Exports LyricLines to SubRip (.SRT) format."""
        srt_blocks = []
        for idx, line in enumerate(lines, 1):
            s_h = int(line.line_start // 3600)
            s_m = int((line.line_start % 3600) // 60)
            s_s = int(line.line_start % 60)
            s_ms = int((line.line_start % 1) * 1000)

            e_h = int(line.line_end // 3600)
            e_m = int((line.line_end % 3600) // 60)
            e_s = int(line.line_end % 60)
            e_ms = int((line.line_end % 1) * 1000)

            start_str = f"{s_h:02d}:{s_m:02d}:{s_s:02d},{s_ms:03d}"
            end_str = f"{e_h:02d}:{e_m:02d}:{e_s:02d},{e_ms:03d}"

            singer_prefix = "[Nam] " if line.singer == "male" else ("[Nữ] " if line.singer == "female" else "")
            srt_blocks.append(f"{idx}\n{start_str} --> {end_str}\n{singer_prefix}{line.full_text}\n")

        return "\n".join(srt_blocks)
