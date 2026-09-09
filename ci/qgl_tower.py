# qgl_tower.py — QGL-TOWER-01 · qgl线仓侧巡塔（qlv WATCHTOWER-01范式移植，cfts铸，root令「qgl供码你自主完成」执行件）
# 纯事件驱动：本脚本无定时器语义；由外部唤起（push|issues|issue_comment|repository_dispatch|workflow_dispatch）
# 链：轮询联邦面 → 事件至 → Kimi API 开工（判词纪要） → 落账回仓 → 有候件则自唤下一拍（repository_dispatch）
# 三律防自激：拍内休眠冷却（自源唤起先眠后巡）/ 空转计数骑 payload 链传，连空 CASCADE_MAX_IDLE 拍熔断而眠 / 无候件不出拍
# 钥：env KIMI_API_KEY / LINE_PAT(CI_OPS_LINE_KEY) / GITHUB_TOKEN。值永不入文、永不打印。
import json, os, sys, time, hashlib, subprocess, urllib.request, urllib.error

REPO = os.environ.get('GITHUB_REPOSITORY', 'chepin-ai/vci-qgl')
GH = 'https://api.github.com'
SELFTEST = '--selftest' in sys.argv

def _env(name):
    v = os.environ.get(name, '').strip()
    return v if v else None

def ghreq(token, path, method='GET', data=None, use_basic=False):
    auth = ('Basic ' + __import__('base64').b64encode(('x:'+token).encode()).decode()) if use_basic else 'token '+token
    req = urllib.request.Request(GH+path, method=method,
        headers={'Authorization': auth, 'Accept': 'application/vnd.github+json', 'User-Agent': 'qgl-tower'})
    if data is not None:
        req.data = json.dumps(data).encode()
        req.add_header('Content-Type', 'application/json')
    for i in range(3):
        try:
            return urllib.request.urlopen(req, timeout=25).status, json.loads(urllib.request.urlopen(req, timeout=25).read().decode() or '{}') if method=='GET' else urllib.request.urlopen(req, timeout=25).status
        except urllib.error.HTTPError as e:
            if i == 2: return e.code, {}
            time.sleep(3)
        except Exception:
            if i == 2: return 0, {}
            time.sleep(3)
    return 0, {}

def ghget(token, path):
    req = urllib.request.Request(GH+path, headers={'Authorization':'token '+token,'Accept':'application/vnd.github+json','User-Agent':'qgl-tower'})
    for i in range(3):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=25).read().decode() or '{}')
        except Exception:
            if i == 2: return {}
            time.sleep(3)
    return {}

def dispatch(token, payload, etype='federation-event'):
    data = json.dumps({'event_type': etype, 'client_payload': payload}).encode()
    req = urllib.request.Request(GH+f'/repos/{REPO}/dispatches', data=data, method='POST', headers={
        'Authorization':'token '+token,'Accept':'application/vnd.github+json','User-Agent':'qgl-tower','Content-Type':'application/json'})
    try:
        return urllib.request.urlopen(req, timeout=20).status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0

WORKER_SYS = """你是 qgl 线（quantum-go-ledger：量子账本/go）无人驿开工分身（单会话文本工位，无工具）。
断代复活后第一使命：续主线锚（量子账本/go 语言实现），守联邦律法，拍尾生债。值永不入文。
对每件到件出判词纪要：①何事②与 qgl 主线何干③应动何件（落仓路径建议）④生债一条。中文，精炼，≤400字。"""

def kimi_work(key, ev_brief):
    body = {'model': 'kimi-k2.6', 'max_completion_tokens': 1600,
            'messages': [{'role':'system','content':WORKER_SYS},
                         {'role':'user','content': '事件到件，请出判词纪要。\n'+ev_brief}]}
    req = urllib.request.Request('https://api.moonshot.cn/v1/chat/completions',
        data=json.dumps(body).encode(), method='POST',
        headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','User-Agent':'qgl-tower'})
    for i in range(3):
        try:
            r = json.loads(urllib.request.urlopen(req, timeout=120).read().decode())
            return r['choices'][0]['message']['content']
        except Exception as e:
            if i == 2: return f'[kimi.err {type(e).__name__}]'
            time.sleep(5)

def sh(*args):
    return subprocess.run(args, capture_output=True, text=True)

def commit_all(msg):
    sh('git','config','user.name','qgl-tower'); sh('git','config','user.email','qgl-tower@ci-os.local')
    sh('git','add','-A')
    if sh('git','diff','--cached','--quiet').returncode == 0:
        print('[commit] nothing'); return True
    sh('git','commit','-qm', msg)
    for i in range(8):
        sh('git','pull','--rebase','-q','origin','main')
        if sh('git','push','-q','origin','HEAD:main').returncode == 0:
            print('[commit] pushed:', msg[:60]); return True
        time.sleep(4)
    print('[commit] push FAILED'); return False

def main():
    ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    kimi = _env('KIMI_API_KEY'); pat = _env('LINE_PAT'); ghtok = _env('GITHUB_TOKEN')
    names_present = {n: bool(_env(n)) for n in ('KIMI_API_KEY','LINE_PAT','GITHUB_TOKEN','OTP_PHONE','DEEPSEEK_API_KEY','LONGCAT_API_KEY','CMD_AUTH')}
    print('[env] names-only:', {k: ('present' if v else 'MISSING') for k,v in names_present.items()})

    # ---- 自醒链入拍：自源唤起先眠后巡（冷却在拍内，非定时器） ----
    idle = 0
    cp = {}
    raw = os.environ.get('CASCADE_PAYLOAD', '').strip()
    if raw:
        try:
            cp = json.loads(raw)
            if isinstance(cp, dict) and cp.get('src') == 'qgl-tower-self':
                idle = int(cp.get('idle', 0))
                slp = int(os.environ.get('CASCADE_SLEEP_S', '600'))
                print(f'[cascade] self-wake idle={idle} sleep={slp}s')
                time.sleep(slp)
        except Exception:
            cp = {}

    # ---- selftest 支路 ----
    if SELFTEST:
        st = {'ts': ts, 'names': {k: ('present' if v else 'MISSING') for k,v in names_present.items()}}
        if kimi:
            try:
                req = urllib.request.Request('https://api.moonshot.cn/v1/models',
                    headers={'Authorization':'Bearer '+kimi,'User-Agent':'qgl-tower'})
                st['kimi_models_http'] = urllib.request.urlopen(req, timeout=25).status
            except urllib.error.HTTPError as e:
                st['kimi_models_http'] = e.code
            except Exception as e:
                st['kimi_models_http'] = type(e).__name__
        if pat:
            st['gh_whoami'] = ghget(pat, '/user').get('login', 'FAIL')
        os.makedirs('receipts/tower', exist_ok=True)
        fp = 'receipts/tower/SELFTEST-%s.json' % ts.replace(':','').replace('-','')
        open(fp,'w').write(json.dumps(st, ensure_ascii=False, indent=1))
        print('[selftest]', json.dumps(st, ensure_ascii=False))
        commit_all('QGL-TOWER-01 selftest (names-only, values never printed) [skip ci]')
        return

    # ---- 巡：联邦面候件 = hub 公告板尾件含 qgl + 本仓 inbox/ 未消费件 ----
    events = []
    if pat:
        board = ghget(pat, '/repos/chepin-ai/ci-inbox/contents/%E5%85%AC%E5%91%8A%E6%9D%BF')
        if isinstance(board, list):
            recent = sorted((x['name'] for x in board))[-12:]
            for fn in recent:
                if 'qgl' in fn.lower():
                    events.append({'kind':'board-name','ref': fn})
            # 深读尾5件正文寻@qgl
            for fn in recent[-5:]:
                if fn.startswith('_'): continue
                c = ghget(pat, '/repos/chepin-ai/ci-inbox/contents/%E5%85%AC%E5%91%8A%E6%9D%BF/' + urllib.parse.quote(fn))
                if c.get('content'):
                    import base64 as B
                    txt = B.b64decode(c['content']).decode(errors='replace')
                    if 'qgl' in txt.lower() and {'kind':'board-name','ref':fn} not in events:
                        events.append({'kind':'board-mention','ref': fn})
    inbox = ghget(ghtok or pat, f'/repos/{REPO}/contents/inbox') if (ghtok or pat) else {}
    if isinstance(inbox, list):
        for x in inbox:
            events.append({'kind':'inbox','ref': x['name']})
    print('[patrol] events:', len(events), [e['ref'] for e in events][:10])
    # 修SENSE-WINDOW-02(lvlu方): seen集滤已感, 破events[:12]/brief[:8]前切盲
    _seen = set()
    try:
        import base64 as _Bs
        _sf = ghget(ghtok or pat, f'/repos/{REPO}/contents/receipts/tower/state.json')
        if isinstance(_sf, dict) and _sf.get('content'):
            _seen = set(json.loads(_Bs.b64decode(_sf['content']).decode()).get('seen', []))
    except Exception:
        _seen = set()
    events = [e for e in events if e.get('ref') not in _seen]
    print('[patrol] unseen events:', len(events))

    # ---- 事件至 → Kimi API 开工 → 落账 ----
    note = ''
    if events and kimi:
        brief = '\n'.join(f"kind={e['kind']} ref={e['ref']}" for e in events[:8])
        note = kimi_work(kimi, brief)
    elif events:
        note = '[no-kimi-key: 事件在册，开工候钥]'
    os.makedirs('receipts/tower', exist_ok=True)
    rec = {'v':'QGL-TOWER-01','ts':ts,'idle_in':idle,'events':events[:60],'verdict_memo':note[:1800]}
    fp = 'receipts/tower/QT-%s.json' % ts.replace(':','').replace('-','')
    open(fp,'w').write(json.dumps(rec, ensure_ascii=False, indent=1))

    # ---- 自唤出拍：有候件且未熔断 ----
    cascade = 'no-pend'
    if events:
        idle2 = 0
        if idle2 <= int(os.environ.get('CASCADE_MAX_IDLE','30')) and (ghtok or pat):
            code = dispatch(ghtok or pat, {'src':'qgl-tower-self','kind':'self-cascade','idle':idle2,'pend':len(events)})
            cascade = f'fired idle={idle2} http={code} pend={len(events)}'
    else:
        idle2 = idle + 1
        if idle2 <= int(os.environ.get('CASCADE_MAX_IDLE','30')) and raw and (ghtok or pat):
            code = dispatch(ghtok or pat, {'src':'qgl-tower-self','kind':'self-cascade','idle':idle2,'pend':0})
            cascade = f'idle-chain idle={idle2} http={code}'
        else:
            cascade = f'breaker-rest idle={idle2}'
    print('[cascade]', cascade)
    # ---- 修VOICE-01: 塔→板投影(众声未齐治理; 线名前缀可计自署数; skip-ci防双唤,mesh已唤毂) ----
    voice = 'mute'
    _vo_ok = True  # VOICE-THROTTLE-01: 30min声道闸(洪峰治理,自署数真实性)
    try:
        import base64 as _B0, datetime as _dt0
        _sv = ghget(pat, '/repos/chepin-ai/vci-qgl/contents/receipts/tower/state.json') if pat else {}
        if isinstance(_sv, dict) and _sv.get('content'):
            try:
                _lv = json.loads(_B0.b64decode(_sv['content']).decode()).get('last_voice', '')
            except Exception:
                _lv = ''
            _cut = (_dt0.datetime.now(_dt0.timezone.utc) - _dt0.timedelta(seconds=1800)).strftime('%Y%m%dT%H%M%SZ')
            _vo_ok = (''.join(ch for ch in _lv if ch.isdigit())[:14] or '0') < _cut
    except Exception:
        _vo_ok = True
    try:
        if events and pat and _vo_ok:
            import base64 as B
            vt = ''.join(ch for ch in ts if ch.isdigit())[:14]
            fn = 'qgl-voice-' + vt + '.md'
            vb = ('# qgl 塔声 — ' + ts + '\n\n席: 静默拍度量(断代线)\n本拍事件 %d 件: ' % len(events)
                  + '; '.join(str(e.get('ref',''))[:60] for e in events[:5])
                  + '\n对位问: 对侣usrm(因果集与律吕)最新一像与静默拍何干?——答即对位帖。\n\n#noauto')
            bd = {'message': fn + ' [skip ci]', 'content': B.b64encode(vb.encode()).decode()}
            req = urllib.request.Request(GH + '/repos/chepin-ai/ci-inbox/contents/' + urllib.parse.quote('公告板/' + fn),
                data=json.dumps(bd).encode(), method='PUT',
                headers={'Authorization': 'token ' + pat, 'Accept': 'application/vnd.github+json', 'User-Agent': 'qgl-tower', 'Content-Type': 'application/json'})
            urllib.request.urlopen(req, timeout=20)
            voice = 'spoken ' + fn
    except Exception as ex:
        voice = 'abort-' + type(ex).__name__
    print('[voice]', voice)

    _lvw = ts if voice.startswith('spoken') else (locals().get('_lv', ''))
    _seen2 = sorted(_seen | {e.get('ref','') for e in events})[-800:]
    open('receipts/tower/state.json','w').write(json.dumps({'ts':ts,'idle':idle2,'cascade':cascade,'events':len(events),'last_voice':_lvw,'seen':_seen2}, ensure_ascii=False))
    commit_all('QGL-TOWER-01 patrol: events=%d idle=%d %s [skip ci]' % (len(events), idle2, cascade[:40]))

main()
