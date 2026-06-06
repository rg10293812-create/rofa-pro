# RUFA Cloud New System

تشغيل Render:
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`

الدخول الافتراضي:
- username: admin
- password: admin123

ملاحظة: يحتوي app.py على قوالب احتياطية داخلية لمنع خطأ TemplateNotFound إذا لم تُرفع templates.
