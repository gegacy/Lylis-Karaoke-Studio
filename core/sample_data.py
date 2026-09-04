"""
Lylis Karaoke Studio - Sample Data matching exact Reference
"""
import os
import math
import wave
import struct

from core.paths import get_asset_path

SAMPLE_LRC_VIETNAMESE = """[00:02.50](00:02.50)Nhân (00:03.10)duyên (00:03.60)phải (00:04.20)kiếm {singer:male}
[00:05.80](00:05.80)Mà (00:06.30)làm (00:06.80)anh (00:07.40)nhớ (00:08.00)ánh (00:08.50)mắt (00:09.10)đầu {singer:male}
[00:11.20](00:11.20)Chắc (00:11.70)em (00:12.20)vừa (00:12.70)buồn (00:13.30)lắm {singer:female}
[00:14.80](00:14.80)Từ (00:15.30)ngày (00:15.80)tôi (00:16.40)đi {singer:female}
[00:18.20](00:18.20)Về (00:18.80)ghé (00:19.40)đến (00:20.00)phía (00:20.60)trước {singer:both}
[00:22.50](00:22.50)Chiếc (00:23.00)nón (00:23.50)ba (00:24.00)tầm (00:24.60)này {singer:both}
[00:26.50](00:26.50)Tà (00:27.00)áo (00:27.50)mở (00:28.00)ba (00:28.50)mở (00:29.20)bảy {singer:female}
[00:31.00](00:31.00)Má (00:31.40)thắm (00:31.80)môi (00:32.30)hồng (00:32.80)dài (00:33.40)lụa {singer:female}
[00:35.00](00:35.00)Tay (00:35.50)ai (00:36.00)khéo (00:36.70)thắt {singer:male}
[00:39.00](00:39.00)Anh (00:39.50)chẳng (00:40.00)cần (00:40.50)non (00:41.20)kia {singer:male}
[00:43.00](00:43.00)Em (00:43.50)đây (00:44.00)chẳng (00:44.50)cần (00:45.00)gác (00:45.50)tía (00:46.00)cung (00:46.80)vàng {singer:female}"""

def ensure_sample_assets():
    assets_dir = get_asset_path()
    try:
        os.makedirs(assets_dir, exist_ok=True)
    except Exception:
        pass
    
    bg_path = get_asset_path('sample_bg.jpg')
    audio_path = get_asset_path('sample_audio.wav')
    
    # Create sample background if not exists
    if not os.path.exists(bg_path):
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (1920, 1080), color=(30, 41, 59))
        draw = ImageDraw.Draw(img)
        draw.ellipse([200, 200, 700, 700], fill=(251, 146, 60))
        draw.ellipse([800, 150, 1300, 650], fill=(56, 189, 248))
        draw.ellipse([1100, 300, 1700, 900], fill=(244, 114, 182))
        img.save(bg_path, 'JPEG')

    # Create sample audio if not exists
    if not os.path.exists(audio_path):
        sample_rate = 44100
        duration = 52.0
        n_samples = int(sample_rate * duration)
        with wave.open(audio_path, 'w') as wav_file:
            wav_file.setnchannels(2)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            frames = bytearray()
            for i in range(n_samples):
                t = i / sample_rate
                # Acoustic melody
                val = (
                    math.sin(2 * math.pi * 220 * t) * 0.3 +
                    math.sin(2 * math.pi * 440 * t) * 0.2 +
                    math.sin(2 * math.pi * 330 * t) * 0.2
                )
                amp = int(val * 32767 * 0.4)
                frames.extend(struct.pack('<hh', amp, amp))
            wav_file.writeframes(frames)
            
    return bg_path, audio_path
