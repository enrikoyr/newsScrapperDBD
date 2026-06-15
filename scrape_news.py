import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import email.utils
import csv
import os
import re

DISTRICTS = [
    "Bengkayang", "Kapuas Hulu", "Kayong Utara", "Ketapang", "Kubu Raya", 
    "Landak", "Melawi", "Mempawah", "Sambas", "Sanggau", "Sekadau", 
    "Sintang", "Pontianak", "Singkawang"
]

def fetch_rss(query):
    encoded_query = urllib.parse.quote(query)
    url = f'https://news.google.com/rss/search?q={encoded_query}&hl=id&gl=ID&ceid=ID:id'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            return response.read()
    except Exception as e:
        print(f"Error fetching RSS for {query}: {e}")
        return None

def scrape_google_news():
    now = datetime.now(timezone.utc)
    one_day_ago = now - timedelta(days=1)
    
    unique_articles = {}
    
    # We do a general query, plus specific queries to make sure we don't miss local news
    queries = ['DBD OR dengue OR "demam berdarah"']
    for d in DISTRICTS:
        queries.append(f'(DBD OR dengue OR "demam berdarah") {d}')
        
    print(f"Fetching news...")
    for q in queries:
        xml_data = fetch_rss(q)
        if not xml_data:
            continue
            
        root = ET.fromstring(xml_data)
        for item in root.findall('.//item'):
            link = item.find('link').text
            if link not in unique_articles:
                pub_date_str = item.find('pubDate').text
                try:
                    pub_date = email.utils.parsedate_to_datetime(pub_date_str)
                except Exception:
                    continue
                
                if pub_date >= one_day_ago:
                    title = item.find('title').text or ""
                    description = item.find('description').text or ""
                    unique_articles[link] = {
                        'title': title,
                        'description': description,
                        'text': f"{title} {description}"
                    }

    print(f"Found {len(unique_articles)} unique DBD articles in the last 24 hours.")
    
    # Initialize counts
    counts = {d: 0 for d in DISTRICTS}
    
    # Count district mentions
    for article in unique_articles.values():
        text = article['text']
        for d in DISTRICTS:
            # Word boundary regex to ensure we match the exact district name
            if re.search(r'\b' + re.escape(d) + r'\b', text, re.IGNORECASE):
                counts[d] += 1
                
    # Prepare output directory
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    # Output to a daily CSV file
    daily_csv = os.path.join(output_dir, "dbd_kalbar_daily_counts.csv")
    with open(daily_csv, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['District', 'News Count'])
        for d in DISTRICTS:
            writer.writerow([d, counts[d]])
            
    print(f"Exported counts to {daily_csv}")
    for d, c in counts.items():
        print(f" - {d}: {c}")

if __name__ == '__main__':
    scrape_google_news()
