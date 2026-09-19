import feedparser
import json
import re

# 1. Your 6 Custom FetchRSS Feed URLs
sources = [
    'https://fetchrss.com/feed/1x7tp94pp9101x7too9x38d0.rss',
    'https://fetchrss.com/feed/1x7tyP0ujCcE1x7uHi87oDDO.rss',
    'https://fetchrss.com/feed/1x7tyP0ujCcE1x7uKlAci92I.rss',
    'https://fetchrss.com/feed/1x7tyP0ujCcE1x7uLI8nM0zi.rss',
    'https://fetchrss.com/feed/1x7tyP0ujCcE1x7uLv9wWFta.rss',
    'https://fetchrss.com/feed/1x7tyP0ujCcE1x7uOG3Rh2c6.rss'
]

# Strict event keyword filter
required_words = ['ceremony', 'celebration', 'celebrations', 'celebrating', 'visit', 'expo', 'week', 'workshop', 'competition', 'sports', 'festival']

# Strict exclusion filter for text-heavy posts
excluded_words = ['notification', 'notifications', 'achievement', 'announcement', 'update', 'ai generated', 'examination', 'exam', 'date sheet', 'datesheet', 'apply', 'schedule', 'fee', 'result', 'roll number']

gallery_data = {'General': []}

def process_item(image_url, caption):
    caption_lower = caption.lower()
    
    # 1. Reject notifications and text banners
    if any(word in caption_lower for word in excluded_words):
        return
        
    # 2. MUST contain an event word
    # (If your JSON comes out empty again, comment these two lines out temporarily by adding a '#' at the start to test if the links have valid pictures)
    if not any(word in caption_lower for word in required_words):
        return

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

for url in sources:
    try:
        print(f"Fetching data from {url}...")
        feed = feedparser.parse(url)
        
        for entry in feed.entries:
            image_url = ''
            
            # FetchRSS handles image tags cleanly
            if 'media_content' in entry and len(entry.media_content) > 0:
                image_url = entry.media_content[0]['url']
            elif 'links' in entry:
                for link in entry.links:
                    if link.get('rel') == 'enclosure' and 'image' in link.get('type', ''):
                        image_url = link.get('href')
                        break
            
            # Fallback for images embedded in the description
            if not image_url and 'summary' in entry:
                match = re.search(r'<img[^>]+src="([^">]+)"', entry.summary)
                if match:
                    image_url = match.group(1)
            
            caption = getattr(entry, 'title', '') + " " + getattr(entry, 'summary', '')
            caption = re.sub(r'<[^>]+>', '', caption) 
            
            if image_url:
                process_item(image_url, caption)
                
    except Exception as e:
        print(f"Error fetching {url}: {e}")

with open('gallery_data.json', 'w', encoding='utf-8') as f:
    json.dump(gallery_data, f, indent=4, ensure_ascii=False)
    print("Gallery data successfully saved!")
