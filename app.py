{% extends 'base.html' %}{% block content %}
<h2>إدارة الصفقات الخارجية</h2>
<p class="small">هذا القسم لإدارة الصفقات الخارجية وتقسيمها احترافياً: نسبة شركة روفا جولدن، نسبة الخارجي / الوسيط، ونسب الموظفين الداخليين حسب الحسابات الموجودة في النظام.</p>

<div class="dash">
  <div class="stat">عدد الصفقات<b>{{st.count}}</b></div>
  <div class="stat">إجمالي المبيعات<b>{{st.total_value|sar}}</b></div>
  <div class="stat">عمولة الشركة<b>{{st.company_commission|sar}}</b></div>
  <div class="stat">نسب الخارجي والموظفين<b>{{(st.external_amount + st.internal_amount)|sar}}</b></div>
  <div class="stat">صافي الشركة<b>{{st.net|sar}}</b></div>
</div>

<div class="card">
  <h3>إنشاء صفقة خارجية</h3>
  <form method="post" id="dealForm">
    <div class="row">
      <input name="title" placeholder="اسم الصفقة / عنوانها" required>
      <input name="property_name" placeholder="العقار أو المشروع">
      <input name="deal_value" placeholder="قيمة الصفقة" required>
      <input name="company_rate" placeholder="نسبة شركة روفا جولدن %" value="2.5">
      <input name="client_name" placeholder="اسم العميل">
      <input name="client_phone" placeholder="جوال العميل">
      <input name="ext_marketer_name" placeholder="اسم الخارجي / الوسيط / الوسيط">
      <input name="ext_marketer_phone" placeholder="جوال الخارجي / الوسيط / الوسيط">
      <input name="ext_marketer_rate" placeholder="نسبة الخارجي / الوسيط %" value="0">
      <select name="status"><option value="open">مفتوحة</option><option value="closed">مكتملة</option><option value="cancelled">ملغاة</option></select>
    </div>

    <h4>توزيع نسب موظفي الشركة الداخليين</h4>
    <p class="small">تظهر هنا أسماء الحسابات الموجودة في إدارة الموظفين. عدّل النسبة لكل موظف له نصيب في الصفقة، واترك غير المستحق صفر.</p>
    <div class="row">
      {% for u in users %}
      <div class="mini-form">
        <label>{{u.full_name or u.username}} <span class="small">({{role_labels.get(u.role,u.role)}})</span></label>
        <input type="hidden" name="share_user_id" value="{{u.id}}">
        <input name="share_rate" placeholder="نسبة الموظف %" value="0">
        <span class="small">النسبة المحفوظة بحسابه: {{u.commission_rate}}%</span>
      </div>
      {% endfor %}
    </div>
    <textarea name="notes" placeholder="ملاحظات الصفقة والاتفاق"></textarea>
    <button class="btn green">إنشاء الصفقة وتقسيم نسب الموظفين</button>
  </form>
</div>

<h3>قائمة الصفقات الخارجية</h3>
<table>
<tr><th>الصفقة</th><th>العقار</th><th>العميل</th><th>قيمة الصفقة</th><th>عمولة الشركة</th><th>الخارجي / الوسيط</th><th>نصيبه</th><th>صافي الشركة</th><th>الحالة</th><th>الدخول</th></tr>
{% for d in deals %}
<tr>
  <td><b>{{d.title}}</b><br><span class="small">{{d.created_at.strftime('%Y-%m-%d')}}</span></td>
  <td>{{d.property_name}}</td>
  <td>{{d.client_name}}<br><span class="small">{{d.client_phone}}</span></td>
  <td>{{d.deal_value|sar}}</td>
  <td>{{d.company_commission|sar}}<br><span class="small">{{d.company_rate}}%</span></td>
  <td>{{d.ext_marketer_name}}<br><span class="small">{{d.ext_marketer_phone}}</span></td>
  <td>{{d.ext_marketer_amount|sar}}<br><span class="small">{{d.ext_marketer_rate}}%</span></td>
  <td><b>{{d.company_net|sar}}</b></td>
  <td>{{{'open':'مفتوحة','closed':'مكتملة','cancelled':'ملغاة'}.get(d.status,d.status)}}</td>
  <td><a class="btn" href="{{url_for('external_deal_detail',deal_id=d.id)}}">تفاصيل</a></td>
</tr>
{% endfor %}
</table>
{% endblock %}
