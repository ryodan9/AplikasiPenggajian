from flask import Flask, jsonify, render_template, request, redirect, request, url_for, session, flash, json, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from functools import wraps
from flask_bootstrap import Bootstrap
from wsgiref.validate import validator
import calendar
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from io import BytesIO
from forms import Login


app = Flask(__name__)

app.config['SECRET_KEY'] = '$#PHenfge24'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/aplikasikaryawan'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = True

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
bootstrap = Bootstrap(app)

class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20))
    password = db.Column(db.Text)

    def __init__(self, username, password):
        self.username = username
        if password != '':
            self.password = bcrypt.generate_password_hash(password). decode('UTF-8')

class Jabatan(db.Model):
    __tablename__ = 'jabatan'
    id = db.Column(db.Integer, primary_key=True)
    nama_jabatan = db.Column(db.String(20))
    persentase_bonus = db.Column(db.Float)

    jabatan = db.relationship('Karyawan', backref=db.backref('jabatan', lazy=True))

    def __init__(self, nama_jabatan, persentase_bonus):
        self.nama_jabatan = nama_jabatan
        self.persentase_bonus = persentase_bonus

class Karyawan(db.Model):
    __tablename__ = 'karyawan'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(30))
    tanggal_lahir = db.Column(db.Date)
    alamat = db.Column(db.Text)
    no_telp = db.Column(db.String(15))
    idjabatan = db.Column(db.Integer, db.ForeignKey('jabatan.id'))

    karyawan = db.relationship('Gaji', backref=db.backref('karyawan', lazy=True))

    def __init__(self, nama, tanggal_lahir, alamat, no_telp, idjabatan):
        self.nama = nama
        self.tanggal_lahir = tanggal_lahir
        self.alamat = alamat
        self.no_telp = no_telp
        self.idjabatan = idjabatan

class Gaji(db.Model):
    __tablename__ = 'gaji'
    id = db.Column(db.Integer, primary_key=True)
    idkaryawan = db.Column(db.Integer, db.ForeignKey('karyawan.id'))
    gaji = db.Column(db.Float)
    bonus = db.Column(db.Float)
    pph = db.Column(db.Float)
    total = db.Column(db.Float)
    bulan = db.Column(db.Integer)
    tahun = db.Column(db.Integer)

    def __init__(self, idkaryawan, gaji, bonus, pph, total, bulan, tahun):
        self.idkaryawan = idkaryawan
        self.gaji = gaji
        self.bonus = bonus
        self.pph = pph
        self.total = total
        self.bulan = bulan
        self.tahun = tahun

db.create_all()

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'login' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrap

# Filter template (fungsi untuk mengembalikan nama bulan)
@app.template_filter('month_name')
def month_name_filter(month):
    return calendar.month_name[month]

# Filter template (fungsi untuk mata uang)
@app.template_filter('currency_format')
def currency_format(value):
    value = float(value)
    return "Rp. {:,.2f}".format(value)

# Route untuk halaman awal
@app.route('/')
def index():
    if session.get('login') == True:
        return redirect(url_for('kelola_karyawan'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('login') == True:
        return redirect(url_for('kelola_karyawan'))
    forms = Login()
    if forms.validate_on_submit():
        admin = Admin.query.filter_by(username=forms.username.data). first()
        if admin:
            if bcrypt.check_password_hash(admin.password, forms.password.data):
                session['login'] = True
                session['id'] = admin.id
                session['username'] = admin.username
                return redirect(url_for('kelola_karyawan'))
        error = "Data yang Anda Masukkan Salah"
        return render_template('login.html', error=error, forms=forms)
    return render_template('login.html', forms=forms)

# Route untuk Halaman Kelola Karyawan
@app.route('/karyawan')
@login_required
def kelola_karyawan():
    karyawan = Karyawan.query.all()
    jabatan = Jabatan.query.all()
    return render_template('karyawan.html', data=karyawan, jabatan=jabatan)

# Route untuk menambah karyawan
@app.route('/tambahkaryawan', methods=['GET', 'POST'])
@login_required
def tambah_karyawan():
    if request.method == "POST":
        nama = request.form['nama']
        tanggal_lahir = request.form['tanggal_lahir']
        alamat = request.form['alamat']
        no_telp = request.form['no_telp']
        idjabatan = request.form['idjabatan']
        db.session.add(Karyawan(nama, tanggal_lahir, alamat, no_telp, idjabatan))
        db.session.commit()
        return redirect(url_for('kelola_karyawan'))

# Route untuk mengedit data karyawan
@app.route('/editkaryawan/<id>', methods=['GET', 'POST'])
@login_required
def edit_karyawan(id):
    karyawan = Karyawan.query.filter_by(id=id). first()
    if request.method == "POST":
        karyawan.nama = request.form['nama']
        karyawan.tanggal_lahir = request.form['tanggal_lahir']
        karyawan.alamat = request.form['alamat']
        karyawan.no_telp = request.form['no_telp']
        karyawan.idjabatan = request.form['idjabatan']
        db.session.add(karyawan)
        db.session.commit()
        return redirect(request.referrer)

# Route untuk menghapus data karyawan
@app.route('/hapuskaryawan/<id>', methods=['GET', 'POST'])
@login_required
def hapus_karyawan(id):
    karyawan = Karyawan.query.filter_by(id=id). first()
    db.session.delete(karyawan)
    db.session.commit()
    return redirect(request.referrer)

# Route untuk Halaman Kelola Gaji
@app.route('/gaji')
@login_required
def kelola_gaji():
    bulan = db.session.query(Gaji.bulan). distinct(). all()
    tahun = db.session.query(Gaji.tahun). distinct(). all()
    gaji = Gaji.query.all()
    karyawan = Karyawan.query.all()
    return render_template('gaji.html', gaji=gaji, karyawan=karyawan, bulan=bulan, tahun=tahun)

@app.route('/calculategaji', methods=['GET', 'POST'])
@login_required
def calculate_gaji():
    if request.method == "POST":
        idkaryawan = request.form['idkaryawan']
        gaji = float(request.form['gaji'])
        
        karyawan = Karyawan.query.get(idkaryawan)
        jabatan = karyawan.jabatan

        bonus = gaji * jabatan.persentase_bonus
        pph = gaji * 0.05
        total = gaji + bonus - pph

        bulan = request.form['bulan']
        tahun = request.form['tahun']
        db.session.add(Gaji(idkaryawan, gaji, bonus, pph, total, bulan, tahun))
        db.session.commit()
        return redirect(url_for('kelola_gaji'))

# Route untuk mengedit gaji karyawan
@app.route('/editgaji/<id>', methods=['GET', 'POST'])
@login_required
def edit_gaji(id):
    gaji = Gaji.query.filter_by(id=id). first()
    if request.method == "POST":
        gaji.idkaryawan = request.form['idkaryawan']
        gaji.gaji = float(request.form['gaji'])
        
        karyawan = Karyawan.query.get(gaji.idkaryawan)
        jabatan = karyawan.jabatan

        gaji.bonus = gaji.gaji * jabatan.persentase_bonus
        gaji.pph = gaji.gaji * 0.05
        gaji.total = gaji.gaji + gaji.bonus - gaji.pph

        gaji.bulan = request.form['bulan']
        gaji.tahun = request.form['tahun']
        db.session.add(gaji)
        db.session.commit()
        return redirect(request.referrer)
    
# Route untuk menghapus gaji karyawan
@app.route('/hapusgaji/<id>', methods=['GET', 'POST'])
@login_required
def hapus_gaji(id):
    gaji = Gaji.query.filter_by(id=id). first()
    db.session.delete(gaji)
    db.session.commit()
    return redirect(request.referrer)

# Laporan gaji karyawan
@app.route('/report', methods=['GET', 'POST'])
@login_required
def generate_report():
    if request.method == "POST":
        bulan = request.form['bulan']
        tahun = request.form['tahun']

        salaries = Gaji.query.filter_by(bulan=bulan, tahun=tahun). all()

        # Membuat DataFrame data gaji
        df = pd.DataFrame(columns=['Nama', 'Gaji Pokok', 'Bonus', 'PPH', 'Total Gaji'])
        for salary in salaries:
            df = df.append({
                'Nama' : salary.karyawan.nama,
                'Gaji Pokok' : salary.gaji,
                'Bonus' : salary.bonus,
                'PPH' : salary.pph,
                'Total Gaji' : salary.total
            }, ignore_index=True)
        
        # Excel
        excel_file = f"report_gaji_bulan-{bulan}_{tahun}.xlsx"
        df.to_excel(excel_file, index=False)
            
        return send_file(excel_file, as_attachment=True) 

@app.route('/slip_gaji/<id>')
def generate_slip_gaji(id):
    salaries = Gaji.query.filter_by(id=id). first()
    
    if Gaji:
        response = make_response(create_pdf(salaries))
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=slip_gaji_{salaries.karyawan.nama}.pdf'
        return response
    else:
        return 'Tidak ditemukan.'

def create_pdf(salaries):
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, leftMargin=50)
    elements = []

    # Membuat style teks
    styles = getSampleStyleSheet()
    header_style = styles['Heading3']
    normal_style = styles['Normal']

    # Header
    header_text = f"Slip Gaji - {salaries.karyawan.nama} - {month_name_filter(salaries.bulan)} {salaries.tahun}"
    
    header = Paragraph(header_text, header_style)
    elements.append(header)

    # Data slip gaji
    data = [
        ['Nama', salaries.karyawan.nama],
        ['Gaji Pokok', f'{currency_format(salaries.gaji)} '],
        ['Bonus', f'{currency_format(salaries.bonus)}'],
        ['PPH 5%', f'{currency_format(salaries.pph)}'],
        ['Jumlah', f'{currency_format(salaries.total)}'],
    ]
    table = Table(data)

    # Mengatur style tabel
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#CCCCCC'),  # Mewarnai baris header
        ('TEXTCOLOR', (0, 0), (-1, 0), '#000000'),  # Warna teks header
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # Pusatkan teks ke kiri
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Font teks header
        ('FONTSIZE', (0, 0), (-1, 0), 12),  # Ukuran font header
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Padding bawah header
        ('BACKGROUND', (0, 1), (-1, -1), '#FFFFFF'),  # Mewarnai baris data
        ('GRID', (0, 0), (-1, -1), 0.5, '#888888'),  # Garis tabel
        ('LEFTPADDING', (0, 0), (-1, -1), 5),  # Padding kiri pada sel
        ('HALIGN', (0, 0), (-1, -1), 'LEFT'),  # Pusatkan tabel ke kiri
    ])
    table.setStyle(table_style)
    elements.append(table)

    # Membuat dokumen PDF
    doc.build(elements)
    pdf_buffer.seek(0)

    return pdf_buffer.getvalue()


@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

