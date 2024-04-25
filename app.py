from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from sumy.parsers.html import HtmlParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.utils import get_stop_words

app = Flask(__name__)

def fetch_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract text content
        parser = HtmlParser.from_string(response.text, url, Tokenizer('english'))
        summarizer = LsaSummarizer()
        summarizer.stop_words = get_stop_words('english')

        # Extract images
        images = [img['src'] for img in soup.find_all('img')]

        # Extract videos
        videos = [video['src'] for video in soup.find_all('video')]

        # Filter out privacy policy and other irrelevant information
        for script in soup(["script", "style", "meta", "noscript", "footer", "header", "nav", "form"]):
            script.extract()

        # Get text content
        content = ' '.join([p.get_text() for p in soup.find_all('p')])

        # Summarize the text content
        summary = summarizer(parser.document, 3)  # Summarize into 3 sentences

        return content, summary, images, videos
    except Exception as e:
        print(f"Error fetching content from {url}: {e}")
        return None, None, None, None

@app.route('/fetch_data', methods=['POST'])
def fetch_data():
    data = request.json
    query = data['query']
    max_urls = data.get('max_urls', 10)

    urls = fetch_urls(query, max_urls)
    response_data = []

    for url in urls:
        content, summary, images, videos = fetch_content(url)
        if content:
            response_data.append({
                'url': url,
                'summary': [str(sentence) for sentence in summary],
                'images': images,
                'videos': videos
            })

    return jsonify(response_data)

def fetch_urls(query, max_urls=10):
    search_url = f"https://www.google.com/search?q={query}"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    urls = []
    for link in soup.find_all('a'):
        url = link.get('href')
        if url.startswith('/url?q='):
            url = url.split('/url?q=')[1].split('&')[0]
            urls.append(url)
            if len(urls) >= max_urls:
                break

    return urls[:max_urls]

if __name__ == '__main__':
    app.run(debug=True)