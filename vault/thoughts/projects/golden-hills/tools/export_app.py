import openpyxl, json, sys, datetime
src, out = sys.argv[1], sys.argv[2]
wb = openpyxl.load_workbook(src, read_only=True)
def rows(name):
    it = wb[name].iter_rows(values_only=True)
    h = next(it)
    return h, [r for r in it if any(v not in (None, '') for v in r)]
ph, pos = rows('Позиции')
positions = [dict(cat=r[0], name=r[1], unit=r[2], note=r[3], stage=r[4]) for r in pos if r[1]]
pmap = {p['name']: p for p in positions}
sh, sup = rows('Поставщики')
def s(v): return None if v in (None, '') else str(v).strip()
suppliers = [dict(name=s(r[0]), type=s(r[1]), cats=s(r[2]), addr=s(r[3]), phone=s(r[4]), site=s(r[5]),
                  checked=s(r[6]), terms=s(r[7]), comment=s(r[8]), works=s(r[9]), person=s(r[10]), basis=s(r[11]))
             for r in sup if r[0]]
smap = {x['name']: x for x in suppliers}
jh, jr = rows('Журнал цен')
print(jh, file=sys.stderr)
prices = []
for r in jr:
    d = dict(zip(jh, r))
    if not d.get('Позиция') or d.get('Цена в прайсе, сум') in (None, ''): continue
    try: p = float(d['Цена в прайсе, сум'])
    except: continue
    k = d.get('Коэф. пересчёта (ед. прайса в 1 баз. ед.)')
    try: k = float(k) if k not in (None, '') else 1
    except: k = 1
    pos_ = pmap.get(d['Позиция'], {})
    sup_ = smap.get(d.get('Поставщик'), {})
    dt = d.get('Дата внесения')
    rec = dict(date=dt.strftime('%Y-%m-%d') if isinstance(dt, datetime.datetime) else s(dt),
        item=d['Позиция'], cat=pos_.get('cat'), unit=pos_.get('unit'), supplier=s(d.get('Поставщик')),
        stype=sup_.get('type'), price=round(p*k, 2), rawprice=p, rawunit=s(d.get('Ед. в прайсе')),
        vat=s(d.get('НДС включён')), delivery=s(d.get('Доставка включена')), stock=s(d.get('Наличие')),
        source=s(d.get('Источник')))
    rec['link']=s(d.get('Ссылка / контакт')); rec['comment']=s(d.get('Комментарий'))
    kd=d.get('Дата КП (из документа)')
    rec['kpdate']=kd.strftime('%Y-%m-%d') if isinstance(kd, datetime.datetime) else s(kd)
    rec['ours']= sup_.get('works')=='Да'
    rec={k:v for k,v in rec.items() if v not in (None,'',False)}
    prices.append(rec)
# Daily digests for the app's «Сводка» tab: conclusions text + PDF file name (published next to data.json)
import pathlib, re
proj = pathlib.Path(__file__).resolve().parent.parent
digests = []
for pdf in sorted((proj / 'сводки').glob('Сводка_цен_*.pdf'), reverse=True):
    day = re.search(r'(\d{4}-\d{2}-\d{2})', pdf.name).group(1)
    notes_f = proj / 'данные' / f'выводы_{day}.txt'
    notes = [l.strip() for l in notes_f.read_text(encoding='utf-8').splitlines() if l.strip()] if notes_f.exists() else []
    digests.append(dict(date=day, pdf=f'svodki/{day}.pdf', notes=notes))
json.dump(dict(generated=datetime.date.today().isoformat(), positions=positions, suppliers=suppliers, prices=prices, digests=digests),
          open(out, 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(positions), len(suppliers), len(prices), file=sys.stderr)
