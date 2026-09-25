import os, secrets, sqlite3
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, send_from_directory
from werkzeug.utils import secure_filename

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / 'tenyeszet.db'
UPLOAD_DIR = BASE / 'static' / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['MAX_CONTENT_LENGTH'] = 12 * 1024 * 1024
ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'LidiaAdmin2026!')
ALLOWED = {'jpg','jpeg','png','webp','gif'}

DEFAULT_CONTENT = {
    'site_name': 'HONEY SHADE KENNEL',
    'operator': 'Ábele Lídia',
    'hero_title': 'TÖRPESPICC\nTENYÉSZET',
    'hero_subtitle': 'HONEY SHADE KENNEL',
    'hero_text': 'Hivatalos FCI törzskönyvvel rendelkező, minőségi Pomerániai Törpespicc tenyészet.',
    'about_title': 'ÜDVÖZÖLJÜK A\nHoney Shade Kennel\nOLDALÁN!',
    'about_text': 'Ábele Lídia vagyok, 2025 óta pomerániai törpespicc tenyésztő. Előtte kutyakozmetikusként dolgoztam otthonomban, ezzel együtt érkezett a pomi szerelem családunk számára.\n\nTenyészetünk elkötelezett a fajta standardnak mindenben megfelelő, kiváló idegrendszerű, egészséges és prémium küllemű pomerániai törpespiccek iránt. Számunkra a kutyatenyésztés nem csupán hobbi, hanem mély szenvedély és felelősség.\n\nMinden nálunk született és élő kutya teljes értékű családtagként, a legnagyobb szeretetben, tisztaságban és folyamatos orvosi felügyelet mellett éli mindennapjait. Különös figyelmet fordítunk a szülők genetikai és egészségügyi szűréseire, valamint a kölykök korai szocializációjára és fejlesztésére.\n\nCélunk, hogy a Honey Shade név a leendő gazdik számára egyet jelentsen a kompromisszumok nélküli prémium minőséggel.\n\nKiskutyáink kizárólag hivatalos FCI törzskönyvvel, mikrochippel, koruknak megfelelő kötelező oltásokkal, rendszeres parazitamentesítéssel és adásvételi szerződéssel költözhetnek az új, gondosan megszűrt családjukhoz.',
    'gallery_title': 'KENNELÜNK VILÁGA',
    'gallery_text': 'A mindennapok, a kölykök fejlődése, a családi környezet és a tenyésztés fontos pillanatai egy helyen.',
    'contact_text': 'Érdeklődés, kölyök iránti jelentkezés vagy további kérdés esetén keressen bizalommal.',
    'email': 'honeyshadekennel@gmail.com',
    'phone': '+36 30 529 32 09',
    'location': 'Magyarország, Mór',
}


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db()
    con.executescript('''
    CREATE TABLE IF NOT EXISTS content (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS gallery (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL, title TEXT DEFAULT '', sort_order INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS puppies (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, color TEXT DEFAULT '', price TEXT DEFAULT '', image TEXT DEFAULT '', description TEXT DEFAULT '', available INTEGER DEFAULT 1, sort_order INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, phone TEXT, message TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, consent INTEGER DEFAULT 0);
    ''')
    for k,v in DEFAULT_CONTENT.items():
        con.execute('INSERT OR IGNORE INTO content(key,value) VALUES(?,?)',(k,v))
    count = con.execute('SELECT COUNT(*) FROM gallery').fetchone()[0]
    if count == 0:
        for i in range(1,21):
            p = UPLOAD_DIR / f'{i:02d}.jpg'
            if p.exists():
                con.execute('INSERT INTO gallery(filename,title,sort_order) VALUES(?,?,?)',(p.name,'',i))
    if con.execute('SELECT COUNT(*) FROM puppies').fetchone()[0] == 0:
        puppies=[
            ('Törpespicc kislány','Cream','350.000 Ft','03.jpg','Érdeklődjön az aktuális elérhetőségről.'),
            ('Törpespicc kisfiú','Orange Sable','380.000 Ft','17.jpg','Érdeklődjön az aktuális elérhetőségről.'),
            ('Törpespicc kislány','White','400.000 Ft','15.jpg','Érdeklődjön az aktuális elérhetőségről.'),
        ]
        for idx,p in enumerate(puppies,1): con.execute('INSERT INTO puppies(name,color,price,image,description,sort_order) VALUES(?,?,?,?,?,?)',(*p,idx))
    con.commit(); con.close()


def content():
    con=db(); rows=con.execute('SELECT key,value FROM content').fetchall(); con.close(); return {r['key']:r['value'] for r in rows}


def admin_required(f):
    @wraps(f)
    def w(*a,**kw):
        if not session.get('admin'): return redirect(url_for('admin_login', next=request.path))
        return f(*a,**kw)
    return w


def csrf():
    if 'csrf' not in session: session['csrf']=secrets.token_urlsafe(24)
    return session['csrf']

@app.context_processor
def inject(): return {'site':content(), 'csrf_token':csrf()}

@app.route('/')
def home():
    con=db(); gallery=con.execute('SELECT * FROM gallery ORDER BY sort_order,id').fetchall(); puppies=con.execute('SELECT * FROM puppies WHERE available=1 ORDER BY sort_order,id').fetchall(); con.close()
    return render_template('index.html', gallery=gallery, puppies=puppies)

@app.post('/contact')
def contact():
    if request.form.get('csrf') != session.get('csrf'): abort(400)
    if not request.form.get('consent'): flash('A kapcsolatfelvételhez az adatkezelési tájékoztató elfogadása szükséges.','error'); return redirect(url_for('home')+'#kapcsolat')
    con=db(); con.execute('INSERT INTO messages(name,email,phone,message,consent) VALUES(?,?,?,?,1)',(request.form.get('name','').strip(),request.form.get('email','').strip(),request.form.get('phone','').strip(),request.form.get('message','').strip())); con.commit(); con.close()
    flash('Köszönjük az üzenetet. Hamarosan felvesszük Önnel a kapcsolatot.','ok'); return redirect(url_for('home')+'#kapcsolat')

@app.route('/jogi/<page>')
def legal(page):
    if page not in {'aszf','adatvedelem','jogi','impresszum','suti'}: abort(404)
    return render_template(f'{page}.html')

@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        if request.form.get('username')==ADMIN_USER and request.form.get('password')==ADMIN_PASSWORD:
            session['admin']=True; return redirect(request.args.get('next') or url_for('admin'))
        flash('Hibás belépési adatok.','error')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout(): session.clear(); return redirect(url_for('home'))

@app.route('/admin')
@admin_required
def admin():
    con=db(); gallery=con.execute('SELECT * FROM gallery ORDER BY sort_order,id').fetchall(); puppies=con.execute('SELECT * FROM puppies ORDER BY sort_order,id').fetchall(); messages=con.execute('SELECT * FROM messages ORDER BY id DESC').fetchall(); con.close()
    return render_template('admin.html',gallery=gallery,puppies=puppies,messages=messages)

@app.post('/admin/content')
@admin_required
def save_content():
    if request.form.get('csrf') != session.get('csrf'): abort(400)
    con=db()
    for k in DEFAULT_CONTENT:
        if k in request.form: con.execute('INSERT OR REPLACE INTO content(key,value) VALUES(?,?)',(k,request.form[k]))
    con.commit(); con.close(); flash('A szövegek mentve.','ok'); return redirect(url_for('admin')+'#szovegek')

@app.post('/admin/upload')
@admin_required
def upload():
    if request.form.get('csrf') != session.get('csrf'): abort(400)
    files=request.files.getlist('images'); con=db(); start=con.execute('SELECT COALESCE(MAX(sort_order),0) FROM gallery').fetchone()[0]
    for n,f in enumerate(files,1):
        if not f or not f.filename: continue
        ext=f.filename.rsplit('.',1)[-1].lower() if '.' in f.filename else ''
        if ext not in ALLOWED: continue
        filename=f'{secrets.token_hex(8)}.{ext}'; f.save(UPLOAD_DIR/filename); con.execute('INSERT INTO gallery(filename,title,sort_order) VALUES(?,?,?)',(filename,request.form.get('title',''),start+n))
    con.commit(); con.close(); flash('A képek feltöltve.','ok'); return redirect(url_for('admin')+'#kepek')

@app.post('/admin/gallery/<int:item_id>/edit')
@admin_required
def edit_gallery(item_id):
    con=db(); con.execute('UPDATE gallery SET title=?,sort_order=? WHERE id=?',(request.form.get('title',''),int(request.form.get('sort_order',0)),item_id)); con.commit(); con.close(); return redirect(url_for('admin')+'#kepek')

@app.post('/admin/gallery/<int:item_id>/delete')
@admin_required
def delete_gallery(item_id):
    con=db(); row=con.execute('SELECT filename FROM gallery WHERE id=?',(item_id,)).fetchone();
    if row: 
        try: (UPLOAD_DIR/row['filename']).unlink()
        except FileNotFoundError: pass
        con.execute('DELETE FROM gallery WHERE id=?',(item_id,)); con.commit()
    con.close(); return redirect(url_for('admin')+'#kepek')

@app.post('/admin/puppy')
@admin_required
def puppy_save():
    if request.form.get('csrf') != session.get('csrf'): abort(400)
    con=db(); data=(request.form.get('name',''),request.form.get('color',''),request.form.get('price',''),request.form.get('image',''),request.form.get('description',''),1 if request.form.get('available') else 0,int(request.form.get('sort_order',0)))
    pid=request.form.get('id')
    if pid: con.execute('UPDATE puppies SET name=?,color=?,price=?,image=?,description=?,available=?,sort_order=? WHERE id=?',(*data,int(pid)))
    else: con.execute('INSERT INTO puppies(name,color,price,image,description,available,sort_order) VALUES(?,?,?,?,?,?,?)',data)
    con.commit(); con.close(); return redirect(url_for('admin')+'#kiskutyak')

@app.post('/admin/puppy/<int:pid>/delete')
@admin_required
def puppy_delete(pid):
    if request.form.get('csrf') != session.get('csrf'): abort(400)
    con=db(); con.execute('DELETE FROM puppies WHERE id=?',(pid,)); con.commit(); con.close(); return redirect(url_for('admin')+'#kiskutyak')

@app.post('/admin/message/<int:mid>/delete')
@admin_required
def message_delete(mid):
    if request.form.get('csrf') != session.get('csrf'): abort(400)
    con=db(); con.execute('DELETE FROM messages WHERE id=?',(mid,)); con.commit(); con.close(); return redirect(url_for('admin')+'#uzenetek')

@app.errorhandler(413)
def too_large(e): return 'A feltöltött fájl túl nagy. Maximum 12 MB.', 413

if __name__=='__main__':
    init_db(); app.run(host='127.0.0.1',port=int(os.environ.get('PORT','5000')),debug=False)
else:
    init_db()
