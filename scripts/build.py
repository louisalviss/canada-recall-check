import json, re, html, shutil, os
from pathlib import Path
DATA=json.load(open(os.environ.get('RECALL_DATA','/tmp/recalls.json'),encoding='utf-8'))
OUT=Path('.')
shutil.rmtree(OUT/"recall",ignore_errors=True); shutil.rmtree(OUT/"category",ignore_errors=True)
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
latest=''.join(f'<div class="card"><a href="recall/{s}/"><strong>{esc(r.get("Title"))}</strong></a><div class="muted">{esc(r.get("Category"))} · {esc(r.get("Last updated"))}</div></div>' for s,r in entries[:40])
catlinks=' · '.join(f'<a href="category/{slug(c)}/">{esc(c)}</a>' for c in sorted(cats)[:30])
body=f'''<main><h1>Canada Recall Check</h1><p>Search and browse recent Government of Canada recalls and safety alerts. This experimental index contains {len(rows):,} active records.</p><p>{catlinks}</p><h2>Latest recalls</h2>{latest}</main>'''
(OUT/'index.html').write_text(shell('Canada Recall Check — recent product, food, drug and vehicle recalls','Browse recent Government of Canada recalls and safety alerts by product and category.',body,BASE+'/'),encoding='utf-8')
pages.insert(0,BASE+'/')
(OUT/'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n',encoding='utf-8')
urls=''.join(f'<url><loc>{u}</loc></url>' for u in pages)
(OUT/'sitemap.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',encoding='utf-8')
(OUT/'README.md').write_text('# Canada Recall Check\n\nStatic SEO experiment generated from Government of Canada open recall data.\n',encoding='utf-8')
print(f'built records={len(rows)} categories={len(cats)} urls={len(pages)}')