import json, re, html, shutil, os
from pathlib import Path
from collections import Counter
DATA=json.load(open(os.environ.get('RECALL_DATA','/tmp/recalls.json'),encoding='utf-8'))
OUT=Path('.')
shutil.rmtree(OUT/"recall",ignore_errors=True); shutil.rmtree(OUT/"category",ignore_errors=True); shutil.rmtree(OUT/"retailer",ignore_errors=True); shutil.rmtree(OUT/"topic",ignore_errors=True)
BASE='https://louisalviss.github.io/canada-recall-check'
def slug(s):
    return (re.sub(r'[^a-z0-9]+','-',str(s).lower()).strip('-')[:90] or 'recall')
def esc(s): return html.escape(str(s or ''))
def clean(s): return re.sub(r'<[^>]+>',' ',str(s or '')).replace('&nbsp;',' ').strip()
def shell(title,desc,body,url):
    return f'''<!doctype html><html lang="en-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc[:155])}"><link rel="canonical" href="{url}"><meta name="robots" content="index,follow"><style>body{{font-family:system-ui,-apple-system,sans-serif;max-width:900px;margin:auto;padding:24px;color:#18181b;line-height:1.55}}a{{color:#155eef}}header{{border-bottom:1px solid #ddd;padding-bottom:14px;margin-bottom:28px}}.muted{{color:#666}}.card{{border:1px solid #ddd;border-radius:12px;padding:16px;margin:12px 0}}.tag{{display:inline-block;background:#f4f4f5;padding:3px 8px;border-radius:99px;font-size:13px}}h1{{line-height:1.15}}footer{{margin-top:48px;border-top:1px solid #ddd;padding-top:20px;color:#666;font-size:14px}}</style></head><body><header><a href="{BASE}/"><strong>Canada Recall Check</strong></a> <span class="muted">Independent recall finder</span></header>{body}<footer>Data source: Government of Canada Recalls and Safety Alerts. Open Government Licence – Canada. Independent site; verify critical information on the official notice.</footer></body></html>'''
active=[x for x in DATA if str(x.get('Archived','0'))!='1']
active.sort(key=lambda x:x.get('Last updated','') or '', reverse=True)
rows=active[:1500]
entries=[]; seen=set()
for r in rows:
    base=slug(r.get('Product') or r.get('Title') or r.get('NID')); s=base; n=2
    while s in seen: s=f'{base}-{n}'; n+=1
    seen.add(s); entries.append((s,r))
pages=[]
for s,r in entries:
    p=OUT/'recall'/s; p.mkdir(parents=True,exist_ok=True)
    issue=clean(r.get('Issue')); action=clean(r.get('What you should do'))
    product=clean(r.get('Product')); cat=clean(r.get('Category')); upd=r.get('Last updated','')
    title=f'{product} recall Canada — {issue}' if issue else f'{product} recall Canada'
    desc=f'Canada recall information for {product}. {issue}. Updated {upd}.'
    body=f'''<main><p class="tag">{esc(cat)}</p><h1>{esc(r.get('Title'))}</h1><p class="muted">Last updated: {esc(upd)} · Recall ID: {esc(r.get('NID'))}</p><div class="card"><h2>Product</h2><p>{esc(product)}</p><h2>Issue</h2><p>{esc(issue or 'See official notice')}</p><h2>What you should do</h2><p>{esc(action or 'See official notice')}</p></div><p><a rel="nofollow" href="{esc(r.get('URL'))}">Verify on the official Government of Canada notice →</a></p></main>'''
    url=f'{BASE}/recall/{s}/'; (p/'index.html').write_text(shell(title,desc,body,url),encoding='utf-8'); pages.append(url)
cats={}
for s,r in entries:
    c=clean(r.get('Category')) or 'Other'; cats.setdefault(c,[]).append((s,r))
for c,items in cats.items():
    cs=slug(c); p=OUT/'category'/cs; p.mkdir(parents=True,exist_ok=True)
    cards=''.join(f'<div class="card"><a href="{BASE}/recall/{s}/"><strong>{esc(r.get("Title"))}</strong></a><div class="muted">{esc(r.get("Last updated"))}</div></div>' for s,r in items[:100])
    body=f'<main><h1>{esc(c)} recalls in Canada</h1><p>{len(items)} recent active records in this test index.</p>{cards}</main>'
    url=f'{BASE}/category/{cs}/'; (p/'index.html').write_text(shell(f'{c} recalls Canada',f'Recent {c} recalls and safety alerts in Canada.',body,url),encoding='utf-8'); pages.append(url)
# Small SEO pilot: historical retailer hubs. These aggregate the full official
# dataset without expanding the individual recall-page footprint beyond the
# existing 1,500-record test index.
retailers={
    'Amazon Canada': r'\bamazon(?:\.ca| canada)?\b',
    'Canadian Tire': r'\bcanadian tire\b',
    'Costco Canada': r'\bcostco\b',
    'Dollarama': r'\bdollarama\b',
    'IKEA Canada': r'\bikea\b',
    'Walmart Canada': r'\bwalmart(?:\.ca| canada)?\b',
}
retailer_index=[]
for name,pattern in retailers.items():
    rx=re.compile(pattern,re.I)
    matches=[]
    for r in DATA:
        searchable=' '.join(clean(r.get(k)) for k in ('Title','Product','Issue','What you should do'))
        if rx.search(searchable): matches.append(r)
    matches.sort(key=lambda x:x.get('Last updated','') or '',reverse=True)
    if not matches: continue
    active_n=sum(str(r.get('Archived','0'))!='1' for r in matches)
    archived_n=len(matches)-active_n
    cat_counts=Counter(clean(r.get('Category')) or 'Other' for r in matches)
    top_cats=', '.join(f'{esc(c)} ({n})' for c,n in cat_counts.most_common(5))
    cards=''.join(
        f'<div class="card"><a rel="nofollow" href="{esc(r.get("URL"))}"><strong>{esc(r.get("Title"))}</strong></a>'
        f'<div class="muted">{esc(r.get("Last updated"))} · {esc(clean(r.get("Category")) or "Other")} · '
        f'{"Archived" if str(r.get("Archived","0"))=="1" else "Active"}</div></div>'
        for r in matches[:100]
    )
    body=(f'<main><h1>{esc(name)} recalls in Canada</h1>'
          f'<p>Historical and current Government of Canada recall records mentioning {esc(name)}.</p>'
          f'<div class="card"><strong>{len(matches)} records</strong> · {active_n} active · {archived_n} archived<br>'
          f'<span class="muted">Common categories: {top_cats}</span></div>'
          f'<p class="muted">This is an independent aggregation. Always verify status, affected products and corrective actions on the official notice.</p>'
          f'{cards}</main>')
    rs=slug(name); p=OUT/'retailer'/rs; p.mkdir(parents=True,exist_ok=True)
    url=f'{BASE}/retailer/{rs}/'
    (p/'index.html').write_text(shell(f'{name} recalls Canada — product recall history',f'Browse current and historical Government of Canada recall records mentioning {name}.',body,url),encoding='utf-8')
    pages.append(url); retailer_index.append((name,rs,len(matches),active_n))
retailer_cards=''.join(f'<div class="card"><a href="{BASE}/retailer/{rs}/"><strong>{esc(name)}</strong></a><div class="muted">{total} records · {active_n} active</div></div>' for name,rs,total,active_n in retailer_index)
retailer_body=f'<main><h1>Retailer recalls in Canada</h1><p>Browse selected retailer recall histories aggregated from Government of Canada recall records.</p>{retailer_cards}</main>'
retailer_url=f'{BASE}/retailer/'; (OUT/'retailer').mkdir(parents=True,exist_ok=True); (OUT/'retailer'/'index.html').write_text(shell('Retailer recalls Canada — recall history by store','Browse selected Canadian retailer recall histories from Government of Canada data.',retailer_body,retailer_url),encoding='utf-8'); pages.append(retailer_url)

# Cohort 2: three narrowly selected topic-history hubs. Selection is based on
# keyword demand + multi-year Canadian recall history + a weak/fragmented sampled SERP.
topic_hubs={
    'Pool recalls': [r'\bpool(?:s)?\b'],
    'Soap recalls': [r'\bsoap(?:s)?\b'],
    'Frigidaire stove and range recalls': [r'\bfrigidaire\b.*\b(?:stove|range|ranges)\b', r'\b(?:stove|range|ranges)\b.*\bfrigidaire\b'],
}
topic_index=[]
for name,patterns in topic_hubs.items():
    rxs=[re.compile(p,re.I) for p in patterns]
    matches=[]
    for r in DATA:
        searchable=' '.join(clean(r.get(k)) for k in ('Title','Product','Issue','What you should do','Category'))
        if any(rx.search(searchable) for rx in rxs): matches.append(r)
    matches.sort(key=lambda x:x.get('Last updated','') or '',reverse=True)
    if not matches: continue
    active_n=sum(str(r.get('Archived','0'))!='1' for r in matches)
    archived_n=len(matches)-active_n
    years=sorted({str(r.get('Last updated',''))[:4] for r in matches if str(r.get('Last updated',''))[:4].isdigit()})
    span=f'{years[0]}–{years[-1]}' if years else 'Unknown'
    cat_counts=Counter(clean(r.get('Category')) or 'Other' for r in matches)
    top_cats=', '.join(f'{esc(c)} ({n})' for c,n in cat_counts.most_common(5))
    cards=''.join(
        f'<div class="card"><a rel="nofollow" href="{esc(r.get("URL"))}"><strong>{esc(r.get("Title"))}</strong></a>'
        f'<div class="muted">{esc(r.get("Last updated"))} · {esc(clean(r.get("Category")) or "Other")} · '
        f'{"Archived" if str(r.get("Archived","0"))=="1" else "Active"}</div></div>'
        for r in matches[:100]
    )
    body=(f'<main><h1>{esc(name)} in Canada</h1>'
          f'<p>Current and historical Government of Canada recall records matching this topic.</p>'
          f'<div class="card"><strong>{len(matches)} records</strong> · {active_n} active · {archived_n} archived · history {esc(span)}<br>'
          f'<span class="muted">Common categories: {top_cats}</span></div>'
          f'<p class="muted">This is an independent topic index. Always verify affected models, product codes and corrective actions on the official notice.</p>'
          f'{cards}</main>')
    ts=slug(name); p=OUT/'topic'/ts; p.mkdir(parents=True,exist_ok=True)
    url=f'{BASE}/topic/{ts}/'
    (p/'index.html').write_text(shell(f'{name} Canada — historical recall list',f'Browse current and historical Canadian recall records for {name.lower()}.',body,url),encoding='utf-8')
    pages.append(url); topic_index.append((name,ts,len(matches),active_n,span))
topic_cards=''.join(f'<div class="card"><a href="{BASE}/topic/{ts}/"><strong>{esc(name)}</strong></a><div class="muted">{total} records · {active_n} active · {esc(span)}</div></div>' for name,ts,total,active_n,span in topic_index)
topic_body=f'<main><h1>Recall topic histories in Canada</h1><p>Small validation cohort of topic-level recall histories built from Government of Canada records.</p>{topic_cards}</main>'
topic_url=f'{BASE}/topic/'; (OUT/'topic').mkdir(parents=True,exist_ok=True); (OUT/'topic'/'index.html').write_text(shell('Recall topic histories Canada','Browse selected multi-year Canadian recall topic histories.',topic_body,topic_url),encoding='utf-8'); pages.append(topic_url)
topiclinks=' · '.join(f'<a href="topic/{ts}/">{esc(name)}</a>' for name,ts,_,_,_ in topic_index)

latest=''.join(f'<div class="card"><a href="recall/{s}/"><strong>{esc(r.get("Title"))}</strong></a><div class="muted">{esc(r.get("Category"))} · {esc(r.get("Last updated"))}</div></div>' for s,r in entries[:40])
catlinks=' · '.join(f'<a href="category/{slug(c)}/">{esc(c)}</a>' for c in sorted(cats)[:30])
body=f'''<main><h1>Canada Recall Check</h1><p>Search and browse recent Government of Canada recalls and safety alerts. This experimental index contains {len(rows):,} active records.</p><p><a href="retailer/"><strong>Browse retailer recall histories →</strong></a> · <a href="topic/"><strong>Browse topic recall histories →</strong></a></p><p><strong>Validation cohort:</strong> {topiclinks}</p><p>{catlinks}</p><h2>Latest recalls</h2>{latest}</main>'''
(OUT/'index.html').write_text(shell('Canada Recall Check — recent product, food, drug and vehicle recalls','Browse recent Government of Canada recalls and safety alerts by product and category.',body,BASE+'/'),encoding='utf-8')
pages.insert(0,BASE+'/')
(OUT/'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n',encoding='utf-8')
urls=''.join(f'<url><loc>{u}</loc></url>' for u in pages)
(OUT/'sitemap.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',encoding='utf-8')
readme_topics='\n'.join(f'- {name}: {BASE}/topic/{ts}/' for name,ts,_,_,_ in topic_index)
readme=f'''# Canada Recall Check

Static SEO experiment generated from Government of Canada open recall data.

## Live site

- Site: {BASE}/
- Sitemap: {BASE}/sitemap.xml
- Retailer recall histories: {BASE}/retailer/
- Topic recall histories: {BASE}/topic/

Current topic validation cohort:

{readme_topics}

## Data source

Government of Canada Recalls and Safety Alerts open data, with links back to the official notices for verification.

## Validation status

The site is intentionally being expanded in small cohorts. Mass programmatic scaling is paused until crawl/index/impression data shows that the aggregate-page formats can rank.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
print(f'built records={len(rows)} categories={len(cats)} urls={len(pages)}')