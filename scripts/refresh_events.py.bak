#!/usr/bin/env python3
import json,re,html
from pathlib import Path
from datetime import datetime,timedelta,timezone
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dtparse

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data/events.json'; SOURCES=ROOT/'scripts/sources.json'; META=ROOT/'data/meta.json'
HEADERS={'User-Agent':'Mozilla/5.0 (compatible; PDX-IRL/0.3; +https://github.com/dartamus/pdx-irl)','Accept-Language':'en-US,en;q=0.9'}
CAT_WORDS={'Music':['music','concert','band','dj','karaoke','singer','rock','pop','country','jazz','hip-hop'],'Singles':['singles','speed dating','dating','mixer','meet cute'],'Art':['art','gallery','museum','film','theater','theatre','dance','zine','poetry','book','design'],'Sports':['sports','game','match','run','race','soccer','basketball','hockey','roller derby','volleyball','timbers','thorns','winterhawks'],'Comedy':['comedy','comedian','stand-up','standup','improv'],'Food + Drink':['food','drink','beer','wine','dinner','tasting','brewery','cocktail','market'],'Nightlife':['nightlife','club','dance party','drag','cabaret','late night'],'Outdoors':['outdoor','hike','walk','run','park','trail','market'],'Weird':['halloween','haunted','ghost','oddities','weird','costume','paranormal','pumpkin']}
MONTHS='January February March April May June July August September October November December Jan Feb Mar Apr May Jun Jul Aug Sep Sept Oct Nov Dec'.split()

def slug(s): return re.sub(r'-+','-',re.sub(r'[^a-z0-9]+','-',s.lower())).strip('-')[:70]
def cats_for(text):
 t=text.lower(); out=[c for c,w in CAT_WORDS.items() if any(x in t for x in w)]; return out or ['Other']
def adult_for(text): return bool(re.search(r'\b(21\+|ages? 21|twenty[- ]one and over)\b',text,re.I))
def val(x):
 if isinstance(x,list): return val(x[0]) if x else ''
 if isinstance(x,dict): return x.get('name') or x.get('streetAddress') or ''
 return str(x or '')
def url_score(url):
 if not url:return 0
 try:
  u=urlparse(url); path=u.path.strip('/'); q=u.query.lower()
  if not path and not q:return 0
  score=1
  if any(x in path.lower() for x in ['/event/','events/','/show/','shows/','concert','ticket']):score+=4
  if len(path.split('/'))>=2:score+=2
  if any(x in q for x in ['event=','eventid=','event_id=','eid=']):score+=3
  return score
 except:return 0

def specific_url(url): return url if url_score(url)>=2 else ''

def make_event(title,date,venue,source,url,desc='',time='See event',end=None,ticket_url=''):
 text=' '.join([title,venue,desc]); cats=cats_for(text); event_url=specific_url(url); ticket_url=specific_url(ticket_url)
 return {'id':slug(title)+'-'+date.replace('-',''),'title':html.unescape(title).strip(),'date':date,'time':time,'venue':venue or 'Portland','category':cats[0],'categories':cats,'adult':adult_for(text),'tags':cats[:4],'event_url':event_url,'ticket_url':ticket_url,'source':source,'source_url':'','description':re.sub(r'\s+',' ',desc).strip()[:260],**({'endDate':end} if end else {})}

def parse_event(obj,source,base):
 typ=obj.get('@type',[]); typ=[typ] if isinstance(typ,str) else typ
 if not any('Event' in str(x) for x in typ): return None
 title=html.unescape(val(obj.get('name'))).strip(); start=obj.get('startDate')
 if not title or not start:return None
 try:d=dtparse.parse(start)
 except:return None
 if d.date()<datetime.now().date()-timedelta(days=1):return None
 loc=obj.get('location',{}); venue=val(loc) or 'Portland'; desc=BeautifulSoup(val(obj.get('description')),'html.parser').get_text(' ',strip=True)
 end=None
 try:
  if obj.get('endDate'): end=dtparse.parse(obj['endDate']).strftime('%Y-%m-%d')
 except:pass
 time=d.strftime('%-I:%M %p') if ('T' in str(start) or ' ' in str(start)) else 'See event'
 event_url=urljoin(base,obj.get('url')) if obj.get('url') else ''
 ticket=''
 offers=obj.get('offers')
 if isinstance(offers,dict): ticket=urljoin(base,val(offers.get('url')))
 elif isinstance(offers,list):
  for offer in offers:
   if isinstance(offer,dict) and offer.get('url'): ticket=urljoin(base,val(offer.get('url')));break
 return make_event(title,d.strftime('%Y-%m-%d'),venue,source,event_url,desc,time,end,ticket)
def walk_json(x,source,base,out):
 if isinstance(x,dict):
  e=parse_event(x,source,base)
  if e:out.append(e)
  for v in x.values():walk_json(v,source,base,out)
 elif isinstance(x,list):
  for v in x:walk_json(v,source,base,out)
def jsonld(soup,src):
 out=[]
 for tag in soup.find_all('script',type='application/ld+json'):
  try:walk_json(json.loads(tag.string or tag.get_text()),src['name'],src['url'],out)
  except:pass
 return out

def parse_date(text):
 # Supports Oct. 23, 2026; Oct 23–25, 2026; Friday, Oct. 23, 2026
 m=re.search(r'\b('+'|'.join(MONTHS)+r')\.?\s+(\d{1,2})(?:\s*[–-]\s*(\d{1,2}))?,?\s+(20\d{2})\b',text,re.I)
 if not m:return None
 try:
  start=dtparse.parse(f'{m.group(1)} {m.group(2)} {m.group(4)}').date(); end=None
  if m.group(3):end=start.replace(day=int(m.group(3)))
  return start.isoformat(),end.isoformat() if end else None
 except:return None

def card_candidates(soup,src):
 out=[]; seen=set()
 for h in soup.find_all(['h2','h3','h4']):
  title=h.get_text(' ',strip=True)
  if len(title)<3 or len(title)>140 or title.lower() in {'upcoming events','all events','events by category','popular concerts in october'}:continue
  box=h.find_parent(['article','li','div']) or h.parent
  text=box.get_text(' ',strip=True)[:1600] if box else title
  parsed=parse_date(text)
  if not parsed:continue
  date,end=parsed
  if dtparse.parse(date).date()<datetime.now().date()-timedelta(days=1):continue
  a=h.find('a',href=True) or (box.find('a',href=True) if box else None); url=urljoin(src['url'],a['href']) if a else ''
  # venue often follows date/title; use first short line-ish string that isn't title/date/category
  venue='Portland'; strings=[x.strip() for x in box.stripped_strings] if box else []
  for s in strings:
   if s!=title and 2<len(s)<80 and not parse_date(s) and not re.search(r'^(editor.s pick|free|starting at|music|sports|comedy|festival|art|food|shopping)$',s,re.I):
    if any(k in s.lower() for k in ['hall','theater','theatre','studio','park','museum','center','centre','ballroom','arena','portland','lounge','club','pub','bar','omsi','zoo','coliseum','pavilion']): venue=s;break
  e=make_event(title,date,venue,src['name'],url,text,'See event',end)
  k=(e['title'].lower(),e['date'])
  if k not in seen:seen.add(k);out.append(e)
 return out

def portland_events(soup,src):
 # This calendar exposes compact event rows in rendered HTML; headings/links are the safest stable anchors.
 out=card_candidates(soup,src)
 if out:return out
 text=soup.get_text(' ',strip=True); today=datetime.now().date();
 # fallback: detect title + "Next Event: Oct 23, 2026 8:00 PM" chunks
 pat=re.compile(r'([A-Z][^→]{2,100}?)\s+Next Event:\s+([A-Z][a-z]{2})\s+(\d{1,2}),\s+(20\d{2})\s+(\d{1,2}:\d{2}\s+[AP]M)',re.I)
 for m in pat.finditer(text):
  try:d=dtparse.parse(f'{m.group(2)} {m.group(3)} {m.group(4)}').date()
  except:continue
  if d<today-timedelta(days=1):continue
  out.append(make_event(m.group(1).strip(),d.isoformat(),'Portland',src['name'],'','',m.group(5)))
 return out

def scrape(src):
 r=requests.get(src['url'],headers=HEADERS,timeout=30);r.raise_for_status();soup=BeautifulSoup(r.text,'html.parser')
 adapter=src.get('adapter','jsonld'); out=jsonld(soup,src)
 if adapter in ('travel_portland','local_radar'): out+=card_candidates(soup,src)
 elif adapter=='portland_events': out+=portland_events(soup,src)
 return out

def key(e):return(re.sub(r'\W+','',e.get('title','').lower()),e.get('date',''),re.sub(r'\W+','',e.get('venue','').lower()))
def main():
 existing=json.loads(DATA.read_text());found=[];report=[]
 for src in json.loads(SOURCES.read_text()):
  try:got=scrape(src);found+=got;report.append({'source':src['name'],'found':len(got),'ok':True})
  except Exception as ex:report.append({'source':src['name'],'found':0,'ok':False,'error':str(ex)[:180]})
 # Migrate v0.3 records and intentionally discard generic home-page links.
 for e in existing:
  legacy=e.pop('url',None)
  e.setdefault('event_url',specific_url(legacy or ''))
  e.setdefault('ticket_url','')
  e.setdefault('source_url','')
 today=datetime.now().date()-timedelta(days=1);pool=[e for e in existing if dtparse.parse(e['date']).date()>=today]+found;merged={}
 for e in pool:
  k=key(e)
  if k in merged:
   old=merged[k];old['categories']=sorted(set(old.get('categories',[old.get('category')])+e.get('categories',[])));old['tags']=sorted(set(old.get('tags',[])+e.get('tags',[])))[:8];old['adult']=old.get('adult',False) or e.get('adult',False)
   if e.get('description') and len(e['description'])>len(old.get('description','')):old['description']=e['description']
   # Never let a generic source/venue homepage beat a specific event page.
   if url_score(e.get('event_url',''))>url_score(old.get('event_url','')):old['event_url']=e.get('event_url','')
   if url_score(e.get('ticket_url',''))>url_score(old.get('ticket_url','')):old['ticket_url']=e.get('ticket_url','')
   if not old.get('source_url') and e.get('source_url'):old['source_url']=e['source_url']
  else:merged[k]=e
 events=sorted(merged.values(),key=lambda e:(e.get('date',''),e.get('time',''),e.get('title','')));DATA.write_text(json.dumps(events,ensure_ascii=False,indent=2)+'\n')
 raw=len(found);fresh_keys=len({key(e) for e in found});dupes=max(0,raw-fresh_keys)
 META.write_text(json.dumps({'updatedAt':datetime.now(timezone.utc).isoformat(),'eventCount':len(events),'rawFound':raw,'duplicatesWithinFresh':dupes,'sources':report},indent=2)+'\n')
 print('\nPDX IRL EVENT REFRESH');print('─'*44)
 for x in report:print(f"{('✓' if x['ok'] else '×')} {x['source']:<29} {x['found']:>4}"+(f"  {x.get('error','')}" if not x['ok'] else ''))
 print('─'*44);print(f'Raw discovered: {raw}');print(f'Fresh duplicates: {dupes}');print(f'LIVE EVENTS: {len(events)}')
if __name__=='__main__':main()
