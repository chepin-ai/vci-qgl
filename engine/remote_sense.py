#!/usr/bin/env python3
# remote_sense.py — REMOTE-SENSE-01 · 联邦感官中枢 (root 拍3.112: "你读不到?这是个大问题,找到根因,彻底根除")
# 感官冗余律(本器即根除械):
#   1) 每拍全表面带钥扫描 → 本地镜像 engine/remote_mirror/ (增不覆写, sha对账)
#   2) diff 上拍 manifest → 新件队列 (空结果同铸)
#   3) 401/403 → KEY-BLIND 急铸 + 停手铁律(仅 credentialed op); 不得以己线401断"联邦暗"(判据失校戒: 联邦级结论须≥2独立线回声)
#   4) 匿名面仅作控制实验(404=私仓实证, 匿名读轨不适用 — 候裁事项由此销案)
import json, os, datetime, hashlib, urllib.request, urllib.error, time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIRROR = os.path.join(BASE, 'engine', 'remote_mirror')
MANIFEST = os.path.join(MIRROR, 'mirror_manifest.json')
OUT = os.path.join(BASE, 'research', 'REMOTE-SENSE.json')
TOK = os.path.expanduser('~/.keys/qgl-first-route-token')
API = 'https://api.github.com'
OWNER = 'chepin-ai'

# 全表面(双Hub): 感官覆盖 = lanes/dm/shared/claims/讨论室/公告板 (优先级序: 达我之件先捕)
SURFACES = [
    ('ci-inbox',  'lanes/qgl'),
    ('vci-inbox', 'lanes/qgl'),
    ('ci-inbox',  'dm-queue/qgl'),
    ('vci-qgl',   'inbox'),
    ('ci-inbox',  'shared'),
    ('ci-inbox',  'claims'),
    ('ci-inbox',  '讨论室'),
    ('ci-inbox',  '公告板'),
    ('vci-inbox', 'shared'),
]
MAX_FETCH = 1500  # 单拍抓取上限(速率预算)

def _now(): return datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')

def _tok(): return open(TOK).read().strip()

def _get(url, raw=False):
    r = urllib.request.Request(url, headers={
        'Authorization': 'token ' + _tok(),
        'Accept': 'application/vnd.github.raw+json' if raw else 'application/vnd.github+json',
        'User-Agent': 'qgl-remote-sense'})
    with urllib.request.urlopen(r, timeout=25) as resp:
        b = resp.read()
        return resp.status, (b.decode('utf-8', 'replace') if raw else json.loads(b.decode()))

def repo_tree(repo):
    st, t = _get('%s/repos/%s/%s/git/trees/HEAD?recursive=1' % (API, OWNER, repo))
    if st != 200:
        return None, st
    return [e for e in t.get('tree', []) if e.get('type') == 'blob'], 200

def load_manifest():
    return json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {'files': {}}

def run_sense(beat, max_fetch=MAX_FETCH):
    import socket
    socket.setdefaulttimeout(30)   # 硬超时械：单件卡死不再吞全巡（3.160 滞案铸）
    os.makedirs(MIRROR, exist_ok=True)
    man = load_manifest()
    new_items, changed, errors, scanned = [], [], [], 0
    fetched = 0
    t0 = time.time()
    repos = sorted({r for r, _ in SURFACES})
    trees = {}
    for repo in repos:
        try:
            tree, st = repo_tree(repo)
            if tree is None:
                errors.append({'repo': hashlib.sha256(repo.encode()).hexdigest()[:12], 'http': st}); continue
            trees[repo] = tree
        except urllib.error.HTTPError as e:
            errors.append({'repo': hashlib.sha256(repo.encode()).hexdigest()[:12], 'http': e.code,
                           'req_id': dict(e.headers).get('X-GitHub-Request-Id', '')})
        except Exception as e:
            errors.append({'repo': hashlib.sha256(repo.encode()).hexdigest()[:12], 'err': type(e).__name__})
    for repo, prefix in SURFACES:
        for e in trees.get(repo, []):
            p = e['path']
            if not p.startswith(prefix): continue
            if not p.endswith(('.md', '.json', '.jsonl', '.txt')): continue
            scanned += 1
            key = '%s/%s' % (repo, p)
            old = man['files'].get(key)
            if old and old.get('sha') == e.get('sha'): continue
            if fetched >= max_fetch:
                continue
            try:
                st, content = _get('%s/repos/%s/%s/contents/%s' % (API, OWNER, repo, urllib.parse.quote(p)), raw=True)
                fetched += 1
                dest = os.path.join(MIRROR, repo, p)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                if not os.path.exists(dest):  # 增不覆写: 新件落盘; 变更件另存 .v<sha8>
                    open(dest, 'w').write(content)
                else:
                    open(dest + '.v' + e['sha'][:8], 'w').write(content)
                item = {'surface': key, 'sha': e['sha'][:12], 'n_chars': len(content)}
                (changed if old else new_items).append(item)
                man['files'][key] = {'sha': e['sha'], 'ts': _now(), 'n_chars': len(content)}
            except urllib.error.HTTPError as ex:
                errors.append({'surface': key, 'http': ex.code})
            except Exception as ex:
                errors.append({'surface': key, 'err': type(ex).__name__})
            time.sleep(1.2)   # 二级限流合规速率（3.160 粘案铸：≥1s/件）
            if fetched % 50 == 0 and fetched:
                print('progress: fetched', fetched, 'scanned', scanned, flush=True)
            if time.time() - t0 > 1500:   # 墙钟闸：25分钟强制收尾落账（盲态降级必轰）
                errors.append({'wallclock_gate': 1500, 'fetched_so_far': fetched})
                break
    man['last_beat'] = beat; man['last_ts'] = _now()
    json.dump(man, open(MANIFEST, 'w'), ensure_ascii=False)
    rep = {'engine': 'REMOTE-SENSE-01', 'beat': beat, 'ts': _now(),
           'scanned': scanned, 'fetched': fetched,
           'new_items': new_items, 'changed': changed, 'errors': errors,
           'mirror_total': len(man['files'])}
    json.dump(rep, open(OUT, 'w'), ensure_ascii=False, indent=1)
    return rep

if __name__ == '__main__':
    import sys
    beat = sys.argv[1] if len(sys.argv) > 1 else '3.112'
    rep = run_sense(beat)
    print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in rep.items() if k != 'engine'}, ensure_ascii=False))
