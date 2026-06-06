import os, urllib.parse, base64, json, zipfile, shutil
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'rufa-golden-change-me')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///rufa_golden_cloud.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

BACKUP_FOLDER = os.getenv('BACKUP_FOLDER', 'backups')
BACKUP_KEEP_LAST = int(os.getenv('BACKUP_KEEP_LAST', '30'))
BACKUP_AUTO_HOUR = int(os.getenv('BACKUP_AUTO_HOUR', '3'))

db = SQLAlchemy(app)

ROLE_LABELS = {'admin':'مدير عام','executive':'مدير تنفيذي','marketer':'موظف','viewer':'مشاهد'}
STATUS_LABELS = {'available':'متاح','reserved':'محجوز','sold':'مباع'}

class User(db.Model):
    __tablename__='users'
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash=db.Column(db.Text, nullable=False)
    full_name=db.Column(db.Text, default='')
    phone=db.Column(db.Text, default='')
    email=db.Column(db.Text, default='')
    commission_rate=db.Column(db.Float, default=2.5)
    role=db.Column(db.String(20), default='viewer', index=True)
    is_active=db.Column(db.Boolean, default=True)
    can_delete=db.Column(db.Boolean, default=False)
    can_manage_users=db.Column(db.Boolean, default=False)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)
    def set_password(self,password): self.password_hash=generate_password_hash(password)
    def check_password(self,password): return check_password_hash(self.password_hash,password)


class ExternalMarketer(db.Model):
    __tablename__='external_marketers'
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.Text, nullable=False, default='')
    phone=db.Column(db.Text, default='')
    email=db.Column(db.Text, default='')
    company=db.Column(db.Text, default='')
    source=db.Column(db.Text, default='خارجي')
    commission_rate=db.Column(db.Float, default=2.5)
    status=db.Column(db.String(20), default='active', index=True)
    notes=db.Column(db.Text, default='')
    created_at=db.Column(db.DateTime, default=datetime.utcnow)

class Property(db.Model):
    __tablename__='properties'
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.Text, default='')
    location=db.Column(db.Text, default='')
    price=db.Column(db.Text, default='')
    specs=db.Column(db.Text, default='')
    status=db.Column(db.String(20), default='available', index=True)
    marketer_id=db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    ext_marketer_id=db.Column(db.Integer, db.ForeignKey('external_marketers.id'), nullable=True, index=True)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)

class Contact(db.Model):
    __tablename__='contacts'
    id=db.Column(db.Integer, primary_key=True)
    category=db.Column(db.Text, index=True)
    name=db.Column(db.Text, default='')
    phone=db.Column(db.Text, default='')
    notes=db.Column(db.Text, default='')
    created_at=db.Column(db.DateTime, default=datetime.utcnow)

class Offer(db.Model):
    __tablename__='offers'
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.Text, default='')
    description=db.Column(db.Text, default='')
    price=db.Column(db.Text, default='')
    image_data=db.Column(db.Text, default='')
    images_data=db.Column(db.Text, default='[]')
    status=db.Column(db.String(20), default='available', index=True)
    marketer_id=db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    ext_marketer_id=db.Column(db.Integer, db.ForeignKey('external_marketers.id'), nullable=True, index=True)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)
    def images_list(self):
        items=[]
        if self.image_data: items.append(self.image_data)
        try:
            more=json.loads(self.images_data or '[]')
            if isinstance(more,list): items.extend([x for x in more if x])
        except Exception: pass
        seen=set(); result=[]
        for item in items:
            if item not in seen: seen.add(item); result.append(item)
        return result

class CustomerMessage(db.Model):
    __tablename__='customer_messages'
    id=db.Column(db.Integer, primary_key=True)
    customer_name=db.Column(db.Text, default='')
    phone=db.Column(db.Text, default='')
    message=db.Column(db.Text, default='')
    created_at=db.Column(db.DateTime, default=datetime.utcnow)

class Sale(db.Model):
    __tablename__='sales'
    id=db.Column(db.Integer, primary_key=True)
    marketer_id=db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    ext_marketer_id=db.Column(db.Integer, db.ForeignKey('external_marketers.id'), nullable=True, index=True)
    offer_id=db.Column(db.Integer, db.ForeignKey('offers.id'), nullable=True, index=True)
    property_id=db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=True, index=True)
    deal_value=db.Column(db.Float, default=0)
    commission_rate=db.Column(db.Float, default=2.5)
    commission_amount=db.Column(db.Float, default=0)
    notes=db.Column(db.Text, default='')
    created_at=db.Column(db.DateTime, default=datetime.utcnow)

class Payout(db.Model):
    __tablename__='payouts'
    id=db.Column(db.Integer, primary_key=True)
    marketer_id=db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    ext_marketer_id=db.Column(db.Integer, db.ForeignKey('external_marketers.id'), nullable=True, index=True)
    amount=db.Column(db.Float, default=0)
    notes=db.Column(db.Text, default='')
    created_at=db.Column(db.DateTime, default=datetime.utcnow)


class ExternalDeal(db.Model):
    __tablename__='external_deals'
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.Text, nullable=False, default='')
    client_name=db.Column(db.Text, default='')
    client_phone=db.Column(db.Text, default='')
    property_name=db.Column(db.Text, default='')
    deal_value=db.Column(db.Float, default=0)
    company_rate=db.Column(db.Float, default=2.5)
    company_commission=db.Column(db.Float, default=0)
    ext_marketer_name=db.Column(db.Text, default='')
    ext_marketer_phone=db.Column(db.Text, default='')
    ext_marketer_rate=db.Column(db.Float, default=0)
    ext_marketer_amount=db.Column(db.Float, default=0)
    company_net=db.Column(db.Float, default=0)
    paid_amount=db.Column(db.Float, default=0)
    status=db.Column(db.String(20), default='open', index=True)
    notes=db.Column(db.Text, default='')
    created_at=db.Column(db.DateTime, default=datetime.utcnow)

class DealShare(db.Model):
    __tablename__='deal_shares'
    id=db.Column(db.Integer, primary_key=True)
    deal_id=db.Column(db.Integer, db.ForeignKey('external_deals.id'), nullable=False, index=True)
    user_id=db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    member_name=db.Column(db.Text, default='')
    rate=db.Column(db.Float, default=0)
    amount=db.Column(db.Float, default=0)
    notes=db.Column(db.Text, default='')
    created_at=db.Column(db.DateTime, default=datetime.utcnow)

class SystemLog(db.Model):
    __tablename__='system_logs'
    id=db.Column(db.Integer, primary_key=True)
    level=db.Column(db.Text, default='info')
    message=db.Column(db.Text, default='')
    user_name=db.Column(db.Text, default='')
    status=db.Column(db.Text, default='جديد')
    created_at=db.Column(db.DateTime, default=datetime.utcnow)

def add_missing_columns(table, columns):
    try:
        inspector=db.inspect(db.engine)
        if table not in inspector.get_table_names(): return
        existing={c['name'] for c in inspector.get_columns(table)}
        dialect=db.engine.dialect.name
        with db.engine.begin() as conn:
            for name, ddl in columns.items():
                if name not in existing:
                    if dialect=='postgresql': conn.execute(db.text(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {name} {ddl}'))
                    else: conn.execute(db.text(f'ALTER TABLE {table} ADD COLUMN {name} {ddl}'))
    except Exception as exc:
        print('Migration warning:', table, exc)

def init_db():
    db.create_all()
    add_missing_columns('users', {'can_delete':'BOOLEAN DEFAULT 0','can_manage_users':'BOOLEAN DEFAULT 0','phone':'TEXT DEFAULT \'\'','email':'TEXT DEFAULT \'\'','commission_rate':'FLOAT DEFAULT 2.5'})
    add_missing_columns('offers', {'images_data':'TEXT DEFAULT \'[]\'','status':'VARCHAR(20) DEFAULT \'available\'','marketer_id':'INTEGER'})
    add_missing_columns('properties', {'status':'VARCHAR(20) DEFAULT \'available\'','marketer_id':'INTEGER'})
    if User.query.count()==0:
        admin=User(username=os.getenv('ADMIN_USERNAME','admin'), full_name='مدير النظام', role='admin', is_active=True, can_delete=True, can_manage_users=True)
        admin.set_password(os.getenv('ADMIN_PASSWORD','admin123'))
        db.session.add(admin); db.session.commit()
    for admin in User.query.filter_by(role='admin').all():
        admin.can_delete=True; admin.can_manage_users=True; admin.is_active=True
    db.session.commit()


@app.context_processor
def inject_user():
    user=get_current_user()
    return dict(current_user=user, role_labels=ROLE_LABELS, status_labels=STATUS_LABELS, can_delete_content=can_delete_content, can_manage_accounts=can_manage_accounts, external_marketer_name=external_marketer_name)

def external_marketer_name(mid):
    if not mid: return '-'
    m=ExternalMarketer.query.get(mid)
    return m.name if m else '-'

def get_current_user():
    uid=session.get('user_id')
    return User.query.get(uid) if uid else None

def login_required(fn):
    @wraps(fn)
    def wrapper(*args,**kwargs):
        user=get_current_user()
        if not user or not user.is_active:
            session.clear(); flash('يرجى تسجيل الدخول أولاً'); return redirect(url_for('login'))
        return fn(*args,**kwargs)
    return wrapper

def can_delete_content(user): return bool(user and user.is_active and (user.role=='admin' or getattr(user,'can_delete',False)))
def can_manage_accounts(user): return bool(user and user.is_active and (user.role=='admin' or getattr(user,'can_manage_users',False)))
def manage_users_required(fn):
    @wraps(fn)
    def wrapper(*args,**kwargs):
        if not can_manage_accounts(get_current_user()): flash('ليس لديك صلاحية إدارة الحسابات'); return redirect(url_for('index'))
        return fn(*args,**kwargs)
    return wrapper

def money(v):
    try: return round(float(v or 0),2)
    except Exception: return 0

def marketer_stats(user_id):
    sales=Sale.query.filter_by(marketer_id=user_id).all(); payouts=Payout.query.filter_by(marketer_id=user_id).all()
    total_sales=sum(money(s.deal_value) for s in sales); total_comm=sum(money(s.commission_amount) for s in sales); total_paid=sum(money(p.amount) for p in payouts)
    return {'sales_count':len(sales),'total_sales':total_sales,'total_commission':total_comm,'total_paid':total_paid,'balance':total_comm-total_paid,
            'offers_count':Offer.query.filter_by(marketer_id=user_id).count(),'properties_count':Property.query.filter_by(marketer_id=user_id).count(),
            'sold_offers':Offer.query.filter_by(marketer_id=user_id,status='sold').count()+Property.query.filter_by(marketer_id=user_id,status='sold').count()}

def external_marketer_stats(mid):
    sales=Sale.query.filter_by(ext_marketer_id=mid).all(); payouts=Payout.query.filter_by(ext_marketer_id=mid).all()
    total_sales=sum(money(s.deal_value) for s in sales); total_comm=sum(money(s.commission_amount) for s in sales); total_paid=sum(money(p.amount) for p in payouts)
    return {
        'sales_count':len(sales), 'total_sales':total_sales, 'total_commission':total_comm, 'total_paid':total_paid, 'balance':total_comm-total_paid,
        'offers_count':Offer.query.filter_by(ext_marketer_id=mid).count(), 'properties_count':Property.query.filter_by(ext_marketer_id=mid).count(),
        'sold_count':Offer.query.filter_by(ext_marketer_id=mid,status='sold').count()+Property.query.filter_by(ext_marketer_id=mid,status='sold').count(),
        'active_offers':Offer.query.filter_by(ext_marketer_id=mid,status='available').count()+Property.query.filter_by(ext_marketer_id=mid,status='available').count()
    }

def safe_backup_name(name):
    name=os.path.basename(name or '')
    if not name.startswith('backup_') or not name.endswith('.zip'):
        return None
    return name

def get_backup_dir():
    path=os.path.join(app.instance_path, BACKUP_FOLDER) if not os.path.isabs(BACKUP_FOLDER) else BACKUP_FOLDER
    os.makedirs(path, exist_ok=True)
    return path

def list_backup_files():
    folder=get_backup_dir()
    rows=[]
    for name in os.listdir(folder):
        if name.startswith('backup_') and name.endswith('.zip'):
            path=os.path.join(folder,name)
            rows.append({'name':name,'size':os.path.getsize(path),'created':datetime.fromtimestamp(os.path.getmtime(path))})
    return sorted(rows, key=lambda x:x['created'], reverse=True)

def cleanup_old_backups():
    rows=list_backup_files()
    for row in rows[BACKUP_KEEP_LAST:]:
        try: os.remove(os.path.join(get_backup_dir(), row['name']))
        except Exception: pass

def export_data_json():
    data={}
    models=[User,ExternalMarketer,Property,Contact,Offer,CustomerMessage,Sale,Payout,ExternalDeal,DealShare,SystemLog]
    for model in models:
        table=[]
        for row in model.query.all():
            item={}
            for col in model.__table__.columns:
                value=getattr(row,col.name)
                if isinstance(value, datetime): value=value.isoformat()
                item[col.name]=value
            table.append(item)
        data[model.__tablename__]=table
    return data

def create_system_backup(created_by='system'):
    """Create a ZIP backup containing SQLite database file when available + JSON data export."""
    with app.app_context():
        db.session.commit()
        folder=get_backup_dir()
        stamp=datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename=f'backup_{stamp}.zip'
        backup_path=os.path.join(folder, filename)
        metadata={'created_at':datetime.now().isoformat(timespec='seconds'),'created_by':created_by,'database_url_type':db.engine.dialect.name,'system':'Rufa Golden Cloud'}
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('metadata.json', json.dumps(metadata, ensure_ascii=False, indent=2))
            z.writestr('data_export.json', json.dumps(export_data_json(), ensure_ascii=False, indent=2))
            db_path=db.engine.url.database
            if db.engine.dialect.name=='sqlite' and db_path:
                if not os.path.isabs(db_path): db_path=os.path.join(app.instance_path, db_path)
                if os.path.exists(db_path): z.write(db_path, 'database.sqlite')
            for folder_name in ['uploads','static/uploads']:
                if os.path.exists(folder_name):
                    for root, dirs, files in os.walk(folder_name):
                        for file in files:
                            path=os.path.join(root,file)
                            z.write(path, path)
        cleanup_old_backups()
        try:
            db.session.add(SystemLog(level='success', message=f'تم إنشاء نسخة احتياطية: {filename}', user_name=created_by, status='معالج'))
            db.session.commit()
        except Exception:
            db.session.rollback()
        return backup_path

def start_backup_scheduler():
    if os.getenv('BACKUP_AUTO_ENABLED','1')!='1': return
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler=BackgroundScheduler(daemon=True)
        scheduler.add_job(lambda: create_system_backup('auto'), 'cron', hour=BACKUP_AUTO_HOUR, minute=0, id='daily_backup', replace_existing=True)
        scheduler.start()
    except Exception as exc:
        print('Backup scheduler disabled:', exc)

# تهيئة قاعدة البيانات ثم تشغيل النسخ الاحتياطي التلقائي بعد تعريف الدالة
with app.app_context():
    init_db()
start_backup_scheduler()

@app.template_filter('sar')
def sar(v): return f"{money(v):,.2f} ريال"

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        user=User.query.filter_by(username=request.form.get('username','').strip()).first()
        if user and user.is_active and user.check_password(request.form.get('password','')):
            session['user_id']=user.id; session['role']=user.role; flash('تم تسجيل الدخول بنجاح'); return redirect(url_for('index'))
        flash('اسم المستخدم أو كلمة المرور غير صحيحة')
    return render_template('login.html')
@app.route('/logout')
def logout(): session.clear(); flash('تم تسجيل الخروج'); return redirect(url_for('login'))

@app.route('/')
def landing(): return render_template('landing.html')
@app.route('/member')
def member_entry(): return redirect(url_for('login'))
@app.route('/dashboard')
@login_required
def index():
    dst=deal_stats()
    stats={'properties':Property.query.count(),'offers':Offer.query.filter(Offer.status!='sold').count(),'deals':dst['count'],'deal_value':dst['total_value'],'company_net':dst['net']}
    recent=ExternalDeal.query.order_by(ExternalDeal.id.desc()).limit(10).all()
    return render_template('index.html', stats=stats, recent=recent, dst=dst)

@app.route('/users', methods=['GET','POST'])
@login_required
@manage_users_required
def users():
    if request.method=='POST':
        username=request.form.get('username','').strip(); password=request.form.get('password','').strip(); role=request.form.get('role','viewer')
        if role not in ROLE_LABELS: role='viewer'
        if not username or not password: flash('اسم المستخدم وكلمة المرور مطلوبة'); return redirect(url_for('users'))
        if User.query.filter_by(username=username).first(): flash('اسم المستخدم موجود مسبقاً'); return redirect(url_for('users'))
        can_delete=request.form.get('can_delete')=='on'; can_manage_users=request.form.get('can_manage_users')=='on'
        if role=='admin': can_delete=True; can_manage_users=True
        user=User(username=username, full_name=request.form.get('full_name',''), phone=request.form.get('phone',''), email=request.form.get('email',''), commission_rate=money(request.form.get('commission_rate',2.5)), role=role, is_active=True, can_delete=can_delete, can_manage_users=can_manage_users)
        user.set_password(password); db.session.add(user); db.session.commit(); flash('تم إضافة الحساب بنجاح'); return redirect(url_for('users'))
    return render_template('users.html', rows=User.query.order_by(User.id.desc()).all(), roles=ROLE_LABELS)

@app.route('/users/delete/<int:uid>', methods=['POST'])
@login_required
@manage_users_required
def delete_user(uid):
    if get_current_user().id==uid: flash('لا يمكنك حذف حسابك الحالي'); return redirect(url_for('users'))
    db.session.delete(User.query.get_or_404(uid)); db.session.commit(); flash('تم حذف المستخدم'); return redirect(url_for('users'))
@app.route('/users/toggle/<int:uid>', methods=['POST'])
@login_required
@manage_users_required
def toggle_user(uid):
    if get_current_user().id==uid: flash('لا يمكنك تعطيل حسابك الحالي'); return redirect(url_for('users'))
    user=User.query.get_or_404(uid); user.is_active=not user.is_active; db.session.commit(); flash('تم تحديث حالة المستخدم'); return redirect(url_for('users'))
@app.route('/users/permissions/<int:uid>', methods=['POST'])
@login_required
@manage_users_required
def update_user_permissions(uid):
    user=User.query.get_or_404(uid); role=request.form.get('role',user.role)
    if role in ROLE_LABELS: user.role=role
    user.phone=request.form.get('phone',user.phone); user.email=request.form.get('email',user.email); user.commission_rate=money(request.form.get('commission_rate',user.commission_rate))
    user.can_delete=request.form.get('can_delete')=='on'; user.can_manage_users=request.form.get('can_manage_users')=='on'; user.is_active=request.form.get('is_active')=='on'
    if user.role=='admin': user.can_delete=True; user.can_manage_users=True; user.is_active=True
    db.session.commit(); flash('تم تحديث بيانات وصلاحيات المستخدم'); return redirect(url_for('users'))


def deal_calc_values(deal_value, company_rate, ext_rate, internal_rates):
    value=money(deal_value)
    company_rate=money(company_rate)
    ext_rate=money(ext_rate)
    company_comm=value*company_rate/100
    ext_amount=value*ext_rate/100
    internal_total=sum(value*money(r)/100 for r in internal_rates)
    company_net=company_comm-ext_amount-internal_total
    return value, company_rate, company_comm, ext_rate, ext_amount, internal_total, company_net

def deal_stats():
    deals=ExternalDeal.query.all()
    total_value=sum(money(d.deal_value) for d in deals)
    company_comm=sum(money(d.company_commission) for d in deals)
    ext=sum(money(d.ext_marketer_amount) for d in deals)
    internal=sum(money(s.amount) for s in DealShare.query.all())
    paid=sum(money(d.paid_amount) for d in deals)
    net=sum(money(d.company_net) for d in deals)
    return {'count':len(deals),'total_value':total_value,'company_commission':company_comm,'external_amount':ext,'internal_amount':internal,'paid':paid,'net':net}

@app.route('/external-deals', methods=['GET','POST'])
@login_required
def external_deals():
    if get_current_user().role not in ['admin','executive']:
        flash('الصفقات الخارجية مخصصة للإدارة فقط'); return redirect(url_for('index'))
    users=User.query.filter(User.role.in_(['admin','executive','marketer']), User.is_active==True).order_by(User.full_name).all()
    if request.method=='POST':
        value=money(request.form.get('deal_value'))
        company_rate=money(request.form.get('company_rate',2.5))
        ext_rate=money(request.form.get('ext_marketer_rate',0))
        share_user_ids=request.form.getlist('share_user_id')
        share_rates=request.form.getlist('share_rate')
        internal_rates=[money(r) for r in share_rates if money(r)>0]
        value, company_rate, company_comm, ext_rate, ext_amount, internal_total, company_net=deal_calc_values(value,company_rate,ext_rate,internal_rates)
        deal=ExternalDeal(
            title=request.form.get('title','').strip() or 'صفقة خارجية',
            client_name=request.form.get('client_name',''), client_phone=request.form.get('client_phone',''),
            property_name=request.form.get('property_name',''), deal_value=value,
            company_rate=company_rate, company_commission=company_comm,
            ext_marketer_name=request.form.get('ext_marketer_name',''), ext_marketer_phone=request.form.get('ext_marketer_phone',''),
            ext_marketer_rate=ext_rate, ext_marketer_amount=ext_amount, company_net=company_net,
            status=request.form.get('status','open'), notes=request.form.get('notes','')
        )
        db.session.add(deal); db.session.flush()
        for uid,rate in zip(share_user_ids, share_rates):
            rate=money(rate)
            if rate<=0: continue
            user=User.query.get(int(uid)) if uid else None
            db.session.add(DealShare(deal_id=deal.id, user_id=user.id if user else None, member_name=(user.full_name or user.username) if user else '', rate=rate, amount=value*rate/100, notes='نسبة موظف داخلي'))
        db.session.commit(); flash('تم إنشاء الصفقة الخارجية وتقسيم نسب الشركة والموظفين تلقائياً')
        return redirect(url_for('external_deal_detail', deal_id=deal.id))
    deals=ExternalDeal.query.order_by(ExternalDeal.id.desc()).all()
    return render_template('external_deals.html', deals=deals, users=users, st=deal_stats())

@app.route('/external-deals/<int:deal_id>', methods=['GET','POST'])
@login_required
def external_deal_detail(deal_id):
    if get_current_user().role not in ['admin','executive']:
        flash('الصفقات الخارجية مخصصة للإدارة فقط'); return redirect(url_for('index'))
    deal=ExternalDeal.query.get_or_404(deal_id)
    users=User.query.filter(User.role.in_(['admin','executive','marketer']), User.is_active==True).order_by(User.full_name).all()
    if request.method=='POST':
        action=request.form.get('action')
        if action=='payout':
            deal.paid_amount=money(deal.paid_amount)+money(request.form.get('amount'))
            db.session.commit(); flash('تم تسجيل مبلغ مصروف على الصفقة')
        elif action=='status':
            deal.status=request.form.get('status',deal.status); db.session.commit(); flash('تم تحديث حالة الصفقة')
        elif action=='add_share':
            uid=int(request.form.get('share_user_id') or 0); rate=money(request.form.get('share_rate'))
            user=User.query.get(uid) if uid else None
            if user and rate>0:
                amount=money(deal.deal_value)*rate/100
                db.session.add(DealShare(deal_id=deal.id,user_id=user.id,member_name=user.full_name or user.username,rate=rate,amount=amount,notes=request.form.get('notes','')))
                deal.company_net=money(deal.company_net)-amount
                db.session.commit(); flash('تم إضافة نسبة الموظف الداخلي')
        return redirect(url_for('external_deal_detail',deal_id=deal.id))
    shares=DealShare.query.filter_by(deal_id=deal.id).order_by(DealShare.id.desc()).all()
    return render_template('external_deal_detail.html', deal=deal, shares=shares, users=users)

@app.route('/external-deals/delete/<int:deal_id>', methods=['POST'])
@login_required
def external_deal_delete(deal_id):
    if get_current_user().role!='admin':
        flash('حذف الصفقات مخصص للمدير العام فقط'); return redirect(url_for('external_deals'))
    deal=ExternalDeal.query.get_or_404(deal_id)
    DealShare.query.filter_by(deal_id=deal.id).delete()
    db.session.delete(deal); db.session.commit(); flash('تم حذف الصفقة الخارجية')
    return redirect(url_for('external_deals'))

@app.route('/marketers', methods=['GET','POST'])
@login_required
def marketers():
    if get_current_user().role not in ['admin','executive']:
        flash('إدارة المسوقين الخارجيين مخصصة للإدارة فقط'); return redirect(url_for('index'))
    if request.method=='POST':
        name=request.form.get('name','').strip()
        if not name:
            flash('اسم المسوق مطلوب'); return redirect(url_for('marketers'))
        row=ExternalMarketer(
            name=name, phone=request.form.get('phone',''), email=request.form.get('email',''),
            company=request.form.get('company',''), source=request.form.get('source','خارجي'),
            commission_rate=money(request.form.get('commission_rate',2.5)),
            status=request.form.get('status','active'), notes=request.form.get('notes','')
        )
        db.session.add(row); db.session.commit(); flash('تم إضافة المسوق الخارجي بنجاح')
        return redirect(url_for('marketer_detail',uid=row.id))
    rows=ExternalMarketer.query.order_by(ExternalMarketer.id.desc()).all()
    return render_template('marketers.html', rows=[(m,external_marketer_stats(m.id)) for m in rows])

@app.route('/marketers/<int:uid>', methods=['GET','POST'])
@login_required
def marketer_detail(uid):
    if get_current_user().role not in ['admin','executive']:
        flash('إدارة المسوقين الخارجيين مخصصة للإدارة فقط'); return redirect(url_for('index'))
    m=ExternalMarketer.query.get_or_404(uid)
    if request.method=='POST':
        action=request.form.get('action')
        if action=='update':
            m.name=request.form.get('name','').strip() or m.name
            m.phone=request.form.get('phone',''); m.email=request.form.get('email',''); m.company=request.form.get('company','')
            m.source=request.form.get('source','خارجي'); m.commission_rate=money(request.form.get('commission_rate',m.commission_rate)); m.status=request.form.get('status','active'); m.notes=request.form.get('notes','')
            db.session.commit(); flash('تم تحديث بيانات المسوق')
        elif action=='sale':
            value=money(request.form.get('deal_value')); rate=money(request.form.get('commission_rate') or m.commission_rate); comm=value*rate/100
            db.session.add(Sale(ext_marketer_id=m.id, offer_id=request.form.get('offer_id') or None, property_id=request.form.get('property_id') or None, deal_value=value, commission_rate=rate, commission_amount=comm, notes=request.form.get('notes','')))
            db.session.commit(); flash('تم تسجيل الصفقة واحتساب العمولة')
        elif action=='payout':
            db.session.add(Payout(ext_marketer_id=m.id, amount=money(request.form.get('amount')), notes=request.form.get('notes','')))
            db.session.commit(); flash('تم تسجيل صرف مبلغ للمسوق')
        return redirect(url_for('marketer_detail',uid=m.id))
    st=external_marketer_stats(uid)
    return render_template('marketer_detail.html', m=m, st=st, sales=Sale.query.filter_by(ext_marketer_id=uid).order_by(Sale.id.desc()).all(), payouts=Payout.query.filter_by(ext_marketer_id=uid).order_by(Payout.id.desc()).all(), offers=Offer.query.filter(Offer.status!='sold').all(), properties=Property.query.filter(Property.status!='sold').all())

@app.route('/marketers/delete/<int:uid>', methods=['POST'])
@login_required
def marketer_delete(uid):
    if get_current_user().role!='admin':
        flash('حذف المسوقين مخصص للمدير العام فقط'); return redirect(url_for('marketers'))
    m=ExternalMarketer.query.get_or_404(uid)
    db.session.delete(m); db.session.commit(); flash('تم حذف المسوق الخارجي')
    return redirect(url_for('marketers'))

@app.route('/finance', methods=['GET','POST'])
@login_required
def finance():
    if get_current_user().role not in ['admin','executive']:
        flash('ليس لديك صلاحية الإدارة المالية'); return redirect(url_for('index'))
    if request.method=='POST':
        action=request.form.get('action'); marketer_id=int(request.form.get('marketer_id') or 0)
        if action=='sale':
            value=money(request.form.get('deal_value')); rate=money(request.form.get('commission_rate') or ExternalMarketer.query.get(marketer_id).commission_rate); comm=value*rate/100
            sale=Sale(ext_marketer_id=marketer_id, offer_id=request.form.get('offer_id') or None, property_id=request.form.get('property_id') or None, deal_value=value, commission_rate=rate, commission_amount=comm, notes=request.form.get('notes',''))
            db.session.add(sale)
            if sale.offer_id: Offer.query.get(int(sale.offer_id)).status='sold'
            if sale.property_id: Property.query.get(int(sale.property_id)).status='sold'
            flash('تم تسجيل البيع وحساب العمولة وإخفاء العرض المباع من صفحة الزائر')
        elif action=='payout':
            db.session.add(Payout(ext_marketer_id=marketer_id, amount=money(request.form.get('amount')), notes=request.form.get('notes',''))); flash('تم تسجيل صرف العمولة وخصمها من الرصيد')
        db.session.commit(); return redirect(url_for('finance'))
    marketers=ExternalMarketer.query.order_by(ExternalMarketer.name).all()
    return render_template('finance.html', marketers=marketers, offers=Offer.query.filter(Offer.status!='sold').all(), properties=Property.query.filter(Property.status!='sold').all(), sales=Sale.query.order_by(Sale.id.desc()).all(), payouts=Payout.query.order_by(Payout.id.desc()).all())

@app.route('/visitor')
def visitor_offers():
    q=request.args.get('q','').strip(); location=request.args.get('location','').strip(); max_price=request.args.get('max_price','').strip()
    query=Offer.query.filter(Offer.status!='sold')
    if q:
        like=f'%{q}%'; query=query.filter(db.or_(Offer.title.ilike(like), Offer.description.ilike(like), Offer.price.ilike(like)))
    if location:
        query=query.filter(Offer.description.ilike(f'%{location}%'))
    offers_rows=query.order_by(Offer.id.desc()).all()
    return render_template('visitor_offers.html', offers=offers_rows, q=q, location=location, max_price=max_price)
@app.route('/visitor/offer/<int:oid>')
def visitor_offer_detail(oid):
    offer=Offer.query.get_or_404(oid)
    if offer.status=='sold': flash('هذا العرض تم بيعه ولم يعد متاحاً'); return redirect(url_for('visitor_offers'))
    return render_template('visitor_offer_detail.html', offer=offer, images=offer.images_list())

@app.route('/properties', methods=['GET','POST'])
@login_required
def properties():
    user=get_current_user()
    if request.method=='POST':
        if user.role not in ['admin','executive','marketer']: flash('ليس لديك صلاحية إضافة عقار'); return redirect(url_for('properties'))
        mid=int(request.form.get('marketer_id') or (user.id if user.role=='marketer' else 0) or 0) or None
        ext_mid=int(request.form.get('ext_marketer_id') or 0) or None
        row=Property(name=request.form.get('name',''), location=request.form.get('location',''), price=request.form.get('price',''), specs=request.form.get('specs',''), status=request.form.get('status','available'), marketer_id=mid, ext_marketer_id=ext_mid)
        db.session.add(row); db.session.commit(); flash('تم حفظ العقار تلقائياً'); return redirect(url_for('properties'))
    q=request.args.get('q','').strip(); query=Property.query
    if user.role=='marketer': query=query.filter_by(marketer_id=user.id)
    if q:
        like=f'%{q}%'; query=query.filter(db.or_(Property.name.ilike(like),Property.location.ilike(like),Property.price.ilike(like),Property.specs.ilike(like)))
    return render_template('properties.html', rows=query.order_by(Property.id.desc()).all(), q=q, marketers=ExternalMarketer.query.order_by(ExternalMarketer.name).all())
@app.route('/properties/<int:pid>')
@login_required
def property_detail(pid): return render_template('property_detail.html', row=Property.query.get_or_404(pid))
@app.route('/properties/status/<int:pid>', methods=['POST'])
@login_required
def property_status(pid):
    row=Property.query.get_or_404(pid); row.status=request.form.get('status','available'); db.session.commit(); flash('تم تحديث حالة العقار'); return redirect(url_for('properties'))
@app.route('/properties/delete/<int:pid>', methods=['POST'])
@login_required
def delete_property(pid):
    if not can_delete_content(get_current_user()): flash('ليس لديك صلاحية الحذف'); return redirect(url_for('properties'))
    db.session.delete(Property.query.get_or_404(pid)); db.session.commit(); flash('تم حذف العقار'); return redirect(url_for('properties'))

@app.route('/contacts/<category>', methods=['GET','POST'])
@login_required
def contacts(category):
    user=get_current_user(); labels={'marketers':'أرقام المسوقين','customers':'أرقام الزباين','developers':'أرقام المطورين'}
    if category not in labels: return redirect(url_for('index'))
    if request.method=='POST':
        if user.role not in ['admin','executive','marketer']: flash('ليس لديك صلاحية إضافة رقم'); return redirect(url_for('contacts',category=category))
        db.session.add(Contact(category=category,name=request.form.get('name',''),phone=request.form.get('phone',''),notes=request.form.get('notes',''))); db.session.commit(); flash('تم حفظ الرقم'); return redirect(url_for('contacts',category=category))
    return render_template('contacts.html', rows=Contact.query.filter_by(category=category).order_by(Contact.id.desc()).all(), category=category, title=labels[category])
@app.route('/contacts/delete/<int:cid>/<category>', methods=['POST'])
@login_required
def delete_contact(cid,category):
    if not can_delete_content(get_current_user()): flash('ليس لديك صلاحية الحذف'); return redirect(url_for('contacts',category=category))
    db.session.delete(Contact.query.get_or_404(cid)); db.session.commit(); flash('تم حذف الرقم'); return redirect(url_for('contacts',category=category))
@app.route('/send_whatsapp', methods=['POST'])
@login_required
def send_whatsapp():
    ids=request.form.getlist('selected'); message=request.form.get('message',''); category=request.form.get('category','marketers')
    if not ids: flash('حدد رقم واحد على الأقل'); return redirect(url_for('contacts',category=category))
    rows=Contact.query.filter(Contact.id.in_([int(x) for x in ids])).all(); links=[]
    for r in rows:
        phone=''.join(ch for ch in (r.phone or '') if ch.isdigit())
        if phone.startswith('0'): phone='966'+phone[1:]
        elif phone and not phone.startswith('966'): phone='966'+phone
        if phone: links.append({'name':r.name,'phone':phone,'url':f'https://wa.me/{phone}?text={urllib.parse.quote(message)}'})
    return render_template('whatsapp_links.html', links=links, message=message)

@app.route('/offers', methods=['GET','POST'])
@login_required
def offers():
    user=get_current_user()
    if request.method=='POST':
        if user.role not in ['admin','executive','marketer']: flash('ليس لديك صلاحية إضافة عرض'); return redirect(url_for('offers'))
        uploaded=[]; files=request.files.getlist('images')
        legacy_file=request.files.get('image')
        if legacy_file and legacy_file.filename and legacy_file not in files: files.insert(0,legacy_file)
        for file in files:
            if file and file.filename:
                raw=file.read()
                if raw: uploaded.append(f"data:{file.mimetype or 'image/jpeg'};base64,"+base64.b64encode(raw).decode('utf-8'))
        mid=int(request.form.get('marketer_id') or (user.id if user.role=='marketer' else 0) or 0) or None
        ext_mid=int(request.form.get('ext_marketer_id') or 0) or None
        row=Offer(title=request.form.get('title',''),description=request.form.get('description',''),price=request.form.get('price',''),image_data=uploaded[0] if uploaded else '',images_data=json.dumps(uploaded[1:] if len(uploaded)>1 else [],ensure_ascii=False),status=request.form.get('status','available'),marketer_id=mid, ext_marketer_id=ext_mid)
        db.session.add(row); db.session.commit(); flash('تم إضافة العرض وحفظه'); return redirect(url_for('offers'))
    query=Offer.query
    if user.role=='marketer': query=query.filter_by(marketer_id=user.id)
    return render_template('offers.html', offers=query.order_by(Offer.id.desc()).all(), marketers=ExternalMarketer.query.order_by(ExternalMarketer.name).all())
@app.route('/messages', methods=['POST'])
@login_required
def messages():
    if get_current_user().role not in ['admin','executive','marketer']: flash('ليس لديك صلاحية حفظ رسائل العملاء'); return redirect(url_for('offers'))
    db.session.add(CustomerMessage(customer_name=request.form.get('customer_name',''),phone=request.form.get('phone',''),message=request.form.get('message',''))); db.session.commit(); flash('تم حفظ رسالة العميل'); return redirect(url_for('offers'))
@app.route('/offers/status/<int:oid>', methods=['POST'])
@login_required
def offer_status(oid):
    if get_current_user().role not in ['admin','executive','marketer']:
        flash('ليس لديك صلاحية تعديل حالة العرض'); return redirect(url_for('offers'))
    row=Offer.query.get_or_404(oid); row.status=request.form.get('status','available'); db.session.commit(); flash('تم تحديث حالة العرض'); return redirect(url_for('offers'))
@app.route('/offers/delete/<int:oid>', methods=['POST'])
@login_required
def delete_offer(oid):
    if not can_delete_content(get_current_user()): flash('ليس لديك صلاحية الحذف'); return redirect(url_for('offers'))
    db.session.delete(Offer.query.get_or_404(oid)); db.session.commit(); flash('تم حذف العرض'); return redirect(url_for('offers'))


@app.route('/backups')
@login_required
def backups_page():
    if get_current_user().role not in ['admin','executive']:
        flash('ليس لديك صلاحية إدارة النسخ الاحتياطية'); return redirect(url_for('index'))
    return render_template('backups.html', backups=list_backup_files(), keep_last=BACKUP_KEEP_LAST, auto_hour=BACKUP_AUTO_HOUR)

@app.route('/backups/create', methods=['POST'])
@login_required
def backup_create_route():
    if get_current_user().role not in ['admin','executive']:
        flash('ليس لديك صلاحية إنشاء النسخ الاحتياطية'); return redirect(url_for('index'))
    path=create_system_backup(get_current_user().username)
    flash('تم إنشاء النسخة الاحتياطية بنجاح')
    return send_file(path, as_attachment=True, download_name=os.path.basename(path))

@app.route('/backups/download/<name>')
@login_required
def backup_download(name):
    if get_current_user().role not in ['admin','executive']:
        abort(403)
    safe=safe_backup_name(name)
    if not safe: abort(404)
    path=os.path.join(get_backup_dir(), safe)
    if not os.path.exists(path): abort(404)
    return send_file(path, as_attachment=True, download_name=safe)

@app.route('/backups/delete/<name>', methods=['POST'])
@login_required
def backup_delete(name):
    if get_current_user().role not in ['admin','executive']:
        flash('ليس لديك صلاحية حذف النسخ الاحتياطية'); return redirect(url_for('index'))
    safe=safe_backup_name(name)
    if safe:
        path=os.path.join(get_backup_dir(), safe)
        if os.path.exists(path): os.remove(path); flash('تم حذف النسخة الاحتياطية')
    return redirect(url_for('backups_page'))

@app.route('/system')
@login_required
def system_health(): return render_template('system.html', logs=SystemLog.query.order_by(SystemLog.id.desc()).limit(50).all())
@app.route('/system/fix', methods=['POST'])
@login_required
def system_fix():
    init_db(); db.session.add(SystemLog(level='success', message='تم فحص الجداول والأعمدة وإضافة الناقص تلقائياً', user_name=(get_current_user().username if get_current_user() else ''), status='معالج')); db.session.commit(); flash('تم الإصلاح التلقائي وفحص قاعدة البيانات'); return redirect(url_for('system_health'))

if __name__=='__main__':
    port=int(os.getenv('PORT','5000')); app.run(host='0.0.0.0', port=port, debug=False)
