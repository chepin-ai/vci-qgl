#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hexaudit.py — SRG(v,k,λ,μ) 算术可行性审计器 v2 (WQ-12-X2, 拍3.162)
v1五条件(拍3.161实证30/30+20/20) + (vi)绝对界: v<=f(f+3)/2 且 v<=g(g+3)/2。
边界律: 算术一致性≠图存在; 本器只出必要条件判决, 不出存在性断言。
"""
import math
from fractions import Fraction

# ---- Q(√D) 精确算术 (会议图分支: 特征值无理时用) ----
class QD:
    """x + y*sqrt(D), x,y∈Q, D 非平方正整数。支持 + * 与符号判定。"""
    def __init__(self, x, y, D):
        self.x, self.y, self.D = Fraction(x), Fraction(y), D
    def __add__(self, o):
        return QD(self.x + o.x, self.y + o.y, self.D)
    def __mul__(self, o):
        return QD(self.x * o.x + self.y * o.y * self.D,
                  self.x * o.y + self.y * o.x, self.D)
    def sub(self, o):
        return QD(self.x - o.x, self.y - o.y, self.D)
    def sign(self):
        """返回 -1/0/+1: 精确判定 x+y√D 的符号。"""
        if self.y == 0:
            return (self.x > 0) - (self.x < 0)
        s = (self.y > 0) - (self.y < 0)          # y 的符号
        t = (self.x > 0) - (self.x < 0)          # x 的符号
        if t == 0:
            return s
        if t == s:
            return s                              # 同号: 直接判
        c = self.x * self.x - self.y * self.y * self.D
        if c == 0:
            return 0
        return t if c > 0 else s                  # |x|>|y|√D 取x号, 反之取y号

def _sum_of_two_squares_ok(n):
    """n 可表为两平方和 ⟺ 每个 ≡3(mod4) 素因子指数为偶(Fermat)。会议图存在之必要(BRC)。"""
    m, p = n, 2
    while p * p <= m:
        if m % p == 0:
            e = 0
            while m % p == 0:
                m //= p; e += 1
            if p % 4 == 3 and e % 2 == 1:
                return False
        p += 1
    if m > 1 and m % 4 == 3:
        return False
    return True

def audit(v, k, lam, mu):
    """返回 (pass:bool, cells:dict, eig:(r,s), mult:(f,g)). 任一必要条件不过即 pass=False。"""
    cells = {}
    # (i) 基本计数恒等式
    cells['i_count'] = (k * (k - lam - 1) == mu * (v - k - 1))
    # (ii) 判别式完全平方
    D = (lam - mu) ** 2 + 4 * (k - mu)
    sq = int(math.isqrt(D))
    square = (D >= 0 and sq * sq == D)
    if D >= 0 and not square:
        # v2.1会议图分支(X2实证修: 五边形(5,2,0,1)捕v2.0缺支):
        # Δ非平方 ⟹ 必须落在会议族(v=4μ+1, k=(v-1)/2, λ=(v-5)/4, μ=(v-1)/4)
        # 且 v 可表两平方和(BRC必要); 特征值无理, f=g=(v-1)/2; Krein在Q(√D)精确判。
        conf = (v == 4 * mu + 1 and 2 * k == v - 1
                and 4 * lam == v - 5 and 4 * mu == v - 1)
        cells['ii_disc'] = bool(conf and _sum_of_two_squares_ok(v))
        if not cells['ii_disc']:
            cells['iii_eig'] = cells['iv_mult'] = cells['v_krein'] = cells['vi_abs'] = False
            return False, cells, None, None
        fm = Fraction(v - 1, 2)
        cells['iii_eig'] = True            # 无理特征值(会议情形合法)
        cells['iv_mult'] = (fm.denominator == 1)  # f=g=(v-1)/2
        r = QD(Fraction(lam - mu, 2), Fraction(1, 2), D)
        s = QD(Fraction(lam - mu, 2), Fraction(-1, 2), D)
        one = QD(1, 0, D); kd = QD(k, 0, D)
        two = QD(2, 0, D)
        a1 = (r + one) * (kd + r + two * r * s)
        b1 = (kd + r) * (s + one) * (s + one)
        a2 = (s + one) * (kd + s + two * r * s)
        b2 = (kd + s) * (r + one) * (r + one)
        k1, k2 = a1.sub(b1), a2.sub(b2)
        cells['v_krein'] = (k1.sign() <= 0 and k2.sign() <= 0)
        cells['vi_abs'] = (2 * v <= fm * (fm + 3) and 2 * v <= fm * (fm + 3))
        return all(cells.values()), cells, ('irr', 'irr'), (int(fm), int(fm))
    cells['ii_disc'] = square
    # (iii) 特征值整数
    r_num, s_num = (lam - mu) + sq, (lam - mu) - sq
    cells['iii_eig'] = (r_num % 2 == 0 and s_num % 2 == 0)
    if not cells['iii_eig']:
        cells['iv_mult'] = cells['v_krein'] = cells['vi_abs'] = False
        return False, cells, None, None
    r, s = r_num // 2, s_num // 2
    # (iv) 重数正整数且 1+f+g=v
    if r == s:
        cells['iv_mult'] = cells['v_krein'] = cells['vi_abs'] = False
        return False, cells, (r, s), None
    f = Fraction(-k - s * (v - 1), r - s)
    g = Fraction(v - 1) - f
    cells['iv_mult'] = (f.denominator == 1 and g.denominator == 1
                        and f > 0 and g > 0 and 1 + f + g == v)
    if not cells['iv_mult']:
        cells['v_krein'] = cells['vi_abs'] = False
        return False, cells, (r, s), None
    f, g = int(f), int(g)
    # (v) Krein 不等式
    k1 = (r + 1) * (k + r + 2 * r * s) - (k + r) * (s + 1) ** 2
    k2 = (s + 1) * (k + s + 2 * s * r) - (k + s) * (r + 1) ** 2
    cells['v_krein'] = (k1 <= 0 and k2 <= 0)
    # (vi) 绝对界
    cells['vi_abs'] = (2 * v <= f * (f + 3) and 2 * v <= g * (g + 3))
    return all(cells.values()), cells, (r, s), (f, g)


def audit_independent(v, k, lam, mu):
    """双实现复核版(异式独立计算, 供 100% 一致性对拍): 换公式路径重算六条件。"""
    ok = True
    ok &= (k * (k - lam - 1) == mu * (v - k - 1))
    D = (lam - mu) ** 2 + 4 * (k - mu)
    t = math.isqrt(D)
    if D >= 0 and t * t != D:
        # 会议支(独立路径): 参数恒等 + 暴力搜 a^2+b^2=v + QD精确Krein
        if not (v == 4 * mu + 1 and 2 * k == v - 1
                and 4 * lam == v - 5 and 4 * mu == v - 1):
            return False
        lim = int(math.isqrt(v)) + 1
        sos = any(a * a + b * b == v for a in range(lim) for b in range(lim))
        if not sos:
            return False
        r = QD(Fraction(lam - mu, 2), Fraction(1, 2), D)
        s = QD(Fraction(lam - mu, 2), Fraction(-1, 2), D)
        one = QD(1, 0, D); kd = QD(k, 0, D); two = QD(2, 0, D)
        a1 = (r + one) * (kd + r + two * r * s)
        b1 = (kd + r) * (s + one) * (s + one)
        a2 = (s + one) * (kd + s + two * r * s)
        b2 = (kd + s) * (r + one) * (r + one)
        k1, k2 = a1.sub(b1), a2.sub(b2)
        if not (k1.sign() <= 0 and k2.sign() <= 0):
            return False
        fm = Fraction(v - 1, 2)
        return bool(2 * v <= fm * (fm + 3))
    ok &= (D >= 0 and t * t == D)
    a = (lam - mu + t) / 2.0
    b2 = (lam - mu - t) / 2.0
    ok &= (a == int(a) and b2 == int(b2))
    a, b2 = int(a), int(b2)
    if a == b2:
        return False
    fv = (-k - b2 * (v - 1)) / (a - b2)
    gv = (v - 1) - fv
    ok &= (fv == int(fv) and gv == int(gv) and fv > 0 and gv > 0)
    if not ok:
        return False
    fv, gv = int(fv), int(gv)
    ok &= ((a + 1) * (k + a + 2 * a * b2) <= (k + a) * (b2 + 1) ** 2)
    ok &= ((b2 + 1) * (k + b2 + 2 * a * b2) <= (k + b2) * (a + 1) ** 2)
    ok &= (2 * v <= fv * (fv + 3) and 2 * v <= gv * (gv + 3))
    return bool(ok)
