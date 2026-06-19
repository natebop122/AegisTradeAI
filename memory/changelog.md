## 2026-06-19
- Webhook secret validation added — rejects requests without correct WEBHOOK_SECRET
- Gmail email alerts fully working (SMTP auth resolved — app password issue was the root cause)
- Phase 4 (notifications) partially complete: email alerts done, error alerts not yet built

## 2026-06-17
- Phase 2 complete: Flask webhook receiver live on port 5000
- Signal validation requires symbol, action (BUY/SELL), price
- Dependencies installed: flask, pandas, numpy, requests, python-dotenv
- Virtual environment configured

# Changelog

2026-06-13

* Repository initialized.
* Memory system created.
* Added README.md.
* Added requirements.txt.
* Added config.py.
* Added main.py.


