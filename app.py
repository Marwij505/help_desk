"""
=========================================================
COMPASS CAMPUS — APP.PY

File utama aplikasi Compass Campus.

File ini bertugas:
1. Membuat aplikasi Flask
2. Memuat konfigurasi dari config.py
3. Menghubungkan aplikasi dengan database
4. Mengaktifkan autentikasi
5. Menampilkan halaman beranda
6. Menangani URL HTML lama
7. Menangani halaman 404 dan error server
8. Menjalankan server lokal Flask
=========================================================
"""

from __future__ import annotations

from typing import Any

from flask_login import (
    current_user,
    login_required,
)

from flask import (
    Flask,
    Response,
    redirect,
    render_template,
    request,
    url_for,
)

from flask_wtf.csrf import (
    CSRFError,
    CSRFProtect,
)

import auth
import database

from config import (
    Config,
    validate_configuration,
)

# Perlindungan CSRF global.
csrf = CSRFProtect()

# =========================================================
# 1. MEMBUAT APLIKASI FLASK
# =========================================================

def create_app(
    test_config: dict[str, Any] | None = None,
) -> Flask:
    """
    Membuat dan mengatur aplikasi Flask Compass Campus.

    Args:
        test_config:
            Konfigurasi tambahan untuk pengujian.
            Nilainya dapat dikosongkan saat aplikasi normal.

    Returns:
        Flask:
            Aplikasi Flask yang siap dijalankan.
    """

    # Memastikan SECRET_KEY dan nama database sudah tersedia.
    validate_configuration()

    # Menentukan folder HTML dan static secara eksplisit.
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path="/static",
    )


    # =====================================================
    # 2. MEMUAT KONFIGURASI
    # =====================================================

    # Memuat konfigurasi utama dari config.py.
    app.config.from_object(Config)

    # Konfigurasi khusus pengujian dapat menimpa
    # konfigurasi utama apabila diberikan.
    if test_config is not None:
        app.config.update(test_config)
        
     # Aktifkan CSRF setelah konfigurasi dimuat
    csrf.init_app(app)


    # =====================================================
    # 3. MENDAFTARKAN DATABASE
    # =====================================================

        # database.init_app(app) akan:
    # - Menutup koneksi setelah request selesai.
    # - Menambahkan perintah terminal test-db.
    database.init_app(app)


    # =====================================================
    # 4.1. MENDAFTARKAN AUTENTIKASI
    # =====================================================

    # auth.init_app(app) akan:
    # - Mengaktifkan Flask-Login.
    # - Mendaftarkan route login.
    # - Mendaftarkan route register.
    # - Mendaftarkan route forgot-password.
    # - Mendaftarkan route logout.
    auth.init_app(app)
    
    # =====================================================
    # 4.2. PENANGANAN TOKEN CSRF TIDAK VALID
    # =====================================================

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error: CSRFError):
        """
        Menampilkan pesan yang mudah dipahami apabila token
        keamanan form hilang atau sudah kedaluwarsa.
        """

        template_by_path = {
            "/login": "login.html",
            "/register": "register.html",
            "/forgot-password": "forgot-password.html",
        }

        template_name = template_by_path.get(
            request.path,
            "login.html",
        )

        return (
            render_template(
                template_name,
                error=(
                    "Sesi formulir sudah berakhir atau tidak valid. "
                    "Muat ulang halaman, lalu coba kembali."
                ),
                success=None,
                form_data={},
            ),
            400,
        )

    # =====================================================
    # 5. ROUTE HALAMAN BERANDA
    # =====================================================

    @app.get("/")
    def index():
        """
        Menampilkan halaman utama Compass Campus.

        Endpoint function harus bernama `index` karena
        auth.py menggunakan:

            url_for("index")
        """

        return render_template(
            "index.html"
        )


    # =====================================================
    # 6. ROUTE PEMERIKSAAN SERVER
    # =====================================================

    @app.get("/health")
    def health_check():
        """
        Memeriksa apakah server Flask berhasil berjalan.

        Halaman ini tidak menampilkan data sensitif.
        """

        return {
            "status": "ok",
            "application": "Compass Campus",
            "database": app.config["DB_NAME"],
        }, 200
    
    @app.get("/session-check")
    @login_required
    def session_check():
        """
        Route sementara untuk memastikan session login aktif.
        """

        return {
            "logged_in": True,
            "user": {
                "id": int(current_user.id),
                "full_name": current_user.full_name,
                "email": current_user.email,
                "role": current_user.role,
            },
        }, 200


    # =====================================================
    # 7. KOMPATIBILITAS LINK HTML LAMA
    # =====================================================

    # Route berikut dipakai sementara karena beberapa link HTML
    # masih menggunakan nama file seperti index.html.
    # Nantinya link tersebut akan diperbarui memakai url_for().

    @app.get("/index.html")
    def legacy_index():
        """
        Mengarahkan URL index.html ke halaman utama.
        """

        return redirect(
            url_for("index")
        )


    @app.get("/login.html")
    def legacy_login():
        """
        Mengarahkan URL login.html menuju route login Flask.
        """

        return redirect(
            url_for("auth.login")
        )


    @app.get("/register.html")
    def legacy_register():
        """
        Mengarahkan URL register.html menuju route register.
        """

        return redirect(
            url_for("auth.register")
        )


    @app.get("/forgot-password.html")
    def legacy_forgot_password():
        """
        Mengarahkan URL forgot-password.html menuju
        route forgot-password Flask.
        """

        return redirect(
            url_for("auth.forgot_password")
        )


    # =====================================================
    # 8. HEADER KEAMANAN DASAR
    # =====================================================

    @app.after_request
    def add_security_headers(
        response: Response,
    ) -> Response:
        """
        Menambahkan header keamanan dasar pada setiap respons.

        Header ini tidak menggantikan validasi backend,
        hashing password, atau perlindungan CSRF.
        """

        response.headers.setdefault(
            "X-Content-Type-Options",
            "nosniff",
        )

        response.headers.setdefault(
            "X-Frame-Options",
            "SAMEORIGIN",
        )

        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin",
        )

        response.headers.setdefault(
            "Permissions-Policy",
            (
                "camera=(), "
                "microphone=(), "
                "geolocation=()"
            ),
        )

        return response


    # =====================================================
    # 9. ERROR HANDLER 404
    # =====================================================

    @app.errorhandler(404)
    def page_not_found(error: Exception):
        """
        Menangani URL atau halaman yang tidak ditemukan.

        Halaman desain khusus 404 akan dibuat nanti.
        """

        app.logger.warning(
            "Halaman tidak ditemukan: %s",
            error,
        )

        return (
            """
            <!DOCTYPE html>
            <html lang="id">
            <head>
                <meta charset="UTF-8">
                <meta
                    name="viewport"
                    content="width=device-width, initial-scale=1.0"
                >
                <title>Halaman Tidak Ditemukan</title>
            </head>
            <body>
                <h1>404</h1>
                <p>Halaman yang kamu cari tidak ditemukan.</p>
                <a href="/">Kembali ke Beranda</a>
            </body>
            </html>
            """,
            404,
        )


    # =====================================================
    # 10. ERROR HANDLER 500
    # =====================================================

    @app.errorhandler(500)
    def internal_server_error(error: Exception):
        """
        Menangani error internal server.

        Detail error tidak ditampilkan kepada pengguna
        agar informasi sistem tidak bocor.
        """

        app.logger.exception(
            "Terjadi kesalahan internal server: %s",
            error,
        )

        return (
            """
            <!DOCTYPE html>
            <html lang="id">
            <head>
                <meta charset="UTF-8">
                <meta
                    name="viewport"
                    content="width=device-width, initial-scale=1.0"
                >
                <title>Kesalahan Server</title>
            </head>
            <body>
                <h1>Terjadi Kesalahan</h1>
                <p>
                    Sistem belum dapat memproses permintaanmu.
                    Silakan coba kembali beberapa saat lagi.
                </p>
                <a href="/">Kembali ke Beranda</a>
            </body>
            </html>
            """,
            500,
        )


    # =====================================================
    # 11. MENGEMBALIKAN APLIKASI
    # =====================================================

    return app


# =========================================================
# 12. MEMBUAT INSTANCE APLIKASI
# =========================================================

# Variabel ini memungkinkan aplikasi dijalankan dengan:
#
# python app.py
#
# atau:
#
# flask --app app run
app = create_app()


# =========================================================
# 13. MENJALANKAN SERVER LOKAL
# =========================================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=app.config["DEBUG"],
    )