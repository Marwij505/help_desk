# help_desk
Help Desk adalah unit layanan terpusat yang dirancang untuk memberikan bantuan teknis atau informasi kepada pengguna guna menyelesaikan masalah tertentu. Dalam konteks pemilihan program studi, Help Desk berfungsi sebagai jembatan komunikasi antara calon mahasiswa dan penyedia layanan pendidikan.

# About this website
Compass Campus atau ComCam adalah platform web Help Desk pendidikan yang membantu calon mahasiswa dan mahasiswa di Indonesia dalam mencari informasi kampus, mengenali minat, menemukan program studi, memperoleh rekomendasi pendidikan, serta mengajukan pertanyaan melalui sistem bantuan.

Website dikembangkan menggunakan HTML, CSS, JavaScript, Python Flask, dan MySQL XAMPP. Tampilan website dirancang responsif agar dapat digunakan melalui desktop, tablet, dan perangkat mobile.

Status proyek: Dalam tahap pengembangan (MASIH LAMA DAN RIBET tapi cocok untuk projek mata kuliah).

# Step by step cara ngerun web ini (Kalau step ini gagal maka tanyalah AI)
1.gunakan dan nyalakan xampp atau sejenisnya yang ada mysql

2.make sure interpreter kalian python versi 3.14.5 atau versi yang bisa menampung library di step 6

3.bikin database sesuai dengan keinginan klean masing-masing (rekomendasi gw help_desk_comcam)

4.jangan lupa mengedit .env sesuai dengan database dan xampp kalian

5.gunakan semua code dari folder database dan masukan ke dalam database kalian masing-masing

6.buka terminal lalu jalankan ini masing-masing

    -python -m pip install --upgrade pip setuptools wheel

    -python -m pip install Flask mysql-connector-python python-dotenv Flask-Login Flask-WTF email-validator requests openai Flask-Limiter     Flask-Caching waitress

    -validasi 1 = python -m pip install -r .\help_desk\requirements.txt

    -validasi 2 = python -c "import flask; import mysql.connector; import dotenv; import flask_login; import flask_wtf; import email_validator; import requests; import openai; import flask_limiter; import flask_caching; import waitress; print('Semua library ComCam berhasil dimuat')"

    -validasi 3 (cek sendiri) = python -m pip list

7.test library dan code di terminal

    -python -c "import secrets; print(secrets.token_hex(32))" -> gunakan hasilnya dan ubah didalam .env di bagian "FLASK_SECRET_KEY"

    -cd C:\Users\Marcell\Repositories\help_desk / cd help_desk
      -python -c "from config import Config, validate_configuration; validate_configuration(); print(Config.DB_NAME, Config.DB_HOST, Config.DB_PORT)"
        -hasilnya nanti = help_desk_comcam 127.0.0.1 3306

      -python -c "import mysql.connector; from config import Config; db = mysql.connector.connect(host=Config.DB_HOST, port=Config.DB_PORT, user=Config.DB_USER, password=Config.DB_PASSWORD, database=Config.DB_NAME); cursor = db.cursor(); cursor.execute('SELECT DATABASE(), VERSION()'); print('Koneksi berhasil:', cursor.fetchone()); cursor.close(); db.close()"
        -hasilnya nanti = Koneksi berhasil: ('help_desk_comcam', '10.x.x-MariaDB')

      -python -m py_compile auth.py
      -python -c "import auth; print('Blueprint:', auth.auth_bp.name)"
        -hasilnya nanti = Blueprint: auth
      
      -python -m py_compile app.py
      -python -c "from app import app; print(app.url_map)"
        -hasilnya banyak
      
      -python -m flask --app app test-db
        -hasilnya banyak
      
      -python -m flask --version
        -hasilnya banyak

8.kalau udah semua, tinggal ngerun webnya di app.py okay kawan-kawan kuh dan ini masih bersifat pengembangan jadi kembangin dah kalo
  kalian ada waktu dengan versi kalian sendiri

9.kalau masih ada garis kuning atau garis-garis anomali, refresh app ngoding klean