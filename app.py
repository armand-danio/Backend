from flask import Flask, render_template_string
import requests
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)

def get_verge_headlines():
    base_url = 'https://www.theverge.com'
    articles = []
    page_url = base_url

    while True:
        try:
            response = requests.get(page_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract all relevant <h2> and <a> tags
            titles = soup.find_all('h2')
            links = soup.find_all('a')

            titles_links = {}
            for h2 in titles:
                title_text = h2.get_text(strip=True)
                for a in links:
                    href = a.get('href')
                    if href and href.startswith('/'):
                        full_link = base_url + href
                        if title_text in a.get_text():
                            titles_links[title_text] = full_link

            for title, link in titles_links.items():
                article_response = requests.get(link)
                article_response.raise_for_status()
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                date_element = article_soup.find('time')

                if date_element:
                    date_string = date_element.get('datetime')
                    if date_string:
                        try:
                            date = datetime.fromisoformat(date_string[:-1])
                            if date >= datetime(2022, 1, 1):
                                articles.append((date, title, link))
                        except ValueError:
                            pass

            next_page = soup.find('a', class_='pagination-next')
            if not next_page or not next_page.get('href'):
                break

            next_page_url = next_page.get('href')
            page_url = base_url + next_page_url if not next_page_url.startswith('http') else next_page_url

        except requests.RequestException as e:
            break

    articles.sort(reverse=True, key=lambda x: x[0])
    return articles

@app.route('/')
def index():
    articles = get_verge_headlines()
    html = '''
    <html>
    <head>
        <title>Title Aggregator</title>
        <style>
            body { font-family: Arial, sans-serif; color: black; background-color: white; }
            h1 { text-align: center; }
            ul { list-style-type: none; padding: 0; }
            li { margin: 10px 0; }
            a { text-decoration: none; color: black; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <h1>Headlines from The Verge</h1>
        <ul>
            {% for date, title, link in articles %}
            <li><a href="{{ link }}" target="_blank">{{ title }}</a> - {{ date.strftime('%Y-%m-%d') }}</li>
            {% endfor %}
        </ul>
    </body>
    </html>
    '''
    return render_template_string(html, articles=articles)

if __name__ == '__main__':
    app.run(debug=True)
