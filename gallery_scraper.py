import feedparser
import json
import re
import requests
import time

# Multiple community-hosted RSS-Bridge instances to bypass IP blocks
base_urls = [
    'https://rss-bridge.org/bridge01/',
    'https://bridge.suumitsu.eu/',
    'https://rss.it-kun.de/'
]

# The specific queries for your boards
queries = [
    '?action=display&bridge=Facebook&context=Facebook+Page&u=Federal.BISE.Official&media_type=all&format=Atom',
    '?action=display&bridge=Facebook&context=Facebook+Page&u=bbiseqta.edu.pk&media_type=all&format=Atom',
    '?action=display&bridge=Facebook&context=Facebook+Page&u=BISEPonline&media_type=all&format=Atom',
    '?action=display&bridge=Twitter&context=By+username&u=EduMinistryPK&format=Atom',
    '?action=display&bridge=Twitter&context=By+username&u=PHEC_official&format=Atom'
]

required_words = ['ceremony', 'celebration', 'celebrations', 'celebrating', 'visit', 'expo', 'week', 'workshop', 'competition', 'sports', 'festival']
excluded_words = ['notification', 'notifications', 'achievement', 'announcement', 'update', 'ai generated', 'examination', 'exam', 'date sheet', 'datesheet', 'apply', 'schedule', 'fee', 'result', 'roll number']

gallery_data = {'General': []}

def process_item(image_url, caption):
    caption_lower = caption.lower()
    
    if any(word in caption_lower for word in excluded_words):
        return
        
    # Filter abhi bhi comment kiya hua hai taake pehle data aana shuru ho
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

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
}

for query in queries:
    success = False
    for base in base_urls:
        url = base + query
        try:
            print(f"Trying to fetch from: {base}...")
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                
                if len(feed.entries) > 0:
                    print(f"Success! Fetched data from {base}")
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
                            
                    success = True
                    break # Data mil gaya, aagay rotation rok do aur next board par jao
                else:
                    print(f"Server {base} returned empty data. Trying next...")
            else:
                print(f"Failed with status {response.status_code}. Trying next...")
        except Exception as e:
            print(f"Error connecting to {base}: {e}")
        
        time.sleep(2) # Anti-spam delay
        
    if not success:
        print(f"WARNING: All servers failed for query: {query}")

with open('gallery_data.json', 'w', encoding='utf-8') as f:
    json.dump(gallery_data, f, indent=4, ensure_ascii=False)
