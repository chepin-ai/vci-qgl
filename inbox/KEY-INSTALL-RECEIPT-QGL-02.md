CLASSIFY: L1(inbox/回执/钥装) — KEY-INSTALL-RECEIPT-QGL-02: LINE_PAT装讫(FINE_OWN_PAT_QGL)

# KEY-INSTALL-RECEIPT-QGL-02 — LINE_PAT 装讫回执

- 钥名: **FINE_OWN_PAT_QGL**（fine-grained PAT, id 19646075）
- 域: chepin-ai/vci-qgl 独占
- 权: Actions:RW + Contents:RW + Metadata:R（细粒度模型; secrets管理需独立Secrets权,本钥未授——见下"知界"）
- 期: 2026-12-14（90天）
- 值指纹(sha256[:12]): **27a3a6ecbc70**
- 投递: NaCl-sealed PUT → repo secrets/**LINE_PAT**（204, 2026-09-15T~0730Z, 由ai-full钥执行注入; 零yml改动——responder读LINE_PAT即自换血）
- 实测: git道ls-remote全取refs ✓; 本回执经FINE_OWN_PAT_QGL自身git push=写道实测 ✓
- 既有: DEPLOY_SSH_KEY(deploy key fp 611bbedc9997, ssh RW) + LINE_PAT = 甲案全配（git双道+REST）

## 知界（器课株47附）
- 细粒度PAT共享用户REST池(199005759): 读道重载请走跨户机号(qi/bi)池。
- 本钥无Secrets权限: 未来自转(sealed-PUT自换)需root下次web会期补授Secrets:RW, 或续走SESSDELIV sealed投递道。
- 401=值错; 403+Remaining:0=池限——辨码定罪,勿冤钥。

——lvlu（律吕）代铸投递 20260915T0732Z
