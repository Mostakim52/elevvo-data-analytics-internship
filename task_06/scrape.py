"""Task 6 — Web scraping and analysis of job postings.

Source: We Work Remotely (https://weworkremotely.com)
robots.txt check (fetched 2026-11-17):
    User-agent: *
    Allow: /
    Disallow: /admin/
    Disallow: /account/
    Disallow: /job-seekers/account/
    Disallow: /job-seekers/profile/
    Disallow: /manage-company/
    Disallow: /*edit?token=/
    Disallow: /*cancel?token=/
    Sitemap: https://weworkremotely.com/sitemap.xml

We only fetch public RSS feeds (explicitly allowed) and category listing pages.
No login-walled, admin or account pages are touched. A descriptive User-Agent
is sent and requests are rate-limited.
"""
import json
import re
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path

BASE = Path(r'H:\Repos\elevvo-internship-data-analytics\untitled-project\task_06')
HEADERS = {'User-Agent': 'ElevvoInternshipResearch/1.0 (+https://weworkremotely.com; educational scraping project)'}

FEEDS = {
    'programming': 'remote-programming-jobs',
    'design': 'remote-design-jobs',
    'data-science': 'remote-data-science-jobs',
    'devops': 'remote-devops-sysadmin-jobs',
    'product': 'remote-product-jobs',
    'sales-marketing': 'remote-sales-marketing-jobs',
    'full-stack': 'remote-full-stack-programming-jobs',
    'front-end': 'remote-front-end-programming-jobs',
    'back-end': 'remote-back-end-programming-jobs',
    'mobile': 'remote-mobile-programming-jobs',
}

def fetch_feed(slug: str) -> str | None:
    url = f'https://weworkremotely.com/categories/{slug}.rss'
    try:
        r = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
        r.raise_for_status()
        return r.text
    except Exception as exc:
        print(f'  feed {slug} failed: {exc}')
        return None

def parse_feed(xml: str, category: str):
    soup = BeautifulSoup(xml, 'xml')
    items = []
    for item in soup.find_all('item'):
        title = (item.find('title').text if item.find('title') else '').strip()
        link = (item.find('link').text if item.find('link') else '').strip() or (item.guid.text if item.guid else '')
        pub = (item.find('pubDate').text if item.find('pubDate') else '').strip()
        desc_html = item.find('description').text if item.find('description') else ''
        desc_text = BeautifulSoup(desc_html, 'html.parser').get_text(' ', strip=True)
        # WWR titles look like "Company: Role title"
        company, role = (title.split(':', 1) + [''])[:2] if ':' in title else ('', title)
        items.append({
            'company': company.strip(),
            'title': role.strip() if role else title,
            'full_title': title,
            'link': link.strip(),
            'posted': pub,
            'description': desc_text,
            'feed_category': category,
            'location': 'Remote',
        })
    return items

def main():
    (BASE / 'raw').mkdir(exist_ok=True)
    all_jobs = []
    for cat, slug in FEEDS.items():
        print('Fetching', cat, '->', slug)
        xml = fetch_feed(slug)
        if not xml:
            continue
        (BASE / 'raw' / f'{cat}.rss').write_text(xml, encoding='utf-8')
        jobs = parse_feed(xml, cat)
        print(f'  parsed {len(jobs)} postings')
        all_jobs.extend(jobs)
        time.sleep(1.5)  # be polite

    # de-duplicate by link
    seen, jobs = set(), []
    for j in all_jobs:
        if j['link'] and j['link'] in seen:
            continue
        seen.add(j['link'])
        jobs.append(j)

    # save raw JSON
    (BASE / 'jobs_raw.json').write_text(json.dumps(jobs, indent=2, ensure_ascii=False), encoding='utf-8')

    # quick save of locations (from description text, "Location: ..." if present)
    for j in jobs:
        m = re.search(r'(?:Location|Headquarters|Country)\s*[:\-]\s*([^.\n|]{2,60})', j['description'], re.I)
        if m:
            j['location_hint'] = m.group(1).strip(' ,;')
        else:
            j['location_hint'] = 'Remote / Unspecified'

    (BASE / 'jobs_raw.json').write_text(json.dumps(jobs, indent=2, ensure_ascii=False), encoding='utf-8')
    print('total unique postings:', len(jobs))

if __name__ == '__main__':
    main()
