"""Le Tremplin: recherche web, registre des annonces et éditions datées."""
import datetime as dt, html, json, os, pathlib, re, urllib.request
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from zoneinfo import ZoneInfo
ROOT=pathlib.Path(__file__).resolve().parents[1]
DATE=dt.datetime.now(ZoneInfo('Europe/Paris')).date().isoformat()
CATEGORIES={'product':'Product Builder / No-Code','ops':'Product Ops / projet','automation':'Automatisation / IA','implementation':'Implémentation / Customer Success','training':'Formation / tutorat','health':'Santé numérique','creator':'Creator economy'}
def read(p): return json.loads((ROOT/p).read_text())
def save(p,v): (ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def norm(u):
    p=urlsplit(u)
    return urlunsplit((p.scheme,p.netloc.lower(),p.path.rstrip('/'),urlencode([(k,v) for k,v in parse_qsl(p.query) if not k.startswith('utm_') and k not in ('from','source','ref')]),''))
def main():
    test=os.getenv('TREMPLIN_TEST_MODE')=='1'
    catalog=read('editions/index.json');registry=read('data/annonces.json')
    if not test and any(e['date']==DATE for e in catalog['editions']):
        print('Edition existante, aucun remplacement');return
    prompt='''Tu rédiges Le Tremplin, veille emploi pour un profil Product & Operations Builder maîtrisant les outils no-code et la coordination opérationnelle. Recherche WEB obligatoire sur les pages employeurs et ATS des offres actives inédites Product Builder, Product Manager, Product Ops, automatisation IA, implémentation SaaS. Contraintes: 100% remote DEPUIS FRANCE, français en réunions, anglais oral simple, max 2-3 déplacements/mois. CDI ou freelance stable, objectif 3000 euros net/mois (ne pas convertir sans hypothèses). Aucun contact ni candidature. Pas de remplissage; zéro offre compatible est un résultat valable. Exclure annonces déjà présentées via URL, entreprise + titre ou même besoin reformulé. Ne pas réinventer liens, dates, salaire, score. Toute condition inconnue reste inconnue. A seulement si critères impératifs confirmés dans sources; B à confirmer, D incompatibilité. Sources primaires et lien DIRECT. Chaque offre contient uniquement des champs de type texte entreprise, titre, url, categorie (clé exacte), contrat, remote_france (oui/non/inconnu), francais (oui/non/inconnu), compatibilite (A/B/D), resume, preuves (extraits courts), vigilance, salaire. Retourner uniquement JSON {"annonces":[...],"synthese":"..."}. categorie doit contenir une clé, parmi '''+json.dumps(CATEGORIES,ensure_ascii=False)+'\nDate: '+DATE+'\nHistorique à exclure: '+json.dumps([{'url':x['url'],'titre':x.get('titre',''),'entreprise':x.get('entreprise','')} for x in registry['items']],ensure_ascii=False)
    req=urllib.request.Request('https://api.openai.com/v1/responses',data=json.dumps({'model':os.getenv('OPENAI_MODEL','gpt-4.1-mini'),'tools':[{'type':'web_search'}],'input':prompt,'max_output_tokens':7000}).encode(),headers={'Authorization':'Bearer '+os.environ['OPENAI_API_KEY'],'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=240) as r: result=json.load(r)
    if not any(x.get('type')=='web_search_call' for x in result.get('output',[])): raise ValueError('Recherche web non effectuée')
    raw='\n'.join(p['text'] for m in result.get('output',[]) if m.get('type')=='message' for p in m.get('content',[]) if p.get('type')=='output_text')
    data=json.loads(re.sub(r'^```(?:json)?\s*|\s*```$','',raw.strip()))
    known={norm(x['url']) for x in registry['items']};identities={(x.get('entreprise','').casefold(),x.get('titre','').casefold()) for x in registry['items'] if x.get('titre')}
    jobs=[]
    invalid=0; duplicates=0
    for a in data['annonces']:
        required=('entreprise','titre','url','categorie','contrat','remote_france','francais','compatibilite','resume','preuves','vigilance','salaire')
        if isinstance(a,dict) and 'catégorie' in a and 'categorie' not in a: a['categorie']=a.pop('catégorie')
        if isinstance(a,dict) and a.get('categorie') in CATEGORIES.values(): a['categorie']=next(k for k,v in CATEGORIES.items() if v==a['categorie'])
        if not isinstance(a,dict) or not all(isinstance(a.get(k),str) for k in required):
            invalid+=1;continue
        u=urlsplit(a['url']);n=norm(a['url']);identity=(a['entreprise'].casefold(),a['titre'].casefold())
        if n in known or identity in identities:
            duplicates+=1;continue
        if u.scheme!='https' or not u.netloc or u.path in ('','/') or a['categorie'] not in CATEGORIES:
            invalid+=1;continue
        if a['compatibilite'] not in ('A','B','D'): continue
        if a['compatibilite']=='A' and (a['remote_france']!='oui' or a['francais']!='oui'): a['compatibilite']='B'
        known.add(n);identities.add(identity);jobs.append(a)
    print('Résultats reçus:',len(data['annonces']),'| doublons:',duplicates,'| invalides:',invalid,'| retenus:',len(jobs))
    if invalid and not jobs: raise ValueError('Tous les résultats nouveaux sont invalides : ne pas annoncer un faux zéro')
    esc=lambda x:html.escape(str(x),quote=True)
    page=(ROOT/'scripts/template.html').read_text()
    page=re.sub(r'12 octobre 2026|LUNDI 12 OCTOBRE 2026',DATE,page)
    page=re.sub(r'<div class="notice">.*?</div>','<div class="notice"><strong>Edition automatique · '+DATE+'</strong><p>'+esc(data['synthese'])+'</p><p>Informations issues d’une recherche automatique, à confirmer sur les annonces avant candidature.</p></div>',page,count=1,flags=re.S)
    body='<div class="notice"><strong>Édition automatique · '+DATE+'</strong><p>'+esc(data['synthese'])+'</p></div><section id="overview"><h2>Vue d’ensemble</h2><div class="card">'+str(len(jobs))+' nouvelles annonces examinées. Aucun contact ni candidature envoyé.</div></section>'
    for k,title in CATEGORIES.items():
        body+='<section id="'+k+'"><h2>'+title+'</h2>'
        selected=[a for a in jobs if a['categorie']==k]
        if not selected: body+='<div class="card">Aucune nouvelle annonce retenue dans cette rubrique.</div>'
        for a in selected:
            body+='<article class="job-card"><span class="job-label checked">'+esc(a['compatibilite'])+'</span><h3>'+esc(a['entreprise']+' — '+a['titre'])+'</h3><p>'+esc(a['resume'])+'</p><p>'+esc(a['contrat']+' · '+a['salaire'])+'</p><p><strong>Remote France :</strong> '+esc(a['remote_france'])+' · Français : '+esc(a['francais'])+'</p><p><strong>Éléments relevés :</strong> '+esc(a['preuves'])+'</p><p><strong>À vérifier :</strong> '+esc(a['vigilance'])+'</p><a target="_blank" rel="noopener noreferrer" href="'+esc(a['url'])+'">Annonce officielle ↗</a></article>'
        body+='</section>'
    for k,title in [('targets','Entreprises cibles'),('niches','Niches à explorer')]: body+='<section id="'+k+'"><h2>'+title+'</h2><div class="card">Voir les besoins métier dans les annonces ci-dessus. Aucune prospection automatique.</div></section>'
    template=(ROOT/'scripts/template.html').read_text()
    for k in ('messages','rules'):
        match=re.search(r'<section class="section" id="'+k+r'">.*?</section>',template,re.S)
        if match:
            section=match.group(0)
            body+=section
    body+='<section id="sources"><h2>Sources</h2><div class="card"><p>Recherche du '+DATE+'. Vérification humaine nécessaire. Aucun seuil artificiel de nombre d’offres.</p>'+''.join('<p><a href="'+esc(a['url'])+'">'+esc(a['entreprise']+' — '+a['titre'])+'</a></p>' for a in jobs)+'</div></section>'
    page=re.sub(r'(<main>).*?(</main>)',lambda m:m[1]+body+m[2],page,flags=re.S)
    page=re.sub(r'<footer>.*?</footer>','<footer>Le Tremplin · '+DATE+' · Edition automatique · Aucune candidature envoyée.</footer>',page,flags=re.S)
    if test:
        (ROOT/'test-preview.html').write_text(page);print('TEST OK:',len(jobs),'nouvelles annonces');return
    (ROOT/'editions'/f'{DATE}.html').write_text(page);(ROOT/'index.html').write_text(page)
    catalog['editions'].insert(0,{'date':DATE,'title':'Le Tremplin — '+DATE,'url':f'/editions/{DATE}.html','verification':'automatique-à-confirmer'})
    registry['items'].extend({**a,'edition':DATE} for a in jobs)
    save('editions/index.json',catalog);save('data/annonces.json',registry)
    print('Edition publiée:',DATE,len(jobs),'nouvelles annonces')
if __name__=='__main__': main()
