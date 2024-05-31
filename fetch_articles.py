import os
import time
from datetime import datetime
import requests
import feedparser
from bs4 import BeautifulSoup
import json
import tiktoken

# Initialize the tokenizer
encoding = tiktoken.encoding_for_model("gpt-4o")

with open('keywords.json', 'r') as f:
    high_interest_keywords = json.load(f)

with open('rss_urls.json', 'r') as f:
    rss_urls = json.load(f)

def count_tokens(text):
    tokens = encoding.encode(text)
    return len(tokens)

def fetch_images_from_article(article_link, id, ds, topic, output_dir="article_images"):
    try:
        response = requests.get(article_link)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch article: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    image_urls = []

    for img_tag in soup.find_all('img'):
        img_url = img_tag.get('src')
        if img_url and img_url.startswith(('http://', 'https://')):
            image_urls.append(img_url)

    article_image_dir = os.path.join(output_dir, ds, topic, str(id))
    os.makedirs(article_image_dir, exist_ok=True)
    downloaded_images = []

    for i, img_url in enumerate(image_urls):
        try:
            img_response = requests.get(img_url)
            img_response.raise_for_status()
            img_filename = os.path.join(article_image_dir, f"img_{i}.png")
            with open(img_filename, 'wb') as img_file:
                img_file.write(img_response.content)
            downloaded_images.append(img_filename)
            print(f"Downloaded image: {img_filename}")
        except requests.RequestException as e:
            print(f"Failed to download image: {e}")

    return downloaded_images

def fetch_articles_from_rss(topic):
    print(f"Fetching articles for topic: {topic}")
    articles = []
    now = time.mktime(datetime.now().timetuple())
    one_day_ago = now - 24 * 3600

    for rss_url in rss_urls.get(topic, []):
        print(f"Parsing RSS feed: {rss_url}")
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            if 'published_parsed' in entry:
                published_time = time.mktime(entry.published_parsed)
                if published_time >= one_day_ago:
                    content = getattr(entry, 'description', None)
                    if content and count_tokens(content) <= 7000:
                        article = {
                            'title': entry.title,
                            'content': content,
                            'link': entry.link,
                            'published': datetime.fromtimestamp(published_time).strftime('%Y-%m-%d %H:%M:%S')
                        }
                        articles.append(article)
                    else:
                        print(f"Skipping article due to excessive length or missing description: {entry.title}")

    return articles

def fetch_and_save_images(top_articles, ds, topic):
    for article, score in top_articles:
        id = article['id']
        fetch_images_from_article(article['link'], id, ds, topic)
