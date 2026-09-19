import feedparser
import json
import re
import requests

# 1. 100% Free Lifetime RSS-Bridge URLs
sources = [
    # Federal Board FB
    'https://rss-bridge.org/bridge01/?action=display&bridge=Facebook&context=Facebook+Page&u=Federal.BISE.Official&media_type=all&format=Atom',
    # Quetta Board FB
    'https://rss-bridge.org/bridge01/?action=display&bridge=Facebook&context=Facebook+Page&u=bbiseqta.edu.pk&media_type=all&format=Atom',
    # Peshawar Board FB
    'https://rss-bridge.org/bridge01/?action=display&bridge=Facebook&context=Facebook+Page&u=BISEPonline&media_type=all&format=Atom',
    # EduMinistry X
    'https://rss-bridge.org/bridge01/?action=display&bridge=Twitter&context=By+username&u=EduMinistryPK&format=Atom',
    # PHEC X
    'https://rss-bridge.org/bridge01/?action=display&bridge=Twitter&context=By+username&u=PHEC_official&format=Atom'
]

# Strict event keyword filter
required_words = ['ceremony', 'celebration', 'celebrations', 'celebrating', 'visit', 'expo', 'week', 'workshop', 'competition', 'sports', 'festival']

# Strict exclusion filter for text-heavy posts
excluded_words = ['notification', 'notifications', 'achievement', 'announcement', 'update', 'ai generated', 'examination', 'exam', 'date sheet', 'datesheet', 'apply', 'schedule', 'fee', 'result', 'roll number']

gallery_data = {'General': []}

def process_item(image_url, caption):
    caption_lower = caption.lower()
    
    # Condition 1: Strict rejection of notifications/forms
    if any(word in caption_lower for word in excluded_words):
        return
        
    # Condition 2: MUST contain an event-related word 
    # (DISABLED FOR NOW TO TEST IF DATA IS FETCHING - Remove the '#' below to enable later)
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

# Masking the script as a real browser to bypass RSS-Bridge blocks
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
}

for url in sources:
    try:
        # Using requests to get the feed content safely
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status() # Check for HTTP errors like 403 or 500
        
        feed = feedparser.parse(response.content)
        
        for entry in feed.entries:
            image_url = ''
            
            # Upgrade: Bulletproof Image Extraction
            # 1. Try standard media content
            if 'media_content' in entry and len(entry.media_content) > 0:
                image_url = entry.media_content[0]['url']
            # 2. Try enclosures
            elif 'links' in entry:
                for link in entry.links:
                    if link.get('rel') == 'enclosure' and 'image' in link.get('type', ''):
                        image_url = link.get('href')
                        break
            # 3. Aggressively parse HTML content for embedded image tags
            if not image_url and 'content' in entry:
                content_value = entry.content[0].value
                match = re.search(r'<img[^>]+src="([^">]+)"', content_value)
                if match:
                    image_url = match.group(1)
            
            # Combine title and summary for the full text check
            caption = getattr(entry, 'title', '') + " " + getattr(entry, 'summary', '')
            caption = re.sub(r'<[^>]+>', '', caption) # Clean HTML tags
            
            if image_url:
                process_item(image_url, caption)
                
    except Exception as e:
        print(f"Error fetching {url}: {e}")

with open('gallery_data.json', 'w', encoding='utf-8') as f:
    json.dump(gallery_data, f, indent=4, ensure_ascii=False)
