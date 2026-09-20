import os
import sys
import glob
import random
import subprocess
import json
import time
import requests
from pydub import AudioSegment

# --- 1. 신박한 감성 곡 제목 & 장르별 프롬프트 설정 ---

CREATIVE_SONG_STORIES = [
    {
        "genre": "piano",
        "title_templates": [
            "새벽 3시 42분, 불 꺼진 방에서 너를 생각하며",
            "그때 너에게 하지 못했던 마지막 한마디",
            "우리가 사랑이라 불렀던 계절의 끝에서",
            "너를 지우려다 하루가 다 지나버렸어",
            "비 내리는 창가에 남겨둔 너의 온기",
            "다시 돌아갈 수 없어서 더 아름다운 날들",
            "어느 날 문득 너의 이름이 떠오를 때",
            "아무도 모르게 흘려보낸 나의 새벽"
        ],
        "desc": "마음이 차분해지는 서정적인 피아노 연주곡입니다. 하루의 피로를 덜어내고 편안한 휴식과 몰입의 시간을 가져보세요.",
        "tags": ["#AI피아노", "#피아노연주", "#힐링피아노", "#수면음악", "#감성피아노", "#이퀄라이저", "#AudioVisualizer", "#PianoMusic"],
        "prompt": "Emotional sentimental Korean ballad acoustic grand piano solo, delicate touch, romantic nostalgic melody, soft strings ambiance, 68 bpm"
    },
    {
        "genre": "lofi",
        "title_templates": [
            "퇴근길 지하철 막차, 이어폰 너머의 위로",
            "아무도 없는 한밤중 편의점 앞에서",
            "어질러진 책상 위 식어버린 커피 한 잔",
            "괜찮은 척 웃어넘긴 하루의 끝",
            "잠들지 못하는 새벽의 소소한 생각들",
            "비 오는 밤, 방 안에서 듣는 따뜻한 비트"
        ],
        "desc": "새벽 감성을 자극하는 아늑한 로파이(Lo-Fi) 칠합 비트입니다. 코딩, 공부, 독서, 야간 작업용으로 추천합니다.",
        "tags": ["#로파이", "#LofiBeats", "#칠합", "#코딩음악", "#새벽감성", "#ChillLofi", "#비주얼라이저", "#StudyVibe"],
        "prompt": "Cozy late night lo-fi chill hip hop beat with warm rhodes electric piano chords, soft vinyl crackle, gentle aesthetic bass, 75 bpm"
    },
    {
        "genre": "citypop",
        "title_templates": [
            "자정이 넘은 한강 다리 위를 달리며",
            "네온사인 불빛 아래 너와 나만의 춤",
            "어젯밤 꿈속에서 본 너의 뒷모습",
            "반짝이는 도심 속 사라져가는 실루엣",
            "도심의 밤바람을 가르는 드라이브"
        ],
        "desc": "레트로한 감성과 그루브가 살아있는 80년대 시티팝 사운드입니다. 야간 드라이브나 기분 전환용으로 감상해보세요.",
        "tags": ["#시티팝", "#CityPop", "#레트로음악", "#드라이브음악", "#RetroVibe", "#80sVibe", "#Visualizer"],
        "prompt": "Groovy 80s Korean retro city pop instrumental, catchy funky bassline, sparkling synth brass, nostalgic breezy night drive, 110 bpm"
    },
    {
        "genre": "ambient",
        "title_templates": [
            "우주 끝자락에 혼자 멈춰선 순간",
            "파도 소리조차 닿지 않는 깊은 밤",
            "지친 영혼을 감싸주는 고요한 숨결",
            "꿈결 속에서 만난 잊혀진 행성",
            "모든 소음이 멈춘 고요의 시간"
        ],
        "desc": "복잡한 생각을 비우고 깊은 명상과 수면에 빠져들 수 있도록 도와주는 앰비언트 힐링 사운드스케이프입니다.",
        "tags": ["#앰비언트", "#명상음악", "#힐링사운드", "#수면음악", "#AmbientMusic", "#Meditation", "#DeepSleep"],
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

# --- 3. 고화질 감성 배경 이미지 다운로드 ---

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

# --- 4. 실시간 반응형 오디오 이퀄라이저 비주얼라이저 비디오 렌더링 ---

def create_equalizer_music_video(image_path, audio_path, song_title, output_path):
    """
    음악의 멜로디와 리듬에 실시간으로 반응하여 춤추는
    반투명 화이트/네온 오디오 이퀄라이저 바(Audio Visualizer) 렌더링
    """
    print("Rendering audio visualizer music video...")
    audio = AudioSegment.from_file(audio_path)
    duration_sec = len(audio) / 1000.0
    safe_title = song_title.replace(":", " -").replace("'", "").replace('"', "")
    
    # FFmpeg 필터 컴플렉스:
    # 1. 배경 이미지 리사이즈 (1280x720) 및 상단 감성 타이틀 박스 오버레이
    # 2. 오디오 주파수 스펙트럼 분석 -> 실시간 반응형 막대 이퀄라이저(showfreqs) 생성 (860x140)
    # 3. 배경 하단 중앙에 이퀄라이저 바를 오버레이
    filter_complex = (
        f"[0:v]scale=1280:720,"
        f"drawtext=text='{safe_title}':x=(w-text_w)/2:y=90:fontsize=30:fontcolor=white@0.95:box=1:boxcolor=black@0.45:boxborderw=12[bg];"
        f"[1:a]showfreqs=s=860x130:mode=bar:fscale=log:colors=white@0.85|white@0.4:win_size=1024[eq];"
        f"[bg][eq]overlay=x=(W-w)/2:y=H-190[v]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-t", str(duration_sec),
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast", "-crf", "22",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest", output_path
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"[Visualizer Render Success] {output_path} (길이: {duration_sec:.1f}s)")
    except Exception as e:
        print(f"Visualizer render error ({e}), falling back to simple video...")
        cmd_fallback = [
            "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
            "-c:v", "libx264", "-t", str(duration_sec), "-pix_fmt", "yuv420p", "-vf", "scale=1280:720",
            "-preset", "ultrafast", "-crf", "22", "-c:a", "aac", "-b:a", "320k", "-shortest", output_path
        ]
        subprocess.run(cmd_fallback, check=True)

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
    
    ai_mp3 = "temp/ai_song.mp3"
    bg_image = "temp/bg.jpg"
    final_video = "output_music_video.mp4"

    # 1. AI 작곡
    generate_musicgen_audio(final_prompt, ai_mp3)

    # 2. 고화질 배경 이미지 다운로드
    fetch_hd_background(genre, bg_image)

    # 3. 음악에 맞춰 실시간 춤추는 오디오 이퀄라이저 비주얼라이저 비디오 렌더링
    create_equalizer_music_video(bg_image, ai_mp3, final_title, final_video)

    # 4. 유튜브 메타데이터 JSON 저장
    tags_str = " ".join(story["tags"])
    desc = (
        f"🎧 {final_title}\n\n"
        f"{story['desc']}\n\n"
        f"Genre: {genre.upper()}\n"
        f"AI Prompt: \"{final_prompt}\"\n\n"
        f"Composed & Visualized by Keyin AI Music Studio.\n\n"
        f"{tags_str}"
    )

    meta_info = {
        "title": final_title[:100],
        "description": desc,
        "artist": "Keyin AI Studio",
        "song_title": final_title
    }
    with open("temp/video_info.json", "w", encoding="utf-8") as f:
        json.dump(meta_info, f, ensure_ascii=False, indent=2)
    print(f"Video metadata saved successfully for: {final_title}")
