from app import db, Admin, Jabatan

username = "admin"
password = "admin"
db.session.add(Admin(username, password))
db.session.commit()

db.session.add_all([
    Jabatan(nama_jabatan= "Manager", persentase_bonus=0.5),
    Jabatan(nama_jabatan= "Supervisor", persentase_bonus=0.4),
    Jabatan(nama_jabatan= "Staff", persentase_bonus=0.3)
])
db.session.commit()