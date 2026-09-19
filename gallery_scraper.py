import feedparser
import json
import re

# 1. RSS Feed URLs (Use RSS.app to generate XML links for FB/X profiles)
sources = [
    'https://rss.app/feeds/v1.1/your_federal_fb_feed.xml',
    'https://rss.app/feeds/v1.1/your_quetta_fb_feed.xml',
    'https://rss.app/feeds/v1.1/your_peshawar_fb_feed.xml',
    'https://rss.app/feeds/v1.1/your_edu_x_feed.xml',
    'https://rss.app/feeds/v1.1/your_phec_x_feed.xml'
]

required_words = ['ceremony', 'celebration', 'celebrations', 'celebrating', 'visit']
excluded_words = ['notifications', 'achievement', 'announcement', 'update', 'ai generated', 'examination', 'date sheet', 'apply']

# Default category for pictures without event names
gallery_data = {'General': []}

def process_item(image_url, caption):
    caption_lower = caption.lower()
    
    # Condition 1: Exclude unwanted posts completely
    if any(word in caption_lower for word in excluded_words):
        return
        
    # Condition 2: Must contain at least one required word
    if not any(word in caption_lower for word in required_words):
        return

    # Extract Event Name if present (e.g., "Event: Students Week")
    event_name = 'General'
    match = re.search(r'(event|expo|week|workshop):\s*([a-zA-Z0-9\s]+)', caption, re.IGNORECASE)
    if match:
        event_name = match.group(2).strip().upper()

    if event_name not in gallery_data:
        gallery_data[event_name] = []
        
    gallery_data[event_name].append({
        'url': image_url,
        'caption': caption
    })

# Fetch Data from all boards
for url in sources:
    feed = feedparser.parse(url)
    for entry in feed.entries:
        # Fetching image and text. (Adjust based on how RSS.app formats your feed)
        image_url = entry.media_content[0]['url'] if 'media_content' in entry else ''
        caption = entry.title + " " + (entry.summary if 'summary' in entry else '')
        
        if image_url:
            process_item(image_url, caption)

# Save filtered output directly to the repo
with open('gallery_data.json', 'w', encoding='utf-8') as f:
    json.dump(gallery_data, f, indent=4, ensure_ascii=False)
