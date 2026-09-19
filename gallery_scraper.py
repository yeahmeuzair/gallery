import feedparser
import json
import re

# 1. Real RSS Feed URLs
sources = [
    'https://rss.app/feeds/f8gwDR5UMtjRwgqE.xml',
    'https://rss.app/feeds/EVFiHoOYNTzFOTsu.xml',
    'https://rss.app/feeds/wEDpserXX52ZixzJ.xml',
    'https://rss.app/feeds/tzobQLUwCkEvsRbO.xml',
    'https://rss.app/feeds/eCF0mVZksIjdj4Lr.xml',
    'https://rss.app/feeds/7UrzKUUXoVYqf06J.xml'
]

# Expanded list to ensure all event types are captured
required_words = ['ceremony', 'celebration', 'celebrations', 'celebrating', 'visit', 'expo', 'week', 'workshop', 'competition', 'sports', 'festival']

# Expanded list to strictly block singular/plural notifications, exams, and forms
excluded_words = ['notification', 'notifications', 'achievement', 'announcement', 'update', 'ai generated', 'examination', 'exam', 'date sheet', 'datesheet', 'apply', 'schedule', 'fee', 'result', 'roll number']

gallery_data = {'General': []}

def process_item(image_url, caption):
    caption_lower = caption.lower()
    
    # Condition 1: Reject unwanted posts (Strict Mode ON)
    if any(word in caption_lower for word in excluded_words):
        return
        
    # Condition 2: MUST contain an event-related word (Re-enabled!)
    if not any(word in caption_lower for word in required_words):
        return

    # Extract Event Name if present
    event_name = 'General'
    match = re.search(r'(event|expo|week|workshop):\s*([a-zA-Z0-9\s]+)', caption, re.IGNORECASE)
    if match:
        event_name = match.group(2).strip().upper()

    if event_name not in gallery_data:
        gallery_data[event_name] = []
        
    # Prevent duplicate images from being added twice
    if not any(img['url'] == image_url for img in gallery_data[event_name]):
        gallery_data[event_name].append({
            'url': image_url,
            'caption': caption.strip()
        })

# Fetch Data from all boards
for url in sources:
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            image_url = ''
            # RSS.app handles images in media_content
            if 'media_content' in entry and len(entry.media_content) > 0:
                image_url = entry.media_content[0]['url']
            
            # Combine title and summary for the full caption
            caption = getattr(entry, 'title', '') + " " + getattr(entry, 'summary', '')
            
            # Clean up any messy HTML tags that RSS.app might include in the text
            caption = re.sub(r'<[^>]+>', '', caption)
            
            if image_url:
                process_item(image_url, caption)
    except Exception as e:
        print(f"Error fetching {url}: {e}")

# Save filtered output
with open('gallery_data.json', 'w', encoding='utf-8') as f:
    json.dump(gallery_data, f, indent=4, ensure_ascii=False)
