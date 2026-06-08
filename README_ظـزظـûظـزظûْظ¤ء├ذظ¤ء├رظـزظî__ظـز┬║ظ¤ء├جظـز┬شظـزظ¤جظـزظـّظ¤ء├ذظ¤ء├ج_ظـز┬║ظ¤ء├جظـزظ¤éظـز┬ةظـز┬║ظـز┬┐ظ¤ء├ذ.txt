طريقة تشغيل نسخة روفا جولدن السحابية مع الصلاحيات

مهم:
هذه النسخة تضيف شاشة تسجيل دخول وإدارة مستخدمين.
يوجد 3 أنواع حسابات:
- admin: مدير عام، جميع الصلاحيات وإضافة الحسابات.
- marketer: مسوق، إضافة عقارات وعروض وأرقام ورسائل، بدون حذف وبدون إضافة مستخدمين.
- viewer: مشاهد، مشاهدة وبحث فقط.

الحساب الافتراضي أول تشغيل:
اسم المستخدم: admin
كلمة المرور: admin123

للأمان على Render أضف Environment Variables:
ADMIN_USERNAME = اسم مديرك
ADMIN_PASSWORD = كلمة مرور قوية
SECRET_KEY = كلمة سر طويلة عشوائية
DATABASE_URL = رابط قاعدة البيانات PostgreSQL/Supabase إن كنت تستخدم قاعدة خارجية

تشغيل Render:
Build Command:
pip install -r requirements.txt

Start Command:
gunicorn app:app

ملاحظة مهمة:
إذا لم تضف DATABASE_URL وكان الموقع على Render بخطة مجانية، قد تكون قاعدة SQLite داخلية وغير مضمونة للحفظ الدائم بعد إعادة النشر. الأفضل استخدام PostgreSQL أو Supabase.
