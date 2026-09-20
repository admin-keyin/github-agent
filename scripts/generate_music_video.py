import os
import sys
import glob
import random
import subprocess
import json
import time
import requests
from pydub import AudioSegment

# --- 1. 신박한 감성 곡 제목 & 가사(스토리) 생성 엔진 ---

CREATIVE_SONG_STORIES = [
    {
        "genre": "piano",
        "title_templates": [
            "새벽 3시 42분, 불 꺼진 방에서 너를 생각하며",
            "그때 너에게 하지 못했던 마지막 한마디",
            "우리가 사랑이라 불렀던 계절의 끝에서",
            "너를 지우려다 하루가 다 지나버렸어",
            "비 내리는 창가에 남겨둔 너의 온기",
            "다시 돌아갈 수 없어서 더 아름다운 날들"
        ],
        "lyrics": [
            "어둠이 내려앉은 방 한구석",
            "켜지지 않는 전화기만 바라보다가",
            "문득 스쳐 지나간 너의 미소에",
            "애써 묻어둔 기억들이 다시 피어나",
            "전하지 못한 말들이 가슴에 남아",
            "오늘 밤도 이렇게 너를 그려본다"
        ],
        "prompt": "Emotional sentimental Korean ballad acoustic grand piano solo, delicate touch, romantic nostalgic melody, soft strings ambiance, 68 bpm"
    },
    {
        "genre": "lofi",
        "title_templates": [
            "퇴근길 지하철 막차, 이어폰 너머의 위로",
            "아무도 없는 한밤중 편의점 앞에서",
            "어질러진 책상 위 식어버린 커피 한 잔",
            "괜찮은 척 웃어넘긴 하루의 끝",
            "잠들지 못하는 새벽의 소소한 생각들"
        ],
        "lyrics": [
            "하루 종일 무거웠던 마음을 내려놓고",
            "창문 틈으로 들어오는 차가운 새벽 공기",
            "이어폰을 타고 흐르는 멜로디에",
            "오늘도 수고했다고 가만히 다독여줘",
            "내일은 조금 더 따뜻한 하루가 되기를"
        ],
        "prompt": "Cozy late night lo-fi chill hip hop beat with warm rhodes electric piano chords, soft vinyl crackle, gentle aesthetic bass, 75 bpm"
    },
    {
        "genre": "citypop",
        "title_templates": [
            "자정이 넘은 한강 다리 위를 달리며",
            "네온사인 불빛 아래 너와 나만의 춤",
            "어젯밤 꿈속에서 본 너의 뒷모습",
            "반짝이는 도심 속 사라져가는 실루엣"
        ],
        "lyrics": [
            "도시는 잠들고 반짝이는 네온 불빛",
            "차가운 밤공기 속을 가르며 달려가",
            "스쳐 지나가는 불빛 사이로",
            "선명해지는 너의 잔상",
            "오늘 밤은 멈추지 않고 어디론가 떠나고 싶어"
        ],
        "prompt": "Groovy 80s Korean retro city pop instrumental, catchy funky bassline, sparkling synth brass, nostalgic breezy night drive, 110 bpm"
    },
    {
        "genre": "ambient",
        "title_templates": [
            "우주 끝자락에 혼자 멈춰선 순간",
            "파도 소리조차 닿지 않는 깊은 밤",
            "지친 영혼을 감싸주는 고요한 숨결",
            "꿈결 속에서 만난 잊혀진 행성"
        ],
        "lyrics": [
            "시간이 멈춘 것만 같은 고요함",
            "모든 소음이 사라진 깊은 바닷속처럼",
            "숨을 들이쉬고 내쉬며",
            "복잡했던 생각들을 멀리 흘려보내",
            "이 평온함 속에 온전히 머물러"
        ],
        "prompt": "Deep meditative cosmic ambient soundscape, soothing ethereal synth pads, peaceful theta wave frequency for deep sleep, 50 bpm"
    }
]

GENRE_IMAGES = {
    "piano": [
        "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1519692933481-e162a57d6721?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1552422535-c45813c61732?auto=format&fit=crop&w=1280&h=720&q=90"
    ],
    "lofi": [
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1280&h=720&q=90"
    ],
    "citypop": [
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=1280&h=720&q=90"
    ],
    "ambient": [
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1280&h=720&q=90"
    ]
}

# --- 2. Meta MusicGen AI 작곡 API 호출 ---

def generate_musicgen_audio(prompt_text, output_mp3_path):
    print(f"\n[AI MusicGen] 작곡 시작: \"{prompt_text}\"")
    api_url = "https://api-inference.huggingface.co/models/facebook/musicgen-small"
    hf_token = os.getenv("HF_TOKEN", "").strip()
    headers = {}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"
        
    payload = {
        "inputs": prompt_text,
        "parameters": {"max_new_tokens": 512, "temperature": 1.0, "top_k": 250}
    }
    
    for attempt in range(3):
        try:
            res = requests.post(api_url, headers=headers, json=payload, timeout=60)
            if res.status_code == 200 and len(res.content) > 10000:
                temp_raw = "temp/ai_raw.wav"
                with open(temp_raw, "wb") as f:
                    f.write(res.content)
                audio = AudioSegment.from_file(temp_raw)
                if len(audio) < 60000:
                    audio = audio.append(audio, crossfade=1500)
                audio = audio.normalize(headroom=0.5).fade_in(1500).fade_out(2500)
                audio.export(output_mp3_path, format="mp3", bitrate="320k")
                print(f"[AI MusicGen] 작곡 완료: {len(audio)/1000:.1f}초")
                return True
            elif res.status_code == 503:
                time.sleep(15)
        except Exception as e:
            print(f"API Retry: {e}")
            time.sleep(5)
            
    # Fallback 음원
    print("[Fallback] assets/audio/ 로컬 고음질 음원 사용")
    audio_files = glob.glob("assets/audio/*.mp3")
    if audio_files:
        chosen = random.choice(audio_files)
        audio = AudioSegment.from_file(chosen).normalize(headroom=0.5).fade_in(1500).fade_out(2500)
        audio.export(output_mp3_path, format="mp3", bitrate="320k")
        return True
    return False

# --- 3. 자막(SRT) 생성 (가사 타이밍 동기화) ---

def create_srt_lyrics_file(lyrics_list, total_duration_sec, output_srt_path):
    """곡 길이에 맞춰 감성 가사가 화면 하단에 차례대로 흐르도록 SRT 자막 파일 생성"""
    if not lyrics_list:
        return
        
    num_lines = len(lyrics_list)
    line_duration = total_duration_sec / (num_lines + 1)
    
    def format_time(seconds):
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    with open(output_srt_path, "w", encoding="utf-8") as f:
        for idx, line in enumerate(lyrics_list):
            start_sec = idx * line_duration + 1.0
            end_sec = min(total_duration_sec - 1.0, (idx + 1) * line_duration + 0.8)
            f.write(f"{idx + 1}\n")
            f.write(f"{format_time(start_sec)} --> {format_time(end_sec)}\n")
            f.write(f"{line}\n\n")
    print(f"SRT Lyrics file created: {output_srt_path}")

# --- 4. 감성 앨범 아트 및 가사 자막 결합 비디오 렌더링 ---

def fetch_hd_background(genre, filename):
    image_pool = GENRE_IMAGES.get(genre, GENRE_IMAGES["piano"])
    chosen_url = random.choice(image_pool)
    try:
        resp = requests.get(chosen_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 1000:
            with open(filename, 'wb') as f:
                f.write(resp.content)
            return
    except Exception as e:
        print(f"Image fetch fallback: {e}")
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x1a2130:s=1280x720:d=1", "-vframes", "1", filename], check=True)

def create_lyric_music_video(image_path, audio_path, srt_path, song_title, output_path):
    """배경 이미지 + 가사 자막 + 곡 제목 오버레이 렌더링"""
    audio = AudioSegment.from_file(audio_path)
    duration_sec = len(audio) / 1000.0
    
    # 폰트 및 스타일 필터
    # 제목 오버레이 및 자막 필터
    safe_title = song_title.replace(":", " -").replace("'", "").replace('"', "")
    video_filter = f"scale=1280:720,drawtext=text='{safe_title}':x=(w-text_w)/2:y=80:fontsize=28:fontcolor=white@0.9:box=1:boxcolor=black@0.4:boxborderw=10"
    
    # 자막 파일이 있으면 subtitles 필터 추가
    if os.path.exists(srt_path):
        video_filter += f",subtitles='{srt_path}':force_style='FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Alignment=2,MarginV=60'"
        
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
        "-c:v", "libx264", "-t", str(duration_sec), "-pix_fmt", "yuv420p",
        "-vf", video_filter,
        "-preset", "ultrafast", "-crf", "22", "-c:a", "aac", "-b:a", "320k", "-shortest", output_path
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"Subtitle render fallback without subs ({e})")
        # 자막 렌더링 실패 시 기본 렌더링
        cmd_fallback = [
            "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
            "-c:v", "libx264", "-t", str(duration_sec), "-pix_fmt", "yuv420p", "-vf", "scale=1280:720",
            "-preset", "ultrafast", "-crf", "22", "-c:a", "aac", "-b:a", "320k", "-shortest", output_path
        ]
        subprocess.run(cmd_fallback, check=True)
        
    print(f"Lyric Music Video created: {output_path} (Duration: {duration_sec:.1f}s)")

# --- 메인 실행 ---

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    genre_input = os.getenv("INPUT_GENRE", "").strip().lower()
    
    # 장르 및 스토리 무작위/지정 매칭
    candidates = [s for s in CREATIVE_SONG_STORIES if s["genre"] == genre_input]
    if not candidates:
        story = random.choice(CREATIVE_SONG_STORIES)
    else:
        story = random.choice(candidates)
        
    genre = story["genre"]
    custom_prompt = os.getenv("INPUT_CUSTOM_PROMPT", "").strip()
    custom_title = os.getenv("INPUT_CUSTOM_TITLE", "").strip()
    
    final_prompt = custom_prompt if custom_prompt else story["prompt"]
    final_title = custom_title if custom_title else random.choice(story["title_templates"])
    lyrics = story["lyrics"]
    
    ai_mp3 = "temp/ai_song.mp3"
    bg_image = "temp/bg.jpg"
    srt_file = "temp/lyrics.srt"
    final_video = "output_music_video.mp4"

    # 1. AI 작곡
    generate_musicgen_audio(final_prompt, ai_mp3)

    # 2. 곡 길이에 맞춘 가사 자막(SRT) 생성
    audio = AudioSegment.from_file(ai_mp3)
    create_srt_lyrics_file(lyrics, len(audio) / 1000.0, srt_file)

    # 3. 고화질 배경 이미지 준비
    fetch_hd_background(genre, bg_image)

    # 4. 감성 가사 자막 + 타이틀 오버레이 리릭 비디오 렌더링
    create_lyric_music_video(bg_image, ai_mp3, srt_file, final_title, final_video)

    # 5. 유튜브 설명란용 가사 전문 및 메타데이터 작성
    lyrics_text = "\n".join(lyrics)
    desc = (
        f"🎧 {final_title}\n\n"
        f"📜 [가사 / Lyrics]\n"
        f"-----------------------------\n"
        f"{lyrics_text}\n"
        f"-----------------------------\n\n"
        f"Genre: {genre.upper()}\n"
        f"Composed & Produced by Keyin AI Studio.\n\n"
        f"#AI작곡 #감성노래 #가사비디오 #LyricVideo #감성발라드 #수면음악 #새벽감성"
    )

    meta_info = {
        "title": final_title[:100],
        "description": desc,
        "artist": "Keyin AI Studio",
        "song_title": final_title
    }
    with open("temp/video_info.json", "w", encoding="utf-8") as f:
        json.dump(meta_info, f, ensure_ascii=False, indent=2)
    print(f"Video metadata saved successfully with lyrics for: {final_title}")
