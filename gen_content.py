import argparse
from datetime import datetime
import os

from openai import OpenAI
from gen_csv import select_top_articles, generate_csv
from gen_tts import generate_tts
from gen_srt import generate_srt
from fetch_articles import fetch_articles_from_rss, fetch_and_save_images

def main(topic, top_n, tts_only, csv_only, srt_only, csv_file, custom_date=None):
    def load_api_key(file_path):
        return open(file_path, 'r').read().strip()
    
    openai_api_key = load_api_key("openai_key.txt")
    client = OpenAI(api_key=openai_api_key)
    
    ds = custom_date if custom_date else datetime.now().strftime("%Y-%m-%d")

    if not tts_only and not srt_only and not csv_only:
        # Fetch articles from the last day
        articles = fetch_articles_from_rss(topic)

        # Assign unique IDs to each article
        for i, article in enumerate(articles):
            article['id'] = i + 1

        # Select the top N articles based on score
        top_articles = select_top_articles(articles, topic, top_n)

        # Print selected top articles for visual check
        print("Selected Top Articles:")
        for article, score in top_articles:
            print(f"Title: {article['title']}, Score: {score}")

        # Fetch and save images for the top articles
        fetch_and_save_images(top_articles, ds, topic)

        # Generate CSV with top articles
        csv_file_path = generate_csv(top_articles, topic, client, ds)
        csv_file = os.path.basename(csv_file_path)


        # Generate TTS files for top articles
        generate_tts(topic, csv_file, client, ds)

        # Generate SRT files for top articles
        generate_srt(topic, csv_file, client, ds)

    elif csv_only:
        # Fetch articles from the last day
        articles = fetch_articles_from_rss(topic)

        # Assign unique IDs to each article
        for i, article in enumerate(articles):
            article['id'] = i + 1

        # Select the top N articles based on score
        top_articles = select_top_articles(articles, topic, top_n)

        # Print selected top articles for visual check
        print("Selected Top Articles:")
        for article, score in top_articles:
            print(f"Title: {article['title']}, Score: {score}")

        # Fetch and save images for the top articles
        fetch_and_save_images(top_articles, ds, topic)

        # Generate CSV with top articles
        csv_file_path = generate_csv(top_articles, topic, client, ds)
        
    elif tts_only:
        # Generate TTS files for top articles
        generate_tts(topic, csv_file, client, ds)

    elif srt_only:
        # Generate SRT files for top articles
        generate_srt(topic, csv_file, client, ds)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some articles.')
    parser.add_argument('topic', type=str, help='Topic to fetch articles')
    parser.add_argument('--top-n', type=int, default=10, help='Number of top articles to select')
    parser.add_argument('--tts-only', nargs='?', const=True, dest='tts_only', help='Generate TTS only, optionally provide CSV file name')
    parser.add_argument('--csv-only', action='store_true', help='Generate CSV only')
    parser.add_argument('--srt-only', nargs='?', const=True, dest='srt_only', help='Generate SRT only, optionally provide CSV file name')
    parser.add_argument('--date', type=str, help='Custom date for fetching articles and generating output (format: YYYY-MM-DD)')
    args = parser.parse_args()

    main(args.topic, args.top_n, args.tts_only, args.csv_only, args.srt_only,
         args.tts_only if isinstance(args.tts_only, str) else args.srt_only if isinstance(args.srt_only, str) else None,
         args.date)
