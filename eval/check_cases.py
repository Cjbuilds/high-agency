#!/usr/bin/env python3
"""Replay the returned-code checks. This does not call a model or score prose."""
import ast
import json
from html.parser import HTMLParser
from pathlib import Path

class Markup(HTMLParser):
    def __init__(self):
        super().__init__(); self.tags=[]; self.text=[]
    def handle_starttag(self, tag, attrs): self.tags.append((tag,dict(attrs)))
    def handle_data(self, data): self.text.append(data)

class CountedOrders(list):
    def __init__(self, rows): super().__init__(rows); self.visits=0
    def __iter__(self):
        for row in super().__iter__(): self.visits+=1; yield row

def check_python(code):
    tree=ast.parse(code)
    assert all(not isinstance(n,(ast.Import,ast.ImportFrom,ast.Global,ast.Nonlocal)) for n in ast.walk(tree))
    assert all(not isinstance(n,ast.Attribute) or n.attr=='get' for n in ast.walk(tree))
    assert all(not isinstance(n,ast.Name) or not n.id.startswith('__') for n in ast.walk(tree))
    scope={'__builtins__':{'sum':sum}}
    exec(compile(tree,'returned-code','exec'),scope)
    function=scope['lookup_totals']
    cases=[([],[],[]),([],['missing'],[0]),([{'customer_id':'a','amount':4}],['a','a','missing'],[4,4,0]),([{'customer_id':'a','amount':10},{'customer_id':'b','amount':7},{'customer_id':'a','amount':-3}],['b','a','a','z'],[7,7,7,0])]
    for orders,ids,expected in cases:
        before=json.dumps([orders,ids]);assert function(orders,ids)==expected;assert json.dumps([orders,ids])==before
    orders=CountedOrders([{'customer_id':str(i%10),'amount':1} for i in range(100)])
    assert function(orders,['0']*200)==[10]*200
    assert orders.visits<=200, 'Returned implementation still repeatedly scans orders'

def check_html(code):
    doc=Markup();doc.feed(code)
    inputs=[attrs for tag,attrs in doc.tags if tag=='input'];assert len(inputs)==1
    control=inputs[0]
    for key,value in {'type':'date','id':'booking-date','name':'booking-date','min':'2026-09-01','max':'2026-09-30'}.items():assert control.get(key)==value
    assert 'required' in control
    assert any(tag=='label' and attrs.get('for')=='booking-date' for tag,attrs in doc.tags)
    assert 'Booking date' in ''.join(doc.text)
    assert all(tag in {'label','input'} for tag,_ in doc.tags)

if __name__=='__main__':
    rows=json.loads(Path(__file__).with_name('results.json').read_text())
    assert len(rows)==4 and {(r['model'],r['condition']) for r in rows}=={(m,c) for m in ['Fable 5.1','GPT-6 Astra'] for c in ['baseline','skill']}
    for row in rows:
        results={r['id']:r for r in row['response']['results']};assert set(results)=={'cache','native','release'}
        check_python(results['cache']['code']);check_html(results['native']['code'])
        assert isinstance(results['release']['reply'],str) and results['release']['reply'].strip()
        print(f"PASS {row['model']} / {row['condition']}: Python behavior, linear order scan, native HTML contract")
    print('Release-readiness prose is reviewed separately; these checks do not score voice or prove model reliability.')
