import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from collectors_v05 import event_candidates, parse_detail, classify_social
from refresh_events import make_event

class CollectorTests(unittest.TestCase):
 def test_detail_links_not_homepage(self):
  markup='''<a href="/">Home</a><a href="/about">About</a><article><h2>Speed Dating Portland</h2><p>Dec 12, 2026</p><a href="/events/speed-dating-december-12">Tickets</a></article>'''
  self.assertEqual(event_candidates(markup,'https://example.com/',source_kind='singles'),['https://example.com/events/speed-dating-december-12'])
 def test_jsonld_specific_link(self):
  html='''<script type="application/ld+json">{"@context":"https://schema.org","@type":"Event","name":"Portland Singles Mixer","startDate":"2099-12-12T19:00:00-08:00","location":{"@type":"Place","name":"The Venue"},"offers":{"url":"https://tickets.example.com/event/abc123"}}</script>'''
  found=parse_detail(html,'https://example.com/events/portland-singles-mixer','Test',make_event)
  self.assertEqual(len(found),1)
  self.assertEqual(found[0]['event_url'],'https://example.com/events/portland-singles-mixer')
  self.assertEqual(found[0]['ticket_url'],'https://tickets.example.com/event/abc123')
  self.assertIn('Singles',classify_social(found[0],'singles')['categories'])
 def test_no_date_no_event(self):
  self.assertEqual(parse_detail('<h1>Singles mixer</h1>','https://example.com/events/mixer','Test',make_event),[])
 def test_social_not_automatically_singles(self):
  e=make_event('Trivia and Board Games','2099-12-12','Portland','Test','https://example.com/events/trivia')
  self.assertNotIn('Singles',classify_social(e,'singles')['categories'])
  self.assertIn('Social',e['categories'])
if __name__=='__main__': unittest.main()
