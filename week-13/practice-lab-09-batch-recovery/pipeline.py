# Worked example: bounded local API pages, validation and recoverable batch output.
import argparse,csv,hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path

def fingerprint(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def timestamp(s):
    value=datetime.strptime(s,'%Y-%m-%dT%H:%M:%SZ')
    if value.strftime('%Y-%m-%dT%H:%M:%SZ')!=s: raise ValueError('timestamp must use YYYY-MM-DDTHH:MM:SSZ')
    return value.replace(tzinfo=timezone.utc)
def run(manifest_path,pages_dir,output_dir):
    manifest_path,pages_dir,output_dir=map(Path,(manifest_path,pages_dir,output_dir))
    output_dir.mkdir(parents=True,exist_ok=False)
    result={'status':'HOLD','manifest':str(manifest_path),'pages_dir':str(pages_dir),'failures':[],'page_hashes':{}}
    evidence=[];accepted={};duplicates=0;bad=0;visited=[]
    try:
        manifest=json.loads(manifest_path.read_text(encoding='utf8'))
        result['manifest_sha256']=fingerprint(manifest_path);result['batch_id']=manifest['batch_id']
        expected_pages=manifest['expected_pages'];expected_ids=manifest['expected_event_ids'];cutoff=timestamp(manifest['cutoff_utc'])
        if not isinstance(expected_pages,list) or not expected_pages or any(not isinstance(x,str) or not re.fullmatch(r'page[1-9][0-9]*',x) for x in expected_pages) or len(set(expected_pages))!=len(expected_pages): raise ValueError('manifest page list invalid')
        if not isinstance(expected_ids,list) or not expected_ids or any(not isinstance(x,str) or not x.strip() for x in expected_ids) or len(set(expected_ids))!=len(expected_ids): raise ValueError('manifest event list invalid')
        page=manifest['first_page']
        while page is not None:
            if not isinstance(page,str) or not re.fullmatch(r'page[1-9][0-9]*',page): raise ValueError('invalid page cursor')
            if page in visited: raise ValueError('page cursor cycle')
            if page not in expected_pages: raise ValueError('unexpected page cursor')
            path=pages_dir/(page+'.json');body=json.loads(path.read_text(encoding='utf8'));result['page_hashes'][page]=fingerprint(path)
            if body['batch_id']!=manifest['batch_id'] or body['page_id']!=page: raise ValueError('page identity or batch mismatch')
            if not isinstance(body['events'],list): raise ValueError('events must be a list')
            visited.append(page)
            for position,event in enumerate(body['events'],1):
                try:
                    if not isinstance(event,dict): raise ValueError('event must be an object')
                    key=event['event_id'];depot=event['depot'];units=event['units'];observed=timestamp(event['observed_at'])
                    if not isinstance(key,str) or not key.strip() or not isinstance(depot,str) or not depot.strip(): raise ValueError('missing identifier')
                    if isinstance(units,bool) or not isinstance(units,int) or units<0: raise ValueError('invalid units')
                    if observed>cutoff: raise ValueError('after cutoff')
                    if key in accepted:
                        if accepted[key]==event: duplicates+=1;kind='replay';reason='identical event'
                        else: bad+=1;kind='error';reason='conflicting event_id'
                    else: accepted[key]=event;kind='accepted';reason=''
                except (KeyError,ValueError,TypeError) as exc:
                    bad+=1;kind='error';reason=str(exc);key=event.get('event_id','') if isinstance(event,dict) else ''
                evidence.append({'page':page,'position':position,'event_id':key,'classification':kind,'reason':reason})
            page=body['next_page']
        if set(visited)!=set(expected_pages): result['failures'].append('page set incomplete')
        missing=sorted(set(expected_ids)-set(accepted));extra=sorted(set(accepted)-set(expected_ids))
        if missing or extra: result['failures'].append('event set differs from manifest')
        if bad: result['failures'].append('invalid or conflicting rows')
        if len(evidence)!=len(accepted)+duplicates+bad: result['failures'].append('row accounting failed')
        result.update(visited_pages=visited,input_rows=len(evidence),accepted_events=len(accepted),replay_rows=duplicates,error_rows=bad,missing_event_ids=missing,unexpected_event_ids=extra)
        if not result['failures']:
            totals={}
            for e in accepted.values(): totals[e['depot']]=totals.get(e['depot'],0)+e['units']
            with (output_dir/'depot_totals.csv').open('w',encoding='utf8',newline='') as f:
                w=csv.writer(f);w.writerow(['depot','units']);w.writerows(sorted(totals.items()))
            result['total_units']=sum(totals.values());result['status']='PASS'
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        result['failures'].append(str(exc))
    with (output_dir/'row_evidence.csv').open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['page','position','event_id','classification','reason']);w.writeheader();w.writerows(evidence)
    result['visited_pages']=visited
    (output_dir/'summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    return result
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('manifest');a.add_argument('pages_dir');a.add_argument('output_dir');x=a.parse_args();print(json.dumps(run(x.manifest,x.pages_dir,x.output_dir),indent=2))
