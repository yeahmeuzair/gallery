import feedparser
import json
import re
import requests
import time

# Robust Fallback System using RSSHub and Nitter
# Format: ['Primary_URL', 'Backup_URL']
sources = [
    # Federal Board FB
    ['https://rsshub.app/facebook/page/Federal.BISE.Official', 'https://rsshub.feedox.com/facebook/page/Federal.BISE.Official'],
    # Quetta Board FB
    ['https://rsshub.app/facebook/page/bbiseqta.edu.pk', 'https://rsshub.feedox.com/facebook/page/bbiseqta.edu.pk'],
    # Peshawar Board FB
    ['https://rsshub.app/facebook/page/BISEPonline', 'https://rsshub.feedox.com/facebook/page/BISEPonline'],
    # EduMinistry X (Twitter)
    ['https://nitter.privacydev.net/EduMinistryPK/rss', 'https://rsshub.app/twitter/user/EduMinistryPK'],
    # PHEC X (Twitter)
    ['https://nitter.privacydev.net/PHEC_official/rss', 'https://rsshub.app/twitter/user/PHEC_official']
]

# Filters
required_words = ['ceremony', 'celebration', 'celebrations', 'celebrating', 'visit', 'expo', 'week', 'workshop', 'competition', 'sports', 'festival']
excluded_words = ['notification', 'notifications', 'achievement', 'announcement', 'update', 'ai generated', 'examination', 'exam', 'date sheet', 'datesheet', 'apply', 'schedule', 'fee', 'result', 'roll number']

gallery_data = {'General': []}

def process_item(image_url, caption):
    caption_lower = caption.lower()
    
    if any(word in caption_lower for word in excluded_words):
        return
        
    # Filter abhi bhi comment (disabled) hai testing ke liye
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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml'
}

for url_list in sources:
    success = False
    for url in url_list:
        try:
            print(f"Trying to fetch: {url}")
            response = requests.get(url, headers=headers, timeout=20)
            
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                
                if len(feed.entries) > 0:
                    print(f"Success! Fetched data from {url}")
                    for entry in feed.entries:
                        image_url = ''
                        
                        # 1. Media Content
                        if 'media_content' in entry and len(entry.media_content) > 0:
                            image_url = entry.media_content[0]['url']
                        # 2. Enclosures
                        elif 'links' in entry:
                            for link in entry.links:
                                if link.get('rel') == 'enclosure' and 'image' in link.get('type', ''):
                                    image_url = link.get('href')
                                    break
                        # 3. HTML parsing (RSSHub and Nitter put images inside the description)
                        if not image_url and ('content' in entry or 'summary' in entry):
                            content_value = entry.content[0].value if 'content' in entry else entry.summary
                            match = re.search(r'<img[^>]+src="([^">]+)"', content_value)
                            if match:
                                image_url = match.group(1)
                        
                        caption = getattr(entry, 'title', '') + " " + getattr(entry, 'summary', '')
                        caption = re.sub(r'<[^>]+>', '', caption)
                        
                        if image_url:
                            process_item(image_url, caption)
                            
                    success = True
                    break # Agar data mil gaya, toh backup URL try karne ki zaroorat nahi
                else:
                    print(f"Empty feed from {url}. Trying backup URL...")
            else:
                print(f"Failed with status {response.status_code}. Trying backup URL...")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        
        time.sleep(2) # Anti-spam delay
        
    if not success:
        print(f"WARNING: All fallback URLs failed for this specific board.")

with open('gallery_data.json', 'w', encoding='utf-8') as f:
    json.dump(gallery_data, f, indent=4, ensure_ascii=False)
