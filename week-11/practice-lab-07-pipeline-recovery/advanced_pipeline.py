"""Worked release gate: retain run evidence and promote only a passing report."""
import argparse,csv,hashlib,json,os
from pathlib import Path

REQUIRED={'event_id','location','units'}
def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def process(source, manifest, depots, run_dir, release_dir):
    source,manifest,depots,run_dir,release_dir=map(Path,(source,manifest,depots,run_dir,release_dir))
    # A unique folder protects previous attempts; fail rather than overwrite evidence.
    run_dir.mkdir(parents=True,exist_ok=False)
    result={'status':'HOLD','source':str(source),'manifest':str(manifest),'depots':str(depots),'failures':[]}
    try:
        result['source_sha256']=digest(source); result['manifest_sha256']=digest(manifest); result['depots_sha256']=digest(depots)
        contract=json.loads(manifest.read_text(encoding='utf8'))
        result['batch_id']=contract['batch_id']
        if contract['file_complete'] is not True: result['failures'].append('incomplete source handoff')
        expected=int(contract['expected_unique_events'])
        with depots.open(encoding='utf8',newline='') as f:
            depot_rows=list(csv.DictReader(f))
        allowed={r['depot'].strip() for r in depot_rows}
        if not allowed or '' in allowed or len(allowed)!=len(depot_rows): raise ValueError('invalid depot reference')
        with source.open(encoding='utf8',newline='') as f:
            reader=csv.DictReader(f)
            missing=REQUIRED-set(reader.fieldnames or [])
            if missing: raise ValueError('missing columns: '+', '.join(sorted(missing)))
            rows=list(reader)
        accepted=[]; rejected=[]; seen=set()
        for line,row in enumerate(rows,2):
            key=(row.get('event_id') or '').strip(); loc=(row.get('location') or '').strip(); reasons=[]
            if not key: reasons.append('missing event_id')
            if key and key in seen: reasons.append('duplicate event_id')
            if key: seen.add(key)
            if loc not in allowed: reasons.append('unknown location')
            try:
                units=int(row.get('units',''))
                if units<0: reasons.append('negative units')
            except (TypeError,ValueError): units=None; reasons.append('invalid units')
            if reasons: rejected.append({'line':line,'event_id':key,'reason':'; '.join(reasons)})
            else: accepted.append({'event_id':key,'location':loc,'units':units})
        result.update(input_rows=len(rows),accepted_rows=len(accepted),rejected_rows=len(rejected),unique_ids=len(seen))
        if len(rows)!=len(accepted)+len(rejected): result['failures'].append('row reconciliation failed')
        if rejected: result['failures'].append('rejected rows')
        if len(seen)!=expected: result['failures'].append('unique event count differs from manifest')
        observed={r['location'] for r in accepted}
        if observed!=allowed: result['failures'].append('missing expected depot coverage')
        result['missing_depots']=sorted(allowed-observed)
        for name,data,fields in [('accepted.csv',accepted,['event_id','location','units']),('rejected.csv',rejected,['line','event_id','reason'])]:
            with (run_dir/name).open('w',encoding='utf8',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(data)
        if not result['failures']:
            totals={loc:0 for loc in allowed}
            for r in accepted: totals[r['location']]+=r['units']
            release_dir.mkdir(parents=True,exist_ok=True)
            staged=run_dir/'candidate.csv'
            with staged.open('w',encoding='utf8',newline='') as f:
                w=csv.writer(f);w.writerow(['location','units']);w.writerows(sorted(totals.items()))
            # Copy into destination filesystem before atomic replace; no claims about concurrent writers.
            temp=release_dir/'report.tmp'
            temp.write_bytes(staged.read_bytes());os.replace(temp,release_dir/'current_report.csv')
            result['status']='PASS';result['published_sha256']=digest(release_dir/'current_report.csv')
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        result['failures'].append(str(exc))
    (run_dir/'summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    return result
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source');a.add_argument('manifest');a.add_argument('depots');a.add_argument('run_dir');a.add_argument('release_dir')
    x=a.parse_args(); print(json.dumps(process(x.source,x.manifest,x.depots,x.run_dir,x.release_dir),indent=2))
