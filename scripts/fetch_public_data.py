from pathlib import Path
import argparse, csv, io, json, math, urllib.request, zipfile
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'empirical'/'public_data_config.json').read_text(encoding='utf-8'))

UCI_URLS={
    179:'https://archive.ics.uci.edu/static/public/179/secom.zip',
    447:'https://archive.ics.uci.edu/static/public/447/condition+monitoring+of+hydraulic+systems.zip',
    341:'https://archive.ics.uci.edu/static/public/341/smartphone+based+recognition+of+human+activities+and+postural+transitions.zip',
}

def _download_zip(dataset_id:int):
    req=urllib.request.Request(UCI_URLS[dataset_id],headers={'User-Agent':'engineering-public-data-acquisition/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r: payload=r.read()
    (ROOT/'data'/'external').mkdir(parents=True,exist_ok=True)
    (ROOT/'data'/'external'/f'uci_{dataset_id}.zip').write_bytes(payload)
    return zipfile.ZipFile(io.BytesIO(payload))

def _csv_writer(path:Path,header):
    path.parent.mkdir(parents=True,exist_ok=True)
    f=path.open('w',encoding='utf-8',newline='')
    return f,csv.writer(f),header

def _fetch_secom(dest:Path,z:zipfile.ZipFile):
    features=[]
    for line in z.read('secom.data').decode('utf-8','replace').splitlines():
        if line.strip(): features.append(line.split())
    labels=[]
    for line in z.read('secom_labels.data').decode('utf-8','replace').splitlines():
        if line.strip():
            parts=line.split(maxsplit=1); labels.append((parts[0],parts[1] if len(parts)>1 else ''))
    n=min(len(features),len(labels)); width=max(len(row) for row in features[:n])
    ff,fw,_=_csv_writer(dest/'features.csv',[f'process_{i:03d}' for i in range(1,width+1)])
    tf,tw,_=_csv_writer(dest/'targets.csv',['yield_label','timestamp'])
    try:
        for row,(label,stamp) in zip(features[:n],labels[:n]): fw.writerow(row+['']*(width-len(row))); tw.writerow([label,stamp])
    finally: ff.close(); tf.close()
    (dest/'metadata.txt').write_text('UCI SECOM archive parsed from secom.data and secom_labels.data; official source URL: '+UCI_URLS[179],encoding='utf-8')

def _line_stats(text):
    out=[]
    for line in text.splitlines():
        vals=[]
        for token in line.split():
            try: vals.append(float(token))
            except ValueError: pass
        if vals:
            mean=sum(vals)/len(vals); var=sum((x-mean)**2 for x in vals)/len(vals)
            out.append((mean,math.sqrt(var),min(vals),max(vals)))
    return out

def _fetch_hydraulic(dest:Path,z:zipfile.ZipFile):
    sensors=['PS1','PS2','PS3','PS4','PS5','PS6','EPS1','FS1','FS2','TS1','TS2','TS3','TS4','VS1','CE','CP','SE']
    stats={name:_line_stats(z.read(name+'.txt').decode('utf-8','replace')) for name in sensors}
    profile=[]
    for line in z.read('profile.txt').decode('utf-8','replace').splitlines():
        vals=line.split()
        if vals: profile.append(vals)
    n=min(len(profile),*(len(stats[name]) for name in sensors)); header=[]
    for name in sensors:
        header.extend([f'{name}_mean',f'{name}_std',f'{name}_min',f'{name}_max'])
    ff,fw,_=_csv_writer(dest/'features.csv',header); tf,tw,_=_csv_writer(dest/'targets.csv',['cooler_condition','valve_condition','pump_leakage','accumulator_pressure','stable_flag'])
    try:
        for i in range(n):
            row=[]
            for name in sensors: row.extend(stats[name][i])
            fw.writerow(row); tw.writerow(profile[i][:5]+['']*max(0,5-len(profile[i])))
    finally: ff.close(); tf.close()
    (dest/'metadata.txt').write_text('UCI Condition Monitoring of Hydraulic Systems archive parsed into per-cycle sensor statistics and profile labels; official source URL: '+UCI_URLS[447],encoding='utf-8')

def _read_lines(z,name):
    return [line.split() for line in z.read(name).decode('utf-8','replace').splitlines() if line.strip()]

def _fetch_rehab(dest:Path,z:zipfile.ZipFile):
    labels=_read_lines(z,'Train/y_train.txt')+_read_lines(z,'Test/y_test.txt'); subjects=_read_lines(z,'Train/subject_id_train.txt')+_read_lines(z,'Test/subject_id_test.txt')
    first=_read_lines(z,'Train/X_train.txt')[0]; width=len(first); header=[f'feature_{i:03d}' for i in range(1,width+1)]
    ff,fw,_=_csv_writer(dest/'features.csv',header); tf,tw,_=_csv_writer(dest/'targets.csv',['activity','subject_id']); count=0
    try:
        for split in ('Train','Test'):
            for row in _read_lines(z,f'{split}/X_{split.lower()}.txt'):
                if count>=len(labels) or count>=len(subjects): break
                fw.writerow(row); tw.writerow([labels[count][0],subjects[count][0]]); count+=1
    finally: ff.close(); tf.close()
    if count!=len(labels) or count!=len(subjects): raise RuntimeError(f'UCI HAR row alignment failed: features={count}, labels={len(labels)}, subjects={len(subjects)}')
    (dest/'metadata.txt').write_text('UCI Smartphone-Based Recognition of Human Activities and Postural Transitions archive parsed from train/test matrices; official source URL: '+UCI_URLS[341],encoding='utf-8')

def fetch_uci(dataset_id:int, dest:Path):
    dest.mkdir(parents=True,exist_ok=True)
    with _download_zip(dataset_id) as z:
        if dataset_id==179: _fetch_secom(dest,z)
        elif dataset_id==447: _fetch_hydraulic(dest,z)
        elif dataset_id==341: _fetch_rehab(dest,z)
        else: raise ValueError(f'Unsupported UCI dataset id: {dataset_id}')

def fetch_afdc(dest:Path,state='IL',api_key='DEMO_KEY'):
    dest.mkdir(parents=True,exist_ok=True)
    url=f'https://developer.nlr.gov/api/alt-fuel-stations/v1.json?fuel_type=ELEC&state={state}&limit=all&api_key={api_key}'
    req=urllib.request.Request(url,headers={'User-Agent':'VOLTERRA-public-data-acquisition/1.0'})
    with urllib.request.urlopen(req,timeout=90) as r: (dest/'afdc_il_ev_stations.json').write_bytes(r.read())

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--state',default='IL'); ap.add_argument('--api-key',default='DEMO_KEY'); a=ap.parse_args()
    d=ROOT/'data'/'raw'/CFG['raw_dir']
    if CFG.get('uci_id'): fetch_uci(int(CFG['uci_id']),d)
    elif CFG['ptype']=='volterra': fetch_afdc(d,a.state,a.api_key)
    else: print('No network acquisition required; published snapshot is bundled.')
    print('PUBLIC_DATA_ACQUISITION=PASS')
