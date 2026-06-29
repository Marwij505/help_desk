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
import secrets

from mysql.connector import Error

from flask_login import (
    current_user,
    login_required,
)

from flask import (
    Flask,
    Response,
    flash,
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

        # Form tiket punya halaman sendiri.
        # Jika token CSRF kedaluwarsa, user dikembalikan ke halaman tiket
        # dengan pesan yang jelas, bukan halaman error mentah.
        if request.path in {"/ticket", "/tickets", "/ticket/create"}:
            flash(
                "Sesi formulir tiket sudah berakhir. Muat ulang halaman, lalu coba kembali.",
                "error",
            )

            return redirect(
                url_for("ticket")
            )

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
    # 4.3. HELPER MODUL TICKETING HELP DESK
    # =====================================================

    TICKET_CATEGORY_OPTIONS = [
        ("program_studi", "Program Studi"),
        ("pemetaan_minat", "Pemetaan Minat"),
        ("akun", "Akun Pengguna"),
        ("data_kampus", "Data Kampus"),
        ("lainnya", "Lainnya"),
    ]

    TICKET_PRIORITY_OPTIONS = [
        ("low", "Rendah"),
        ("normal", "Normal"),
        ("high", "Tinggi"),
    ]

    TICKET_STATUS_LABELS = {
        "dikirim": "Dikirim",
        "diproses": "Diproses",
        "selesai": "Selesai",
    }

    TICKET_PRIORITY_LABELS = {
        "low": "Rendah",
        "normal": "Normal",
        "high": "Tinggi",
    }

    TICKET_CATEGORY_LABELS = dict(TICKET_CATEGORY_OPTIONS)


    def ensure_help_desk_tables() -> None:
        """
        Membuat tabel ticketing jika belum tersedia.

        Fungsi ini sengaja dibuat idempotent dengan CREATE TABLE IF NOT EXISTS.
        Jadi aman dipanggil berulang setiap kali user membuka halaman ticket.
        """

        with database.get_cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS help_tickets (
                    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                    user_id INT UNSIGNED NOT NULL,
                    ticket_code VARCHAR(24) NOT NULL,
                    category ENUM(
                        'program_studi',
                        'pemetaan_minat',
                        'akun',
                        'data_kampus',
                        'lainnya'
                    ) NOT NULL DEFAULT 'lainnya',
                    subject VARCHAR(120) NOT NULL,
                    message TEXT NOT NULL,
                    priority ENUM('low', 'normal', 'high')
                        NOT NULL DEFAULT 'normal',
                    status ENUM('dikirim', 'diproses', 'selesai')
                        NOT NULL DEFAULT 'dikirim',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
                    closed_at DATETIME DEFAULT NULL,
                    PRIMARY KEY (id),
                    UNIQUE KEY uq_help_tickets_code (ticket_code),
                    INDEX idx_help_tickets_user_id (user_id),
                    INDEX idx_help_tickets_status (status),
                    INDEX idx_help_tickets_created_at (created_at),
                    CONSTRAINT fk_help_tickets_user
                        FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                ) ENGINE=InnoDB
                  DEFAULT CHARACTER SET utf8mb4
                  COLLATE utf8mb4_unicode_ci
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS ticket_messages (
                    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                    ticket_id BIGINT UNSIGNED NOT NULL,
                    sender_id INT UNSIGNED DEFAULT NULL,
                    sender_type ENUM('user', 'admin', 'system')
                        NOT NULL DEFAULT 'user',
                    message TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    INDEX idx_ticket_messages_ticket_id (ticket_id),
                    INDEX idx_ticket_messages_sender_id (sender_id),
                    CONSTRAINT fk_ticket_messages_ticket
                        FOREIGN KEY (ticket_id)
                        REFERENCES help_tickets(id)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    CONSTRAINT fk_ticket_messages_sender
                        FOREIGN KEY (sender_id)
                        REFERENCES users(id)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                ) ENGINE=InnoDB
                  DEFAULT CHARACTER SET utf8mb4
                  COLLATE utf8mb4_unicode_ci
                """
            )

        database.commit_db()


    def get_empty_ticket_summary() -> dict[str, int]:
        """
        Ringkasan default ketika pengguna belum login atau database belum siap.
        """

        return {
            "total": 0,
            "active": 0,
            "submitted": 0,
            "in_progress": 0,
            "closed": 0,
        }


    def enrich_ticket_row(ticket_row: dict[str, Any]) -> dict[str, Any]:
        """
        Menambahkan label tampilan agar template tetap sederhana.
        """

        ticket = dict(ticket_row)
        created_at = ticket.get("created_at")

        if hasattr(created_at, "strftime"):
            ticket["created_label"] = created_at.strftime("%d/%m/%Y %H:%M")
        else:
            ticket["created_label"] = str(created_at or "-")

        ticket["status_label"] = TICKET_STATUS_LABELS.get(
            str(ticket.get("status")),
            "Dikirim",
        )
        ticket["priority_label"] = TICKET_PRIORITY_LABELS.get(
            str(ticket.get("priority")),
            "Normal",
        )
        ticket["category_label"] = TICKET_CATEGORY_LABELS.get(
            str(ticket.get("category")),
            "Lainnya",
        )

        return ticket


    def load_user_ticket_context() -> dict[str, Any]:
        """
        Mengambil ringkasan dan daftar tiket terbaru milik user yang sedang login.

        Jika terjadi gangguan database, halaman tetap terbuka.
        Error dicatat di log server agar tidak mengganggu pengalaman pengguna.
        """

        context = {
            "ticket_summary": get_empty_ticket_summary(),
            "user_tickets": [],
            "ticket_category_options": TICKET_CATEGORY_OPTIONS,
            "ticket_priority_options": TICKET_PRIORITY_OPTIONS,
        }

        if not current_user.is_authenticated:
            return context

        try:
            ensure_help_desk_tables()

            user_id = int(current_user.id)

            with database.get_cursor(dictionary=True) as cursor:
                cursor.execute(
                    """
                    SELECT
                        COUNT(*) AS total,
                        COALESCE(SUM(status != 'selesai'), 0) AS active,
                        COALESCE(SUM(status = 'dikirim'), 0) AS submitted,
                        COALESCE(SUM(status = 'diproses'), 0) AS in_progress,
                        COALESCE(SUM(status = 'selesai'), 0) AS closed
                    FROM help_tickets
                    WHERE user_id = %s
                    """,
                    (user_id,),
                )

                summary = cursor.fetchone() or {}

                context["ticket_summary"] = {
                    "total": int(summary.get("total") or 0),
                    "active": int(summary.get("active") or 0),
                    "submitted": int(summary.get("submitted") or 0),
                    "in_progress": int(summary.get("in_progress") or 0),
                    "closed": int(summary.get("closed") or 0),
                }

                cursor.execute(
                    """
                    SELECT
                        id,
                        ticket_code,
                        category,
                        subject,
                        message,
                        priority,
                        status,
                        created_at,
                        updated_at
                    FROM help_tickets
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT 5
                    """,
                    (user_id,),
                )

                rows = cursor.fetchall() or []
                context["user_tickets"] = [
                    enrich_ticket_row(row)
                    for row in rows
                ]

        except (Error, RuntimeError):
            database.rollback_db()
            app.logger.exception(
                "Ringkasan tiket pengguna gagal dimuat."
            )

        return context


    def build_index_context(
        *,
        search_query: str = "",
        search_notice: str | None = None,
    ) -> dict[str, Any]:
        """
        Menyatukan data ringkas yang dibutuhkan index.html.

        Catatan Babak 3:
        - Form dan daftar tiket tidak lagi diletakkan di index.html.
        - Index hanya mengambil ringkasan tiket aktif untuk Area Akun.
        - Modul tiket lengkap berada di templates/ticket.html.
        """

        context = {
            "search_query": search_query,
            "search_notice": search_notice,
        }

        context.update(
            load_user_ticket_context()
        )

        return context


    def validate_ticket_form(form_data: Any) -> tuple[dict[str, str], list[str]]:
        """
        Validasi backend untuk form tiket Help Desk.

        Validasi tetap dilakukan di backend walaupun nanti form HTML
        sudah memakai required, maxlength, dan pilihan select.
        """

        allowed_categories = {item[0] for item in TICKET_CATEGORY_OPTIONS}
        allowed_priorities = {item[0] for item in TICKET_PRIORITY_OPTIONS}

        cleaned_data = {
            "category": str(form_data.get("category", "lainnya")).strip(),
            "priority": str(form_data.get("priority", "normal")).strip(),
            "subject": str(form_data.get("subject", "")).strip(),
            "message": str(form_data.get("message", "")).strip(),
        }

        errors: list[str] = []

        if cleaned_data["category"] not in allowed_categories:
            errors.append("Kategori tiket tidak valid.")

        if cleaned_data["priority"] not in allowed_priorities:
            errors.append("Prioritas tiket tidak valid.")

        if len(cleaned_data["subject"]) < 5:
            errors.append("Judul tiket minimal 5 karakter.")

        if len(cleaned_data["subject"]) > 120:
            errors.append("Judul tiket maksimal 120 karakter.")

        if len(cleaned_data["message"]) < 15:
            errors.append("Isi pertanyaan minimal 15 karakter.")

        if len(cleaned_data["message"]) > 2000:
            errors.append("Isi pertanyaan maksimal 2000 karakter.")

        return cleaned_data, errors


    # =====================================================
    # 5. ROUTE HALAMAN BERANDA
    # =====================================================

    @app.get("/")
    def index():
        """
        Menampilkan halaman utama Compass Campus.
        Index adalah home page, bukan dashboard.
        """

        return render_template(
            "index.html",
            **build_index_context(),
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
    
    @app.get("/search")
    def search():
        """
        Route sementara untuk pencarian dari home page.

        Nanti route ini bisa diarahkan ke halaman pencarian khusus
        setelah modul data kampus dan program studi dibuat.
        """

        search_query = request.args.get("q", "").strip()

        search_notice = None

        if search_query:
            search_notice = (
                f"Hasil pencarian untuk '{search_query}' akan ditampilkan "
                "setelah modul data kampus dan program studi diaktifkan."
            )

        return render_template(
            "index.html",
            **build_index_context(
                search_query=search_query,
                search_notice=search_notice,
            ),
        )
    
    @app.get("/pencarian")
    def pencarian_legacy():
        """
        Alias sementara agar link lama /pencarian tetap berjalan.
        Route utama pencarian sekarang memakai /search.
        """

        return search()

    @app.get("/dashboard")
    @login_required
    def dashboard():
        """
        Alias lama agar URL /dashboard tetap aman.
        Compass Campus tidak memakai dashboard terpisah.
        Semua aktivitas pengguna berada di index.html.
        """

        return redirect(
            url_for("index")
        )
    
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
    # 6.1. ROUTE HALAMAN TIKET HELP DESK
    # =====================================================

    @app.get("/ticket")
    def ticket():
        """
        Menampilkan halaman khusus Help Desk Ticketing.

        Babak 3 dipisahkan dari index agar struktur proyek rapi:
        - template: templates/ticket.html
        - style: static/css/ticket.css
        - script: static/js/ticket.js
        """

        return render_template(
            "ticket.html",
            **load_user_ticket_context(),
        )


    @app.get("/tickets")
    def tickets_legacy():
        """
        Alias aman jika ada URL lama /tickets.
        Semua diarahkan ke halaman utama modul tiket /ticket.
        """

        return redirect(
            url_for("ticket")
        )


    # =====================================================
    # 6.2. ROUTE MEMBUAT TIKET HELP DESK
    # =====================================================

    @app.post("/ticket/create")
    @app.post("/tickets")
    @login_required
    def create_ticket():
        """
        Menyimpan tiket baru dari form Help Desk di halaman ticket.html.

        Babak 3 fokus pada sisi pengguna:
        - pengguna login dapat membuat tiket,
        - tiket tersimpan ke database,
        - ringkasan dan daftar tiket tampil di ticket.html.
        """

        cleaned_data, errors = validate_ticket_form(request.form)

        if errors:
            flash(errors[0], "error")

            return redirect(
                url_for("ticket")
            )

        ticket_code = (
            f"CC-{int(current_user.id):04d}-"
            f"{secrets.token_hex(3).upper()}"
        )

        try:
            ensure_help_desk_tables()

            with database.get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO help_tickets (
                        user_id,
                        ticket_code,
                        category,
                        subject,
                        message,
                        priority,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, 'dikirim')
                    """,
                    (
                        int(current_user.id),
                        ticket_code,
                        cleaned_data["category"],
                        cleaned_data["subject"],
                        cleaned_data["message"],
                        cleaned_data["priority"],
                    ),
                )

                ticket_id = cursor.lastrowid

                cursor.execute(
                    """
                    INSERT INTO ticket_messages (
                        ticket_id,
                        sender_id,
                        sender_type,
                        message
                    )
                    VALUES (%s, %s, 'user', %s)
                    """,
                    (
                        ticket_id,
                        int(current_user.id),
                        cleaned_data["message"],
                    ),
                )

            database.commit_db()

            flash(
                f"Tiket {ticket_code} berhasil dikirim. Tim ComCam akan meninjau pertanyaanmu.",
                "success",
            )

        except (Error, RuntimeError):
            database.rollback_db()
            app.logger.exception(
                "Tiket Help Desk gagal dibuat."
            )

            flash(
                "Tiket belum dapat dikirim. Silakan coba kembali beberapa saat lagi.",
                "error",
            )

        return redirect(
            url_for("ticket")
        )


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


    @app.get("/ticket.html")
    def legacy_ticket():
        """
        Mengarahkan URL ticket.html menuju route ticket Flask.
        """

        return redirect(
            url_for("ticket")
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