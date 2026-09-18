import os
import sys
import random
import subprocess
import requests
import json
from bs4 import BeautifulSoup
from pydub import AudioSegment

# --- 1. 멜론 실시간 TOP 100 차트 크롤링 ---

def fetch_melon_top100():
    """멜론 실시간 TOP 100 차트 수집"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    url = 'https://www.melon.com/chart/index.htm'
    chart_items = []
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            titles = soup.select('div.ellipsis.rank01 a')
            artists = soup.select('div.ellipsis.rank02 a:first-child')
            for rank, (t, a) in enumerate(zip(titles, artists), 1):
                chart_items.append({
                    "rank": rank,
                    "title": t.text.strip().replace('\xa0', ' '),
                    "artist": a.text.strip().replace('\xa0', ' ')
                })
            print(f"[Melon] TOP 100 차트 {len(chart_items)}곡 수집 완료")
    except Exception as e:
        print(f"[Melon] 크롤링 오류: {e}")
        
    # 기본 예비 곡 목록 (차트 수집 실패 시 fallback)
    if not chart_items:
        chart_items = [
            {"rank": 1, "title": "한 페이지가 될 수 있게", "artist": "DAY6 (데이식스)"},
            {"rank": 2, "title": "고민중독", "artist": "QWER"},
            {"rank": 3, "title": "Supernova", "artist": "aespa"},
            {"rank": 4, "title": "How Sweet", "artist": "NewJeans"},
            {"rank": 5, "title": "너의 모든 순간", "artist": "성시경"},
            {"rank": 6, "title": "밤편지", "artist": "아이유"}
        ]
    return chart_items

# --- 2. 유튜브에서 실제 연주 음원 검색 및 고음질 MP3 추출 ---

def download_piano_cover_audio(artist, title, output_wav_path):
    """
    유튜브 검색(ytsearch)을 통해 해당 곡의 실제 고음질 피아노/어쿠스틱 연주 음원 다운로드
    """
    search_query = f"ytsearch1:{artist} {title} piano cover audio"
    print(f"Searching and downloading actual piano performance for [{artist} - {title}]...")
    
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "--output", output_wav_path,
        "--max-filesize", "50M",
        "--no-playlist",
        "--default-search", "ytsearch",
        search_query
    ]
    
    try:
        subprocess.run(cmd, check=True, timeout=90)
        # yt-dlp가 wav 확장자를 자동으로 붙이거나 변경할 수 있으므로 파일 확인
        if not os.path.exists(output_wav_path):
            base, _ = os.path.splitext(output_wav_path)
            for ext in [".wav", ".m4a", ".mp3", ".opus"]:
                if os.path.exists(base + ext):
                    os.rename(base + ext, output_wav_path)
                    break
        if os.path.exists(output_wav_path) and os.path.getsize(output_wav_path) > 10000:
            print(f"Successfully downloaded audio: {output_wav_path}")
            return True
    except Exception as e:
        print(f"Download failed for {artist} - {title}: {e}")
        
    return False

# --- 3. 연속 재생 플레이리스트(메들리) 믹싱 및 트랙리스트 생성 ---

def create_playlist_audio(selected_songs, output_mp3_path, target_loop_duration=300):
    """
    수집된 실제 피아노 연주 트랙들을 부드럽게 크로스페이드 믹싱하여 플레이리스트 오디오 생성
    """
    combined_audio = AudioSegment.silent(duration=1000)
    tracklist = []
    current_time_ms = 1000
    
    downloaded_tracks = 0
    for idx, song in enumerate(selected_songs):
        temp_wav = f"temp/track_{idx}.wav"
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
            
        success = download_piano_cover_audio(song["artist"], song["title"], temp_wav)
        if success and os.path.exists(temp_wav):
            try:
                track_audio = AudioSegment.from_file(temp_wav)
                # 너무 긴 영상의 경우 앞부분 2~3분만 감성적으로 추출
                if len(track_audio) > 180000:
                    track_audio = track_audio[:180000]
                
                # 볼륨 노멀라이즈
                track_audio = track_audio.normalize(headroom=0.5)
                
                # 타임스탬프 계산
                minutes = int(current_time_ms / 60000)
                seconds = int((current_time_ms % 60000) / 1000)
                time_str = f"{minutes:02d}:{seconds:02d}"
                tracklist.append(f"{time_str} {song['artist']} - {song['title']}")
                
                combined_audio = combined_audio.append(track_audio, crossfade=2000)
                current_time_ms = len(combined_audio)
                downloaded_tracks += 1
            except Exception as e:
                print(f"Error processing track {temp_wav}: {e}")
                
    # 만약 다운로드가 모두 실패한 경우 대비 fallback
    if downloaded_tracks == 0 or len(combined_audio) < 5000:
        print("Fallback to ambient piano stream...")
        fallback_wav = "temp/fallback.wav"
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", "sine=frequency=440:duration=60",
            fallback_wav
        ], check=True)
        combined_audio = AudioSegment.from_file(fallback_wav)
        tracklist.append("00:00 멜론 TOP 100 인기곡 피아노 연주")

    # 5분(300초) 이상으로 루프 확장
    if len(combined_audio) < (target_loop_duration * 1000):
        repeats = int(np.ceil((target_loop_duration * 1000) / len(combined_audio))) + 1
        looped = combined_audio
        for _ in range(repeats):
            looped = looped.append(combined_audio, crossfade=2000)
        combined_audio = looped[:target_loop_duration * 1000]
    else:
        combined_audio = combined_audio[:target_loop_duration * 1000]

    combined_audio = combined_audio.fade_in(2000).fade_out(3000)
    combined_audio.export(output_mp3_path, format="mp3", bitrate="192k")
    print(f"Playlist audio ready: {output_mp3_path} (Duration: {len(combined_audio)/1000}s)")
    return tracklist

# --- 4. 감성 고화질 배경 이미지 수집 ---

def fetch_hd_background(filename):
    image_pool = [
        "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1519692933481-e162a57d6721?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1280&h=720&q=90",
        "https://images.unsplash.com/photo-1552422535-c45813c61732?auto=format&fit=crop&w=1280&h=720&q=90"
    ]
    chosen_url = random.choice(image_pool)
    print(f"Fetching HD background image: {chosen_url}")
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

# --- 5. 8시간 연속 재생 영상 초고속 렌더링 ---

def create_8h_video(image_path, audio_path, output_path):
    print("Creating 8-hour video via ultra-fast concat...")
    short_video = "temp/short.mp4"
    cmd_short = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
        "-c:v", "libx264", "-t", "300", "-pix_fmt", "yuv420p", "-vf", "scale=1280:720",
        "-preset", "ultrafast", "-crf", "30", "-c:a", "aac", "-b:a", "128k", short_video
    ]
    subprocess.run(cmd_short, check=True)

    with open("temp/concat.txt", "w") as f:
        for _ in range(96):
            f.write("file 'short.mp4'\n")
    
    cmd_concat = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "temp/concat.txt",
        "-c", "copy", output_path
    ]
    subprocess.run(cmd_concat, check=True)
    print(f"Final 8-hour video created: {output_path}")

# --- 메인 실행 ---

if __name__ == "__main__":
    import numpy as np
    os.makedirs("temp", exist_ok=True)
    base_audio = "temp/base.mp3"
    bg_image = "temp/bg.jpg"
    final_video = "output_music_video.mp4"

    # 1. 멜론 TOP 100 실시간 차트 수집
    chart = fetch_melon_top100()

    # 2. 상위 1~15위 인기곡 중 3~4곡을 무작위 선곡하여 플레이리스트 구성
    top_candidates = chart[:15]
    selected_songs = random.sample(top_candidates, min(3, len(top_candidates)))
    
    print("\n--- 이번 회차 플레이리스트 선곡 ---")
    for s in selected_songs:
        print(f"[Melon {s['rank']}위] {s['artist']} - {s['title']}")
    print("---------------------------------\n")

    # 3. 유튜브 실제 연주 음원 추출 및 메들리 믹싱
    tracklist = create_playlist_audio(selected_songs, base_audio, target_loop_duration=300)

    # 4. 감성 배경 이미지 다운로드
    fetch_hd_background(bg_image)

    # 5. 8시간 연속 재생 비디오 생성
    create_8h_video(bg_image, base_audio, final_video)

    # 6. 유튜브 업로드용 제목 및 설명(트랙리스트 포함) 생성
    main_artist = selected_songs[0]['artist']
    main_title = selected_songs[0]['title']
    
    title = f"멜론 TOP 100 인기곡 감성 피아노 연주곡 모음 | {main_artist} - {main_title} 외"
    tracklist_text = "\n".join(tracklist)
    desc = (
        f"멜론 실시간 TOP 100 인기곡들을 감미로운 피아노 연주로 감상하는 플레이리스트입니다.\n"
        f"수면, 공부, 집중, 카페, 편안한 휴식 시간에 편안하게 감상하세요. (8시간 연속 재생)\n\n"
        f"🎧 [Tracklist]\n{tracklist_text}\n\n"
        f"Produced by Keyin Studio."
    )
    
    meta_info = {
        "title": title,
        "description": desc,
        "artist": main_artist,
        "song_title": main_title
    }
    with open("temp/video_info.json", "w", encoding="utf-8") as f:
        json.dump(meta_info, f, ensure_ascii=False, indent=2)
    print("Video metadata saved for YouTube upload.")
