"""
Lylis Karaoke Studio - AI Lyric Alignment Service
Maps official lyric words onto Whisper audio timestamps while preserving Vietnamese Unicode diacritics
"""
import re
import difflib
from typing import List, Dict, Any

class LyricAligner:
    @staticmethod
    def normalize_word(word: str) -> str:
        """Strips punctuation and lowercases while retaining Vietnamese vowels."""
        clean = re.sub(r'[^\w\s]', '', word.lower())
        return clean.strip()

    @classmethod
    def align_official_lyrics(
        cls, 
        official_text: str, 
        whisper_lines: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Aligns raw official lyric lines against Whisper word timestamps using SequenceMatcher.
        """
        # Flatten all Whisper words with their timestamps
        flat_whisper = []
        for line in whisper_lines:
            for w in line.get('words', []):
                flat_whisper.append(w)

        if not flat_whisper:
            return []

        whisper_norm_words = [cls.normalize_word(w['word']) for w in flat_whisper]

        # Parse official lines
        official_lines = [l.strip() for l in official_text.splitlines() if l.strip()]
        aligned_result = []

        w_cursor = 0
        total_whisper = len(flat_whisper)

        for line_str in official_lines:
            words_in_line = line_str.split()
            if not words_in_line:
                continue

            line_words_norm = [cls.normalize_word(w) for w in words_in_line]
            num_words = len(words_in_line)

            # Look ahead in whisper words window
            window_size = min(total_whisper - w_cursor, num_words * 3)
            window = whisper_norm_words[w_cursor : w_cursor + window_size]

            matcher = difflib.SequenceMatcher(None, line_words_norm, window)
            matches = matcher.get_matching_blocks()

            matched_words = []
            last_end_time = flat_whisper[w_cursor]['start'] if w_cursor < total_whisper else 0.0

            for match in matches:
                a_idx, b_idx, size = match.a, match.b, match.size
                if size == 0:
                    continue
                for i in range(size):
                    src_word = words_in_line[a_idx + i]
                    whisper_idx = w_cursor + b_idx + i
                    if whisper_idx < total_whisper:
                        target = flat_whisper[whisper_idx]
                        matched_words.append({
                            'word': src_word,
                            'start': target['start'],
                            'end': target['end']
                        })
                        last_end_time = target['end']

            # Handle words missing in audio segment by linear interpolation
            if len(matched_words) < num_words:
                start_t = flat_whisper[w_cursor]['start'] if w_cursor < total_whisper else last_end_time
                end_t = flat_whisper[min(total_whisper - 1, w_cursor + num_words)]['end'] if w_cursor < total_whisper else start_t + num_words * 0.4
                total_span = max(0.2, end_t - start_t)
                dur = total_span / num_words
                matched_words = []
                for idx, w in enumerate(words_in_line):
                    matched_words.append({
                        'word': w,
                        'start': round(start_t + idx * dur, 2),
                        'end': round(start_t + (idx + 1) * dur, 2)
                    })

            w_cursor = min(total_whisper, w_cursor + num_words)

            if matched_words:
                aligned_result.append({
                    'text': line_str,
                    'start': matched_words[0]['start'],
                    'end': matched_words[-1]['end'],
                    'words': matched_words
                })

        return aligned_result
