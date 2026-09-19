import feedparser
import json
import re
import requests
import os
import urllib.parse

# Fetch API Key from GitHub Secrets
API_KEY = os.environ.get('SCRAPER_API_KEY')

if not API_KEY:
    print("Error: SCRAPER_API_KEY not found in environment variables!")
    exit(1)

# Using RSSHub URLs routed through ScraperAPI to bypass Cloudflare 403 blocks
sources = [
    'https://rsshub.app/facebook/page/Federal.BISE.Official',
    'https://rsshub.app/facebook/page/bbiseqta.edu.pk',
    'https://rsshub.app/facebook/page/BISEPonline',
    'https://rsshub.app/twitter/user/EduMinistryPK',
    'https://rsshub.app/twitter/user/PHEC_official'
]

required_words = ['ceremony', 'celebration', 'celebrations', 'celebrating', 'visit', 'expo', 'week', 'workshop', 'competition', 'sports', 'festival']
excluded_words = ['notification', 'notifications', 'achievement', 'announcement', 'update', 'ai generated', 'examination', 'exam', 'date sheet', 'datesheet', 'apply', 'schedule', 'fee', 'result', 'roll number']

gallery_data = {'General': []}

def process_item(image_url, caption):
    caption_lower = caption.lower()
    
    if any(word in caption_lower for word in excluded_words):
        return
        
    # The required event filter is currently disabled for testing
    # if not any(word in caption_lower for word in required_words):
    #     return

    event_name = 'General'
    match = re.search(r'(event|expo|week|workshop):\s*([a-zA-Z0-9\s]+)', caption, re.IGNORECASE)
    if match:
        event_name = match.group(2).strip().upper()

    if event_name not in gallery_data:
        gallery_data[event_name] = []
        
    if not any(img['url'] == image_url for img in gallery_data[event_name]):
        gallery_data[event_name].append({
            'url': image_url,
            'caption': caption.strip()
        })

for target_url in sources:
    # Route RSSHub through ScraperAPI
    encoded_url = urllib.parse.quote(target_url)
    scraper_url = f"http://api.scraperapi.com?api_key={API_KEY}&url={encoded_url}"
    
    try:
        # Extract the page name for clean console logging
        page_name = target_url.split('/')[-1]
        print(f"Fetching {page_name} via ScraperAPI...")
        
        response = requests.get(scraper_url, timeout=60)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries:
                image_url = ''
                
                if 'media_content' in entry and len(entry.media_content) > 0:
                    image_url = entry.media_content[0]['url']
                elif 'links' in entry:
                    for link in entry.links:
                        if link.get('rel') == 'enclosure' and 'image' in link.get('type', ''):
                            image_url = link.get('href')
                            break
                            
                if not image_url and 'content' in entry:
                    content_value = entry.content[0].value
                    match = re.search(r'<img[^>]+src="([^">]+)"', content_value)
                    if match:
                        image_url = match.group(1)
                
                caption = getattr(entry, 'title', '') + " " + getattr(entry, 'summary', '')
                caption = re.sub(r'<[^>]+>', '', caption)
                
                if image_url:
                    process_item(image_url, caption)
        else:
            print(f"Failed with status: {response.status_code}")
            
    except Exception as e:
        print(f"Error fetching data: {e}")

with open('gallery_data.json', 'w', encoding='utf-8') as f:
    json.dump(gallery_data, f, indent=4, ensure_ascii=False)
