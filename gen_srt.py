import whisper
import openai
import srt
from datetime import timedelta
import os
import argparse

def load_openai_api_key(filepath="openai_key.txt"):
    with open(filepath, "r") as file:
        return file.read().strip()

def transcribe_audio(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result['segments']

def split_text_to_segments(text, max_words=5):
    words = text.split()
    segments = []
    for i in range(0, len(words), max_words):
        segment_text = ' '.join(words[i:i+max_words])
        segments.append(segment_text)
    return segments

def create_srt_segments(whisper_segments, max_words=5):
    srt_segments = []
    for segment in whisper_segments:
        text_segments = split_text_to_segments(segment['text'], max_words)
        segment_duration = (segment['end'] - segment['start']) / len(text_segments)
        current_start = segment['start']
        for text in text_segments:
            current_end = current_start + segment_duration
            srt_segments.append({
                'start': current_start,
                'end': current_end,
                'text': text
            })
            current_start = current_end
    return srt_segments

def format_srt(segments):
    subtitles = []
    for i, segment in enumerate(segments):
        start = timedelta(seconds=segment['start'])
        end = timedelta(seconds=segment['end'])
        subtitles.append(srt.Subtitle(index=i+1, start=start, end=end, content=segment['text']))
    return srt.compose(subtitles)

def correct_srt_text(srt_text, original_text, api_key):
    openai.api_key = api_key
    prompt = f"""
    Here is an input SRT file from an audio transcription:
    {srt_text}
    
    Correct the spelling and punctuation referencing the text below, to follow the transcription without changing the duration of each segment.:
    {original_text}
    
    Output only the full, corrected spelling and punctuation SRT file matching the durations of the input SRT, 
    matching the spelling and punctuation of the provided text, formatted properly according to the standard SRT format.
    Don't use markdown or any other formatting. Just output pure text, line by line.
    
    Corrected SRT:
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    corrected_srt = response.choices[0].message['content'].strip()
    return corrected_srt

def generate_srt(date, topic, output_srt_path, start_from=1):
    api_key = load_openai_api_key()
    audio_dir = os.path.join("output", date, topic, "tts")
    audio_files = sorted([os.path.join(audio_dir, f) for f in os.listdir(audio_dir) if f.endswith('.mp3')])

    if not audio_files:
        print(f"No audio files found in {audio_dir}")
        return

    for i, audio_path in enumerate(audio_files[start_from-1:], start=start_from):
        whisper_segments = transcribe_audio(audio_path)
        srt_segments = create_srt_segments(whisper_segments)
        srt_text = format_srt(srt_segments)
        original_text = " ".join([segment['text'] for segment in whisper_segments])
        corrected_srt_text = correct_srt_text(srt_text, original_text, api_key)

        individual_srt_path = os.path.join(output_srt_path, f"srt_file_{i}.srt")
        with open(individual_srt_path, 'w', encoding='utf-8') as f:
            f.write(corrected_srt_text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate SRT files from audio using Whisper and GPT-4.')
    parser.add_argument('date', type=str, help='Date for the output files (format: YYYY-MM-DD).')
    parser.add_argument('topic', type=str, help='Topic for the output files.')
    parser.add_argument('output_srt_path', type=str, help='Path to the output SRT directory.')
    parser.add_argument('--start-from', type=int, default=1, help='Start index for SRT generation.')
    args = parser.parse_args()
    
    generate_srt(args.date, args.topic, args.output_srt_path, args.start_from)
