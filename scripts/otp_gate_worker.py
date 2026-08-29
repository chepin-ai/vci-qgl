# -*- coding: utf-8 -*-
"""CI-OS 端 OTP 工蜂 v2(cisvr 修 2026-08-29T19Z root令⑧ 自主令):
 v2 修三疵:
  1) 发码道实证化——限流(频繁/稍后/上限)→RATE_LIMITED; 倒计时/已发送→CODE_SENT_CONFIRMED;
     皆不满足→CODE_SENT_UNVERIFIED; 页文快照(数字掩码)落 inbox/otp_gate_diag.json
  2) 登录态持久化真修——storage_state 双写 inbox/kimi_session.json(非隐藏)+.kimi_session.json(兼容)
  3) 邮码道预留(EMAIL_MODE 环境变量=1 时走邮箱码登录,邮道凭据由 repo secret 注入,本版占位)
真人闸门 = root 的手机；码只存在于 job 内存(::add-mask::)，真码文件即删(PII 闸)。
手机号取 repo secret 〈RED〉。"""
import asyncio, glob, json, os, sys, datetime, re

PHONE = os.environ.get("〈RED〉", "").strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def now():
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

def write_state(status, note):
    state = {"status": status, "note": note, "ts": now(), "worker": "cios-otp-gate-v2"}
    with open("inbox/otp_gate_state.json", "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    print(f"STATE={status}: {note}")

def write_diag(body, tag):
    try:
        masked = re.sub(r"\d{2,}", lambda m: "*" * len(m.group()), body)[:600]
        with open("inbox/otp_gate_diag.json", "w") as df:
            json.dump({"ts": now(), "tag": tag,
                       "kw": {k: (k in body) for k in ["滑块","安全验证","频繁","稍后","上限","已发送","重新发送","验证码错误","不正确","已过期","失效"]},
                       "body_masked": masked}, df, ensure_ascii=False, indent=1)
    except Exception as e:
        print("diag write fail", e)

async def open_login(pg):
    await pg.goto("https://www.kimi.com/", wait_until="commit", timeout=90000)
    await pg.wait_for_timeout(5000)
    for sel in ["text=登录以同步历史会话", "button:has-text('登录')"]:
        try:
            await pg.click(sel, timeout=4000); break
        except Exception: pass
    await pg.wait_for_timeout(1500)
    await pg.get_by_placeholder("手机号").fill(PHONE)
    try:
        await pg.check("input[type=checkbox]", timeout=3000)
    except Exception:
        try: await pg.click("label:has-text('已阅读同意')")
        except Exception: pass

async def main():
    from playwright.async_api import async_playwright
    send_only = "--send-only" in sys.argv
    verify_only = None
    for a in sys.argv:
        if a.startswith("--verify-only"):
            verify_only = a.split("=")[-1] if "=" in a else sys.argv[sys.argv.index(a)+1]
    sends = sorted(glob.glob("inbox/sendcode-*.json"))
    otps = sorted(glob.glob("inbox/otp-*.json"))
    if send_only:
        sends = ["(issue-trigger)"]
    if verify_only:
        otps = ["(issue-trigger-otp)"]; sends = []
    if not sends and not otps:
        print("nothing to consume"); return
    if not PHONE:
        write_state("FAILED", "repo secret 〈RED〉 未设置"); sys.exit(1)
    async with async_playwright() as pw:
        b = await pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        ctx = await b.new_context(user_agent=UA, viewport={"width": 1440, "height": 900}, locale="zh-CN")
        pg = await ctx.new_page()
        await pg.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        if sends:
            await open_login(pg)
            await pg.locator("button", has_text="发送验证码").first.click()
            await pg.wait_for_timeout(3500)
            body = await pg.locator("body").inner_text()
            write_diag(body, "send")
            if "滑块" in body or "安全验证" in body:
                write_state("BLOCKED", "发码遇滑块风控——请 root 手动到 kimi.com 点发送验证码后在此递码")
            elif "频繁" in body or "稍后" in body or "上限" in body:
                write_state("RATE_LIMITED", "发码被限流(实证见otp_gate_diag)——短信实未发出;请隔时窗再发,或root手动kimi.com发码后递码")
            elif re.search(r"\d+\s*s", body) or "重新发送" in body or "已发送" in body:
                write_state("CODE_SENT_CONFIRMED", "实证:按钮倒计时/已发送字样在——真短信已发,请递交验证码(码窗≈10min)")
            else:
                write_state("CODE_SENT_UNVERIFIED", "页文未见倒计时亦未见风控——发码成否未定,实证见otp_gate_diag;若1min内无短信请按RATE_LIMITED处置")
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
            write_diag(body, "verify")
            ok = ("我的 Kimi" in body or "历史会话" in body) and "手机号码登录" not in body \
                 and not any(k in body for k in ["验证码错误", "不正确", "已过期", "失效", "频繁"])
            if ok:
                await ctx.storage_state(path="inbox/kimi_session.json")
                await ctx.storage_state(path="inbox/.kimi_session.json")
                write_state("DONE", "核对成功·登录态已成并双写持久化(非隐藏名kimi_session.json在列)")
            else:
                write_state("FAILED", "码错误或已过期——请重发后立即递交新码")
            if os.path.exists(f): os.remove(f)
        await b.close()

asyncio.run(main())
