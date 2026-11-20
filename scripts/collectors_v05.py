"""Two-stage discovery for event listing pages. Standard library-friendly and testable."""
import json
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

EVENT_PATH = re.compile(r'/(?:events?|e|shows?|concerts?|tickets?|calendar|speed-dating|singles|dating|performances?)/|/\d{7,}(?:/|$)', re.I)
BLOCKED = re.compile(r'/(?:login|signup|register|account|privacy|terms|contact|about|blog|category|tags?|feed|wp-admin)(?:/|$)', re.I)
SINGLES = re.compile(r'\b(single[s]?|speed[ -]?dat(?:e|ing)|matchmak(?:er|ing)|dating|meet[ -]?cute|singles mixer|queer dating)\b', re.I)
SOCIAL = re.compile(r'\b(trivia|meetup|social|mixer|game night|board game|make friends|community gathering)\b', re.I)


def clean_link(href, base):
    if not href or href.startswith(('#','mailto:','tel:','javascript:')): return ''
    u, _ = urldefrag(urljoin(base, href))
    p = urlparse(u)
    if p.scheme not in ('https','http') or not p.netloc: return ''
    return u


def event_candidates(html, base, limit=18, source_kind='general'):
    """Find likely event *detail* pages, not generic calendar homepages."""
    soup = BeautifulSoup(html, 'html.parser')
    found = {}
    base_host = urlparse(base).hostname or ''
    for a in soup.select('a[href]'):
        url = clean_link(a.get('href'), base)
        if not url: continue
        p = urlparse(url)
        path = p.path.lower()
        if BLOCKED.search(path) or url.rstrip('/') == base.rstrip('/'): continue
        label = a.get_text(' ', strip=True)[:160]
        if not label:
            img = a.find('img', alt=True)
            label = img.get('alt', '') if img else ''
        nearby = a.find_parent(['article', 'li'])
        context = (nearby.get_text(' ', strip=True) if nearby else label)[:400]
        score = 0
        if EVENT_PATH.search(path): score += 3
        if re.search(r'/(?:20\d\d/\d\d|\d{4,}|[^/]{14,}-[^/]{6,})', path): score += 1
        if re.search(r'\b(tickets?|rsvp|details|buy|register|event)\b', label, re.I): score += 1
        if re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2}\b', context, re.I): score += 2
        if source_kind == 'singles' and SINGLES.search(label+' '+context): score += 3
        if p.hostname != base_host and not EVENT_PATH.search(path): score -= 3
        if score < (3 if source_kind == 'singles' else 4): continue
        found[url] = max(found.get(url, 0), score)
    return [url for url, _ in sorted(found.items(), key=lambda x: -x[1])[:limit]]


def parse_detail(html, page_url, source_name, make_event):
    """Only publish when event identity and start date are on the destination page."""
    soup = BeautifulSoup(html, 'html.parser')
    result = []
    def walk(o):
        if isinstance(o, list):
            for v in o: walk(v)
        elif isinstance(o, dict):
            typ = o.get('@type', [])
            if isinstance(typ, str): typ = [typ]
            if any('Event' in str(t) for t in typ):
                title = o.get('name', '')
                start = o.get('startDate', '')
                if isinstance(title, str) and isinstance(start, str):
                    try:
                        date = dateparser.parse(start)
                        if date.date() >= datetime.now().date()-timedelta(days=1):
                            loc = o.get('location', {})
                            venue = loc.get('name', '') if isinstance(loc, dict) else (loc[0].get('name','') if isinstance(loc,list) and loc and isinstance(loc[0],dict) else '')
                            desc = BeautifulSoup(str(o.get('description','')), 'html.parser').get_text(' ', strip=True)
                            ticket = ''
                            offers = o.get('offers', [])
                            if isinstance(offers, dict): offers = [offers]
                            for offer in offers:
                                if isinstance(offer,dict) and isinstance(offer.get('url'),str):
                                    ticket = clean_link(offer['url'],page_url);break
                            event_url = clean_link(o.get('url'),page_url) if isinstance(o.get('url'),str) else page_url
                            # Destination page is a known event detail, unlike the listing page.
                            if not event_url or not EVENT_PATH.search(urlparse(event_url).path): event_url = page_url
                            e = make_event(title,date.strftime('%Y-%m-%d'),venue or 'Portland',source_name,event_url,desc,date.strftime('%-I:%M %p') if 'T' in start else 'See event',ticket_url=ticket)
                            result.append(e)
                    except (ValueError,TypeError,OverflowError): pass
            for v in o.values(): walk(v)
    for tag in soup.select('script[type="application/ld+json"]'):
        try: walk(json.loads(tag.string or tag.get_text()))
        except (ValueError,TypeError): continue
    if result: return result
    # No date inference from the current year or link text: require an explicit date on detail page.
    title = soup.find('meta', property='og:title')
    title = title.get('content','') if title else (soup.h1.get_text(' ',strip=True) if soup.h1 else '')
    date_tag = soup.find('meta', attrs={'property':'event:start_time'}) or soup.find('meta',attrs={'name':'startDate'})
    time_tag = soup.find('time', datetime=True)
    start = date_tag.get('content') if date_tag else (time_tag.get('datetime') if time_tag else '')
    if not start or not title or not EVENT_PATH.search(urlparse(page_url).path): return []
    try:
        d = dateparser.parse(start)
        if d.date() < datetime.now().date()-timedelta(days=1): return []
        description = soup.find('meta', attrs={'name':'description'})
        desc = description.get('content','') if description else ''
        return [make_event(title,d.strftime('%Y-%m-%d'),'Portland',source_name,page_url,desc,d.strftime('%-I:%M %p') if 'T' in start else 'See event')]
    except (ValueError,TypeError,OverflowError): return []


def classify_social(event, source_kind):
    text = ' '.join(str(event.get(k,'')) for k in ('title','description','venue'))
    categories = event.get('categories',[])
    if SINGLES.search(text):
        categories = list(dict.fromkeys(['Singles','Social']+categories))
        event['category'] = 'Singles'
    elif SOCIAL.search(text):
        categories = list(dict.fromkeys(['Social']+categories))
        if event.get('category') == 'Other': event['category'] = 'Social'
    event['categories'] = categories
    event['tags'] = list(dict.fromkeys(event.get('tags',[])+categories))[:8]
    return event
