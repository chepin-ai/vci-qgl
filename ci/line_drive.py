# line_drive.py — LINE-DRIVE-01 · 公域塔驱动私域线仓（系统共识: 公域CI通道驱动私域CI, 私域零Actions依赖）
# 纯事件驱动: 无定时器语义; 由 repository_dispatch / workflow_dispatch / 塔内链唤起。
# 链: LINE_PAT 读私域线仓 inbox/** → 未消费件出收执 → 回写私域 outbox/ + 本塔 receipts → 有候件自唤下一拍。
# 律: 名值分离(NAME-HYGIENE-97)——值永不入文、永不打印; seen集防重; 空转计数熔断。
import json, os, sys, time, base64, urllib.request, urllib.error, subprocess

GH = 'https://api.github.com'
TOWER = os.environ.get('GITHUB_REPOSITORY', '')
LINE = os.environ.get('LINE', 'line')
LINE_REPOS = [r.strip() for r in os.environ.get('LINE_REPOS', '').split(',') if r.strip()]
SELFTEST = '--selftest' in sys.argv

def _env(n):
    v = os.environ.get(n, '').strip()
    return v or None

def gh(pat, path, method='GET', data=None):
    req = urllib.request.Request(GH + path, method=method, headers={
        'Authorization': 'token ' + pat, 'Accept': 'application/vnd.github+json',
        'User-Agent': 'line-drive', 'Content-Type': 'application/json'})
    if data is not None:
        req.data = json.dumps(data).encode()
    for i in range(3):
        try:
            r = urllib.request.urlopen(req, timeout=25)
            body = r.read().decode()
            return r.status, (json.loads(body) if body else {})
        except urllib.error.HTTPError as e:
            if i == 2: return e.code, {}
            time.sleep(3)
        except Exception:
            if i == 2: return 0, {}
            time.sleep(3)
    return 0, {}

def sh(*a):
    return subprocess.run(a, capture_output=True, text=True)

def commit_all(msg):
    sh('git','config','user.name','line-drive'); sh('git','config','user.email','line-drive@ci-os.local')
    sh('git','add','-A')
    if sh('git','diff','--cached','--quiet').returncode == 0:
        print('[commit] nothing'); return True
    sh('git','commit','-qm', msg)
    br = sh('git','rev-parse','--abbrev-ref','HEAD').stdout.strip() or 'main'
    for i in range(8):
        sh('git','pull','--rebase','-q','origin',br)
        if sh('git','push','-q','origin','HEAD:'+br).returncode == 0:
            print('[commit] pushed:', msg[:64]); return True
        time.sleep(4)
    print('[commit] push FAILED'); return False

def main():
    ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    tst = ts.replace(':','').replace('-','')
    pat = _env('LINE_PAT') or _env('AI_FULL_PAT')
    ghtok = _env('GITHUB_TOKEN')
    print('[env] names-only:', {n: ('present' if _env(n) else 'MISSING') for n in ('LINE_PAT','AI_FULL_PAT','GITHUB_TOKEN')})
    os.makedirs('receipts/line-drive', exist_ok=True)

    # seen 集（塔侧状态）
    seen = set()
    sc, sf = gh(ghtok or pat or '', f'/repos/{TOWER}/contents/receipts/line-drive/state.json') if (ghtok or pat) else (0,{})
    if isinstance(sf, dict) and sf.get('content'):
        try: seen = set(json.loads(base64.b64decode(sf['content']).decode()).get('seen', []))
        except Exception: seen = set()

    if SELFTEST:
        st = {'v':'LINE-DRIVE-01','ts':ts,'line':LINE,'repos':LINE_REPOS,
              'names':{n:('present' if _env(n) else 'MISSING') for n in ('LINE_PAT','AI_FULL_PAT')}}
        if pat:
            c,u = gh(pat,'/user'); st['whoami_http']=c; st['login']=u.get('login','?')
            for lr in LINE_REPOS:
                c,_ = gh(pat, f'/repos/chepin-ai/{lr}'); st.setdefault('repo_access',{})[lr]=c
        fp = f'receipts/line-drive/SELFTEST-{tst}.json'
        open(fp,'w').write(json.dumps(st, ensure_ascii=False, indent=1))
        print('[selftest]', json.dumps(st, ensure_ascii=False))
        commit_all(f'LINE-DRIVE-01 selftest @{LINE} (names-only) [skip ci]')
        return

    events = []
    for lr in LINE_REPOS:
        if not pat: break
        c, lst = gh(pat, f'/repos/chepin-ai/{lr}/contents/inbox')
        if c == 404:
            # inbox 未建: 驱动即建（公域写入私域的第一件）
            body = {'message': f'inbox 目录建制 (LINE-DRIVE-01 公域驱动, {ts}) [skip ci]',
                    'content': base64.b64encode(b'').decode()}
            c2, _ = gh(pat, f'/repos/chepin-ai/{lr}/contents/inbox/.gitkeep', method='PUT', data=body)
            events.append({'kind':'repo-init','repo':lr,'http':c2})
            continue
        if not isinstance(lst, list):
            events.append({'kind':'repo-unreadable','repo':lr,'http':c}); continue
        for x in lst:
            ref = f'{lr}:{x["name"]}'
            if ref in seen or x['name'].startswith('.'): continue
            c3, fobj = gh(pat, f'/repos/chepin-ai/{lr}/contents/inbox/{urllib.parse.quote(x["name"])}')
            head = ''
            if isinstance(fobj, dict) and fobj.get('content'):
                head = base64.b64decode(fobj['content']).decode(errors='replace')[:600]
            events.append({'kind':'inbox','repo':lr,'ref':x['name'],'head':head})
    print('[drive] new events:', len(events))

    # 收执回写私域 outbox/（私域零Actions: 写由公域runner完成）
    acked = []
    for e in events:
        if e.get('kind') != 'inbox' or not pat: continue
        lr, name = e['repo'], e['ref']
        ack = {'v':'LINE-DRIVE-01','ts':ts,'tower':TOWER,'line':LINE,
               'src':f'inbox/{name}','head_excerpt':e.get('head','')[:300],
               'law':'公域CI通道驱动私域CI; 名值分离; 事件驱动'}
        body = {'message': f'outbox收执 {name} (LINE-DRIVE-01@{LINE}) [skip ci]',
                'content': base64.b64encode(json.dumps(ack,ensure_ascii=False,indent=1).encode()).decode()}
        c4, _ = gh(pat, f'/repos/chepin-ai/{lr}/contents/outbox/ack-{tst}-{name.replace("/","_")}.json', method='PUT', data=body)
        acked.append({'repo':lr,'ref':name,'http':c4})
        seen.add(f'{lr}:{name}')
    print('[drive] acked:', acked)

    rec = {'v':'LINE-DRIVE-01','ts':ts,'line':LINE,'repos':LINE_REPOS,'events':events[:80],'acked':acked}
    open(f'receipts/line-drive/LD-{tst}.json','w').write(json.dumps(rec, ensure_ascii=False, indent=1))
    open('receipts/line-drive/state.json','w').write(json.dumps({'ts':ts,'seen':sorted(seen)[-1200:]}, ensure_ascii=False))
    commit_all(f'LINE-DRIVE-01 drive @{LINE}: events={len(events)} acked={len(acked)} [skip ci]')

    # 自唤链: 有候件则唤起下一拍（事件驱动; 熔断由塔塔纪律兜底）
    if events and (ghtok or pat):
        data = {'event_type':'federation-event',
                'client_payload':{'src':'line-drive-self','line':LINE,'pend':len(events)}}
        c5, _ = gh(ghtok or pat, f'/repos/{TOWER}/dispatches', method='POST', data=data)
        print('[cascade] fired http=', c5)

main()
