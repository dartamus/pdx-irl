#!/usr/bin/env python3
import json, re, hashlib, html, sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dtparse

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'events.json'; SOURCES=ROOT/'scripts'/'sources.json'; META=ROOT/'data'/'meta.json'
HEADERS={'User-Agent':'PDX-IRL/0.2 event indexer (+https://github.com/dartamus/pdx-irl)'}
CAT_WORDS={
 'Music':['music','concert','band','dj','karaoke','singer'], 'Singles':['singles','speed dating','dating','mixer'],
 'Art':['art','gallery','museum','film','theater','theatre','dance','zine','poetry','book'],
 'Sports':['sports','game','match','run','race','soccer','basketball','hockey','roller derby'],
 'Comedy':['comedy','comedian','stand-up','standup','improv'], 'Food + Drink':['food','drink','beer','wine','dinner','tasting','brewery','cocktail','market'],
 'Nightlife':['nightlife','club','dance party','drag','cabaret','late night'], 'Outdoors':['outdoor','hike','walk','run','park','trail','market'],
 'Weird':['halloween','haunted','ghost','oddities','weird','costume','paranormal']}

def slug(s): return re.sub(r'-+','-',re.sub(r'[^a-z0-9]+','-',s.lower())).strip('-')[:70]
def cats_for(text):
 t=text.lower(); out=[c for c,words in CAT_WORDS.items() if any(w in t for w in words)]
 return out or ['Other']
def adult_for(text): return bool(re.search(r'\b(21\+|ages? 21|twenty[- ]one and over)\b',text,re.I))
def val(x):
 if isinstance(x,list): return val(x[0]) if x else ''
 if isinstance(x,dict): return x.get('name') or x.get('streetAddress') or ''
 return str(x or '')
def parse_event(obj, source, base):
 typ=obj.get('@type',[]); typ=[typ] if isinstance(typ,str) else typ
 if not any('Event' in str(x) for x in typ): return None
 title=html.unescape(val(obj.get('name'))).strip(); start=obj.get('startDate')
 if not title or not start: return None
 try: d=dtparse.parse(start)
 except Exception: return None
 if d.date() < (datetime.now().date()-timedelta(days=1)): return None
 loc=obj.get('location',{}); venue=val(loc) or 'Portland'
 desc=BeautifulSoup(val(obj.get('description')),'html.parser').get_text(' ',strip=True)
 text=' '.join([title,venue,desc])
 categories=cats_for(text); url=obj.get('url') or base
 time=d.strftime('%-I:%M %p') if ('T' in str(start) or ' ' in str(start)) else 'See event'
 return {'id':slug(title)+'-'+d.strftime('%Y%m%d'),'title':title,'date':d.strftime('%Y-%m-%d'),'time':time,'venue':venue,
         'category':categories[0],'categories':categories,'adult':adult_for(text),'tags':categories[:3],
         'url':urljoin(base,url),'source':source,'description':desc[:240]}
def walk_json(x, source, base, out):
 if isinstance(x,dict):
  e=parse_event(x,source,base)
  if e: out.append(e)
  for v in x.values(): walk_json(v,source,base,out)
 elif isinstance(x,list):
  for v in x: walk_json(v,source,base,out)
def scrape(src):
 r=requests.get(src['url'],headers=HEADERS,timeout=25); r.raise_for_status(); soup=BeautifulSoup(r.text,'html.parser'); out=[]
 for tag in soup.find_all('script',type='application/ld+json'):
  raw=tag.string or tag.get_text()
  try: walk_json(json.loads(raw),src['name'],src['url'],out)
  except Exception: continue
 return out

def key(e): return (re.sub(r'\W+','',e.get('title','').lower()),e.get('date',''),re.sub(r'\W+','',e.get('venue','').lower()))
def main():
 existing=json.loads(DATA.read_text()); found=[]; report=[]
 for src in json.loads(SOURCES.read_text()):
  try:
   got=scrape(src); found+=got; report.append({'source':src['name'],'found':len(got),'ok':True})
  except Exception as ex: report.append({'source':src['name'],'found':0,'ok':False,'error':str(ex)[:160]})
 # Keep future hand-curated/previous events, then merge fresh scraped records over duplicates.
 today=datetime.now().date()-timedelta(days=1)
 pool=[e for e in existing if dtparse.parse(e['date']).date()>=today]+found
 merged={}
 for e in pool:
  k=key(e)
  if k in merged:
   old=merged[k]; old['categories']=sorted(set(old.get('categories',[old.get('category')])+e.get('categories',[])))
   old['tags']=sorted(set(old.get('tags',[])+e.get('tags',[])))[:8]
   if e.get('description') and not old.get('description'): old['description']=e['description']
  else: merged[k]=e
 events=sorted(merged.values(),key=lambda e:(e.get('date',''),e.get('time',''),e.get('title','')))
 DATA.write_text(json.dumps(events,ensure_ascii=False,indent=2)+'\n')
 META.write_text(json.dumps({'updatedAt':datetime.now(timezone.utc).isoformat(),'eventCount':len(events),'sources':report},indent=2)+'\n')
 print(f'PDX IRL: {len(events)} events; {sum(x["found"] for x in report)} freshly discovered')
 for x in report: print(('✓' if x['ok'] else '×'),x['source'],x['found'],x.get('error',''))
if __name__=='__main__': main()
