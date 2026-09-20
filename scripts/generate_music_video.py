import os
import sys
import glob
import random
import subprocess
import json
import time
import requests
from pydub import AudioSegment

# --- 1. 무한 조합 동적 프롬프트 & 신박한 제목 생성 엔진 ---

INSTRUMENTS = {
    "piano": [
        "acoustic grand piano solo", "warm upright piano with soft felt dampers",
        "cinematic piano with subtle violin strings", "romantic jazz piano with delicate touches",
        "flowing arpeggio new age piano", "melancholic ballad piano with vintage studio room reverb"
    ],
    "lofi": [
        "warm Rhodes electric piano and cozy boom bap drums", "mellow nylon acoustic guitar and lo-fi hip hop beat",
        "vintage synth chords with gentle vinyl crackle and chill groove", "rainy ambient window sound with soft jazz piano chords",
        "deep warm 808 sub bass and relaxed soulful lofi melody"
    ],
    "citypop": [
        "80s Tokyo nighttime groove with funky slap bass and bright synth brass",
        "breezy seaside city pop with catchy electric guitar riffs and retro drums",
        "nostalgic analog synthesizers with upbeat 80s disco groove and sax accents"
    ],
    "jazz": [
        "laid-back bossa nova acoustic guitar with soft shaker rhythm",
        "smoky late-night jazz club trio with upright bass and brushed snare",
        "sweet lyrical saxophone over gentle acoustic jazz piano chords"
    ],
    "ambient": [
        "serene cosmic synth pads with 432Hz deep relaxation drone",
        "ethereal floating ambient soundscape with crystal harp overtones",
        "peaceful ocean waves and slow cinematic atmospheric pads"
    ]
}

MOODS = [
    "deeply emotional and nostalgic", "warm and cozy for deep relaxation",
    "peaceful and calming for sleep", "focus and inspiring for study and coding",
    "wistful and bittersweet", "dreamy and cinematic", "heartwarming and serene"
]

KEYS = ["C Major", "A Minor", "D Major", "B Minor", "G Major", "E Minor", "F Major", "D Minor", "Ab Major", "Eb Major"]
TEMPOS = {
    "piano": [60, 64, 68, 72, 76],
    "lofi": [70, 74, 78, 82],
    "citypop": [108, 114, 120],
    "jazz": [75, 80, 85, 90],
    "ambient": [48, 52, 56, 60]
}

# 신박하고 시적인 스토리형 제목 풀
POETIC_TITLE_PIECES = {
    "piano": [
        ("새벽 {h}시 {m}분", ["불 꺼진 방에서 너를 떠올리며", "나지막이 흐르는 피아노", "잊혀지지 않는 계절의 기억", "우리가 머물렀던 그 자리에"]),
        ("그때 너에게", ["하지 못했던 마지막 한마디", "전하지 못한 편지 한 장", "꼭 들려주고 싶었던 노래", "남겨둔 작은 온기"]),
        ("비 내리는 {w}", ["창가에 맺힌 너의 얼굴", "작은 우산 아래의 우리", "골목길 카페에서", "흘러나오는 선율"]),
        ("언젠가 우리가", ["다시 만날 수 있다면", "사랑이라 불렀던 날들의 끝", "서로를 기억하게 될 때", "지나온 계절을 돌아보며"])
    ],
    "lofi": [
        ("퇴근길 지하철 막차", ["이어폰 너머로 번지는 위로", "창밖으로 스쳐가는 도심의 불빛", "나를 다독이는 따뜻한 비트"]),
        ("새벽 2시", ["편의점 앞 흐린 가로등 아래", "어질러진 책상 위 식어버린 커피", "조용히 흘러가는 나만의 시간"]),
        ("잠들지 못하는 밤", ["창문 틈으로 스며드는 새벽 공기", "괜찮은 척 웃어넘긴 하루의 끝", "따뜻한 이불 속에서 듣는 노래"])
    ],
    "citypop": [
        ("자정이 넘은", ["한강 다리 위를 달리며", "네온사인 불빛 아래 너와 나만의 춤", "도심의 밤바람을 가르는 드라이브"]),
        ("80년대 서울의 밤", ["반짝이는 빌딩 숲과 너의 실루엣", "레트로 카세트테이프에서 흘러나오는 노래", "도시의 낭만이 가득한 밤"])
    ],
    "jazz": [
        ("골목길 모퉁이", ["작은 재즈 카페의 온기", "비 내리는 밤의 색소폰", "따뜻한 와인 한 잔과 흐르는 음악"]),
        ("늦은 밤 홀로 앉아", ["조용히 울리는 콘트라베이스", "피아노 건반 위로 흩어지는 생각들"])
    ],
    "ambient": [
        ("우주 끝자락에", ["혼자 멈춰선 고요의 순간", "숨결조차 닿지 않는 평온함", "별들의 속삭임이 머무는 곳"]),
        ("깊은 밤의 쉼표", ["모든 소음이 사라진 깊은 바닷속", "지친 마음을 감싸주는 고요한 숨결"])
    ]
}

GENRE_IMAGES = {
    "piano": [
        "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1519692933481-e162a57d6721?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1552422535-c45813c61732?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1280&h=720&q=90"
    ],
    "lofi": [
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=1280&h=720&q=90"
    ],
    "citypop": [
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=1280&h=720&q=90"
    ],
    "jazz": [
        "https://images.unsplash.com/photo-1511192336575-5a79af67a629?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1415201364774-f6f0bb35f28f?auto=format&fit=crop&w=1280&h=720&q=90"
    ],
    "ambient": [
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1280&h=720&q=90"
    ]
}

def build_dynamic_prompt_and_title(genre):
    """매번 100% 새로운 화음, 분위기, 템포의 동적 프롬프트 및 신박한 제목 생성"""
    inst = random.choice(INSTRUMENTS.get(genre, INSTRUMENTS["piano"]))
    mood = random.choice(MOODS)
    key = random.choice(KEYS)
    bpm = random.choice(TEMPOS.get(genre, [70]))
    
    # AI 프롬프트 (중복 방지 난수 텍스트 태그 포함)
    prompt = f"{inst}, in {key} key, {mood}, beautiful melodic progression, studio quality mastering, {bpm} bpm"
    
    # 신박한 제목 생성
    pieces = POETIC_TITLE_PIECES.get(genre, POETIC_TITLE_PIECES["piano"])
    prefix_template, suffixes = random.choice(pieces)
    
    # 시간/요일 변수 채우기
    prefix = prefix_template.format(
        h=random.choice([1, 2, 3, 4]),
        m=random.choice([12, 25, 34, 42, 51]),
        w=random.choice(["월요일", "수요일", "금요일", "주말 밤", "오후"])
    )
    suffix = random.choice(suffixes)
    title = f"{prefix}, {suffix}"
    
    return prompt, title, bpm, key

# --- 2. Meta MusicGen AI 작곡 API (Random Seed & No-Cache 강제 적용) ---

def generate_musicgen_audio(prompt_text, output_mp3_path):
    """
    무작위 시드(Random Seed) 및 캐시 무효화 헤더를 적용하여
    매 실행마다 완전히 새로운 멜로디와 화음의 곡 작곡
    """
    random_seed = random.randint(100000, 999999999)
    print(f"\n[AI MusicGen] 독창적 신곡 작곡 시작 (Seed: {random_seed})")
    print(f"-> Prompt: \"{prompt_text}\"")
    
    api_url = "https://api-inference.huggingface.co/models/facebook/musicgen-small"
    hf_token = os.getenv("HF_TOKEN", "").strip()
    
    # 캐시 방지 및 시드 설정
    headers = {
        "x-use-cache": "false", # 이전과 똑같은 파일 반환 방지!
        "Cache-Control": "no-cache"
    }
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"
        
    payload = {
        "inputs": prompt_text,
        "parameters": {
            "max_new_tokens": 512,
            "temperature": random.uniform(0.9, 1.2), # 창의성 조절
            "top_k": 250,
            "seed": random_seed # 매번 다른 곡 생성의 핵심!
        }
    }
    
    for attempt in range(3):
        try:
            res = requests.post(api_url, headers=headers, json=payload, timeout=60)
            if res.status_code == 200 and len(res.content) > 10000:
                temp_raw = "temp/ai_raw.wav"
                with open(temp_raw, "wb") as f:
                    f.write(res.content)
                audio = AudioSegment.from_file(temp_raw)
                
                # 자연스러운 1분 내외 완성형 트랙 구성
                if len(audio) < 55000:
                    audio = audio.append(audio, crossfade=1500)
                    
                audio = audio.normalize(headroom=0.5).fade_in(1500).fade_out(2500)
                audio.export(output_mp3_path, format="mp3", bitrate="320k")
                print(f"[AI MusicGen] 새로운 곡 작곡 완료: {len(audio)/1000:.1f}초")
                return True
            elif res.status_code == 503:
                time.sleep(15)
        except Exception as e:
            print(f"API Retry ({attempt+1}/3): {e}")
            time.sleep(5)
            
    # Fallback 로컬 음원 (만약 있을 경우)
    print("[Fallback] 로컬 음원을 가져옵니다.")
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
    audio = AudioSegment.from_file(audio_path)
    duration_sec = len(audio) / 1000.0
    safe_title = song_title.replace(":", " -").replace("'", "").replace('"', "")
    
    # 실시간 이퀄라이저 바 오버레이 필터
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
        print(f"[Visualizer Success] {output_path} (Duration: {duration_sec:.1f}s)")
    except Exception as e:
        print(f"Visualizer fallback simple render ({e})")
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
            "-c:v", "libx264", "-t", str(duration_sec), "-pix_fmt", "yuv420p", "-vf", "scale=1280:720",
            "-preset", "ultrafast", "-crf", "22", "-c:a", "aac", "-b:a", "320k", "-shortest", output_path
        ], check=True)

# --- 메인 실행 ---

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    genre_input = os.getenv("INPUT_GENRE", "").strip().lower()
    available_genres = ["piano", "lofi", "citypop", "jazz", "ambient"]
    
    # 장르가 비어있으면 랜덤 선택
    if genre_input not in available_genres:
        genre = random.choice(available_genres)
    else:
        genre = genre_input
        
    custom_prompt = os.getenv("INPUT_CUSTOM_PROMPT", "").strip()
    custom_title = os.getenv("INPUT_CUSTOM_TITLE", "").strip()
    
    # 1. 매번 100% 다른 동적 프롬프트 & 신박한 제목 생성
    auto_prompt, auto_title, bpm, key = build_dynamic_prompt_and_title(genre)
    
    final_prompt = custom_prompt if custom_prompt else auto_prompt
    final_title = custom_title if custom_title else f"[AI Music] {auto_title}"
    
    ai_mp3 = "temp/ai_song.mp3"
    bg_image = "temp/bg.jpg"
    final_video = "output_music_video.mp4"

    # 2. Random Seed & No-Cache 적용 AI 작곡
    generate_musicgen_audio(final_prompt, ai_mp3)

    # 3. 고화질 배경 이미지 다운로드
    fetch_hd_background(genre, bg_image)

    # 4. 음악에 반응하는 실시간 이퀄라이저 비디오 렌더링
    create_equalizer_music_video(bg_image, ai_mp3, final_title, final_video)

    # 5. 유튜브 메타데이터 JSON 저장
    desc = (
        f"🎧 {final_title}\n\n"
        f"Key: {key} | BPM: {bpm} | Genre: {genre.upper()}\n"
        f"AI Prompt: \"{final_prompt}\"\n\n"
        f"Composed & Visualized by Keyin AI Music Studio.\n\n"
        f"#{genre.upper()} #AIMusic #AI작곡 #감성음악 #이퀄라이저 #Visualizer #RelaxingMusic #MusicGen"
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
