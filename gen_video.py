import os
import random
import argparse
from PIL import Image
import numpy as np
from moviepy.editor import (
    VideoFileClip, concatenate_videoclips, ImageClip, TextClip, CompositeVideoClip,
    AudioFileClip, CompositeAudioClip, vfx, AudioClip
)
import pysrt
import pandas as pd

# Ensure ImageMagick is found by MoviePy
os.environ["IMAGE_MAGICK_BINARY"] = "/usr/bin/convert"  # Adjust this path as necessary

# Set the FFmpeg path to the correct binary
os.environ["FFMPEG_BINARY"] = "/usr/local/bin/ffmpeg"

# Set the font path to the local Montserrat-Bold font
FONT_PATH = 'fonts/Montserrat-Bold.ttf'

def load_subtitles(srt_file, max_words=7):
    subs = pysrt.open(srt_file)
    captions = []

    for sub in subs:
        start = sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds + sub.start.milliseconds / 1000.0
        end = sub.end.hours * 3600 + sub.end.minutes * 60 + sub.end.seconds + sub.end.milliseconds / 1000.0
        sub_texts = split_subtitle_text(sub.text, max_words)
        duration_per_chunk = (end - start) / len(sub_texts)

        for i, text in enumerate(sub_texts):
            chunk_start = start + i * duration_per_chunk
            chunk_end = chunk_start + duration_per_chunk
            captions.append({
                'start': chunk_start,
                'end': chunk_end,
                'text': text
            })

    return captions

def split_subtitle_text(sub_text, max_words=7):
    words = sub_text.split()
    split_text = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= max_words:
            split_text.append(" ".join(current_chunk))
            current_chunk = []

    if current_chunk:
        split_text.append(" ".join(current_chunk))

    return split_text

def create_caption_clips(caption, clip_size, font_path=FONT_PATH, fontsize=96, emphasis_fontsize=128, color='white', emphasis_color='yellow', stroke_color='black', stroke_width=4):
    words = caption['text'].split()
    duration_per_word = (caption['end'] - caption['start']) / len(words)
    clips = []

    for i in range(len(words)):
        # Create the clip for the current text without the last word
        if i > 0:
            preceding_text = " ".join(words[:i])
            preceding_clip = TextClip(
                preceding_text,
                font=font_path,
                fontsize=fontsize,
                color=color,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                size=clip_size,
                method='caption'
            ).set_position('center').set_start(caption['start'] + i * duration_per_word).set_duration(duration_per_word)
            clips.append(preceding_clip)
        
        # Create the clip for the last word
        last_word_clip = TextClip(
            words[i],
            font=font_path,
            fontsize=emphasis_fontsize,
            color=emphasis_color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            size=clip_size,
            method='caption'
        ).set_position('center').set_start(caption['start'] + i * duration_per_word).set_duration(duration_per_word)
        clips.append(last_word_clip)

    return clips

def filter_and_resize_images(image_paths):
    valid_images = []
    for image_path in image_paths:
        with Image.open(image_path) as img:
            print(f"Checking image {image_path} with resolution ({img.width}x{img.height})", flush=True)
            if img.width >= 540 and img.height >= 540 and img.width != 800 and img.height != 800:  # Engadget's logo sometimes appears as 800x800
                valid_images.append(image_path)
    
    if len(valid_images) > 3:
        valid_images = random.sample(valid_images, 3)
    
    resized_clips = []
    for image_path in valid_images:
        clip = ImageClip(image_path).resize(width=1080)
        # Ensure the image has three channels (RGB)
        if clip.img.ndim == 2:  # If the image is grayscale, convert to RGB
            clip = clip.fl_image(lambda img: np.stack([img] * 3, axis=-1))
        elif clip.img.shape[-1] == 1:  # Another grayscale check for single-channel images
            clip = clip.fl_image(lambda img: np.concatenate([img] * 3, axis=-1))
        if clip.h < 1920:
            top_margin = (1920 - clip.h) // 2
            bottom_margin = 1920 - clip.h - top_margin
            clip = clip.margin(top=top_margin, bottom=bottom_margin, color=(0, 0, 0))
        clip = clip.set_position(("center", "center"))
        clip = clip.fx(vfx.resize, lambda t: 1 + 0.03 * t)  # Apply a mild zoom effect
        resized_clips.append(clip.set_duration(5))  # Set each image clip to 5 seconds duration
    
    return resized_clips


def generate_silence(duration, fps=44100):
    # Create an array of zeros representing silence
    silent_array = [0] * int(duration * fps)
    
    def make_frame(t):
        return silent_array
    
    return AudioClip(make_frame, duration=duration, fps=fps)


def generate_video(topic, date_string, start_from):
    csv_path = f'output/{date_string}/{topic}/{topic}_{date_string}.csv'
    df = pd.read_csv(csv_path)
    tts_dir = f'output/{date_string}/{topic}/tts'
    srt_dir = f'output/{date_string}/{topic}/srt'
    video_output_dir = f'output/{date_string}/{topic}/video'
    images_base_dir = f'article_images/{date_string}/{topic}'

    # Ensure the output directory exists
    os.makedirs(video_output_dir, exist_ok=True)

    # Find all TTS and SRT files in the directories
    tts_files = [f for f in os.listdir(tts_dir) if f.endswith('.mp3')]
    srt_files = [f for f in os.listdir(srt_dir) if f.endswith('.srt')]

    # Ensure TTS and SRT directories are not empty and contain the same number of files
    if not tts_files or not srt_files or len(tts_files) != len(srt_files):
        print(f"Error: TTS or SRT files not found or do not match in '{tts_dir}' or '{srt_dir}'.")
        return

    stock_videos_dir = f'stock_videos/{topic}'
    if not os.path.isdir(stock_videos_dir):
        print(f"Error: Stock videos directory '{stock_videos_dir}' not found.")
        return

    # Load stock videos
    all_stock_videos = [os.path.join(stock_videos_dir, f) for f in os.listdir(stock_videos_dir) if os.path.isfile(os.path.join(stock_videos_dir, f))]

    for i in range(start_from - 1, len(df)):
        row = df.iloc[i]
        tts_file = os.path.join(tts_dir, f'tts_file_{i + 1}.mp3')
        srt_file = os.path.join(srt_dir, f'srt_file_{i + 1}.srt')
        article_id = row['ID']
        image_dir = os.path.join(images_base_dir, str(article_id))

        print(f"Processing article ID {article_id}", flush=True)

        if not os.path.exists(tts_file) or not os.path.exists(srt_file):
            print(f"Error: TTS or SRT file '{tts_file}' or '{srt_file}' does not exist.", flush=True)
            continue
        
        volume_scaling = {
            'technology': 0.2,
            'business': 0.2,
            'world': 0.2
        }

        tts_audio = AudioFileClip(tts_file)
        background_music = AudioFileClip(f"background_music_{topic}.mp3").volumex(volume_scaling[topic])

        combined_audio = CompositeAudioClip([background_music, tts_audio.set_start(0)])
        
        subtitles = load_subtitles(srt_file)
        total_duration = tts_audio.duration

        video_clips = []
        current_time = 0
        last_video = None  # Track the last used video to avoid immediate repetition

        # Check for images and insert them as the 1st, 3rd, and 5th clips if available
        image_clips = []
        if os.path.exists(image_dir):
            image_files = [os.path.join(image_dir, f) for f in os.listdir(image_dir) if f.endswith(('jpg', 'jpeg', 'png'))]
            print(f"Found image files for article ID {article_id}: {image_files}", flush=True)
            image_clips = filter_and_resize_images(image_files)
            print(f"Filtered and resized image clips: {len(image_clips)}", flush=True)

        if len(image_clips) >= 1:
            video_clips.append(image_clips[0])

        while current_time < total_duration:
            video_segment_path = random.choice(all_stock_videos)
            while video_segment_path == last_video:
                video_segment_path = random.choice(all_stock_videos)
            last_video = video_segment_path

            video_segment = VideoFileClip(video_segment_path).resize((1080, 1920))  # Ensure vertical HD

            if current_time + 5 > total_duration:
                segment_duration = total_duration - current_time
            else:
                segment_duration = 5

            video_segment = video_segment.subclip(0, segment_duration)
            video_segment = video_segment.set_start(current_time).set_duration(segment_duration)
            video_clips.append(video_segment)

            current_time += segment_duration

            if len(image_clips) >= 2 and len(video_clips) == 2:
                video_clips.append(image_clips[1])

            if len(image_clips) >= 3 and len(video_clips) == 4:
                video_clips.append(image_clips[2])

        # Concatenate video clips
        final_video = concatenate_videoclips(video_clips, method="compose")

        # Create caption clips with different settings for the first caption
        caption_clips = []
        for j, caption in enumerate(subtitles):
            caption_clips.extend(create_caption_clips(caption, final_video.size, fontsize=96, stroke_width=2))

        # Combine video and captions
        final_video = CompositeVideoClip([final_video, *caption_clips]).set_audio(combined_audio)
        final_video = final_video.set_duration(total_duration)

        # Write the final video with limited threads to avoid CPU overuse
        output_file = os.path.join(video_output_dir, f"video_file_{i + 1}.mp4")
        final_video.write_videofile(output_file, fps=30, codec='libx264', audio_codec='aac', temp_audiofile='temp-audio.m4a', remove_temp=True, threads=8, preset='ultrafast')
        #final_video.write_videofile(output_file, fps=30, codec='hevc_nvenc', audio_codec='aac', temp_audiofile='temp-audio.m4a', remove_temp=True, threads=4, preset='fast')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a video using TTS and SRT files.')
    parser.add_argument('topic', type=str, help='Topic for the video')
    parser.add_argument('--date', type=str, required=True, help='Date string for the files')
    parser.add_argument('--start-from', type=int, required=True, help='Index of the first video to start from (1-based index)')
    args = parser.parse_args()

    generate_video(args.topic, args.date, args.start_from)
