import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-change-me')
db_url = os.getenv('DATABASE_URL', 'sqlite:///rufa_cloud.db')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

ROLE_LABELS = {'admin':'مدير عام','employee':'موظف','viewer':'مشاهد'}

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40), default='')
    role = db.Column(db.String(30), default='employee')
    base_rate = db.Column(db.Float, default=0.0)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    def set_password(self, p): self.password_hash = generate_password_hash(p)
    def check_password(self, p): return check_password_hash(self.password_hash, p)

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    district = db.Column(db.String(100), default='')
    price = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(30), default='available')
    exclusive = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, default='')
    price = db.Column(db.Float, default=0.0)
    active = db.Column(db.Boolean, default=True)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ExternalDeal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    project_name = db.Column(db.String(160), default='')
    deal_value = db.Column(db.Float, default=0.0)
    company_rate = db.Column(db.Float, default=0.0)
    broker_name = db.Column(db.String(120), default='')
    broker_phone = db.Column(db.String(40), default='')
    broker_rate = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(30), default='open')
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DealEmployeeShare(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('external_deal.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rate = db.Column(db.Float, default=0.0)
    deal = db.relationship('ExternalDeal', backref=db.backref('employee_shares', cascade='all, delete-orphan'))
    employee = db.relationship('User')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def admin_required(f):
    @wraps(f)
    def w(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('ليست لديك صلاحية لهذه الصفحة')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return w

def edit_required(f):
    @wraps(f)
    def w(*args, **kwargs):
        if current_user.role == 'viewer':
            flash('المشاهد لا يملك صلاحية الإضافة أو التعديل')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return w

def money(v):
    return f"{float(v or 0):,.2f} ريال"
app.jinja_env.filters['sar'] = money

def init_db():
    db.create_all()
    if not User.query.filter_by(role='admin').first():
        u = User(username=os.getenv('ADMIN_USERNAME','admin'), full_name='مدير النظام', role='admin', base_rate=0)
        u.set_password(os.getenv('ADMIN_PASSWORD','admin123'))
        db.session.add(u); db.session.commit()

@app.before_request
def setup():
    if not getattr(app, '_db_ready', False):
        with app.app_context(): init_db()
        app._db_ready = True

@app.route('/')
def home():
    return redirect(url_for('dashboard') if current_user.is_authenticated else url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.active and user.check_password(request.form['password']):
            login_user(user); return redirect(url_for('dashboard'))
        flash('بيانات الدخول غير صحيحة')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user(); return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    data = dict(
        employees=User.query.filter(User.role!='admin').count(),
        properties=Property.query.count(),
        offers=Offer.query.count(),
        deals=ExternalDeal.query.count(),
        total=sum(d.deal_value for d in ExternalDeal.query.all())
    )
    return render_template('dashboard.html', data=data)

@app.route('/employees')
@login_required
@admin_required
def employees():
    return render_template('employees.html', employees=User.query.order_by(User.id.desc()).all(), roles=ROLE_LABELS)

@app.route('/employees/new', methods=['GET','POST'])
@login_required
@admin_required
def employee_new():
    if request.method == 'POST':
        u = User(username=request.form['username'], full_name=request.form['full_name'], phone=request.form.get('phone',''), role=request.form.get('role','employee'), base_rate=float(request.form.get('base_rate') or 0), active=True)
        u.set_password(request.form.get('password') or '123456')
        db.session.add(u); db.session.commit(); flash('تمت إضافة الموظف')
        return redirect(url_for('employees'))
    return render_template('employee_form.html', roles=ROLE_LABELS)

@app.route('/properties')
@login_required
def properties():
    return render_template('properties.html', properties=Property.query.order_by(Property.id.desc()).all())

@app.route('/properties/new', methods=['GET','POST'])
@login_required
@edit_required
def property_new():
    if request.method == 'POST':
        p = Property(title=request.form['title'], district=request.form.get('district',''), price=float(request.form.get('price') or 0), status=request.form.get('status','available'), exclusive=bool(request.form.get('exclusive')), notes=request.form.get('notes',''))
        db.session.add(p); db.session.commit(); flash('تم حفظ العقار')
        return redirect(url_for('properties'))
    return render_template('property_form.html')

@app.route('/offers')
@login_required
def offers():
    return render_template('offers.html', offers=Offer.query.order_by(Offer.id.desc()).all())

@app.route('/offers/new', methods=['GET','POST'])
@login_required
@edit_required
def offer_new():
    if request.method == 'POST':
        o = Offer(title=request.form['title'], description=request.form.get('description',''), price=float(request.form.get('price') or 0), active=bool(request.form.get('active')))
        db.session.add(o); db.session.commit(); flash('تم حفظ العرض')
        return redirect(url_for('offers'))
    return render_template('offer_form.html')

@app.route('/external-deals')
@login_required
def external_deals():
    return render_template('external_deals.html', deals=ExternalDeal.query.order_by(ExternalDeal.id.desc()).all())

@app.route('/external-deals/new', methods=['GET','POST'])
@login_required
@edit_required
def external_deal_new():
    employees = User.query.filter_by(role='employee', active=True).all()
    if request.method == 'POST':
        d = ExternalDeal(title=request.form['title'], project_name=request.form.get('project_name',''), deal_value=float(request.form.get('deal_value') or 0), company_rate=float(request.form.get('company_rate') or 0), broker_name=request.form.get('broker_name',''), broker_phone=request.form.get('broker_phone',''), broker_rate=float(request.form.get('broker_rate') or 0), status=request.form.get('status','open'), notes=request.form.get('notes',''))
        db.session.add(d); db.session.flush()
        for e in employees:
            rate = float(request.form.get(f'emp_rate_{e.id}') or 0)
            if rate > 0:
                db.session.add(DealEmployeeShare(deal_id=d.id, employee_id=e.id, rate=rate))
        db.session.commit(); flash('تم إنشاء الصفقة الخارجية')
        return redirect(url_for('external_deal_detail', deal_id=d.id))
    return render_template('external_deal_form.html', employees=employees)

@app.route('/external-deals/<int:deal_id>')
@login_required
def external_deal_detail(deal_id):
    deal = db.get_or_404(ExternalDeal, deal_id)
    return render_template('external_deal_detail.html', deal=deal)

@app.route('/reports')
@login_required
def reports():
    deals = ExternalDeal.query.all()
    total = sum(d.deal_value for d in deals)
    company = sum(d.deal_value * d.company_rate / 100 for d in deals)
    broker = sum(d.deal_value * d.broker_rate / 100 for d in deals)
    return render_template('reports.html', total=total, company=company, broker=broker, deals=deals)

if __name__ == '__main__':
    with app.app_context(): init_db()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
