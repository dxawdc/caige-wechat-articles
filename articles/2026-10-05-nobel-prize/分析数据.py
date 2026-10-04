"""官方数据整理、统计口径、数据质量核验和公众号图表输入。"""
from pathlib import Path
from datetime import date
from fractions import Fraction
from collections import Counter
import json, re
import pandas as pd
import pycountry
from babel import Locale
import pymupdf

ROOT = Path(__file__).resolve().parent
RAW = ROOT / '数据' / '原始'
OUT = ROOT / '数据' / '整理'
OUT.mkdir(parents=True, exist_ok=True)
CUTOFF = 2025
CATS = {'Physics':'物理学','Chemistry':'化学','Physiology or Medicine':'生理学或医学','Literature':'文学','Peace':'和平','Economic Sciences':'经济学'}
ORDER = list(CATS.values())
LOCALE = Locale.parse('zh_Hans')
ALIASES = {'USA':'US','United Kingdom':'GB','Scotland':'GB','Northern Ireland':'GB','the Netherlands':'NL','Czech Republic':'CZ','East Timor':'TL','Taiwan':'CN','Faroe Islands (Denmark)':'DK','Guadeloupe, France':'FR','South Korea':'KR','Russia':'RU','Iran':'IR','Vietnam':'VN','Turkey':'TR','North Macedonia':'MK','Democratic Republic of the Congo':'CD','Venezuela':'VE'}

def read(name):
    return json.loads((RAW/name).read_text(encoding='utf-8'))

def en(value):
    return value.get('en','') if isinstance(value,dict) else ''

def country(value):
    if not value:
        return ('','','')
    code = ALIASES.get(value)
    if not code:
        code = pycountry.countries.lookup(value).alpha_2
    item = pycountry.countries.get(alpha_2=code)
    name = LOCALE.territories.get(code,value)
    name = {'US':'美国','GB':'英国','CN':'中国','CZ':'捷克','CD':'刚果（金）','KR':'韩国'}.get(code,name)
    return (code,item.alpha_3,name)

def write(df,name):
    df.to_csv(OUT/name,index=False,encoding='utf-8-sig',float_format='%.6f')

def normalize_school(name,city):
    # 仅明确记录的校内单位与校区归并；不将共同资助研究所或国家实验室并入高校。
    if name.startswith('University of California'):
        campus={'Berkeley, CA':'Berkeley','Irvine, CA':'Irvine','Los Angeles, CA':'Los Angeles','San Diego, CA':'San Diego','San Francisco, CA':'San Francisco','Santa Barbara, CA':'Santa Barbara'}
        if city in campus: return 'University of California, '+campus[city]
    if name.startswith('Harvard '): return 'Harvard University'
    for university in ['Stanford University','Massachusetts Institute of Technology (MIT)','Yale University','Johns Hopkins University','New York University','University of Pennsylvania','University of Wisconsin','University of Michigan','Columbia University','University of Chicago','University of Cambridge','University of Oxford','Princeton University','Cornell University']:
        if name==university or name.startswith(university+',') or name.startswith(university+' School'):
            return university
    if name=='Rockefeller Institute for Medical Research': return 'Rockefeller University'
    if name=='Trinity College' and city=='Cambridge': return 'University of Cambridge'
    if name=='All Souls College' and city=='Oxford': return 'University of Oxford'
    if name=='University College': return 'University College ('+city+')'
    if name=='Trinity College': return 'Trinity College ('+city+')'
    return name

def analyze():
    laureates=read('laureates.json')['laureates']
    rawprizes=read('prizes.json')['nobelPrizes']
    events=[]; affiliations=[]; people=[]; mappings={}
    for l in laureates:
        prizes=[p for p in l.get('nobelPrizes',[]) if int(p['awardYear'])<=CUTOFF]
        if not prizes: continue
        individual='gender' in l
        birth=l.get('birth',{})
        place=birth.get('place',{})
        birthplace=en(place.get('countryNow',{}))
        code,a3,cn=country(birthplace)
        if birthplace: mappings[birthplace]=(code,a3,cn)
        name=en(l.get('knownName',{})) or en(l.get('orgName',{})) or en(l.get('fullName',{}))
        base={'laureate_id':l['id'],'name':name,'entity_type':'person' if individual else 'organization','gender':l.get('gender','organization'),'birth_date':birth.get('date',''),'birth_country_historical':en(place.get('country',{})),'birth_country_now_raw':birthplace,'birth_country_code':code,'birth_country_alpha3':a3,'birth_country_cn':cn,'birth_city':en(place.get('cityNow',{})),'birth_continent':en(place.get('continent',{})),'prize_count':len(prizes)}
        people.append(base)
        for p in prizes:
            year=int(p['awardYear']); cat=CATS[en(p['category'])]
            age=None
            birthday=base['birth_date']
            if individual and re.fullmatch(r'\d{4}-\d{2}-\d{2}',birthday):
                try:
                    d=date.fromisoformat(birthday); ref=date(year,12,10)
                    age=year-d.year-((ref.month,ref.day)<(d.month,d.day))
                except ValueError: pass
            share=float(Fraction(p.get('portion','1')))
            e={**base,'year':year,'category':cat,'portion_raw':p.get('portion','1'),'portion':share,'prize_status':p.get('prizeStatus',''),'age_dec10':age,'prize_amount_sek':p.get('prizeAmount'),'prize_amount_adjusted_sek':p.get('prizeAmountAdjusted'),'nominal_share_sek':p.get('prizeAmount',0)*share,'motivation_en':en(p.get('motivation',{})),'date_announced':p.get('dateAwarded',''),'source_url':next((x['href'] for x in p.get('links',[]) if x.get('class')==['laureate facts']), '')}
            events.append(e)
            for a in p.get('affiliations',[]):
                ac=en(a.get('countryNow',{})) or en(a.get('country',{})); cc,ca3,ccn=country(ac)
                inst=en(a.get('nameNow',{})) or en(a.get('name',{}))
                original=en(a.get('name',{})); city=en(a.get('cityNow',{})) or en(a.get('city',{}))
                affiliations.append({'laureate_id':l['id'],'name':name,'year':year,'category':cat,'institution':inst,'institution_original':original,'institution_normalized':normalize_school(original,city),'country_now_raw':ac,'country_code':cc,'country_alpha3':ca3,'country_cn':ccn,'city':city})
    e=pd.DataFrame(events); l=pd.DataFrame(people); a=pd.DataFrame(affiliations).drop_duplicates(['laureate_id','year','category','institution_original','city','country_code'])
    write(l,'获奖主体.csv'); write(e,'获奖记录.csv'); write(a,'获奖时任职机构.csv')
    write(pd.DataFrame([{'source_country_now':k,'iso_alpha2':v[0],'iso_alpha3':v[1],'country_cn':v[2]} for k,v in sorted(mappings.items())]),'出生地国家映射.csv')

    prize_rows=[]
    noaward=[]
    for p in rawprizes:
        year=int(p['awardYear'])
        if year>CUTOFF: continue
        cat=CATS[en(p['category'])]
        recipients=p.get('laureates',[])
        if not recipients:
            noaward.append({'year':year,'category':cat,'reason':en(p.get('topMotivation',{}))})
            continue
        prize_rows.append({'year':year,'category':cat,'recipients':len(recipients),'prize_amount_sek':p.get('prizeAmount'),'prize_amount_adjusted_sek':p.get('prizeAmountAdjusted'),'date_announced':p.get('dateAwarded','')})
    p=pd.DataFrame(prize_rows); write(p,'年度学科奖项.csv'); write(pd.DataFrame(noaward),'未颁奖年份.csv')
    cat=e.groupby('category').agg(award_records=('laureate_id','size'),unique_recipients=('laureate_id','nunique')).join(p.groupby('category').agg(prizes=('year','size'),solo_prizes=('recipients',lambda x:int((x==1).sum())),two_prizes=('recipients',lambda x:int((x==2).sum())),three_prizes=('recipients',lambda x:int((x==3).sum())))).reindex(ORDER).reset_index()
    write(cat,'学科统计.csv')
    persons=l[l.entity_type=='person']; pe=e[e.entity_type=='person']
    birth=persons[persons.birth_country_code!=''].groupby(['birth_country_code','birth_country_alpha3','birth_country_cn']).agg(unique_people=('laureate_id','nunique')).reset_index().sort_values(['unique_people','birth_country_cn'],ascending=[False,True])
    records=pe.groupby('birth_country_code').size(); birth['award_records']=birth.birth_country_code.map(records); write(birth,'出生地国家排名.csv')
    rep=l[l.prize_count>1].sort_values(['prize_count','name'],ascending=[False,True]).copy()
    rep['prizes_detail']=rep.laureate_id.map(e.groupby('laureate_id').apply(lambda d:'、'.join(str(x.year)+' '+x.category for x in d.sort_values('year').itertuples()),include_groups=False))
    write(rep,'多次获奖排名.csv')
    inst=a.groupby(['institution_original','city','country_cn']).agg(unique_people=('laureate_id','nunique'),award_records=('laureate_id','size')).reset_index().sort_values(['unique_people','institution_original'],ascending=[False,True])
    write(inst,'任职机构排名.csv')
    # 单独列出明确为大学/理工学院/大学医学院的机构；研究所/实验室保留在完整榜。
    normalized=a.drop_duplicates(['laureate_id','year','category','institution_normalized']).groupby('institution_normalized').agg(unique_people=('laureate_id','nunique'),award_records=('laureate_id','size'),countries=('country_cn',lambda x:' / '.join(sorted(set(x))))).reset_index().sort_values(['unique_people','institution_normalized'],ascending=[False,True])
    mask=normalized.institution_normalized.str.contains(r'University|Universität|Université|Institute of Technology|École Normale|Ecole Normale|College|Karolinska',case=False,regex=True)
    universities=normalized[mask].copy(); write(universities,'高校排名.csv')
    write(a[['institution_original','city','country_cn','institution_normalized']].drop_duplicates().sort_values(['institution_normalized','institution_original','city']),'高校机构名称归并.csv')
    by_country=a.drop_duplicates(['laureate_id','year','category','country_code']).groupby(['country_code','country_cn']).agg(award_records=('laureate_id','size'),unique_people=('laureate_id','nunique')).reset_index().sort_values('award_records',ascending=False); write(by_country,'任职国家排名.csv')

    # 官方PDF逐行取前四个数值列；保留125年奖金，空缺的投资资本列不参与解析。
    money=[]
    for page in pymupdf.open(RAW/'prize-amounts-2025.pdf'):
        text=page.get_text(); lines=text.splitlines()
        for i,line in enumerate(lines):
            if re.fullmatch(r'(19|20)\d{2}',line.strip()):
                y=int(line.strip()); vals=lines[i+1:i+5]
                if len(vals)==4 and vals[3].strip().endswith('%'):
                    nums=[int(re.sub(r'[^0-9]','',v)) for v in vals]
                    money.append({'year':y,'price_index':nums[0],'nominal_sek':nums[1],'real_2025_sek':nums[2],'real_vs_1901_percent_rounded':nums[3]})
    m=pd.DataFrame(money).sort_values('year'); write(m,'奖金历史.csv')
    # 独立的2026年已公布名义奖金，不补造2026年实际币值。
    from bs4 import BeautifulSoup
    text2026=BeautifulSoup((RAW/'prize-money-2026.html').read_text(encoding='utf8'),'html.parser').get_text(' ',strip=True)
    assert '2026 Nobel Prize will be SEK 12 million' in text2026
    write(pd.DataFrame([{'year':2026,'nominal_sek':12000000,'announced_date':'2026-09-18','source_url':'https://www.nobelpeaceprize.org/presse/pressemeldinger/the-nobel-prize-is-increased-by-sek-1-million'}]),'2026年已公布奖金.csv')
    # 用API中同期完整奖项金额交叉核验PDF；未颁奖年份保留PDF公布金额。
    mismatches=[]
    for row in p.itertuples():
        mr=m[m.year==row.year].iloc[0]
        if row.prize_amount_sek!=mr.nominal_sek or row.prize_amount_adjusted_sek!=mr.real_2025_sek:
            mismatches.append({'year':row.year,'category':row.category,'api_nominal':row.prize_amount_sek,'pdf_nominal':int(mr.nominal_sek),'api_adjusted':row.prize_amount_adjusted_sek,'pdf_adjusted':int(mr.real_2025_sek)})
    write(pe.groupby('category').agg(people_records=('laureate_id','size'),female_records=('gender',lambda x:int((x=='female').sum())),median_age=('age_dec10','median'),min_age=('age_dec10','min'),max_age=('age_dec10','max'),known_age_records=('age_dec10','count')).reindex(ORDER).reset_index(),'性别与年龄学科统计.csv')
    pe=pe.copy(); pe['decade']=(pe.year//10)*10
    dec=pe.groupby('decade').agg(people_records=('laureate_id','size'),female_records=('gender',lambda x:int((x=='female').sum())),median_age=('age_dec10','median')); dec['female_percent']=100*dec.female_records/dec.people_records; write(dec.reset_index(),'十年性别年龄趋势.csv')
    for df,label in [(p,'奖项'),(e,'人次')]:
        write(df.groupby(['year','category']).size().unstack(fill_value=0).reindex(range(1901,2026),fill_value=0).reindex(columns=ORDER).reset_index(),f'年度{label}趋势.csv')
    p['period']=pd.cut(p.year,bins=[1900,1950,2000,2025],labels=['1901—1950','1951—2000','2001—2025'])
    share=p.groupby(['period','recipients'],observed=True).size().unstack(fill_value=0).reindex(columns=[1,2,3],fill_value=0)
    share.columns=['solo','two','three']; share['total']=share.sum(axis=1); write(share.reset_index(),'共享奖项时期统计.csv')
    merge=a.merge(e[['laureate_id','year','category','birth_country_code','birth_country_cn']],on=['laureate_id','year','category'],validate='many_to_one')
    mobility=merge.drop_duplicates(['laureate_id','year','category','country_code']); mobility=mobility[mobility.birth_country_code!='']; write(mobility,'出生地与任职国家.csv')
    checks={
      'unique_entities':len(l),'unique_people':len(persons),'unique_organizations':int((l.entity_type=='organization').sum()),'award_records':len(e),'personal_award_records':len(pe),'organization_award_records':int((e.entity_type=='organization').sum()),'awarded_prizes':len(p),'unawarded_category_years':len(noaward),
      'duplicate_award_keys':int(e.duplicated(['laureate_id','year','category']).sum()),'birth_country_missing_people':int((persons.birth_country_code=='').sum()),'known_age_records':int(pe.age_dec10.notna().sum()),'female_unique_people':int((persons.gender=='female').sum()),'female_award_records':int((pe.gender=='female').sum()),'affiliation_award_records':len(e.merge(a[['laureate_id','year','category']].drop_duplicates(),on=['laureate_id','year','category'])),'affiliation_unique_people':int(a.laureate_id.nunique()),'affiliation_edges':len(a),'affiliation_countries_edges':len(mobility),'money_rows':len(m),'money_api_pdf_mismatches':mismatches,
      'shares_sum_mismatches':{str(k):v for k,v in e.groupby(['year','category']).portion.sum().items() if abs(v-1)>1e-8},
      'prize_api_vs_laureate_api_key_mismatch':sorted(set(zip(p.year,p.category))^set(zip(e.year,e.category))),
      'full_award_triplet_mismatches':sorted(set(zip(e.laureate_id,e.year,e.category))^set((x['id'],int(pr['awardYear']),CATS[en(pr['category'])]) for pr in rawprizes if int(pr['awardYear'])<=CUTOFF for x in pr.get('laureates',[]))),
      'youngest':pe.sort_values(['age_dec10','year']).head(3)[['name','year','category','age_dec10']].to_dict('records'), 'oldest':pe.sort_values(['age_dec10','year'],ascending=False).head(3)[['name','year','category','age_dec10']].to_dict('records'),
    }
    assert len(l)==1018 and len(persons)==990 and len(e)==1026 and len(p)==633
    assert checks['duplicate_award_keys']==0 and not checks['prize_api_vs_laureate_api_key_mismatch'] and not checks['full_award_triplet_mismatches'] and not checks['shares_sum_mismatches']
    assert int(birth.unique_people.sum())+checks['birth_country_missing_people']==990
    assert int(p.recipients.sum())==1026
    assert len(m)==125 and set(m.year)==set(range(1901,2026))
    (ROOT/'验收').mkdir(exist_ok=True)
    (ROOT/'验收'/'数据核验.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(checks,ensure_ascii=False,indent=2))
    print('COUNTRIES',birth.head(15).to_string(index=False)); print('UNIVERSITIES',universities.head(20).to_string(index=False)); print('REPEAT',rep[['name','prize_count','prizes_detail']].to_string(index=False)); print('GENDER',dec.to_string())

if __name__=='__main__':
    analyze()
