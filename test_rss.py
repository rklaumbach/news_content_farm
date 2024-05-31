from datetime import datetime, timedelta
import feedparser

rss_urls = {
    'world': [
        'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
        'http://feeds.bbci.co.uk/news/world/rss.xml',
        'https://www.aljazeera.com/xml/rss/all.xml',
    ],
    'business_finance': [
        'https://rss.nytimes.com/services/xml/rss/nyt/Business.xml',
        'https://www.marketwatch.com/rss/topstories',
        'https://www.ft.com/?format=rss',
        'https://www.cnbc.com/id/100003114/device/rss/rss.html',
    ],
    'technology': [
        'https://www.theverge.com/rss/index.xml',
        'https://www.wired.com/feed/rss',
        'https://www.cnet.com/rss/news/',
        'https://techcrunch.com/feed/',
        'https://www.engadget.com/rss.xml',
    ],
    'science': [
        'https://rss.nytimes.com/services/xml/rss/nyt/Science.xml',
        'https://www.livescience.com/feeds/all',
        'https://www.nationalgeographic.com/content/natgeo/en_us/science/_jcr_content/content/feed.rss',
        'https://rss.sciam.com/ScientificAmerican-Global',
        'https://www.nasa.gov/rss/dyn/breaking_news.rss',
        'https://www.newscientist.com/feed/home',
        'https://www.popsci.com/rss.xml',
        'https://www.nature.com/nature/articles?type=research&format=rss',
        'https://www.sciencedaily.com/rss/top/science.xml',
    ]
}


def print_article_counts(rss_urls):
    for category, urls in rss_urls.items():
        print(f"Category: {category}")
        for url in urls:
            feed = feedparser.parse(url)
            articles_last_day = 0
            for entry in feed.entries:
                if hasattr(entry, 'published_parsed'):
                    article_date = datetime(*entry.published_parsed[:6])
                    if article_date > datetime.now() - timedelta(days=1):
                        articles_last_day += 1
            print(f"URL: {url}")
            print(f"Total Articles from Last Day: {articles_last_day}")
        print("\n")

print_article_counts(rss_urls)
