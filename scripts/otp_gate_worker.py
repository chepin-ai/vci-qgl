# -*- coding: utf-8 -*-
"""CI-OS 端 OTP 工蜂（T171）：跑在 GitHub Actions runner 上，push 触发即消费。
sendcode-*.json → 浏览器自动化走 kimi.com 官方登录页发真短信 → otp_gate_state: CODE_SENT
otp-*.json      → 填码完成登录核对 → otp_gate_state: DONE / FAILED → 真码文件即删（PII 闸）
手机号取 repo secret OTP_PHONE（root 一次性设置）；真码只存在于 job 内存，::add-mask:: 防日志泄露。"""
import asyncio, glob, json, os, sys, datetime

PHONE = os.environ.get("OTP_PHONE", "").strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def now():
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

def write_state(status, note):
    state = {"status": status, "note": note, "ts": now(), "worker": "cios-otp-gate"}
    with open("inbox/otp_gate_state.json", "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    print(f"STATE={status}: {note}")

async def open_login(pg):
    await pg.goto("https://www.kimi.com/", wait_until="commit", timeout=90000)
    await pg.wait_for_timeout(5000)
    for sel in ["text=登录以同步历史会话", "button:has-text('登录')"]:
        try:
            await pg.click(sel, timeout=4000); break
        except Exception: pass
    await pg.wait_for_timeout(1500)
    import re as _re0
    ph = _re0.sub(r"\D", "", PHONE)           # 去空格/横线/加号
    if len(ph) == 13 and ph.startswith("86"):  # 去国别码（页面已自带 +86）
        ph = ph[2:]
    print(f"phone normalized: len={len(ph)}")  # 只印长度，PII 闸
    await pg.get_by_placeholder("手机号").fill(ph)
    try:
        await pg.check("input[type=checkbox]", timeout=3000)
    except Exception:
        await pg.click("label:has-text('已阅读同意')")

async def main():
    from playwright.async_api import async_playwright
    send_only = "--send-only" in sys.argv   # issue 触发路：无 inbox 文件，直接发码
    verify_only = None                    # issue 触发路[OTP]：--verify-only 123456
    for a in sys.argv:
        if a.startswith("--verify-only"): verify_only = a.split("=")[-1] if "=" in a else sys.argv[sys.argv.index(a)+1]
    sends = sorted(glob.glob("inbox/sendcode-*.json"))
    otps = sorted(glob.glob("inbox/otp-*.json"))
    if send_only:
        sends = ["(issue-trigger)"]
    if verify_only:
        otps = ["(issue-trigger-otp)"]; sends = []
    if not sends and not otps:
        print("nothing to consume"); return
    if not PHONE:
        write_state("FAILED", "repo secret OTP_PHONE 未设置——root 请在 Settings→Secrets→Actions 添加（一次性）"); sys.exit(1)
    async with async_playwright() as pw:
        b = await pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        ctx = await b.new_context(user_agent=UA, viewport={"width": 1440, "height": 900}, locale="zh-CN")
        pg = await ctx.new_page()
        await pg.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        if sends:
            await open_login(pg)
            btn = pg.locator("button", has_text="发送验证码").first
            await btn.click()
            await pg.wait_for_timeout(6000)
            body = await pg.locator("body").inner_text()
            try: btxt = await btn.inner_text()
            except Exception: btxt = ""
            import re as _re
            countdown = bool(_re.search(r"(\d+\s*s|重新发送|秒后)", btxt)) or bool(_re.search(r"(\d+\s*s|重新发送|秒后)", body))
            err_hit = next((k for k in ["格式不正确","发送失败","操作频繁","请稍后再试","过于频繁","请先勾选"] if k in body), None)  # v2.3：剔除页面固有词「手机号」防误报
            # PII 闸：截图前掩掉输入框真值
            try:
                await pg.evaluate("document.querySelectorAll('input').forEach(i=>{i.value='***';i.placeholder='***'})")
                await pg.screenshot(path="inbox/otp_send_shot.png")
            except Exception: pass
            if "滑块" in body or "安全验证" in body:
                write_state("BLOCKED", "发码遇滑块风控——请 root 手动到 kimi.com 点发送验证码后在此递码")
            elif err_hit:
                write_state("FAILED", f"发码被页面拒绝（关键词:{err_hit}）——未证实送达，请查 artifact 截图")
            elif countdown:
                write_state("CODE_SENT_CONFIRMED", "发码钮已进入倒数态——短信已离站（正向回执），请查收手机并递交验证码")
            else:
                write_state("CODE_CLICK_UNVERIFIED", "点击已执行但无正向回执（钮未现倒数/无报错）——送达未证实，请查 artifact 截图")
            for f in sends:
                if os.path.exists(f): os.remove(f)
        for f in otps:
            code = verify_only if verify_only else json.load(open(f)).get("code", "").strip()
            print(f"::add-mask::{code}")
            await open_login(pg)
            await pg.get_by_placeholder("验证码").fill(code)
            await pg.locator("button", has_text="登录").last.click()
            await pg.wait_for_timeout(5000)
            body = await pg.locator("body").inner_text()
            ok = ("我的 Kimi" in body or "历史会话" in body) and "手机号码登录" not in body \
                 and not any(k in body for k in ["验证码错误", "不正确", "已过期", "失效", "频繁"])
            if ok:
                await ctx.storage_state(path="inbox/.kimi_session.json")   # 登录态工件（后续步骤加密入 artifacts）
                write_state("DONE", "核对成功·登录态已成——后台即刻持态开展工作")
            else:
                write_state("FAILED", "码错误或已过期——请点「发码到我手机」重发后立即递交新码")
            if os.path.exists(f): os.remove(f)   # 真码即删，PII 闸
        await b.close()

asyncio.run(main())
