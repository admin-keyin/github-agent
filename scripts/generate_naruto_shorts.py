import os
import sys
import glob
import json
import random
import asyncio
import subprocess
import requests
import unicodedata
from pathlib import Path
from pydub import AudioSegment
from PIL import Image, ImageDraw, ImageFont

# --- 1. 나루토 대표 매치업 및 캐릭터 데이터베이스 ---

NARUTO_CHARACTERS = [
    "우치하 이타치", "페인 (텐도)", "지라이야 (선인 모드)", "나루토 (선인 모드)",
    "나루토 (쿠라마 링크)", "나미카제 미나토", "우치하 마다라", "센주 하시라마",
    "우치하 사스케 (윤회안)", "하타케 카카시 (카무이)", "마이트 가이 (8문 둔갑)",
    "우치하 오비토 (육도)", "사소리", "데이다라", "센주 토비라마",
    "오로치마루", "츠나데", "가아라", "킬러 비", "야쿠시 카부토 (선인)"
]

CURATED_MATCHUPS = [
    ("우치하 이타치", "페인 (텐도)"),
    ("지라이야 (선인 모드)", "나루토 (선인 모드)"),
    ("나미카제 미나토", "우치하 이타치"),
    ("사소리", "데이다라"),
    ("우치하 마다라", "센주 하시라마"),
    ("마이트 가이 (8문 둔갑)", "우치하 마다라"),
    ("하타케 카카시 (카무이)", "우치하 오비토 (육도)"),
    ("우치하 사스케 (윤회안)", "나루토 (쿠라마 링크)"),
    ("센주 토비라마", "나미카제 미나토"),
    ("오로치마루", "지라이야 (선인 모드)")
]

FALLBACK_MATCHUP_DB = {
    ("우치하 이타치", "페인 (텐도)"): {
        "matchup": {
            "character_a": "우치하 이타치",
            "character_b": "페인 (텐도)",
            "title": "이타치 VS 페인, 세계관 최강 눈싸움 승자는?!"
        },
        "stats": [
            {
                "category": "체술 (Taijutsu)",
                "winner": "character_a",
                "score": "1 - 0",
                "reason": "단도술과 순신술을 활용한 근접전 센스는 이타치의 근소 우위!",
                "duration": 2.5
            },
            {
                "category": "파괴력 (Destructive Power)",
                "winner": "character_b",
                "score": "1 - 1",
                "reason": "초신라천정과 지폭천성의 압도적 광역 파괴력은 페인의 압승!",
                "duration": 2.5
            },
            {
                "category": "환술 (Genjutsu)",
                "winner": "character_a",
                "score": "2 - 1",
                "reason": "츠쿠요미와 이자나미 보유, 환술 분야는 이타치 독점!",
                "duration": 2.5
            },
            {
                "category": "차크라량 (Chakra Pool)",
                "winner": "character_b",
                "score": "2 - 2",
                "reason": "지병으로 조루 차크라인 이타치 대비 우즈마키 혈통 나가토의 압도적 풀!",
                "duration": 2.5
            },
            {
                "category": "전투 지능 (Battle IQ)",
                "winner": "character_a",
                "score": "3 - 2",
                "reason": "카부토전과 지폭천성 파법을 즉석에서 간파한 천재적 두뇌!",
                "duration": 2.5
            }
        ],
        "final_verdict": {
            "winner": "character_b",
            "final_score": "PAIN WINS (High-Diff)",
            "narration": "환술과 지능으로 몰아붙여도 결국 육도의 시야 공유와 지폭천성을 버텨내긴 역부족! 최종 승자는 페인입니다.",
            "duration": 4.5
        }
    }
}


# --- 2. Gemini API를 통한 나루토 스탯 비교 JSON 생성 ---

def get_gemini_matchup_data(char_a, char_b, gemini_api_key=None):
    """
    Gemini Pro API를 호출하여 나루토 스탯 비교 JSON을 생성합니다.
    API 키가 없거나 실패할 경우, 스마트 알고리즘 밸런스 데이터를 반환합니다.
    """
    api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
    
    prompt = f"""
당신은 나루토 공식 파워밸런스 전문 분석가입니다.
아래 두 나루토 캐릭터의 1:1 진검승부 매치업을 분석하여 반드시 아래 JSON 형식으로만 응답하세요.

캐릭터 A: {char_a}
캐릭터 B: {char_b}

비교 항목(5개):
1. 체술 (Taijutsu)
2. 인술 및 파괴력 (Ninjutsu & Power)
3. 환술 (Genjutsu)
4. 차크라량 및 스태미나 (Chakra Pool)
5. 전투 지능 및 속도 (Battle IQ & Speed)

JSON 응답 스키마:
{{
  "matchup": {{
    "character_a": "{char_a}",
    "character_b": "{char_b}",
    "title": "{char_a} VS {char_b}, 과연 누가 이길까?"
  }},
  "stats": [
    {{
      "category": "스탯 카테고리 이름",
      "winner": "character_a 또는 character_b",
      "score": "현재 누적 스코어 (예: 1 - 0)",
      "reason": "해당 스탯 승리 이유 1줄 요약 (유튜브 숏츠용 자극적이고 재밌는 문장)",
      "duration": 2.5
    }}
  ],
  "final_verdict": {{
    "winner": "character_a 또는 character_b",
    "final_score": "최종 승자 영문 (예: {char_a} WINS 또는 {char_b} WINS)",
    "narration": "최종 승부 결론 및 내레이션 1~2문장 (댓글 논쟁 유도 멘트 포함)",
    "duration": 4.5
  }}
}}
"""

    if api_key:
        print(f"[Gemini Pro API] '{char_a} VS {char_b}' 스탯 비교 분석 요청 중...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "response_mime_type": "application/json"
            }
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                res_json = resp.json()
                text_content = res_json['candidates'][0]['content']['parts'][0]['text']
                data = json.loads(text_content)
                print("[Gemini Pro API] 스탯 분석 데이터 수신 성공!")
                return data
            else:
                print(f"[Gemini API Notice] Status {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[Gemini API Exception]: {e}")

    # Fallback 로직
    print(f"[Engine Fallback] '{char_a} VS {char_b}' 내장 밸런스 데이터로 생성합니다.")
    pair_key = (char_a, char_b)
    if pair_key in FALLBACK_MATCHUP_DB:
        return FALLBACK_MATCHUP_DB[pair_key]

    categories = [
        ("체술 (Taijutsu)", "체술 숙련도와 근접전 센스 격돌!"),
        ("인술 (Ninjutsu)", "비전 인술과 광역 파괴력 대결!"),
        ("환술 (Genjutsu)", "동술 및 정신계 환술 제어력!"),
        ("차크라량 (Chakra Pool)", "혈통과 차크라 유지력의 차이!"),
        ("전투 지능 (Battle IQ)", "전황을 뒤집는 전술적 두뇌 플레이!")
    ]

    stats = []
    score_a = 0
    score_b = 0
    for cat_name, desc in categories:
        winner = random.choice(["character_a", "character_b"])
        if winner == "character_a":
            score_a += 1
            win_name = char_a
        else:
            score_b += 1
            win_name = char_b
        stats.append({
            "category": cat_name,
            "winner": winner,
            "score": f"{score_a} - {score_b}",
            "reason": f"{win_name}의 압도적인 {cat_name} 우세! {desc}",
            "duration": 2.5
        })

    final_winner = "character_a" if score_a >= score_b else "character_b"
    final_win_name = char_a if final_winner == "character_a" else char_b
    return {
        "matchup": {
            "character_a": char_a,
            "character_b": char_b,
            "title": f"{char_a} VS {char_b}, 치열한 닌자 대전 승자는?!"
        },
        "stats": stats,
        "final_verdict": {
            "winner": final_winner,
            "final_score": f"{final_win_name} WINS!",
            "narration": f"치열한 접전 끝에 전술과 파괴력에서 앞선 {final_win_name}의 승리! 여러분의 생각은 어떠신가요?",
            "duration": 4.5
        }
    }


# --- 3. Edge-TTS & gTTS를 이용한 고음질 한국어 내레이션 음성 생성 ---

def generate_single_tts(text, output_file, voice="ko-KR-InJoonNeural"):
    """
    Edge-TTS를 시도하고, 실패 시 gTTS(Google TTS)로 완벽하게 폴백 생성합니다.
    """
    try:
        import edge_tts
        async def _edge():
            communicate = edge_tts.Communicate(text, voice, rate="+15%")
            await communicate.save(output_file)
        asyncio.run(_edge())
        if os.path.exists(output_file) and os.path.getsize(output_file) > 500:
            return
    except Exception as e:
        print(f"[Edge-TTS Retry with gTTS]: {e}")

    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang='ko')
        tts.save(output_file)
        print(f"[gTTS Success] {output_file}")
    except Exception as e2:
        print(f"[TTS Fallback Simple Tone]: {e2}")
        # 극단적 에러 시 무음 세그먼트 생성
        silent = AudioSegment.silent(duration=2500)
        silent.export(output_file, format="mp3")

def generate_voice_track(matchup_data, output_audio_path="temp/naruto_narration.mp3"):
    """
    각 스탯별 해설 및 최종 내레이션 TTS를 순차 결합하여 완성된 오디오 트랙을 생성합니다.
    """
    os.makedirs("temp/tts", exist_ok=True)
    combined_audio = AudioSegment.silent(duration=500) # 인트로 0.5초 여백

    # 1. 인트로 음성
    intro_text = f"{matchup_data['matchup']['character_a']} 대 {matchup_data['matchup']['character_b']}! 과연 승자는 누구일까요?"
    intro_path = "temp/tts/intro.mp3"
    generate_single_tts(intro_text, intro_path)
    intro_seg = AudioSegment.from_file(intro_path)
    combined_audio += intro_seg + AudioSegment.silent(duration=400)

    # 2. 각 스탯 음성
    for idx, stat in enumerate(matchup_data["stats"]):
        stat_text = f"{stat['category']}! {stat['reason']}"
        stat_path = f"temp/tts/stat_{idx}.mp3"
        generate_single_tts(stat_text, stat_path)
        stat_seg = AudioSegment.from_file(stat_path)
        combined_audio += stat_seg + AudioSegment.silent(duration=300)

    # 3. 최종 판정 음성
    final_text = f"최종 결과! {matchup_data['final_verdict']['narration']}"
    final_path = "temp/tts/final.mp3"
    generate_single_tts(final_text, final_path)
    final_seg = AudioSegment.from_file(final_path)
    combined_audio += final_seg + AudioSegment.silent(duration=600)

    combined_audio.export(output_audio_path, format="mp3", bitrate="192k")
    print(f"[TTS Complete] {output_audio_path} (총 길이: {len(combined_audio)/1000:.1f}초)")
    return len(combined_audio) / 1000.0


# --- 4. 캐릭터 카드 이미지 및 숏츠 프레임 생성기 (Pillow 1080x1920) ---

def get_font(size=40, bold=False):
    font_paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf" if bold else "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/nanum/NanumGothicBold.ttf" if bold else "/usr/share/fonts/nanum/NanumGothic.ttf",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/AppleSDGothicNeo.ttc"
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def create_character_avatar(char_name, size=(420, 560), is_top=True):
    """
    캐릭터 이미지가 assets/characters/에 있으면 로드하고, 없으면 나루토 테마의 멋진 아바타 카드를 생성합니다.
    """
    clean_name = char_name.split()[0].replace("(", "").replace(")", "")
    custom_img_paths = [
        f"assets/characters/{char_name}.png",
        f"assets/characters/{clean_name}.png",
        f"assets/characters/{char_name}.jpg",
        f"assets/characters/{clean_name}.jpg"
    ]
    for p in custom_img_paths:
        if os.path.exists(p):
            try:
                img = Image.open(p).convert("RGBA")
                img = img.resize(size, Image.Resampling.LANCZOS)
                return img
            except Exception:
                pass

    # 나루토 테마 일러스트 카드 (A: 붉은색/차크라, B: 푸른색/뇌절 번개 테마)
    img = Image.new("RGBA", size, (20, 20, 30, 255))
    draw = ImageDraw.Draw(img)
    bg_color = (180, 40, 30) if is_top else (30, 70, 180)
    draw.rounded_rectangle([10, 10, size[0]-10, size[1]-10], radius=24, fill=bg_color, outline=(255, 215, 0), width=4)
    
    font_char = get_font(size=44, bold=True)
    draw.text((size[0]//2, size[1]//2), char_name, font=font_char, fill=(255, 255, 255), anchor="mm")
    return img

def create_shorts_frame_png(matchup_data, step_idx, output_png_path, width=1080, height=1920):
    """
    1080x1920 숏츠 프레임 생성 (상단 Char A, 하단 Char B, 중앙 스탯/스코어)
    """
    img = Image.new("RGBA", (width, height), (12, 14, 20, 255))
    draw = ImageDraw.Draw(img)

    char_a = matchup_data["matchup"]["character_a"]
    char_b = matchup_data["matchup"]["character_b"]

    # 1. 상단 캐릭터 A 영역 (Y: 100 ~ 780)
    avatar_a = create_character_avatar(char_a, size=(500, 600), is_top=True)
    img.paste(avatar_a, ((width - 500)//2, 140), avatar_a)
    font_title = get_font(52, bold=True)
    draw.text((width//2, 80), char_a, font=font_title, fill=(255, 220, 100), anchor="mm")

    # 2. 하단 캐릭터 B 영역 (Y: 1140 ~ 1820)
    avatar_b = create_character_avatar(char_b, size=(500, 600), is_top=False)
    img.paste(avatar_b, ((width - 500)//2, 1180), avatar_b)
    draw.text((width//2, 1840), char_b, font=font_title, fill=(100, 220, 255), anchor="mm")

    # 3. 중앙 영역 (Y: 820 ~ 1100) - 스탯 / VS 뱃지 / 스코어
    draw.rounded_rectangle([60, 810, width-60, 1110], radius=28, fill=(10, 10, 15, 235), outline=(255, 215, 0), width=4)

    if step_idx < len(matchup_data["stats"]):
        curr_stat = matchup_data["stats"][step_idx]
        cat_text = curr_stat["category"]
        score_text = curr_stat["score"]
        reason_text = curr_stat["reason"]
        winner = curr_stat["winner"]

        font_cat = get_font(46, bold=True)
        font_score = get_font(60, bold=True)
        font_reason = get_font(32, bold=False)

        draw.text((width//2, 865), cat_text, font=font_cat, fill=(255, 215, 0), anchor="mm")
        
        # 승자 색상 표시
        score_color = (255, 80, 80) if winner == "character_a" else (80, 180, 255)
        draw.text((width//2, 945), f"SCORE: {score_text}", font=font_score, fill=score_color, anchor="mm")
        
        # 자막 사유
        draw.text((width//2, 1035), reason_text, font=font_reason, fill=(240, 240, 240), anchor="mm")
    else:
        # 최종 결과 프레임
        verdict = matchup_data["final_verdict"]
        font_verdict = get_font(54, bold=True)
        font_narr = get_font(30, bold=False)
        draw.text((width//2, 875), "🏆 FINAL VERDICT 🏆", font=font_verdict, fill=(255, 215, 0), anchor="mm")
        draw.text((width//2, 955), verdict["final_score"], font=font_verdict, fill=(255, 100, 100), anchor="mm")
        draw.text((width//2, 1040), verdict["narration"][:35] + "...", font=font_narr, fill=(230, 230, 230), anchor="mm")

    img.save(output_png_path, "PNG")


# --- 5. 숏츠 비디오 합성 및 렌더링 (1080x1920 MP4) ---

def render_naruto_shorts_video(matchup_data, voice_track, output_mp4="output_naruto_shorts.mp4"):
    """
    모든 프레임 이미지와 TTS 음성, BGM을 결합하여 1080x1920 세로형 숏츠 비디오를 생성합니다.
    """
    os.makedirs("temp/frames", exist_ok=True)
    num_stats = len(matchup_data["stats"])

    # 음성 전체 길이 확인
    voice_audio = AudioSegment.from_file(voice_track)
    total_voice_sec = len(voice_audio) / 1000.0

    # 1. 각 단계별 프레임 PNG 생성
    frame_files = []
    for i in range(num_stats):
        frame_path = f"temp/frames/frame_{i}.png"
        create_shorts_frame_png(matchup_data, i, frame_path)
        frame_files.append(frame_path)
    
    final_frame_path = f"temp/frames/frame_final.png"
    create_shorts_frame_png(matchup_data, num_stats, final_frame_path)
    frame_files.append(final_frame_path)

    # 2. FFmpeg concat 파일 생성 (음성 길이에 맞춰 각 스탯 및 최종 결과 씬 시간 분배)
    # 총 (num_stats + 1) 개 씬
    stat_duration = max(2.5, (total_voice_sec - 5.0) / num_stats)
    final_duration = 5.0

    concat_txt = "temp/frames/input.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for i in range(num_stats):
            f.write(f"file 'frame_{i}.png'\n")
            f.write(f"duration {stat_duration:.2f}\n")
        f.write(f"file 'frame_final.png'\n")
        f.write(f"duration {final_duration:.2f}\n")
        f.write(f"file 'frame_final.png'\n") # EOF 버그 방지

    # 3. BGM 준비 (assets/audio/music/*.mp3 또는 생성된 음원 루프)
    bgm_files = glob.glob("assets/audio/music/*.mp3") + glob.glob("assets/audio/*/*.mp3")
    bgm_path = random.choice(bgm_files) if bgm_files else None

    # 4. FFmpeg 비디오 렌더링
    video_temp = os.path.abspath("temp/video_no_audio.mp4")
    concat_abs = os.path.abspath(concat_txt)
    cmd_video = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_abs,
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-preset", "ultrafast",
        video_temp
    ]
    subprocess.run(cmd_video, check=True, cwd="temp/frames")

    # 5. 음성 + BGM 볼륨 믹싱 및 최종 MP4 출력
    if bgm_path and os.path.exists(bgm_path):
        filter_audio = "[1:a]volume=1.0[v_voice];[2:a]volume=0.25,aloop=loop=-1:size=2e+09[v_bgm];[v_voice][v_bgm]amix=inputs=2:duration=first[aout]"
        cmd_final = [
            "ffmpeg", "-y",
            "-i", video_temp,
            "-i", voice_track,
            "-i", bgm_path,
            "-filter_complex", filter_audio,
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", output_mp4
        ]
    else:
        cmd_final = [
            "ffmpeg", "-y",
            "-i", video_temp,
            "-i", voice_track,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", output_mp4
        ]

    subprocess.run(cmd_final, check=True)
    print(f"\n=======================================================")
    print(f" [Naruto VS Shorts Render Success!]")
    print(f" [Output File] {output_mp4} (1080x1920 Shorts)")
    print(f"=======================================================\n")


# --- 6. 메인 실행 진입점 ---

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)

    input_char_a = os.getenv("INPUT_CHAR_A", "").strip()
    input_char_b = os.getenv("INPUT_CHAR_B", "").strip()

    # 캐릭터 선택 (미지정 시 대표 매치업에서 자동 추첨)
    if input_char_a and input_char_b:
        char_a = input_char_a
        char_b = input_char_b
    else:
        char_a, char_b = random.choice(CURATED_MATCHUPS)

    print(f"\n[Naruto Matchup Selected] '{char_a}' VS '{char_b}'")

    # 1. Gemini Pro 스탯 분석 JSON 생성
    matchup_data = get_gemini_matchup_data(char_a, char_b)

    # 2. Edge-TTS 내레이션 음성 생성
    voice_track = "temp/naruto_narration.mp3"
    voice_duration = generate_voice_track(matchup_data, voice_track)

    # 3. 1080x1920 숏츠 비디오 합성
    output_video = "output_naruto_shorts.mp4"
    render_naruto_shorts_video(matchup_data, voice_track, output_video)

    # 4. 유튜브 숏츠 업로드용 메타데이터 JSON 저장
    final_title = f"{matchup_data['matchup']['title']} #Shorts"
    desc = (
        f"🔥 {char_a} VS {char_b} 나루토 세기의 대결!\n\n"
        f"과연 승자는 누구일까요? 여러분의 의견을 댓글로 남겨주세요!\n\n"
        f"#{char_a.replace(' ', '')} #{char_b.replace(' ', '')} #나루토 #가상대결 #나루토쇼츠 #애니쇼츠 #Shorts #Naruto"
    )

    meta_info = {
        "title": final_title[:100],
        "description": desc,
        "artist": "Naruto VS Studio",
        "song_title": final_title
    }
    with open("temp/video_info.json", "w", encoding="utf-8") as f:
        json.dump(meta_info, f, ensure_ascii=False, indent=2)
    print(f"[Metadata Saved] {final_title}")
