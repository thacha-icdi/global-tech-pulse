#!/usr/bin/env python3
"""Aggregate technology RSS feeds into a JSON file for static hosting."""
import datetime as dt
import email.utils
import html
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'news.json'
FEEDS = [
    ('TechCrunch', 'https://techcrunch.com/feed/'),
    ('The Verge', 'https://www.theverge.com/rss/index.xml'),
    ('Ars Technica', 'https://feeds.arstechnica.com/arstechnica/index'),
    ('MIT Technology Review', 'https://www.technologyreview.com/feed/'),
    ('Wired', 'https://www.wired.com/feed/rss'),
    ('VentureBeat', 'https://venturebeat.com/feed/'),
    ('Google Blog', 'https://blog.google/rss/'),
    ('Microsoft Blog', 'https://blogs.microsoft.com/feed/'),
    ('NVIDIA Blog', 'https://blogs.nvidia.com/feed/'),
]
KEYWORDS = {
    'Cybersecurity': ['cybersecurity','ransomware','hacker','hackers','breach','malware','phishing','vulnerability','zero-day','security flaw'],
    'Chips': ['semiconductor','chipmaker','chip manufacturing','gpu','processor','nvidia','tsmc','intel','amd','silicon','chip'],
    'AI': ['artificial intelligence','generative ai','machine learning','openai','anthropic','chatgpt','gemini','deepmind','llm','ai model','ai agent'],
    'Policy': ['regulation','antitrust','lawmakers','legislation','tech policy','privacy law','digital markets act','export restriction','government ban'],
    'Startups': ['startup','venture capital','seed round','series a','series b','funding round','fundraising','unicorn','ipo'],
    'Big Tech': ['apple','google','microsoft','amazon','meta','tesla','alphabet','samsung','tiktok','bytedance','spacex'],
}

def clean(s):
    s = re.sub(r'<[^>]+>', ' ', html.unescape(s or ''))
    return re.sub(r'\s+', ' ', s).strip()

def node_text(e, *names):
    for n in names:
        v = e.find(n)
        if v is not None:
            t = ''.join(v.itertext()).strip()
            if t:
                return t
    return ''

def parse_date(s):
    if not s:
        return None
    try:
        d = email.utils.parsedate_to_datetime(s)
    except (ValueError, TypeError):
        try:
            d = dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
        except ValueError:
            return None
    return d.replace(tzinfo=d.tzinfo or dt.timezone.utc).astimezone(dt.timezone.utc)

def category(title, summary):
    blob = (title + ' ' + summary).lower()
    for cat, terms in KEYWORDS.items():
        if any(t in blob for t in terms):
            return cat
    return 'Big Tech'

def load_feed(name, url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; GlobalTechPulse/1.0; RSS Reader)', 'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*'})
    with urllib.request.urlopen(req, timeout=18) as response:
        body = response.read(3_000_000)
    tree = ET.fromstring(body)
    ns = {'a': 'http://www.w3.org/2005/Atom', 'c': 'http://purl.org/rss/1.0/modules/content/'}
    entries = tree.findall('./channel/item') or tree.findall('a:entry', ns) or tree.findall('.//{http://purl.org/rss/1.0/}item')
    items = []
    for e in entries[:35]:
        title = clean(node_text(e, 'title', '{http://www.w3.org/2005/Atom}title'))
        summary = clean(node_text(e, 'description', 'summary', '{http://www.w3.org/2005/Atom}summary', '{http://www.w3.org/2005/Atom}content'))[:260]
        link = node_text(e, 'link')
        if not link:
            for anchor in e.findall('{http://www.w3.org/2005/Atom}link'):
                if anchor.get('rel', 'alternate') == 'alternate':
                    link = anchor.get('href', '')
                    break
        pub = node_text(e, 'pubDate', 'published', 'updated', '{http://www.w3.org/2005/Atom}published', '{http://www.w3.org/2005/Atom}updated', '{http://purl.org/dc/elements/1.1/}date')
        timestamp = parse_date(pub)
        if not title or not link.startswith(('https://', 'http://')) or timestamp is None:
            continue
        items.append({'title': title, 'summary': summary, 'url': link, 'source': name, 'published': timestamp.isoformat().replace('+00:00','Z'), 'category': category(title,summary)})
    return items

def main():
    now = dt.datetime.now(dt.timezone.utc)
    previous = []
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding='utf-8')).get('items', [])
        except (json.JSONDecodeError, OSError):
            pass
    items = []
    working = []
    for name, url in FEEDS:
        try:
            result = load_feed(name, url)
            print(f'{name}: {len(result)} items')
            if result:
                working.append({'name': name, 'url': url})
                items.extend(result)
        except Exception as exc:
            print(f'WARNING {name}: {exc}')
    # Retain prior stories if one or more feeds are unavailable.
    items.extend(previous)
    seen = set()
    deduped = []
    for item in sorted(items, key=lambda x: x.get('published',''), reverse=True):
        key = item.get('url', '').split('#')[0].split('?')[0].rstrip('/')
        if key and key not in seen:
            seen.add(key)
            deduped.append(item)
    if not deduped:
        print('No feed data available; keeping existing file.')
        return
    # News history capped to 400 articles, retaining the latest stories.
    sources = [{'name': name, 'url': url} for name, url in FEEDS]
    payload = {'updated_at': now.isoformat().replace('+00:00', 'Z'), 'sources': sources, 'items': deduped[:400]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {len(payload["items"])} stories; {len(working)} reachable feeds')

if __name__ == '__main__':
    main()
