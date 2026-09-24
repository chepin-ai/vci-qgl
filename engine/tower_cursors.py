"""TOWER-CURSORS-147 — 塔扫增量游标件 (root 3.147全局激活令; DEBT-FIX-146驱动, M4实测54.5s债)
理: 全扫 glob('**/awake*.log', recursive) 扫~15万节点(research/10万+app/4万), 54-56s/拍。
    增量: 目录mtime游标——目录加/删件则mtime变; 仅对mtime变更目录下探寻件(maxdepth 3)。
    兜底: 游标缺/坏→全扫; 漂移≠0→判冲, 不领证(双轨对照判据, TOWER-INCREMENTAL-PREREG-147)。
"""
import json, os, time

BASE = '/mnt/agents/output'
CURSOR = 'engine/tower_cursors.json'
SKIP = {'app/node_modules', '.git', '__pycache__', 'pylib'}


def _dirs_under(base, maxdepth=3):
    """枚举(相对路径, mtime), 跳过SKIP族与node_modules任意深处。"""
    out = {}
    base = base.rstrip('/')
    for root, dirs, _files in os.walk(base):
        rel = os.path.relpath(root, base)
        depth = 0 if rel == '.' else rel.count(os.sep) + 1
        dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__')]
        if rel != '.':
            try: out[rel] = os.stat(root).st_mtime
            except OSError: pass
        if depth >= maxdepth:
            dirs[:] = []
    return out


def scan_awake_incr(base=BASE, cursor_file=CURSOR, maxdepth=3):
    """增量awake*.log扫: (found_list, stats)。首跑=建游标全扫。"""
    t0 = time.time()
    cur = _dirs_under(base, maxdepth)
    try:
        old = json.load(open(os.path.join(base, cursor_file)))
    except Exception:
        old = {}
    changed = [d for d, m in cur.items() if old.get(d) != m]
    found = []
    for d in changed:
        full = os.path.join(base, d)
        try:
            for fn in os.listdir(full):
                if fn.startswith('awake') and fn.endswith('.log'):
                    found.append(os.path.join(d, fn))
        except OSError:
            pass
    # 游标外已知件保留: 旧found中目录未变者仍有效
    prev_found = old.get('_found', []) if isinstance(old, dict) else []
    kept = [f for f in prev_found if os.path.dirname(f) not in changed and os.path.exists(os.path.join(base, f))]
    found = sorted(set(found) | set(kept))
    out = dict(cur); out['_found'] = found
    json.dump(out, open(os.path.join(base, cursor_file), 'w'))
    stats = {'dirs_total': len(cur), 'dirs_changed': len(changed), 'elapsed_s': round(time.time() - t0, 3)}
    return found, stats


def scan_awake_full(base=BASE):
    """对照轨: 传统递归glob。"""
    import glob as g
    t0 = time.time()
    found = sorted(os.path.relpath(p, base) for p in g.glob(os.path.join(base, '**/awake*.log'), recursive=True)
                   if 'node_modules' not in p)
    return found, {'elapsed_s': round(time.time() - t0, 3)}
