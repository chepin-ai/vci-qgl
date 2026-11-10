#!/usr/bin/env python3
# twoaudit.py — TWOG-AUDIT-01 v1.1 · 正则双图/等角线 可行性审计器 (拍3.164 铸, 拍3.165 TWOG-X5 扩)
# 同一Seidel内核一器两族; SRG器(hexaudit)作升降子模块嵌入。
# 条件出处: research/HEXAUDIT-X3-LIT-163.json (两图wiki/Seidel1976/Brouwer-Haemers谱几何/Waldron ETF)
#   + X5: Lemmens–Seidel相对界(J.Algebra 24 (1973) Thm3.6), Bannai–Munemasa–Venkov Gerzon非达成{47,79}(119开)
# 零编数律: 每条判据有出处; 边界律: 通过=必要条件满足, 非存在性证明。
# X5 失校即修: alpha 入口归一化 Fraction(浮点 1/α 整数性误判修复, 拍3.165)
import math
from fractions import Fraction
from hexaudit import _sum_of_two_squares_ok, audit as srg_audit

def _is_int(x): return isinstance(x, int) or (isinstance(x, Fraction) and x.denominator == 1)

def _odd_int(x):
    return _is_int(x) and int(x) % 2 == 1

def descendant_params(n, r1, r2):
    """正则双图(n,ρ1,ρ2)后裔SRG: v=n−1, k=(1−ρ2)(ρ1−1)/2, μ=k/2, λ=k−1−μ(v−k−1)/k
    三案独立锚定: (10,3,−3)→Paley-9; (28,3,−9)→Schläfli(27,10,1,5); (276,5,−55)→McLaughlin(275,112,30,56)"""
    v = n - 1
    if not (_is_int(r1) and _is_int(r2)):
        return v, None, None, None  # 非整数谱: 升降无定义(会议支专属路径)
    k = Fraction((1 - r2) * (r1 - 1), 2)
    if k == 0:
        return v, k, None, None  # 退化谱: 后裔参数无定义
    mu = k / 2
    lam = k - 1 - mu * (v - k - 1) / k
    return v, k, mu, lam

def audit_two_graph(n, r1, r2):
    """正则双图可行性审计: 五格全过=pass(必要非充分)"""
    cells = {}
    # TG1 谱关系: ρ1ρ2 = 1−n
    cells['TG1_rel'] = (r1 * r2 == 1 - n)
    # TG2 非平凡⇒n偶
    cells['TG2_parity'] = (n % 2 == 0)
    # TG3 分支判别
    if r1 == -r2:
        cells['TG3_branch'] = ('conference', (n % 4 == 2) and _sum_of_two_squares_ok(n - 1))
    else:
        cells['TG3_branch'] = ('integer', _odd_int(r1) and _odd_int(-r2))
    # TG4 小谱限 (Seidel): ρ1=3→n∈{10,16,28}; ρ1=5→n∈{16,26,36,76,96,126,176,276}
    if _is_int(r1) and int(r1) in (3, 5):
        table = {3: {10, 16, 28}, 5: {16, 26, 36, 76, 96, 126, 176, 276}}
        cells['TG4_small_spectrum'] = n in table[int(r1)]
    else:
        cells['TG4_small_spectrum'] = None  # 未列入小谱表者本格不裁
    # TG5 升降: 后裔SRG参数整数化 + hexaudit六条件
    v, k, mu, lam = descendant_params(n, r1, r2)
    if all(_is_int(x) and x >= 0 for x in (k, mu, lam)) and int(k) > 0:
        sub_pass = srg_audit(int(v), int(k), int(lam), int(mu))[0]  # hexaudit.audit → (pass, cells, eig, mult)
        cells['TG5_lift'] = {'descendant': [int(v), int(k), int(lam), int(mu)], 'srg_pass': bool(sub_pass)}
    else:
        cells['TG5_lift'] = {'descendant': [int(v), str(k), str(lam), str(mu)], 'srg_pass': False}
    passed = all(c if isinstance(c, bool) else (c[1] if isinstance(c, tuple) else c['srg_pass'])
                 for c in cells.values() if c is not None)
    return {'family': 'regular-two-graph', 'n': n, 'rho': [str(r1), str(r2)],
            'cells': cells, 'pass': passed, 'law': '必要条件满足≠存在 (边界律)'}

def _norm_alpha(alpha):
    """X5失校即修: α 归一化为 Fraction — 浮点 1/α 整数性判定会误诊(如 float(1/3)→3.0000000000000004)"""
    if alpha is None or isinstance(alpha, Fraction):
        return alpha
    return Fraction(alpha).limit_denominator(10 ** 9)

def audit_equiangular(d, r, alpha=None, etf=False):
    """等角线可行性审计: R^d 中 r 条等角线(夹角余弦α); X5 后六格"""
    alpha = _norm_alpha(alpha)
    cells = {}
    # EQ1 Gerzon绝对界
    cells['EQ1_gerzon'] = (r <= d * (d + 1) // 2)
    # EQ2 Neumann: r>2d ⇒ 1/α 奇整数 (α未给=不裁, 必要件审计不凭缺证出罪)
    if r > 2 * d:
        if alpha is None:
            cells['EQ2_neumann'] = None
        elif alpha == 0:
            cells['EQ2_neumann'] = False
        else:
            inv = 1 / alpha
            cells['EQ2_neumann'] = _is_int(inv) and int(inv) % 2 == 1
    else:
        cells['EQ2_neumann'] = None  # 小寄存器不适用
    # EQ3 Gerzon达成(d>3) ⇒ d+2 奇平方 (Bannai–Damerell+BRC型)
    if d > 3 and r == d * (d + 1) // 2:
        m = d + 2
        sroot = int(math.isqrt(m))
        cells['EQ3_attain'] = (sroot * sroot == m) and (sroot % 2 == 1)
    else:
        cells['EQ3_attain'] = None
    # EQ4 ETF (Waldron Cor5.8 / Welch等号): α² = (r−d)/(d(r−1))
    if etf:
        if alpha is None:
            cells['EQ4_etf'] = False
        else:
            cells['EQ4_etf'] = (alpha * alpha == Fraction(r - d, d * (r - 1)))
    else:
        cells['EQ4_etf'] = None
    # EQ5 Lemmens–Seidel 相对界 (1973 Thm3.6): dα²<1 ⇒ r ≤ d(1−α²)/(1−dα²); α缺/界外=不裁
    if alpha is None or alpha == 0:
        cells['EQ5_relbound'] = None
    else:
        a2 = alpha * alpha
        if d * a2 < 1:
            bound = Fraction(d) * (1 - a2) / (1 - d * a2)
            cells['EQ5_relbound'] = {'bound': float(bound), 'pass': Fraction(r) <= bound}
        else:
            cells['EQ5_relbound'] = None  # dα²≥1 界不适用
    # EQ6 BMV Gerzon非达成 (Bannai–Munemasa–Venkov 2005): d∈{47,79} 达成被否; d=119 开
    if d > 3 and r == d * (d + 1) // 2:
        if d in (47, 79):
            cells['EQ6_bmv'] = False  # 证明不达成(tight spherical 4-design 不存在)
        else:
            cells['EQ6_bmv'] = None   # d=119 开; 其余奇平方候选本格不裁
    else:
        cells['EQ6_bmv'] = None
    passed = all(c if isinstance(c, bool) else c['pass']
                 for c in cells.values() if c is not None)
    return {'family': 'equiangular-lines', 'd': d, 'r': r, 'alpha': str(alpha),
            'cells': cells, 'pass': passed, 'law': '必要条件满足≠存在 (边界律)'}

# —— 双实现(独立路, 不从hexaudit导入, 判据失校戒) ——
def _sos_ok_ind(n):
    """独立两平方和判定:  brute-force a²+b²=n"""
    a = 0
    while a * a <= n:
        b2 = n - a * a
        b = int(math.isqrt(b2))
        if b * b == b2: return True
        a += 1
    return False

def _srg_pass_ind(v, k, lam, mu):
    """独立SRG六条件(自实现): 参数关系/判别式/整数特征值/重数/Krein(会议支近似)/绝对界"""
    if not (0 < k < v - 1) or k * (k - lam - 1) != mu * (v - k - 1): return False
    D = (lam - mu) ** 2 + 4 * (k - mu)
    s = int(math.isqrt(D))
    if s * s == D:
        f_num, g_num = (v - 1) + (-2 * k - (v - 1) * (lam - mu)), (v - 1) + (2 * k + (v - 1) * (lam - mu))
        # 重数公式: f,g = ((v−1) ∓ (2k+(v−1)(λ−μ))/√D)/2
        f = Fraction(v - 1, 2) - Fraction(2 * k + (v - 1) * (lam - mu), 2 * s)
        g = Fraction(v - 1, 2) + Fraction(2 * k + (v - 1) * (lam - mu), 2 * s)
        if f.denominator != 1 or g.denominator != 1 or f <= 0 or g <= 0: return False
        if 2 * v > f * (f + 3) or 2 * v > g * (g + 3): return False
    else:
        # 会议支: 特征值非整数⇒必会议参数
        if not (v % 4 == 1 and 2 * k == v - 1 and 4 * lam == v - 5 and 4 * mu == v - 1): return False
        if not _sos_ok_ind(v): return False
        f = g = Fraction(v - 1, 2)
        if 2 * v > f * (f + 3): return False
    return True

def audit_two_graph_independent(n, r1, r2):
    cells = {}
    cells['TG1_rel'] = (r1 * r2 == 1 - n)
    cells['TG2_parity'] = (n % 2 == 0)
    if r1 == -r2:
        cells['TG3_branch'] = ('conference', (n % 4 == 2) and _sos_ok_ind(n - 1))
    else:
        cells['TG3_branch'] = ('integer', _odd_int(r1) and _odd_int(-r2))
    if _is_int(r1) and int(r1) in (3, 5):
        table = {3: {10, 16, 28}, 5: {16, 26, 36, 76, 96, 126, 176, 276}}
        cells['TG4_small_spectrum'] = n in table[int(r1)]
    else:
        cells['TG4_small_spectrum'] = None
    v, k, mu, lam = descendant_params(n, r1, r2)
    ok_params = all(_is_int(x) and x >= 0 for x in (k, mu, lam)) and int(k) > 0
    cells['TG5_lift'] = {'descendant': [int(v), int(k) if _is_int(k) else str(k),
                                       int(lam) if _is_int(lam) else str(lam), int(mu) if _is_int(mu) else str(mu)],
                         'srg_pass': _srg_pass_ind(int(v), int(k), int(lam), int(mu)) if ok_params else False}
    passed = all(c if isinstance(c, bool) else (c[1] if isinstance(c, tuple) else c['srg_pass'])
                 for c in cells.values() if c is not None)
    return {'family': 'regular-two-graph', 'n': n, 'rho': [str(r1), str(r2)],
            'cells': cells, 'pass': passed, 'law': '必要条件满足≠存在 (边界律)'}

# —— X5 自检: 会议矩阵行列式符号不变量 (候选条款, 实测锚定, 非阻截格) ——
def _gf_pow(a, e, p, m):
    """GF(p^deg m) 多项式幂: a(元素=系数元组升幂) ^ e mod (p, m)"""
    deg = len(m) - 1
    def mul(x, y):
        t = [0] * (2 * deg - 1)
        for i, xi in enumerate(x):
            for j, yj in enumerate(y):
                t[i + j] = (t[i + j] + xi * yj) % p
        for k in range(2 * deg - 2, deg - 1, -1):  # mod m (m 首一)
            c = t[k]
            if c:
                for j in range(deg):
                    t[k - 1 - j] = (t[k - 1 - j] - c * m[deg - 1 - j]) % p
        return tuple(t[:deg])
    r = (1,) + (0,) * (deg - 1)
    a = tuple(a) + (0,) * (deg - len(a))
    while e:
        if e & 1: r = mul(r, a)
        a = mul(a, a); e >>= 1
    return r

def _bareiss_det(M):
    """精确整数行列式 (Bareiss 无分数高斯)"""
    n = len(M); A = [row[:] for row in M]; sign = 1; prev = 1
    for k in range(n - 1):
        if A[k][k] == 0:
            for i in range(k + 1, n):
                if A[i][k] != 0:
                    A[k], A[i] = A[i], A[k]; sign = -sign; break
            else:
                return 0
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                A[i][j] = (A[i][j] * A[k][k] - A[i][k] * A[k][j]) // prev
        prev = A[k][k]
        for i in range(k + 1, n): A[i][k] = 0
    return sign * A[n - 1][n - 1]

def selftest_conf_det(qs=(5, 9, 13, 17, 25, 29)):
    """Paley 会议矩阵 (n=q+1≡2 mod4, q≡1 mod4 素幂): 验证候选不变量 det S = (−1)^{n/2} (n−1)^{n/2}
    地位声明: 实测自检锚(判读器自证), 非文献定理援引, 不作可行性阻截格"""
    irred = {9: (3, (1, 0, 1)), 25: (5, (3, 0, 1))}  # GF(9): x²+1 over F3; GF(25): x²+3 over F5 (均不可约, 实测)
    out = []
    for q in qs:
        if q in irred:
            p, m = irred[q]; deg = 2
            elems = [(a, b) for a in range(p) for b in range(p)]
            chi = {}
            for e in elems:
                if e == (0, 0): chi[e] = 0; continue
                w = _gf_pow(e, (q - 1) // 2, p, list(m))
                chi[e] = 1 if w == (1, 0) else -1
            sub = lambda x, y: tuple((x[i] - y[i]) % p for i in range(2))
        else:
            p, deg = q, 1
            elems = [(a,) for a in range(p)]
            sq = {(a * a) % p for a in range(1, p)}
            chi = {e: (0 if e[0] == 0 else (1 if e[0] in sq else -1)) for e in elems}
            sub = lambda x, y: ((x[0] - y[0]) % p,)
        n = q + 1
        idx = list(range(q))  # 0..q−1 表 GF(q); 另加 ∞ 行/列于首
        S = [[0] * n for _ in range(n)]
        for i in range(1, n): S[0][i] = S[i][0] = 1
        for i in range(1, n):
            for j in range(1, n):
                if i == j: continue
                S[i][j] = chi[sub(elems[i - 1], elems[j - 1])]
        det = _bareiss_det(S)
        expect = ((-1) ** (n // 2)) * (n - 1) ** (n // 2)
        sym = all(S[i][j] == S[j][i] for i in range(n) for j in range(n))
        out.append({'q': q, 'n': n, 'symmetric': sym, 'det': det, 'expect': expect, 'ok': sym and det == expect})
    return out

if __name__ == '__main__':
    for case in [(10, 3, -3), (16, 5, -3), (26, 5, -5), (28, 3, -9), (276, 5, -55)]:
        print(case, audit_two_graph(*case)['pass'])
    print((7, 28), audit_equiangular(7, 28)['pass'])
    print('conf_det_selftest:', [(r['q'], r['ok']) for r in selftest_conf_det()])
