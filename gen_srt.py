import csv
import os
import sys
from datetime import datetime, timedelta
import whisper
import srt
from openai import OpenAI

def transcribe_audio_for_timing(audio_path):
    try:
        model = whisper.load_model("base")
    except AttributeError:
        raise ImportError("Could not load Whisper model. Ensure the Whisper library is installed correctly.")
    
    result = model.transcribe(audio_path)
    return result['segments']

def merge_texts(hook_text, tldr_text):
    return f"{hook_text} {tldr_text}"

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

def split_segment(segment):
    words = segment['text'].split()
    halfway = len(words) // 2

    first_half = ' '.join(words[:halfway])
    second_half = ' '.join(words[halfway:])

    start_time = segment['start']
    end_time = segment['end']
    duration = end_time - start_time
    half_duration = duration / 2

    first_segment = {
        'start': start_time,
        'end': start_time + half_duration,
        'text': first_half
    }

    second_segment = {
        'start': start_time + half_duration,
        'end': end_time,
        'text': second_half
    }

    return [first_segment, second_segment]

def create_srt_with_segments(segments, output_srt_path):
    subs = []

    for segment in segments:
        start = timedelta(seconds=segment['start'])
        end = timedelta(seconds=segment['end'])
        sub = srt.Subtitle(index=len(subs) + 1, start=start, end=end, content=segment['text'])
        subs.append(sub)

    srt_content = srt.compose(subs)

    with open(output_srt_path, 'w', encoding='utf-8') as f:
        f.write(srt_content)

    print(f"SRT file saved: {output_srt_path}")

def correct_spelling_and_punctuation(segments, merged_text, client):
    srt_text = ""
    for i, segment in enumerate(segments):
        start = str(timedelta(seconds=segment['start']))
        end = str(timedelta(seconds=segment['end']))
        srt_text += f"{i + 1}\n{start} --> {end}\n{segment['text']}\n\n"
    
    prompt = f"""
    Here is an input SRT file from an audio transcription:
    {srt_text}
    
    Correct the spelling and punctuation referencing the text below, to follow the transcription without changing the duration of each segment.:
    {merged_text}
    
    Output only the full, corrected spelling and punctuation SRT file matching the durations of the input SRT, 
    matching the spelling and punctuation of the provided text, formatted properly according to the standard SRT format.
    Don't use markdown or any other formatting. Just output pure text, line by line.
    
    Corrected SRT:
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    corrected_text = response.choices[0].message.content.strip()

    corrected_segments = []
    corrected_lines = corrected_text.split("\n\n")

    for line in corrected_lines:
        parts = line.split("\n")
        if len(parts) < 3:
            continue
        index = int(parts[0])
        time_range = parts[1].split(" --> ")
        start_time = time_range[0].strip()
        end_time = time_range[1].strip()

        def parse_time(time_str):
            time_parts = time_str.split(':')
            if len(time_parts) == 2:
                minutes, seconds = map(float, time_parts)
                return timedelta(minutes=minutes, seconds=seconds).total_seconds()
            elif len(time_parts) == 3:
                hours, minutes, seconds = map(float, time_parts)
                return timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()
            else:
                raise ValueError(f"Invalid time format: {time_str}")

        try:
            start = parse_time(start_time)
            end = parse_time(end_time)
        except ValueError:
            continue

        text = parts[2]
        corrected_segments.append({'start': start, 'end': end, 'text': text})

    return corrected_segments

def generate_srt(topic, csv_file, client, custom_date=None):
    ds = custom_date if custom_date else datetime.now().strftime('%Y-%m-%d')
    if not csv_file:
        # Automatically infer the most recent CSV file path
        csv_file_path = get_most_recent_file(f"output/{ds}/{topic}")
        if not csv_file_path:
            print("No CSV file found for SRT generation.")
            sys.exit(1)
    else:
        # Use the provided CSV file with the custom date (ds)
        csv_file_path = os.path.join("output", ds, topic, csv_file)

    if not os.path.isfile(csv_file_path):
        print(f"Error: CSV file '{csv_file_path}' not found.")
        sys.exit(1)

    # Extract date string from the CSV file path
    srt_output_dir = os.path.join("output", ds, topic, "srt")
    
    os.makedirs(srt_output_dir, exist_ok=True)

    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader):
            hook = row['Hook']
            tldr = row['TLDR']
            tts_file = os.path.join("output", ds, topic, "tts", f"tts_file_{i + 1}.mp3")
            if not os.path.isfile(tts_file):
                print(f"Error: TTS file '{tts_file}' not found.")
                continue

            segments = transcribe_audio_for_timing(tts_file)

            # Merge hook and TLDR for subtitle content
            merged_text = merge_texts(hook, tldr)

            # Correct the spelling and punctuation of the segments
            corrected_segments = correct_spelling_and_punctuation(segments, merged_text, client)

            # Split each segment into two
            new_segments = []
            for segment in corrected_segments:
                new_segments.extend(split_segment(segment))

            create_srt_with_segments(new_segments, os.path.join(srt_output_dir, f"srt_file_{i+1}.srt"))
            print(f"SRT file created: {os.path.join(srt_output_dir, f'srt_file_{i+1}.srt')}")

def get_most_recent_file(directory):
    files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    if not files:
        return None
    most_recent_file = max(files, key=os.path.getmtime)
    return most_recent_file
