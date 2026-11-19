# Worked batch model: grain, temporal join diagnostics and release gates.
import argparse,csv,hashlib,json,sqlite3
from datetime import date
from pathlib import Path

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read_csv(p,required):
    with p.open(newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f)
        missing=set(required)-set(reader.fieldnames or [])
        if missing: raise ValueError('missing columns: '+', '.join(sorted(missing)))
        return list(reader)
def run(source,catalog,output):
    source,catalog,output=Path(source),Path(catalog),Path(output)
    output.mkdir(parents=True,exist_ok=False)
    summary={'status':'HOLD','source':str(source),'catalog':str(catalog),'failures':[]}
    try:
        summary.update(source_sha256=digest(source),catalog_sha256=digest(catalog))
        raw=read_csv(source,['line_id','order_id','sale_date','product_id','quantity','unit_cents'])
        refs=read_csv(catalog,['product_id','category','valid_from','valid_to'])
        if not raw: raise ValueError('empty transaction batch requires investigation')
        if not refs: raise ValueError('empty catalog')
        canonical={};replays=[];errors=[]
        for n,row in enumerate(raw,2):
            try:
                if not all(row[k].strip() for k in ['line_id','order_id','product_id']): raise ValueError('blank identifier')
                date.fromisoformat(row['sale_date']); q=int(row['quantity']); cents=int(row['unit_cents'])
                if q<=0 or cents<0: raise ValueError('invalid amount or quantity')
                k=row['line_id'].strip(); item=(k,row['order_id'].strip(),row['sale_date'],row['product_id'].strip(),q,cents)
                if k in canonical:
                    if canonical[k]==item: replays.append(n)
                    else: errors.append({'line':n,'reason':'conflicting line_id'})
                else: canonical[k]=item
            except (ValueError,KeyError,TypeError) as exc: errors.append({'line':n,'reason':str(exc)})
        source_errors=len(errors)
        for n,row in enumerate(refs,2):
            try:
                if not row['product_id'].strip() or not row['category'].strip(): raise ValueError('blank catalog field')
                if date.fromisoformat(row['valid_from'])>=date.fromisoformat(row['valid_to']): raise ValueError('invalid interval')
            except (ValueError,KeyError,TypeError) as exc: errors.append({'line':n,'reason':'catalog: '+str(exc)})
        summary.update(input_rows=len(raw),canonical_lines=len(canonical),replay_rows=len(replays),error_rows=source_errors,source_net_cents=sum(r[4]*r[5] for r in canonical.values()))
        if len(raw)!=len(canonical)+len(replays)+source_errors: raise ValueError('source row accounting failed')
        if errors:
            summary['failures'].append('invalid or conflicting rows'); summary['errors']=errors
        else:
            con=sqlite3.connect(':memory:')
            con.executescript('CREATE TABLE sales(line_id TEXT PRIMARY KEY,order_id TEXT,sale_date TEXT,product_id TEXT,quantity INTEGER,unit_cents INTEGER); CREATE TABLE catalog(product_id TEXT,category TEXT,valid_from TEXT,valid_to TEXT);')
            con.executemany('INSERT INTO sales VALUES (?,?,?,?,?,?)',canonical.values())
            con.executemany('INSERT INTO catalog VALUES (?,?,?,?)',[(r['product_id'],r['category'],r['valid_from'],r['valid_to']) for r in refs])
            diagnostic=con.execute('SELECT s.line_id,COUNT(c.product_id) AS matches FROM sales s LEFT JOIN catalog c ON s.product_id=c.product_id AND s.sale_date>=c.valid_from AND s.sale_date<c.valid_to GROUP BY s.line_id ORDER BY s.line_id').fetchall()
            with (output/'join_diagnostics.csv').open('w',encoding='utf8',newline='') as f:
                w=csv.writer(f);w.writerow(['line_id','matches']);w.writerows(diagnostic)
            summary['unmatched_lines']=sum(m==0 for _,m in diagnostic);summary['ambiguous_lines']=sum(m>1 for _,m in diagnostic)
            if any(m!=1 for _,m in diagnostic): summary['failures'].append('each line must have exactly one reference match')
            else:
                con.execute('CREATE TABLE fact_sales AS SELECT s.line_id,s.order_id,s.sale_date,s.product_id,c.category,s.quantity,s.unit_cents,s.quantity*s.unit_cents AS net_cents FROM sales s JOIN catalog c ON s.product_id=c.product_id AND s.sale_date>=c.valid_from AND s.sale_date<c.valid_to')
                report=con.execute('SELECT category,COUNT(*),SUM(quantity),SUM(net_cents) FROM fact_sales GROUP BY category ORDER BY category').fetchall()
                facts=con.execute('SELECT line_id,order_id,sale_date,product_id,category,quantity,unit_cents,net_cents FROM fact_sales ORDER BY line_id').fetchall()
                summary['fact_rows']=len(facts);summary['distinct_orders']=con.execute('SELECT COUNT(DISTINCT order_id) FROM fact_sales').fetchone()[0];summary['report_net_cents']=sum(r[3] for r in report)
                if summary['fact_rows']!=len(canonical) or summary['report_net_cents']!=summary['source_net_cents']: summary['failures'].append('fact or amount reconciliation failed')
                if not summary['failures']:
                    for name,header,rows in [('fact_sales.csv',['line_id','order_id','sale_date','product_id','category','quantity','unit_cents','net_cents'],facts),('category_report.csv',['category','line_count','units','net_cents'],report)]:
                        with (output/name).open('w',encoding='utf8',newline='') as f:
                            w=csv.writer(f);w.writerow(header);w.writerows(rows)
                    summary['status']='PASS'
            con.close()
    except (OSError,ValueError,KeyError,TypeError,sqlite3.Error) as exc: summary['failures'].append(str(exc))
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
    return summary
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source');a.add_argument('catalog');a.add_argument('output');x=a.parse_args();print(json.dumps(run(x.source,x.catalog,x.output),indent=2))
