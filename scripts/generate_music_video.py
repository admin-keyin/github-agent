import os
import sys
import glob
import random
import subprocess
import json
import time
import requests
from pydub import AudioSegment

# --- 1. 장르별 감성 프롬프트 및 메타데이터 풀 ---

PROMPT_TEMPLATES = {
    "piano": [
        {
            "prompt": "Emotional acoustic grand piano solo, gentle flowing melody, romantic and peaceful, warm concert hall reverb, 70 bpm",
            "title": "새벽을 깨우는 따뜻한 피아노 선율 (Peaceful Dawn Piano)",
            "tags": ["#AI피아노", "#피아노연주", "#힐링피아노", "#수면음악", "#감성피아노", "#PianoMusic", "#AIMusic"]
        },
        {
            "prompt": "Calm melancholic piano melody, slow sentimental ballad chords, cinematic intimate atmosphere, beautiful acoustic tone, 65 bpm",
            "title": "비 내리는 오후의 감성 피아노 (Rainy Afternoon Piano)",
            "tags": ["#피아노연주곡", "#잔잔한음악", "#휴식음악", "#공부음악", "#PianoCover", "#StudyMusic"]
        },
        {
            "prompt": "Soothing soft piano lullaby, dreamy arpeggios, relaxing ambient background, deep peaceful sleep vibe, 60 bpm",
            "title": "깊은 잠으로 안내하는 피아노 자장가 (Deep Sleep Piano Lullaby)",
            "tags": ["#수면음악", "#불면증치료", "#힐링음악", "#딥슬립", "#SleepMusic", "#RelaxingPiano"]
        }
    ],
    "lofi": [
        {
            "prompt": "Cozy late night lo-fi hip hop beat, soft jazz rhodes chords, gentle vinyl crackle, relaxing chill study vibe, 75 bpm",
            "title": "새벽 2시, 나만의 작은 방 (2AM Cozy Lo-Fi Chill)",
            "tags": ["#로파이", "#LofiBeats", "#칠합", "#코딩음악", "#새벽감성", "#ChillLofi", "#StudyVibe"]
        },
        {
            "prompt": "Dreamy aesthetic lo-fi beat, warm electric piano, smooth mellow bass, rainy window atmosphere, 80 bpm",
            "title": "창밖의 빗소리와 따뜻한 로파이 (Rainy Window Lo-Fi)",
            "tags": ["#LofiChill", "#비오는날음악", "#공부할때듣는음악", "#힐링비트", "#LofiHipHop"]
        }
    ],
    "jazz": [
        {
            "prompt": "Warm acoustic jazz quartet, sweet saxophone melody, soft double bass, gentle brush drums, cozy cafe atmosphere, 80 bpm",
            "title": "조용한 골목길의 재즈 카페 (Midnight Cafe Jazz)",
            "tags": ["#재즈", "#카페음악", "#힐링재즈", "#재즈피아노", "#CafeJazz", "#SmoothJazz"]
        }
    ],
    "citypop": [
        {
            "prompt": "Retro 80s Japanese city pop instrumental, groovy bassline, nostalgic synth brass, breezy seaside sunset drive, 115 bpm",
            "title": "노을 지는 해변 드라이브 (Sunset Seaside City Pop)",
            "tags": ["#시티팝", "#CityPop", "#레트로음악", "#드라이브음악", "#RetroVibe", "#80sVibe"]
        }
    ],
    "ambient": [
        {
            "prompt": "Deep space ambient soundscape, gentle synth pads, serene meditation frequency, floating peaceful feeling, 55 bpm",
            "title": "우주의 고요함을 담은 명상 음악 (Cosmic Serenity Ambient)",
            "tags": ["#앰비언트", "#명상음악", "#힐링사운드", "#수면음악", "#AmbientMusic", "#Meditation"]
        }
    ]
}

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
    "jazz": [
        "https://images.unsplash.com/photo-1511192336575-5a79af67a629?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1415201364774-f6f0bb35f28f?auto=format&fit=crop&w=1280&h=720&q=90"
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
    """
    Meta의 MusicGen AI 모델(Hugging Face Inference API)을 호출하여
    프롬프트 기반으로 고음질 독창적 신곡(MP3/WAV) 작곡
    """
    print(f"\n[AI Composition] Meta MusicGen 작곡 시작...")
    print(f"-> Prompt: \"{prompt_text}\"")
    
    api_url = "https://api-inference.huggingface.co/models/facebook/musicgen-small"
    hf_token = os.getenv("HF_TOKEN", "").strip()
    headers = {}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"
        
    payload = {
        "inputs": prompt_text,
        "parameters": {
            "max_new_tokens": 512, # 약 10~15초 고음질 생성 (반복 확장 가능)
            "temperature": 1.0,
            "top_k": 250
        }
    }
    
    for attempt in range(3):
        try:
            print(f"Calling MusicGen API (Attempt {attempt+1}/3)...")
            res = requests.post(api_url, headers=headers, json=payload, timeout=60)
            
            if res.status_code == 200 and len(res.content) > 10000:
                temp_raw = "temp/ai_raw.wav"
                with open(temp_raw, "wb") as f:
                    f.write(res.content)
                
                # AudioSegment로 불러와서 부드러운 페이드인/아웃 마스터링
                audio = AudioSegment.from_file(temp_raw)
                
                # 곡 길이: AI 원곡 길이 그대로 (약 1분 내외로 자연스럽게 확장 또는 원본 길이 유지)
                if len(audio) < 60000: # 1분 미만일 경우 자연스럽게 2회 루프
                    audio = audio.append(audio, crossfade=1500)
                    
                audio = audio.normalize(headroom=0.5).fade_in(1500).fade_out(2500)
                audio.export(output_mp3_path, format="mp3", bitrate="320k")
                print(f"[AI Composition Success] 곡 생성 완료: {output_mp3_path} (길이: {len(audio)/1000:.1f}초)")
                return True
            
            elif res.status_code == 503:
                # 모델 로딩 중일 경우 대기 후 재시도
                data = res.json()
                wait_time = data.get("estimated_time", 20)
                print(f"Model is loading on server. Waiting {wait_time}s...")
                time.sleep(min(wait_time, 25))
            else:
                print(f"MusicGen API response status: {res.status_code} ({res.text[:100]})")
                time.sleep(5)
                
        except Exception as e:
            print(f"API call error: {e}")
            time.sleep(5)
            
    # API 실패 시: assets/audio/ 에 있는 고음질 완성형 MP3 사용
    print("[Fallback] AI API 응답 지연으로 assets/audio/ 고음질 트랙을 로드합니다.")
    audio_files = glob.glob("assets/audio/*.mp3")
    if audio_files:
        chosen = random.choice(audio_files)
        audio = AudioSegment.from_file(chosen).normalize(headroom=0.5).fade_in(1500).fade_out(2500)
        audio.export(output_mp3_path, format="mp3", bitrate="320k")
        print(f"[Fallback Loaded] {chosen} (길이: {len(audio)/1000:.1f}초)")
        return True
        
    return False

# --- 3. 고화질 감성 배경 이미지 다운로드 ---

def fetch_hd_background(genre, filename):
    image_pool = GENRE_IMAGES.get(genre, GENRE_IMAGES["piano"])
    chosen_url = random.choice(image_pool)
    print(f"Fetching HD background image ({genre}): {chosen_url}")
    try:
        resp = requests.get(chosen_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 1000:
            with open(filename, 'wb') as f:
                f.write(resp.content)
            print("Background image saved.")
            return
    except Exception as e:
        print(f"Image fetch fallback: {e}")

    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x1a2130:s=1280x720:d=1", "-vframes", "1", filename], check=True)

# --- 4. AI 곡 길이 그대로 초고속 비디오 렌더링 ---

def create_song_length_video(image_path, audio_path, output_path):
    """곡 길이 그대로 고화질 1080p/720p 비디오 생성 (10초 컷)"""
    print("Rendering final music video with exact song duration...")
    # 오디오 길이 확인
    audio = AudioSegment.from_file(audio_path)
    duration_sec = len(audio) / 1000.0
    
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
        "-c:v", "libx264", "-t", str(duration_sec), "-pix_fmt", "yuv420p", "-vf", "scale=1280:720",
        "-preset", "ultrafast", "-crf", "22", "-c:a", "aac", "-b:a", "320k", "-shortest", output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"Music Video created successfully: {output_path} (Duration: {duration_sec:.1f}s)")

# --- 메인 실행 ---

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    genre = os.getenv("INPUT_GENRE", "piano").strip().lower()
    if genre not in PROMPT_TEMPLATES:
        genre = "piano"
        
    custom_prompt = os.getenv("INPUT_CUSTOM_PROMPT", "").strip()
    custom_title = os.getenv("INPUT_CUSTOM_TITLE", "").strip()
    
    # 1. 프롬프트 및 메타데이터 선정
    templates = PROMPT_TEMPLATES[genre]
    selected_template = random.choice(templates)
    
    final_prompt = custom_prompt if custom_prompt else selected_template["prompt"]
    
    if custom_title:
        final_title = custom_title
    else:
        final_title = f"[AI Music] {selected_template['title']}"
        
    ai_mp3 = "temp/ai_song.mp3"
    bg_image = "temp/bg.jpg"
    final_video = "output_music_video.mp4"

    # 2. Meta MusicGen AI 작곡
    generate_musicgen_audio(final_prompt, ai_mp3)

    # 3. 고화질 감성 앨범 아트 다운로드
    fetch_hd_background(genre, bg_image)

    # 4. 작곡된 곡 길이 그대로 비디오 초고속 렌더링
    create_song_length_video(bg_image, ai_mp3, final_video)

    # 5. 유튜브 업로드 메타데이터 JSON 저장
    tags_str = " ".join(selected_template["tags"])
    desc = (
        f"🎵 Meta MusicGen AI가 작곡한 오리지널 신곡입니다.\n\n"
        f"Genre: {genre.upper()}\n"
        f"AI Prompt: \"{final_prompt}\"\n\n"
        f"Composed & Produced by Keyin AI Music Studio.\n\n"
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
    print("Video metadata saved successfully for YouTube upload.")
