import csv
import os
import sys
from datetime import datetime
from openai import OpenAI

def generate_tts(topic, csv_file, client, custom_date=None):
    ds = custom_date if custom_date else datetime.now().strftime('%Y-%m-%d')
    if not csv_file:
        # Automatically infer the most recent CSV file path
        csv_file_path = get_most_recent_file(f"output/{ds}/{topic}")
        if not csv_file_path:
            print("No CSV file found for TTS generation.")
            sys.exit(1)
    else:
        # Use the provided CSV file with the custom date (ds)
        csv_file_path = os.path.join("output", ds, topic, csv_file)

    if not os.path.isfile(csv_file_path):
        print(f"Error: CSV file '{csv_file_path}' not found.")
        sys.exit(1)

    # Extract date string from the CSV file path
    tts_output_dir = os.path.join("output", ds, topic, "tts")
    
    os.makedirs(tts_output_dir, exist_ok=True)

    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader):
            hook = row['Hook']
            tldr = row['TLDR']
            full_text = f"{hook} {tldr}"
            file_name = os.path.join(tts_output_dir, f"tts_file_{i+1}.mp3")

            response = client.audio.speech.create(
                model="tts-1-hd",
                input=full_text,
                voice="alloy",
                response_format="mp3"
            )

            with open(file_name, "wb") as audio_file:
                audio_file.write(response.content)

            print(f"Saved TTS audio to {file_name}")

def get_most_recent_file(directory):
    files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    if not files:
        return None
    most_recent_file = max(files, key=os.path.getmtime)
    return most_recent_file
