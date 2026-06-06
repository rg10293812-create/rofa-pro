{% extends 'base.html' %}{% block content %}
<a class="btn gray" href="{{url_for('external_deals')}}">رجوع للصفقات الخارجية</a>
<h2>تفاصيل الصفقة: {{deal.title}}</h2>

<div class="dash">
  <div class="stat">قيمة الصفقة<b>{{deal.deal_value|sar}}</b></div>
  <div class="stat">عمولة الشركة<b>{{deal.company_commission|sar}}</b></div>
  <div class="stat">نصيب الخارجي / الوسيط<b>{{deal.ext_marketer_amount|sar}}</b></div>
  <div class="stat">صافي الشركة<b>{{deal.company_net|sar}}</b></div>
  <div class="stat">المصروف<b>{{deal.paid_amount|sar}}</b></div>
</div>

<div class="row">
  <div class="card">
    <h3>بيانات الصفقة</h3>
    <table>
      <tr><th>العقار</th><td>{{deal.property_name}}</td></tr>
      <tr><th>العميل</th><td>{{deal.client_name}} - {{deal.client_phone}}</td></tr>
      <tr><th>الخارجي / الوسيط</th><td>{{deal.ext_marketer_name}} - {{deal.ext_marketer_phone}}</td></tr>
      <tr><th>نسبة الشركة</th><td>{{deal.company_rate}}%</td></tr>
      <tr><th>نسبة الخارجي / الوسيط</th><td>{{deal.ext_marketer_rate}}%</td></tr>
      <tr><th>الحالة</th><td>{{{'open':'مفتوحة','closed':'مكتملة','cancelled':'ملغاة'}.get(deal.status,deal.status)}}</td></tr>
      <tr><th>ملاحظات</th><td>{{deal.notes}}</td></tr>
    </table>
  </div>
  <div class="card">
    <h3>تحديث الحالة</h3>
    <form method="post"><input type="hidden" name="action" value="status"><select name="status"><option value="open" {% if deal.status=='open' %}selected{% endif %}>مفتوحة</option><option value="closed" {% if deal.status=='closed' %}selected{% endif %}>مكتملة</option><option value="cancelled" {% if deal.status=='cancelled' %}selected{% endif %}>ملغاة</option></select><button class="btn green">حفظ الحالة</button></form>
    <hr>
    <h3>تسجيل صرف</h3>
    <form method="post"><input type="hidden" name="action" value="payout"><input name="amount" placeholder="المبلغ المصروف"><button class="btn gold">تسجيل الصرف</button></form>
  </div>
  <div class="card">
    <h3>إضافة موظف داخلي للصفقة</h3>
    <form method="post"><input type="hidden" name="action" value="add_share"><select name="share_user_id">{% for u in users %}<option value="{{u.id}}">{{u.full_name or u.username}} - {{role_labels.get(u.role,u.role)}} - النسبة الافتراضية {{u.commission_rate}}%</option>{% endfor %}</select><input name="share_rate" placeholder="نسبة الموظف %"><input name="notes" placeholder="ملاحظات"><button class="btn black">إضافة نسبة الموظف</button></form>
    {% if current_user.role=='admin' %}<hr><form method="post" action="{{url_for('external_deal_delete',deal_id=deal.id)}}" onsubmit="return confirm('حذف الصفقة؟')"><button class="btn red">حذف الصفقة</button></form>{% endif %}
  </div>
</div>

<h3>توزيع موظفي الشركة</h3>
<table><tr><th>الموظف</th><th>النسبة</th><th>المبلغ</th><th>ملاحظات</th></tr>
{% for s in shares %}<tr><td>{{s.member_name}}</td><td>{{s.rate}}%</td><td>{{s.amount|sar}}</td><td>{{s.notes}}</td></tr>{% endfor %}</table>
{% endblock %}
