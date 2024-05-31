import csv
import os
import json
import tiktoken
from fetch_articles import count_tokens

# Initialize the tokenizer
encoding = tiktoken.encoding_for_model("gpt-4o")

with open('keywords.json', 'r') as f:
    high_interest_keywords = json.load(f)

def score_article(article, topic):
    score = 0
    title = article['title'].lower()
    content = article['content'].lower()

    keywords = high_interest_keywords.get(topic, [])
    matching_keywords = []

    for keyword in keywords:
        keyword_count = title.count(keyword) + content.count(keyword)
        if keyword_count > 0:
            matching_keywords.append((keyword, keyword_count))
            score += keyword_count

    print(f"Title: {article['title']}\nScore: {score}\nMatching Keywords: {matching_keywords}\n")
    
    return score

def select_top_articles(articles, topic, top_n=10):
    scored_articles = [(article, score_article(article, topic)) for article in articles]
    scored_articles.sort(key=lambda x: x[1], reverse=True)
    
    for article, score in scored_articles:
        print(f"Article Title: {article['title']}\nScore: {score}\n")
    
    return scored_articles[:top_n]

def generate_hook_and_tldr(article, client):
    title = article['title']
    content = article['content']
    
    # Truncate content if it's too long
    max_content_length = 7000  # Token limit for content
    if count_tokens(content) > max_content_length:
        content = encoding.decode(encoding.encode(content)[:max_content_length]) + "..."

    prompt = f"""
    Based on the following article, generate a hook and a TLDR summary optimized for short-form video.
    Requirements:
    - Hook: An enticing, stimulating, engaging, concise text to grab the viewer's attention. Avoid filler words.
    - TLDR: A brief, but comprehensive summary of the article in a few sentences. Fully summarize the article content in a concise, yet engaging manner.
        Roughly 60 - 75 words or 30 - 40 seconds of speech.
        End with a question directed at viewers or a cliffhanger relevant to the article, which you suggest they read more about. 
        Mention the article link is in the description.
        Include call to action, a suggestion for viewers to like, comment, and follow for more news.

    Title: {title}
    Content: {content}

    Provide the output in the following format:
    Hook: [concise, stimulating, engaging text]
    TLDR: [summary]
    
    Example:
    Hook: Can You Believe Pixar's Shocking Decision Amid Creative Struggles?
    TLDR: Struggling both creatively and at the box office, Pixar will lay off workers and stop producing original content for Disney+. Facing significant challenges, the animation studio is now shifting its focus away from new Disney+ shows to potentially regain its former glory. This move aims to stabilize and revitalize Pixar's creative output. Remember to like, comment your opinion, and follow for more updates!
    """

    print(f"Generating hook and TLDR for article: {title}")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    generated_text = response.choices[0].message.content.strip()
    print(f"Generated hook and TLDR for article: {title}")
    return generated_text

def generate_csv(top_articles, topic, client, ds):
    csv_rows = [["ID", "Hook", "TLDR", "Title", "Description", "Score"]]
    
    for article, score in top_articles:
        generated_text = generate_hook_and_tldr(article, client)
        if generated_text and 'TLDR:' in generated_text:
            hook, tldr = generated_text.split('TLDR:', 1)
            hook = hook.replace('Hook:', '').strip()
            tldr = tldr.strip()
            csv_row = [
                article['id'],  # Add article ID as the primary key
                hook,
                tldr,
                article['title'].strip(),
                f"#news #{topic}news {article['link'].strip()}",
                score
            ]
            csv_rows.append(csv_row)
        else:
            print(f"Skipping article: {article['title']} due to generation error")

    output_csv_path = f"output/{ds}/{topic}/{topic}_{ds}.csv"
    
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    with open(output_csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        for row in csv_rows:
            writer.writerow(row)

    print(f"CSV file generated: {output_csv_path}")
    return output_csv_path
