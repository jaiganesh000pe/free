"""Agent 4: bulk email via smtplib with deliverability best practices:
- one persistent TLS connection, throttled sending, daily cap
- personalised plain+HTML multipart, real Message-ID/Date, Reply-To
- RFC 8058 one-click List-Unsubscribe + in-body unsubscribe + physical address
- suppression list honoured, only addresses found on public profiles
- (you must still set SPF/DKIM/DMARC on your sending domain)"""
import smtplib, time, html, requests
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from .. import tracking
from ..config import Config
from ..store import suppressed

def _from():
    return Config.SENDER_EMAIL or Config.SMTP_USER

def configured():
    if Config.EMAIL_BACKEND == "brevo":
        return bool(Config.BREVO_API_KEY and _from())
    return bool(Config.SMTP_HOST and Config.SMTP_USER)

class _Safe(dict):
    def __missing__(self, k): return ""

def _build(run, c, subject, body, base):
    first = (c["name"].split() or [""])[0]
    ctx = _Safe(first_name=first, name=c["name"], job_title=run["profile"]["title"])
    text = body.format_map(ctx)
    unsub = f'{base}/unsubscribe/{tracking.make(run["id"], c["id"], email=c["email"])}'
    pixel = f'{base}/t/o/{tracking.make(run["id"], c["id"])}.gif'
    link = f'{base}/t/c/{tracking.make(run["id"], c["id"], url=c["url"])}'
    footer = f"\n\n--\n{Config.SENDER_NAME} | {Config.SENDER_ADDRESS}\nUnsubscribe: {unsub}"
    m = EmailMessage()
    m["Subject"] = subject.format_map(ctx)
    m["From"] = formataddr((Config.SENDER_NAME, _from()))
    m["To"] = c["email"]
    m["Reply-To"] = _from()
    m["Date"] = formatdate(localtime=True)
    m["Message-ID"] = make_msgid(domain=_from().split("@")[-1] or "localhost")
    m["List-Unsubscribe"] = f"<{unsub}>"
    m["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    m.set_content(text + footer)
    body_html = "<br>".join(html.escape(text).splitlines())
    m.add_alternative(
        f'<div style="font-family:Arial,sans-serif;font-size:14px">{body_html}'
        f'<p><a href="{link}">View the role</a></p>'
        f'<p style="color:#888;font-size:12px">{html.escape(Config.SENDER_NAME)} | '
        f'{html.escape(Config.SENDER_ADDRESS)} | <a href="{unsub}">Unsubscribe</a></p>'
        f'<img src="{pixel}" width="1" height="1" alt=""></div>', subtype="html")
    return m

def _connect():
    s = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=30)
    s.starttls(); s.login(Config.SMTP_USER, Config.SMTP_PASS)
    return s

def _brevo_send(msg, c):
    """HTTPS (port 443) API: works on Render free, where SMTP ports are blocked."""
    payload = {"sender": {"name": Config.SENDER_NAME, "email": _from()},
               "to": [{"email": c["email"], "name": c["name"]}],
               "subject": msg["Subject"],
               "textContent": msg.get_body(("plain",)).get_content(),
               "htmlContent": msg.get_body(("html",)).get_content(),
               "headers": {"List-Unsubscribe": msg["List-Unsubscribe"],
                           "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"}}
    for _ in range(2):
        r = requests.post("https://api.brevo.com/v3/smtp/email", json=payload, timeout=30,
                          headers={"api-key": Config.BREVO_API_KEY, "accept": "application/json"})
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", 10))); continue
        return r.status_code in (200, 201)
    return False

def _send_bulk_brevo(run, recipients, subject, body, base):
    delay = 60.0 / max(1, Config.SEND_PER_MINUTE)
    for c in recipients[:Config.DAILY_CAP]:
        if c["email"].lower() in suppressed:
            continue
        try:
            ok = _brevo_send(_build(run, c, subject, body, base), c)
        except Exception:
            ok = False
        if ok: c["emailed"] = True; run["sent"] += 1
        else: run["failed"].append(c["id"])
        time.sleep(delay)
    run["send_status"] = "done"

def send_bulk(run, recipients, subject, body, base):
    """Runs in a background thread; updates run['sent'] / run['send_status']."""
    run["send_status"] = "sending"; run["failed"] = []
    if Config.EMAIL_BACKEND == "brevo":
        return _send_bulk_brevo(run, recipients, subject, body, base)
    delay = 60.0 / max(1, Config.SEND_PER_MINUTE)
    try:
        smtp = _connect()
        for i, c in enumerate(recipients[:Config.DAILY_CAP]):
            if c["email"].lower() in suppressed:
                continue
            try:
                smtp.send_message(_build(run, c, subject, body, base))
                c["emailed"] = True; run["sent"] += 1
            except (smtplib.SMTPServerDisconnected, smtplib.SMTPException):
                run["failed"].append(c["id"])
                try: smtp = _connect()
                except Exception: break
            time.sleep(delay)
        smtp.quit()
        run["send_status"] = "done"
    except Exception as e:
        run["send_status"] = f"error: {e}"[:200]
