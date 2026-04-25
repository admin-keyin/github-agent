import os
import requests
from moviepy.editor import ImageClip, AudioFileClip
import sys

def download_file(url, filename):
    print(f"Downloading {url}...")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded: {filename}")
    else:
        print(f"Failed to download: {url}")
        sys.exit(1)

def generate_ai_image(prompt, filename):
    print(f"Generating AI image for prompt: {prompt}")
    # Pollinations.ai provides free AI images via URL
    encoded_prompt = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1920&height=1080&nologo=true&seed=42"
    download_file(url, filename)

def create_video(image_path, audio_path, output_path):
    print("Combining image and audio into video...")
    audio = AudioFileClip(audio_path)
    # Create image clip with the same duration as audio
    image_clip = ImageClip(image_path).set_duration(audio.duration)
    # Set the audio to the image clip
    video = image_clip.set_audio(audio)
    # Write the result to a file
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    print(f"Video created: {output_path}")

if __name__ == "__main__":
    # Example royalty-free music (Bensound or similar public sources)
    # Note: Using a direct link to a CC-BY or Public Domain track
    FREE_MUSIC_URL = "https://www.bensound.com/bensound-music/bensound-creativeminds.mp3" # Placeholder - user might need to update
    
    # Let's try a more reliable public domain source if possible, or just use a placeholder
    # For this demo, I'll use a known public URL
    music_url = os.getenv("MUSIC_URL", "https://cdn.pixabay.com/audio/2022/05/27/audio_180873748b.mp3") 
    image_prompt = os.getenv("IMAGE_PROMPT", "Beautiful cinematic landscape, lo-fi aesthetic, sunset, 4k")
    
    os.makedirs("temp", exist_ok=True)
    audio_file = "temp/music.mp3"
    image_file = "temp/background.jpg"
    video_file = "output_music_video.mp4"

    download_file(music_url, audio_file)
    generate_ai_image(image_prompt, image_file)
    create_video(image_file, audio_file, video_file)
