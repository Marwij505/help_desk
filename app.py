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

from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from flask_login import (
    current_user,
    login_required,
    logout_user,
)

from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template,
    request,
    session,
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

    # Token hidup server lokal.
    # Token ini berubah setiap Flask direstart.
    # Dipakai untuk membedakan session biasa dan Remember Me.
    app.config["SERVER_BOOT_ID"] = secrets.token_hex(16)

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
    # 4.2. PENJAGA SESSION LOKAL DAN REMEMBER ME
    # =====================================================

    @app.before_request
    def enforce_local_session_lifetime():
        """
        Membuat perilaku Remember Me lebih realistis untuk demo lokal.

        Aturan:
        1. Jika user tidak mencentang Remember Me, session hanya berlaku
           selama server Flask yang sama masih hidup.
        2. Jika server Flask dimatikan lalu dinyalakan ulang, user biasa
           dipaksa login ulang.
        3. Jika user mencentang Remember Me, login boleh bertahan karena
           browser menyimpan remember cookie Flask-Login.

        Catatan:
        Token ini bukan pengganti sistem session produksi. Untuk produksi,
        gunakan server-side session store seperti Redis atau database.
        """

        if request.endpoint == "static":
            return None

        if not current_user.is_authenticated:
            return None

        remember_enabled = (
            session.get("remember_enabled") == "1"
            or session.get("_fresh") is False
        )

        if remember_enabled:
            # Remember Me aktif atau user dipulihkan dari remember cookie.
            # Session boleh melewati restart server.
            session["remember_enabled"] = "1"
            session["server_boot_id"] = app.config["SERVER_BOOT_ID"]
            return None

        server_boot_id = session.get("server_boot_id")

        if server_boot_id == app.config["SERVER_BOOT_ID"]:
            return None

        # Remember Me tidak aktif dan server sudah restart.
        # User dikeluarkan dari session, lalu diarahkan ke homepage publik.
        # Catatan penting:
        # - Jangan arahkan ke halaman login otomatis.
        # - Homepage index akan tampil sebagai mode tanpa akun.
        # - Ini membuat alur lebih natural saat server lokal dimatikan
        #   lalu dinyalakan ulang tanpa Remember Me.
        logout_user()
        session.clear()

        return redirect(
            url_for("index")
        )
    
    # =====================================================
    # 4.3. PENANGANAN TOKEN CSRF TIDAK VALID
    # =====================================================

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error: CSRFError):
        """
        Menampilkan pesan yang mudah dipahami apabila token
        keamanan form hilang atau sudah kedaluwarsa.
        """

        # Form tiket dan admin punya halaman sendiri.
        # Jika token CSRF kedaluwarsa, user dikembalikan ke halaman modul
        # dengan pesan yang jelas, bukan halaman error mentah.
        if request.path in {"/ticket", "/tickets", "/ticket/create"}:
            flash(
                "Sesi formulir tiket sudah berakhir. Muat ulang halaman, lalu coba kembali.",
                "error",
            )

            return redirect(
                url_for("ticket") + "#ticket-list"
            )

        if request.path.startswith("/admin"):
            flash(
                "Sesi formulir admin sudah berakhir. Muat ulang halaman, lalu coba kembali.",
                "error",
            )

            return redirect(
                url_for("admin_panel") + "#admin-tickets"
            )

        if request.path.startswith("/recommendation") or request.path.startswith("/pemetaan-minat"):
            flash(
                "Sesi formulir pemetaan minat sudah berakhir. Muat ulang halaman, lalu coba kembali.",
                "error",
            )

            return redirect(
                url_for("recommendation") + "#interest-form"
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

        # Field tambahan dari query LEFT JOIN ticket_messages.
        # Aman diberi default 0 agar template tidak error jika query lama dipakai.
        ticket["message_count"] = int(ticket.get("message_count") or 0)
        ticket["admin_reply_count"] = int(ticket.get("admin_reply_count") or 0)

        last_admin_reply_at = ticket.get("last_admin_reply_at")
        if hasattr(last_admin_reply_at, "strftime"):
            ticket["last_admin_reply_label"] = last_admin_reply_at.strftime("%d/%m/%Y %H:%M")
        else:
            ticket["last_admin_reply_label"] = str(last_admin_reply_at or "-")

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
            # Detail tiket dipakai saat user membuka /ticket/<id>.
            # Jika None, halaman hanya menampilkan daftar tiket seperti biasa.
            "selected_ticket": None,
            "ticket_messages": [],
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
                        t.id,
                        t.ticket_code,
                        t.category,
                        t.subject,
                        t.message,
                        t.priority,
                        t.status,
                        t.created_at,
                        t.updated_at,
                        COUNT(tm.id) AS message_count,
                        COALESCE(SUM(tm.sender_type = 'admin'), 0) AS admin_reply_count,
                        MAX(CASE WHEN tm.sender_type = 'admin' THEN tm.created_at END) AS last_admin_reply_at
                    FROM help_tickets t
                    LEFT JOIN ticket_messages tm
                        ON tm.ticket_id = t.id
                    WHERE t.user_id = %s
                    GROUP BY
                        t.id,
                        t.ticket_code,
                        t.category,
                        t.subject,
                        t.message,
                        t.priority,
                        t.status,
                        t.created_at,
                        t.updated_at
                    ORDER BY t.updated_at DESC, t.created_at DESC
                    LIMIT 8
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
        search_focus: str = "",
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
            "search_focus": search_focus,
        }

        context.update(
            load_user_ticket_context()
        )

        return context


    # =====================================================
    # 4.4. HELPER BABAK 5 - DATA KAMPUS DAN DETAIL PROGRAM STUDI
    # =====================================================

    DEFAULT_PROGRAM_SLUG = "teknik-informatika"

    FALLBACK_CAMPUS_DATA = {
        "campus_name": "Universitas Esa Unggul",
        "campus_slug": "universitas-esa-unggul",
        "campus_city": "Bekasi",
        "campus_address": "Harapan Indah, Bekasi",
        "campus_type": "Perguruan Tinggi Swasta",
        "campus_website": "https://www.esaunggul.ac.id",
        "campus_description": (
            "Universitas Esa Unggul adalah kampus swasta yang menyediakan "
            "berbagai pilihan program studi untuk calon mahasiswa baru."
        ),
        "program_name": "Teknik Informatika",
        "program_slug": "teknik-informatika",
        "faculty": "Fakultas Ilmu Komputer",
        "degree": "S1",
        "accreditation": "Baik Sekali",
        "learning_mode": "Reguler",
        "duration": "8 Semester",
        "tuition_range": "Informasi biaya mengikuti kebijakan kampus",
        "summary": (
            "Teknik Informatika cocok untuk pengguna yang tertarik pada "
            "pemrograman, rekayasa perangkat lunak, kecerdasan buatan, data, "
            "dan pengembangan sistem digital."
        ),
        "curriculum_points": [
            "Dasar pemrograman dan struktur data",
            "Basis data dan analisis sistem",
            "Rekayasa perangkat lunak",
            "Jaringan komputer dan keamanan",
            "Kecerdasan buatan dan data science",
        ],
        "career_paths": [
            "Software Developer",
            "Backend Developer",
            "Data Analyst",
            "AI Engineer",
            "System Analyst",
        ],
        "skills": [
            "Problem solving",
            "Logika algoritma",
            "Pemrograman",
            "Analisis data",
            "Kolaborasi tim",
        ],
        "facilities": [
            "Laboratorium komputer",
            "Akses pembelajaran digital",
            "Dukungan dosen dan konselor akademik",
            "Kegiatan pengembangan minat mahasiswa",
        ],
    }

    def split_semicolon_text(value: Any) -> list[str]:
        """
        Mengubah teks database berbasis tanda titik koma menjadi list.

        Format ini dipilih agar schema tetap sederhana dan mudah dibaca
        lewat phpMyAdmin tanpa membutuhkan kolom JSON.
        """

        return [
            item.strip()
            for item in str(value or "").split(";")
            if item.strip()
        ]


    def ensure_campus_tables() -> None:
        """
        Membuat tabel kampus dan program studi untuk Babak 5.

        Fungsi ini aman dipanggil berulang karena memakai
        CREATE TABLE IF NOT EXISTS dan INSERT IGNORE.
        Jika schema-5.sql sudah dijalankan manual, fungsi ini tetap aman.
        """

        with database.get_cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS campuses (
                    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                    slug VARCHAR(120) NOT NULL,
                    campus_name VARCHAR(160) NOT NULL,
                    city VARCHAR(100) NOT NULL,
                    address VARCHAR(255) DEFAULT NULL,
                    website VARCHAR(180) DEFAULT NULL,
                    campus_type VARCHAR(100) DEFAULT NULL,
                    description TEXT DEFAULT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    UNIQUE KEY uq_campuses_slug (slug)
                ) ENGINE=InnoDB
                  DEFAULT CHARACTER SET utf8mb4
                  COLLATE utf8mb4_unicode_ci
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS study_programs (
                    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                    campus_id BIGINT UNSIGNED NOT NULL,
                    slug VARCHAR(120) NOT NULL,
                    program_name VARCHAR(160) NOT NULL,
                    faculty VARCHAR(160) NOT NULL,
                    degree VARCHAR(40) NOT NULL DEFAULT 'S1',
                    accreditation VARCHAR(80) DEFAULT 'Dalam pendataan',
                    learning_mode VARCHAR(80) DEFAULT 'Reguler',
                    duration VARCHAR(80) DEFAULT '8 Semester',
                    tuition_range VARCHAR(180) DEFAULT NULL,
                    summary TEXT NOT NULL,
                    curriculum_points TEXT DEFAULT NULL,
                    career_paths TEXT DEFAULT NULL,
                    skills TEXT DEFAULT NULL,
                    facilities TEXT DEFAULT NULL,
                    is_active TINYINT(1) NOT NULL DEFAULT 1,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    UNIQUE KEY uq_study_programs_slug (slug),
                    INDEX idx_study_programs_campus_id (campus_id),
                    INDEX idx_study_programs_faculty (faculty),
                    INDEX idx_study_programs_active (is_active),
                    CONSTRAINT fk_study_programs_campus
                        FOREIGN KEY (campus_id)
                        REFERENCES campuses(id)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                ) ENGINE=InnoDB
                  DEFAULT CHARACTER SET utf8mb4
                  COLLATE utf8mb4_unicode_ci
                """
            )

            # -------------------------------------------------
            # BABAK 5B - SEED DATA KAMPUS TERNAMA INDONESIA
            # -------------------------------------------------
            # Data ini disiapkan sebagai seed realistis untuk demo.
            # Untuk rilis final, akreditasi dan deskripsi wajib diverifikasi
            # ulang memakai PDDikti, BAN-PT/LAM, dan website resmi kampus.

            seed_campuses = [(1,
  'universitas-esa-unggul',
  'Universitas Esa Unggul',
  'Jakarta dan Bekasi',
  'Jakarta Barat dan Harapan Indah Bekasi',
  'https://www.esaunggul.ac.id',
  'Perguruan Tinggi Swasta',
  'Kampus swasta dengan pilihan program studi lintas bidang. Data ini dipakai sebagai seed awal ComCam dan perlu '
  'diverifikasi kembali dengan sumber resmi kampus.'),
 (2,
  'universitas-indonesia',
  'Universitas Indonesia',
  'Depok dan Jakarta',
  'Depok, Jawa Barat dan Salemba, Jakarta',
  'https://www.ui.ac.id',
  'Perguruan Tinggi Negeri',
  'Perguruan tinggi negeri besar di Indonesia dengan program lintas rumpun ilmu. Data ringkas ini digunakan untuk '
  'simulasi direktori awal.'),
 (3,
  'institut-teknologi-bandung',
  'Institut Teknologi Bandung',
  'Bandung',
  'Bandung, Jawa Barat',
  'https://www.itb.ac.id',
  'Perguruan Tinggi Negeri',
  'Kampus negeri yang dikenal kuat pada bidang sains, teknologi, seni, desain, dan rekayasa. Data ini bersifat seed '
  'awal untuk demo ComCam.'),
 (4,
  'universitas-gadjah-mada',
  'Universitas Gadjah Mada',
  'Yogyakarta',
  'Sleman, Daerah Istimewa Yogyakarta',
  'https://www.ugm.ac.id',
  'Perguruan Tinggi Negeri',
  'Perguruan tinggi negeri besar di Yogyakarta dengan pilihan program studi luas. Data ini perlu diverifikasi sebelum '
  'dipakai sebagai informasi final.'),
 (5,
  'institut-pertanian-bogor',
  'IPB University',
  'Bogor',
  'Dramaga, Bogor, Jawa Barat',
  'https://www.ipb.ac.id',
  'Perguruan Tinggi Negeri',
  'Kampus negeri yang kuat pada rumpun pertanian, pangan, biosains, bisnis, dan teknologi terapan. Data ini adalah '
  'seed awal ComCam.'),
 (6,
  'institut-teknologi-sepuluh-nopember',
  'Institut Teknologi Sepuluh Nopember',
  'Surabaya',
  'Sukolilo, Surabaya, Jawa Timur',
  'https://www.its.ac.id',
  'Perguruan Tinggi Negeri',
  'Kampus negeri berbasis teknologi, sains, maritim, sistem informasi, dan rekayasa. Data disiapkan untuk demo '
  'realistis.'),
 (7,
  'universitas-airlangga',
  'Universitas Airlangga',
  'Surabaya',
  'Surabaya, Jawa Timur',
  'https://www.unair.ac.id',
  'Perguruan Tinggi Negeri',
  'Kampus negeri dengan kekuatan pada kesehatan, sosial, ekonomi, dan sains. Data awal ini perlu dicocokkan dengan '
  'sumber resmi.'),
 (8,
  'universitas-diponegoro',
  'Universitas Diponegoro',
  'Semarang',
  'Tembalang, Semarang, Jawa Tengah',
  'https://www.undip.ac.id',
  'Perguruan Tinggi Negeri',
  'Kampus negeri di Semarang dengan beragam program studi sains, sosial, ekonomi, dan teknik. Data ini untuk kebutuhan '
  'simulasi.'),
 (9,
  'universitas-brawijaya',
  'Universitas Brawijaya',
  'Malang',
  'Malang, Jawa Timur',
  'https://www.ub.ac.id',
  'Perguruan Tinggi Negeri',
  'Kampus negeri di Malang dengan pilihan program studi luas pada sosial, ekonomi, teknologi, kesehatan, dan '
  'pertanian.'),
 (10,
  'universitas-padjadjaran',
  'Universitas Padjadjaran',
  'Bandung dan Sumedang',
  'Jatinangor, Sumedang dan Bandung, Jawa Barat',
  'https://www.unpad.ac.id',
  'Perguruan Tinggi Negeri',
  'Kampus negeri di Jawa Barat dengan rumpun sosial, kesehatan, hukum, komunikasi, dan sains. Data ini bersifat seed '
  'demo.'),
 (11,
  'telkom-university',
  'Telkom University',
  'Bandung',
  'Bandung, Jawa Barat',
  'https://telkomuniversity.ac.id',
  'Perguruan Tinggi Swasta',
  'Kampus swasta yang dikenal pada bidang teknologi informasi, bisnis digital, desain, komunikasi, dan rekayasa.'),
 (12,
  'binus-university',
  'BINUS University',
  'Jakarta dan Tangerang',
  'Jakarta, Tangerang, dan beberapa lokasi kampus lain',
  'https://binus.ac.id',
  'Perguruan Tinggi Swasta',
  'Kampus swasta dengan program populer di bidang komputer, bisnis, desain, komunikasi, dan sistem informasi.'),
 (13,
  'universitas-gunadarma',
  'Universitas Gunadarma',
  'Depok dan Jakarta',
  'Depok dan Jakarta',
  'https://www.gunadarma.ac.id',
  'Perguruan Tinggi Swasta',
  'Kampus swasta yang dikenal pada bidang komputer, ekonomi, psikologi, dan teknik. Data ini digunakan sebagai seed '
  'awal.'),
 (14,
  'universitas-katolik-indonesia-atma-jaya',
  'Universitas Katolik Indonesia Atma Jaya',
  'Jakarta',
  'Jakarta',
  'https://www.atmajaya.ac.id',
  'Perguruan Tinggi Swasta',
  'Kampus swasta dengan program di bidang bisnis, psikologi, teknik, pendidikan, dan ilmu kesehatan.'),
 (15,
  'universitas-trisakti',
  'Universitas Trisakti',
  'Jakarta',
  'Jakarta Barat, DKI Jakarta',
  'https://trisakti.ac.id',
  'Perguruan Tinggi Swasta',
  'Kampus swasta di Jakarta dengan pilihan program pada teknik, ekonomi, arsitektur, hukum, dan bidang profesional.')]

            cursor.executemany(
                """
                INSERT INTO campuses (
                    id, slug, campus_name, city, address, website, campus_type, description
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    campus_name = VALUES(campus_name),
                    city = VALUES(city),
                    address = VALUES(address),
                    website = VALUES(website),
                    campus_type = VALUES(campus_type),
                    description = VALUES(description),
                    updated_at = CURRENT_TIMESTAMP
                """,
                seed_campuses,
            )

            seed_programs = [(1,
  'teknik-informatika',
  'Teknik Informatika',
  'Fakultas Ilmu Komputer',
  'S1',
  'Baik Sekali',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk mempelajari pemrograman, rekayasa perangkat lunak, jaringan, keamanan, data, dan kecerdasan buatan.',
  'Dasar pemrograman;Struktur data;Basis data;Rekayasa perangkat lunak;Kecerdasan buatan',
  'Software Developer;Backend Developer;Data Analyst;AI Engineer;System Analyst',
  'Problem solving;Logika algoritma;Pemrograman;Analisis data;Kolaborasi',
  'Laboratorium komputer;Akses pembelajaran digital;Bimbingan akademik;Kegiatan minat mahasiswa'),
 (1,
  'sistem-informasi',
  'Sistem Informasi',
  'Fakultas Ilmu Komputer',
  'S1',
  'Baik Sekali',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi yang menghubungkan teknologi, proses bisnis, basis data, analisis sistem, dan kebutuhan organisasi.',
  'Analisis proses bisnis;Basis data;Manajemen proyek TI;Enterprise system;UI/UX dasar',
  'Business Analyst;System Analyst;IT Project Officer;Product Owner;Database Administrator',
  'Analisis kebutuhan;Komunikasi bisnis;Pemodelan sistem;Manajemen data;Dokumentasi',
  'Laboratorium komputer;Studi kasus bisnis digital;Simulasi proyek;Akses materi digital'),
 (1,
  'manajemen',
  'Manajemen',
  'Fakultas Ekonomi dan Bisnis',
  'S1',
  'Baik Sekali',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk memahami pengelolaan organisasi, bisnis, pemasaran, SDM, keuangan, dan strategi.',
  'Pengantar manajemen;Pemasaran;Keuangan;SDM;Kewirausahaan',
  'Management Trainee;Marketing Officer;HR Officer;Business Development;Entrepreneur',
  'Kepemimpinan;Analisis bisnis;Komunikasi;Strategi;Negosiasi',
  'Kelas diskusi;Studi kasus bisnis;Kegiatan kewirausahaan;Bimbingan akademik'),
 (1,
  'desain-komunikasi-visual',
  'Desain Komunikasi Visual',
  'Fakultas Desain dan Industri Kreatif',
  'S1',
  'Dalam verifikasi',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk memahami desain, visual branding, ilustrasi, media digital, dan komunikasi visual.',
  'Dasar desain;Tipografi;Ilustrasi digital;Branding;Desain UI',
  'Graphic Designer;UI Designer;Brand Designer;Illustrator;Creative Content Designer',
  'Kreativitas visual;Komposisi;Software desain;Storytelling visual;Riset pengguna',
  'Studio desain;Perangkat desain digital;Galeri karya;Pendampingan portofolio'),
 (1,
  'ilmu-komunikasi',
  'Ilmu Komunikasi',
  'Fakultas Ilmu Komunikasi',
  'S1',
  'Baik Sekali',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk memahami komunikasi massa, public relations, media digital, konten, dan strategi komunikasi.',
  'Dasar komunikasi;Public relations;Komunikasi digital;Produksi konten;Riset media',
  'Public Relations Officer;Content Strategist;Social Media Specialist;Media Planner;Communication Officer',
  'Public speaking;Menulis;Riset audiens;Produksi konten;Manajemen komunikasi',
  'Studio media;Ruang praktik komunikasi;Kegiatan produksi konten;Bimbingan portofolio'),
 (1,
  'akuntansi',
  'Akuntansi',
  'Fakultas Ekonomi dan Bisnis',
  'S1',
  'Baik Sekali',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk mempelajari pencatatan keuangan, audit, perpajakan, dan pelaporan bisnis.',
  'Akuntansi dasar;Akuntansi keuangan;Perpajakan;Audit;Sistem informasi akuntansi',
  'Accounting Staff;Auditor;Tax Officer;Finance Officer;Budget Analyst',
  'Ketelitian;Analisis angka;Etika profesi;Pelaporan keuangan;Software akuntansi',
  'Laboratorium akuntansi;Studi kasus laporan keuangan;Simulasi pajak;Bimbingan akademik'),
 (2,
  'ui-ilmu-komputer',
  'Ilmu Komputer',
  'Fakultas Ilmu Komputer',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk mempelajari fondasi komputasi, algoritma, sistem perangkat lunak, data, dan kecerdasan buatan.',
  'Algoritma;Matematika diskrit;Sistem operasi;Basis data;Machine learning',
  'Software Engineer;Research Assistant;Data Scientist;AI Engineer;Cybersecurity Analyst',
  'Pemrograman;Berpikir komputasional;Riset teknis;Analisis sistem;Pemecahan masalah',
  'Laboratorium komputer;Komunitas teknologi;Akses riset;Ekosistem akademik besar'),
 (2,
  'ui-kedokteran',
  'Pendidikan Dokter',
  'Fakultas Kedokteran',
  'S1',
  'Perlu verifikasi LAM-PTKes',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk menyiapkan calon dokter melalui ilmu biomedis, klinik, etika, dan pelayanan kesehatan.',
  'Anatomi;Fisiologi;Patologi;Keterampilan klinik;Etika kedokteran',
  'Dokter;Peneliti kesehatan;Medical Officer;Akademisi klinik',
  'Empati;Analisis klinis;Komunikasi pasien;Ketelitian;Etika profesi',
  'Laboratorium biomedis;Rumah sakit pendidikan;Klinik keterampilan;Perpustakaan kesehatan'),
 (2,
  'ui-psikologi',
  'Psikologi',
  'Fakultas Psikologi',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk memahami perilaku manusia, proses mental, asesmen psikologi, dan intervensi berbasis ilmu.',
  'Psikologi umum;Statistika psikologi;Psikometri;Psikologi perkembangan;Psikologi industri',
  'HR Specialist;Konselor lanjutan;Research Assistant;Talent Assessment Officer',
  'Observasi;Wawancara;Analisis data;Empati;Etika asesmen',
  'Laboratorium psikologi;Ruang observasi;Kegiatan riset;Bimbingan akademik'),
 (2,
  'ui-akuntansi',
  'Akuntansi',
  'Fakultas Ekonomi dan Bisnis',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk mempelajari akuntansi keuangan, audit, sistem informasi akuntansi, dan pengambilan keputusan bisnis.',
  'Akuntansi keuangan;Audit;Perpajakan;Manajemen keuangan;Sistem informasi akuntansi',
  'Auditor;Accountant;Tax Consultant;Financial Analyst',
  'Analisis laporan;Ketelitian;Etika profesi;Pengolahan data;Problem solving',
  'Laboratorium bisnis;Studi kasus perusahaan;Kegiatan organisasi;Akses literatur ekonomi'),
 (3,
  'itb-teknik-informatika',
  'Teknik Informatika',
  'Sekolah Teknik Elektro dan Informatika',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi teknik komputasi yang kuat pada algoritma, sistem perangkat lunak, kecerdasan buatan, dan infrastruktur digital.',
  'Algoritma;Pemrograman lanjut;Sistem operasi;Jaringan komputer;AI',
  'Software Engineer;AI Engineer;Cybersecurity Engineer;System Architect',
  'Logika kuat;Matematika komputasi;Pemrograman;Riset teknis;Kolaborasi proyek',
  'Laboratorium komputasi;Ekosistem teknologi;Komunitas riset;Project-based learning'),
 (3,
  'itb-teknik-elektro',
  'Teknik Elektro',
  'Sekolah Teknik Elektro dan Informatika',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk memahami elektronika, sistem tenaga, telekomunikasi, kontrol, dan teknologi perangkat keras.',
  'Rangkaian listrik;Elektronika;Sistem kontrol;Telekomunikasi;Sinyal dan sistem',
  'Electrical Engineer;Control Engineer;Telecommunication Engineer;Hardware Engineer',
  'Analisis rangkaian;Matematika teknik;Eksperimen;Desain sistem;Pemecahan masalah',
  'Laboratorium elektro;Proyek rekayasa;Peralatan praktikum;Komunitas teknologi'),
 (3,
  'itb-teknik-sipil',
  'Teknik Sipil',
  'Fakultas Teknik Sipil dan Lingkungan',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk merancang, membangun, dan mengelola infrastruktur seperti gedung, jalan, jembatan, dan air.',
  'Mekanika teknik;Struktur beton;Transportasi;Geoteknik;Manajemen konstruksi',
  'Civil Engineer;Site Engineer;Structural Engineer;Project Engineer',
  'Analisis struktur;Manajemen proyek;Ketelitian;Pengukuran lapangan;Software teknik',
  'Laboratorium struktur;Laboratorium tanah;Praktik lapangan;Studio perancangan'),
 (3,
  'itb-desain-produk',
  'Desain Produk',
  'Fakultas Seni Rupa dan Desain',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk merancang produk yang fungsional, estetis, ergonomis, dan sesuai kebutuhan pengguna.',
  'Dasar desain;Ergonomi;Material produk;Prototyping;Desain berkelanjutan',
  'Product Designer;Industrial Designer;UX Designer;Design Researcher',
  'Riset pengguna;Sketsa;Prototyping;Kreativitas;Pemecahan masalah',
  'Studio desain;Workshop prototipe;Galeri karya;Peralatan produksi'),
 (4,
  'ugm-kedokteran',
  'Pendidikan Dokter',
  'Fakultas Kedokteran, Kesehatan Masyarakat, dan Keperawatan',
  'S1',
  'Perlu verifikasi LAM-PTKes',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk menyiapkan calon dokter dengan dasar biomedis, klinik, kesehatan masyarakat, dan etika profesi.',
  'Biomedis;Anatomi;Keterampilan klinik;Patologi;Ilmu kesehatan masyarakat',
  'Dokter;Medical Officer;Peneliti kesehatan;Akademisi klinik',
  'Komunikasi pasien;Analisis klinis;Empati;Etika profesi;Kerja tim',
  'Laboratorium medis;Rumah sakit pendidikan;Klinik keterampilan;Lingkungan riset'),
 (4,
  'ugm-hukum',
  'Ilmu Hukum',
  'Fakultas Hukum',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk memahami sistem hukum, peraturan, argumentasi hukum, kontrak, dan penyelesaian sengketa.',
  'Pengantar hukum;Hukum pidana;Hukum perdata;Hukum tata negara;Metode penelitian hukum',
  'Legal Officer;Advokat setelah pendidikan profesi;Policy Analyst;Compliance Officer',
  'Argumentasi;Analisis peraturan;Menulis hukum;Negosiasi;Etika profesi',
  'Moot court;Perpustakaan hukum;Klinik hukum;Diskusi kasus'),
 (4,
  'ugm-manajemen',
  'Manajemen',
  'Fakultas Ekonomika dan Bisnis',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk mempelajari pengelolaan bisnis, strategi, pemasaran, keuangan, operasi, dan SDM.',
  'Manajemen dasar;Keuangan;Pemasaran;Operasi;Strategi bisnis',
  'Management Trainee;Business Analyst;Marketing Strategist;Entrepreneur',
  'Analisis bisnis;Komunikasi;Kepemimpinan;Pengambilan keputusan;Kolaborasi',
  'Laboratorium bisnis;Studi kasus;Komunitas kewirausahaan;Akses riset ekonomi'),
 (4,
  'ugm-ilmu-komputer',
  'Ilmu Komputer',
  'Fakultas Matematika dan Ilmu Pengetahuan Alam',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi komputasi untuk mempelajari algoritma, pemrograman, basis data, AI, dan komputasi ilmiah.',
  'Pemrograman;Algoritma;Basis data;Komputasi ilmiah;Machine learning',
  'Software Developer;Data Analyst;AI Engineer;Research Assistant',
  'Logika komputasi;Analisis data;Pemrograman;Pemodelan;Riset',
  'Laboratorium komputer;Kegiatan riset;Komunitas teknologi;Akses literatur'),
 (5,
  'ipb-agribisnis',
  'Agribisnis',
  'Fakultas Ekonomi dan Manajemen',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk mempelajari bisnis pertanian, rantai pasok pangan, pemasaran agribisnis, dan kewirausahaan.',
  'Ekonomi pertanian;Pemasaran agribisnis;Rantai pasok;Kewirausahaan;Manajemen usaha tani',
  'Agribusiness Analyst;Supply Chain Officer;Business Development;Entrepreneur pangan',
  'Analisis pasar;Manajemen rantai pasok;Komunikasi bisnis;Riset lapangan;Kewirausahaan',
  'Laboratorium bisnis;Kebun praktik;Studi lapangan;Inkubasi bisnis'),
 (5,
  'ipb-teknologi-pangan',
  'Teknologi Pangan',
  'Fakultas Teknologi Pertanian',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk memahami pengolahan pangan, keamanan pangan, mutu, inovasi produk, dan teknologi industri pangan.',
  'Kimia pangan;Mikrobiologi pangan;Teknologi proses;Keamanan pangan;Pengendalian mutu',
  'Food Technologist;Quality Control;R&D Product;Food Safety Officer',
  'Analisis laboratorium;Ketelitian;Inovasi produk;Higiene pangan;Problem solving',
  'Laboratorium pangan;Pilot plant;Praktikum mutu;Riset produk'),
 (5,
  'ipb-ilmu-gizi',
  'Ilmu Gizi',
  'Fakultas Ekologi Manusia',
  'S1',
  'Perlu verifikasi LAM-PTKes',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk mempelajari gizi manusia, dietetik, kesehatan masyarakat, pangan, dan intervensi gizi.',
  'Dasar gizi;Dietetik;Biokimia gizi;Gizi masyarakat;Penilaian status gizi',
  'Nutritionist;Dietitian setelah pendidikan profesi;Food Service Officer;Community Nutrition Officer',
  'Komunikasi kesehatan;Analisis gizi;Empati;Edukasi masyarakat;Riset data',
  'Laboratorium gizi;Praktik komunitas;Klinik pembelajaran;Kegiatan edukasi'),
 (6,
  'its-sistem-informasi',
  'Sistem Informasi',
  'Fakultas Teknologi Elektro dan Informatika Cerdas',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk menggabungkan teknologi, bisnis, data, analisis proses, dan transformasi digital organisasi.',
  'Analisis sistem;Basis data;Manajemen proyek TI;Data analytics;Enterprise architecture',
  'Business Analyst;Data Analyst;IT Consultant;Product Owner',
  'Analisis kebutuhan;Manajemen data;Komunikasi bisnis;Dokumentasi;Kolaborasi',
  'Laboratorium SI;Proyek industri;Komunitas teknologi;Studi kasus digital'),
 (6,
  'its-teknik-informatika',
  'Teknik Informatika',
  'Fakultas Teknologi Elektro dan Informatika Cerdas',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi teknik komputasi untuk pemrograman, AI, jaringan, keamanan, dan rekayasa perangkat lunak.',
  'Algoritma;Pemrograman lanjut;Basis data;Jaringan;AI',
  'Software Engineer;Backend Developer;AI Engineer;Cybersecurity Analyst',
  'Pemrograman;Analisis sistem;Matematika komputasi;Problem solving;Kerja tim',
  'Laboratorium komputer;Proyek perangkat lunak;Komunitas riset;Akses pembelajaran'),
 (6,
  'its-teknik-industri',
  'Teknik Industri',
  'Fakultas Teknologi Industri dan Rekayasa Sistem',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk merancang sistem kerja, produksi, rantai pasok, optimasi, dan peningkatan produktivitas.',
  'Statistika industri;Ergonomi;Riset operasi;Manajemen produksi;Supply chain',
  'Industrial Engineer;Process Improvement Analyst;Supply Chain Planner;Operations Analyst',
  'Optimasi;Analisis proses;Pemodelan sistem;Manajemen proyek;Komunikasi',
  'Laboratorium ergonomi;Simulasi industri;Studi lapangan;Software optimasi'),
 (7,
  'unair-farmasi',
  'Farmasi',
  'Fakultas Farmasi',
  'S1',
  'Perlu verifikasi LAM-PTKes',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk mempelajari obat, formulasi, farmakologi, pelayanan kefarmasian, dan pengembangan produk kesehatan.',
  'Kimia farmasi;Farmakologi;Teknologi sediaan;Farmasi klinik;Regulasi obat',
  'Pharmacist setelah profesi;R&D Farmasi;Quality Assurance;Regulatory Affairs',
  'Ketelitian;Analisis laboratorium;Etika kesehatan;Komunikasi pasien;Riset',
  'Laboratorium farmasi;Praktikum formulasi;Fasilitas riset;Kerja sama kesehatan'),
 (7,
  'unair-kesehatan-masyarakat',
  'Kesehatan Masyarakat',
  'Fakultas Kesehatan Masyarakat',
  'S1',
  'Perlu verifikasi LAM-PTKes',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk memahami epidemiologi, promosi kesehatan, kebijakan, keselamatan kerja, dan kesehatan lingkungan.',
  'Epidemiologi;Biostatistika;Promosi kesehatan;K3;Kesehatan lingkungan',
  'Public Health Officer;Health Promoter;Epidemiology Assistant;K3 Officer',
  'Analisis data;Komunikasi masyarakat;Riset lapangan;Perencanaan program;Advokasi',
  'Laboratorium kesehatan;Praktik komunitas;Riset lapangan;Kegiatan edukasi'),
 (7,
  'unair-manajemen',
  'Manajemen',
  'Fakultas Ekonomi dan Bisnis',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi bisnis untuk strategi, pemasaran, operasi, keuangan, organisasi, dan kewirausahaan.',
  'Manajemen dasar;Keuangan;Pemasaran;Operasi;Kewirausahaan',
  'Management Trainee;Marketing Officer;Business Analyst;Entrepreneur',
  'Kepemimpinan;Analisis pasar;Komunikasi;Pengambilan keputusan;Negosiasi',
  'Laboratorium bisnis;Studi kasus;Kegiatan kewirausahaan;Komunitas mahasiswa'),
 (8,
  'undip-teknik-sipil',
  'Teknik Sipil',
  'Fakultas Teknik',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk merancang dan mengelola infrastruktur bangunan, jalan, jembatan, air, dan proyek konstruksi.',
  'Mekanika teknik;Struktur;Hidrologi;Transportasi;Manajemen konstruksi',
  'Civil Engineer;Structural Engineer;Site Engineer;Project Planner',
  'Analisis struktur;Pengukuran;Manajemen proyek;Software teknik;Ketelitian',
  'Laboratorium struktur;Laboratorium tanah;Studio perancangan;Praktik lapangan'),
 (8,
  'undip-ilmu-komunikasi',
  'Ilmu Komunikasi',
  'Fakultas Ilmu Sosial dan Ilmu Politik',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk mempelajari komunikasi strategis, media, public relations, riset audiens, dan komunikasi digital.',
  'Teori komunikasi;Public relations;Media digital;Riset komunikasi;Produksi konten',
  'PR Officer;Content Strategist;Media Planner;Communication Analyst',
  'Menulis;Public speaking;Riset audiens;Produksi konten;Strategi komunikasi',
  'Studio komunikasi;Kegiatan media;Diskusi kasus;Praktik produksi'),
 (8,
  'undip-akuntansi',
  'Akuntansi',
  'Fakultas Ekonomika dan Bisnis',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk mempelajari laporan keuangan, audit, perpajakan, sistem informasi akuntansi, dan tata kelola.',
  'Akuntansi keuangan;Audit;Perpajakan;Akuntansi manajemen;SIA',
  'Auditor;Accountant;Tax Officer;Finance Analyst',
  'Ketelitian;Analisis angka;Etika;Pelaporan;Pengolahan data',
  'Laboratorium akuntansi;Studi kasus perusahaan;Simulasi laporan;Akses literatur'),
 (9,
  'ub-administrasi-bisnis',
  'Ilmu Administrasi Bisnis',
  'Fakultas Ilmu Administrasi',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk memahami organisasi bisnis, pemasaran, kewirausahaan, administrasi perusahaan, dan strategi layanan.',
  'Administrasi bisnis;Pemasaran;Keuangan bisnis;Kewirausahaan;Perilaku organisasi',
  'Business Development;Marketing Officer;Operations Staff;Entrepreneur',
  'Komunikasi bisnis;Analisis pasar;Manajemen proses;Negosiasi;Perencanaan',
  'Laboratorium bisnis;Studi kasus;Kegiatan kewirausahaan;Diskusi proyek'),
 (9,
  'ub-teknik-informatika',
  'Teknik Informatika',
  'Fakultas Ilmu Komputer',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk mempelajari sistem komputasi, pemrograman, data, perangkat lunak, dan teknologi cerdas.',
  'Pemrograman;Basis data;Jaringan;Rekayasa perangkat lunak;AI',
  'Software Developer;Data Analyst;Backend Developer;System Analyst',
  'Pemrograman;Analisis masalah;Logika komputasi;Kolaborasi;Riset teknis',
  'Laboratorium komputer;Proyek teknologi;Komunitas IT;Kegiatan riset'),
 (9,
  'ub-manajemen',
  'Manajemen',
  'Fakultas Ekonomi dan Bisnis',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk memahami fungsi bisnis, strategi, keuangan, pemasaran, SDM, dan kewirausahaan.',
  'Manajemen dasar;Keuangan;Pemasaran;SDM;Strategi',
  'Management Trainee;Business Analyst;HR Officer;Entrepreneur',
  'Leadership;Analisis bisnis;Komunikasi;Strategi;Problem solving',
  'Laboratorium bisnis;Studi kasus;Komunitas kewirausahaan;Bimbingan akademik'),
 (10,
  'unpad-ilmu-komunikasi',
  'Ilmu Komunikasi',
  'Fakultas Ilmu Komunikasi',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk mempelajari public relations, jurnalistik, komunikasi digital, media, dan riset komunikasi.',
  'Teori komunikasi;Jurnalistik;Public relations;Komunikasi digital;Riset komunikasi',
  'PR Officer;Journalist;Content Strategist;Media Analyst',
  'Menulis;Public speaking;Riset audiens;Produksi media;Strategi pesan',
  'Studio komunikasi;Praktik media;Kegiatan produksi;Diskusi kasus'),
 (10,
  'unpad-psikologi',
  'Psikologi',
  'Fakultas Psikologi',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk memahami perilaku, proses mental, asesmen, perkembangan, organisasi, dan kesehatan mental.',
  'Psikologi umum;Psikometri;Psikologi perkembangan;Psikologi sosial;Metode riset',
  'HR Specialist;Research Assistant;Talent Assessment Officer;Konselor setelah pendidikan lanjut',
  'Observasi;Wawancara;Analisis data;Empati;Etika',
  'Laboratorium psikologi;Ruang observasi;Riset lapangan;Bimbingan akademik'),
 (10,
  'unpad-hukum',
  'Ilmu Hukum',
  'Fakultas Hukum',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk memahami prinsip hukum, kontrak, litigasi, kebijakan publik, dan tata kelola.',
  'Pengantar hukum;Hukum pidana;Hukum perdata;Hukum bisnis;Metode riset hukum',
  'Legal Officer;Compliance Staff;Policy Analyst;Advokat setelah profesi',
  'Argumentasi;Analisis peraturan;Menulis hukum;Negosiasi;Etika',
  'Moot court;Perpustakaan hukum;Klinik hukum;Diskusi kasus'),
 (11,
  'telkom-informatika',
  'Informatika',
  'Fakultas Informatika',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi teknologi untuk pemrograman, data, cloud, AI, keamanan, dan pengembangan produk digital.',
  'Pemrograman;Algoritma;Cloud computing;Data science;Keamanan siber',
  'Software Engineer;Cloud Engineer;AI Engineer;Security Analyst',
  'Pemrograman;Problem solving;Analisis data;Kolaborasi agile;Riset produk',
  'Laboratorium IT;Proyek industri;Komunitas startup;Infrastruktur digital'),
 (11,
  'telkom-sistem-informasi',
  'Sistem Informasi',
  'Fakultas Rekayasa Industri',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi yang menghubungkan sistem digital, proses bisnis, data, manajemen proyek, dan inovasi layanan.',
  'Analisis sistem;Proses bisnis;Basis data;Manajemen proyek;Data analytics',
  'Business Analyst;Product Owner;IT Consultant;Data Analyst',
  'Komunikasi bisnis;Analisis data;Dokumentasi;Agile teamwork;Problem solving',
  'Laboratorium SI;Project-based learning;Studi kasus industri;Ekosistem digital'),
 (11,
  'telkom-dkv',
  'Desain Komunikasi Visual',
  'Fakultas Industri Kreatif',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi desain untuk branding, UI, ilustrasi, animasi, media kreatif, dan komunikasi visual digital.',
  'Dasar desain;Brand identity;Tipografi;Ilustrasi;Desain interaktif',
  'Graphic Designer;UI Designer;Brand Designer;Motion Designer',
  'Kreativitas;Software desain;Riset visual;Storytelling;Portofolio',
  'Studio desain;Workshop kreatif;Galeri karya;Komunitas kreatif'),
 (12,
  'binus-computer-science',
  'Computer Science',
  'School of Computer Science',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi komputer untuk software engineering, AI, data, web, mobile, dan teknologi digital.',
  'Programming;Data structures;Software engineering;AI;Database systems',
  'Software Engineer;Mobile Developer;AI Engineer;Data Analyst',
  'Coding;Computational thinking;Team project;Problem solving;Product thinking',
  'Computer lab;Industry project;Innovation ecosystem;Digital learning'),
 (12,
  'binus-information-systems',
  'Information Systems',
  'School of Information Systems',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk menggabungkan teknologi, bisnis, enterprise system, data, dan transformasi digital.',
  'Business process;Database;Enterprise system;Project management;Data analytics',
  'System Analyst;Business Analyst;IT Consultant;Product Owner',
  'Business analysis;Documentation;Data management;Communication;Agile collaboration',
  'IS lab;Case-based learning;Industry collaboration;Digital platform'),
 (12,
  'binus-vcd',
  'Visual Communication Design',
  'School of Design',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi desain visual untuk branding, media digital, ilustrasi, UI, dan komunikasi kreatif.',
  'Design principles;Typography;Branding;Digital illustration;UI design',
  'Graphic Designer;Brand Designer;UI Designer;Creative Designer',
  'Visual thinking;Design software;Creative research;Composition;Portfolio building',
  'Design studio;Creative lab;Portfolio mentoring;Exhibition activities'),
 (13,
  'gunadarma-sistem-informasi',
  'Sistem Informasi',
  'Fakultas Ilmu Komputer dan Teknologi Informasi',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk mempelajari analisis sistem, basis data, pemrograman, bisnis, dan implementasi sistem informasi.',
  'Basis data;Analisis sistem;Pemrograman;Manajemen proyek;Sistem enterprise',
  'System Analyst;IT Support Analyst;Business Analyst;Database Officer',
  'Analisis kebutuhan;Pemrograman dasar;Dokumentasi;Data handling;Komunikasi',
  'Laboratorium komputer;Kegiatan praktikum;Proyek sistem;Akses materi digital'),
 (13,
  'gunadarma-teknik-informatika',
  'Teknik Informatika',
  'Fakultas Teknologi Industri',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk mengembangkan kemampuan pemrograman, jaringan, perangkat lunak, database, dan teknologi komputasi.',
  'Algoritma;Pemrograman;Basis data;Jaringan komputer;Rekayasa perangkat lunak',
  'Programmer;Software Developer;Network Support;System Analyst',
  'Coding;Problem solving;Analisis sistem;Kerja tim;Ketelitian',
  'Laboratorium komputer;Praktikum jaringan;Proyek aplikasi;Kegiatan IT'),
 (13,
  'gunadarma-psikologi',
  'Psikologi',
  'Fakultas Psikologi',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk mempelajari perilaku, perkembangan, psikometri, industri organisasi, dan riset psikologi.',
  'Psikologi umum;Psikometri;Perkembangan;Sosial;Industri organisasi',
  'HR Staff;Talent Assessment;Research Assistant;Konselor setelah studi lanjut',
  'Observasi;Wawancara;Empati;Analisis data;Etika',
  'Laboratorium psikologi;Ruang observasi;Kegiatan riset;Diskusi kasus'),
 (14,
  'atma-psikologi',
  'Psikologi',
  'Fakultas Psikologi',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk memahami perilaku manusia, asesmen, perkembangan, kesehatan mental, dan psikologi organisasi.',
  'Psikologi dasar;Psikometri;Konseling dasar;Psikologi industri;Metode riset',
  'HR Specialist;Research Assistant;Talent Officer;Konselor setelah pendidikan lanjut',
  'Empati;Observasi;Analisis data;Komunikasi;Etika',
  'Laboratorium psikologi;Kegiatan riset;Diskusi kasus;Bimbingan akademik'),
 (14,
  'atma-teknik-industri',
  'Teknik Industri',
  'Fakultas Teknik',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk merancang sistem produksi, layanan, optimasi proses, ergonomi, dan rantai pasok.',
  'Riset operasi;Ergonomi;Manajemen produksi;Statistika;Supply chain',
  'Industrial Engineer;Process Analyst;Production Planner;Supply Chain Officer',
  'Optimasi;Analisis proses;Manajemen proyek;Komunikasi;Data analysis',
  'Laboratorium teknik industri;Simulasi sistem;Proyek industri;Studi kasus'),
 (14,
  'atma-akuntansi',
  'Akuntansi',
  'Fakultas Ekonomi dan Bisnis',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk memahami akuntansi, audit, perpajakan, pelaporan keuangan, dan tata kelola bisnis.',
  'Akuntansi keuangan;Audit;Pajak;Akuntansi manajemen;SIA',
  'Auditor;Accountant;Tax Officer;Financial Staff',
  'Ketelitian;Analisis angka;Etika;Pelaporan;Komunikasi bisnis',
  'Laboratorium bisnis;Studi kasus keuangan;Diskusi profesional;Akses literatur'),
 (15,
  'trisakti-arsitektur',
  'Arsitektur',
  'Fakultas Teknik Sipil dan Perencanaan',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk merancang bangunan, ruang, lingkungan, konsep desain, dan gambar teknis arsitektur.',
  'Studio desain;Struktur bangunan;Sejarah arsitektur;Perancangan kota;Teknologi bangunan',
  'Architect setelah profesi;Interior Designer;Urban Design Assistant;Drafter',
  'Sketsa;Perancangan ruang;Software desain;Kreativitas;Presentasi visual',
  'Studio arsitektur;Workshop maket;Ruang presentasi;Praktik desain'),
 (15,
  'trisakti-teknik-perminyakan',
  'Teknik Perminyakan',
  'Fakultas Teknologi Kebumian dan Energi',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi untuk memahami eksplorasi, produksi, reservoir, pengeboran, dan pengelolaan energi migas.',
  'Geologi dasar;Reservoir;Pengeboran;Produksi migas;Manajemen energi',
  'Petroleum Engineer;Drilling Engineer;Reservoir Analyst;Energy Analyst',
  'Analisis data teknis;Matematika teknik;Keselamatan kerja;Problem solving;Kerja lapangan',
  'Laboratorium kebumian;Simulasi reservoir;Praktik lapangan;Kegiatan industri'),
 (15,
  'trisakti-manajemen',
  'Manajemen',
  'Fakultas Ekonomi dan Bisnis',
  'S1',
  'Perlu verifikasi BAN-PT/LAM',
  'Reguler',
  '8 Semester',
  'Cek laman resmi kampus untuk biaya terbaru',
  'Program studi bisnis untuk memahami pemasaran, keuangan, SDM, operasi, strategi, dan kewirausahaan.',
  'Manajemen dasar;Pemasaran;Keuangan;SDM;Kewirausahaan',
  'Management Trainee;Marketing Officer;Business Analyst;Entrepreneur',
  'Leadership;Komunikasi;Analisis bisnis;Strategi;Negosiasi',
  'Laboratorium bisnis;Studi kasus;Kegiatan wirausaha;Bimbingan akademik')]

            cursor.executemany(
                """
                INSERT INTO study_programs (
                    campus_id, slug, program_name, faculty, degree, accreditation,
                    learning_mode, duration, tuition_range, summary, curriculum_points,
                    career_paths, skills, facilities
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    campus_id = VALUES(campus_id),
                    program_name = VALUES(program_name),
                    faculty = VALUES(faculty),
                    degree = VALUES(degree),
                    accreditation = VALUES(accreditation),
                    learning_mode = VALUES(learning_mode),
                    duration = VALUES(duration),
                    tuition_range = VALUES(tuition_range),
                    summary = VALUES(summary),
                    curriculum_points = VALUES(curriculum_points),
                    career_paths = VALUES(career_paths),
                    skills = VALUES(skills),
                    facilities = VALUES(facilities),
                    is_active = 1,
                    updated_at = CURRENT_TIMESTAMP
                """,
                seed_programs,
            )

        database.commit_db()


    def normalize_program_row(row: dict[str, Any]) -> dict[str, Any]:
        """
        Menyiapkan data program studi agar mudah ditampilkan template.
        """

        program = dict(row)
        program["curriculum_points"] = split_semicolon_text(program.get("curriculum_points"))
        program["career_paths"] = split_semicolon_text(program.get("career_paths"))
        program["skills"] = split_semicolon_text(program.get("skills"))
        program["facilities"] = split_semicolon_text(program.get("facilities"))
        return program


    def load_program_directory(limit: int = 36) -> list[dict[str, Any]]:
        """
        Mengambil daftar program studi untuk direktori Babak 5B.

        Direktori ini belum menjadi modul search penuh.
        Tujuannya agar halaman campus-detail terasa realistis saat demo
        karena calon mahasiswa dapat melihat beberapa pilihan kampus dan prodi.
        """

        with database.get_cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT
                    sp.slug,
                    sp.program_name,
                    sp.faculty,
                    sp.degree,
                    sp.accreditation,
                    c.campus_name,
                    c.city AS campus_city,
                    c.campus_type
                FROM study_programs sp
                INNER JOIN campuses c
                    ON c.id = sp.campus_id
                WHERE sp.is_active = 1
                ORDER BY c.campus_name ASC, sp.program_name ASC
                LIMIT %s
                """,
                (limit,),
            )

            return cursor.fetchall() or []


    def load_directory_stats() -> dict[str, int]:
        """
        Menghitung statistik ringkas data kampus Babak 5B.
        """

        stats = {
            "campus_count": 0,
            "program_count": 0,
        }

        with database.get_cursor(dictionary=True) as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM campuses")
            campus_row = cursor.fetchone() or {}

            cursor.execute("SELECT COUNT(*) AS total FROM study_programs WHERE is_active = 1")
            program_row = cursor.fetchone() or {}

        stats["campus_count"] = int(campus_row.get("total") or 0)
        stats["program_count"] = int(program_row.get("total") or 0)
        return stats


    def build_fallback_campus_context() -> dict[str, Any]:
        """
        Fallback agar halaman detail tetap tampil jika database belum siap.
        """

        related_programs = [
            {"program_name": "Sistem Informasi", "slug": "sistem-informasi", "faculty": "Fakultas Ilmu Komputer", "degree": "S1"},
            {"program_name": "Manajemen", "slug": "manajemen", "faculty": "Fakultas Ekonomi dan Bisnis", "degree": "S1"},
            {"program_name": "Desain Komunikasi Visual", "slug": "desain-komunikasi-visual", "faculty": "Fakultas Desain dan Industri Kreatif", "degree": "S1"},
        ]

        return {
            "program": dict(FALLBACK_CAMPUS_DATA),
            "related_programs": related_programs,
            "directory_programs": related_programs,
            "directory_stats": {
                "campus_count": 1,
                "program_count": len(related_programs) + 1,
            },
            "campus_error": None,
        }


    def load_campus_detail_context(program_slug: str | None = None) -> dict[str, Any]:
        """
        Mengambil data detail program studi dari database Babak 5.
        """

        safe_slug = (program_slug or DEFAULT_PROGRAM_SLUG).strip().lower()

        try:
            ensure_campus_tables()

            with database.get_cursor(dictionary=True) as cursor:
                cursor.execute(
                    """
                    SELECT
                        sp.id,
                        sp.slug AS program_slug,
                        sp.program_name,
                        sp.faculty,
                        sp.degree,
                        sp.accreditation,
                        sp.learning_mode,
                        sp.duration,
                        sp.tuition_range,
                        sp.summary,
                        sp.curriculum_points,
                        sp.career_paths,
                        sp.skills,
                        sp.facilities,
                        c.slug AS campus_slug,
                        c.campus_name,
                        c.city AS campus_city,
                        c.address AS campus_address,
                        c.website AS campus_website,
                        c.campus_type,
                        c.description AS campus_description
                    FROM study_programs sp
                    INNER JOIN campuses c ON c.id = sp.campus_id
                    WHERE sp.slug = %s AND sp.is_active = 1
                    LIMIT 1
                    """,
                    (safe_slug,),
                )
                row = cursor.fetchone()

                if row is None and safe_slug != DEFAULT_PROGRAM_SLUG:
                    cursor.execute(
                        """
                        SELECT
                            sp.id,
                            sp.slug AS program_slug,
                            sp.program_name,
                            sp.faculty,
                            sp.degree,
                            sp.accreditation,
                            sp.learning_mode,
                            sp.duration,
                            sp.tuition_range,
                            sp.summary,
                            sp.curriculum_points,
                            sp.career_paths,
                            sp.skills,
                            sp.facilities,
                            c.slug AS campus_slug,
                            c.campus_name,
                            c.city AS campus_city,
                            c.address AS campus_address,
                            c.website AS campus_website,
                            c.campus_type,
                            c.description AS campus_description
                        FROM study_programs sp
                        INNER JOIN campuses c ON c.id = sp.campus_id
                        WHERE sp.slug = %s AND sp.is_active = 1
                        LIMIT 1
                        """,
                        (DEFAULT_PROGRAM_SLUG,),
                    )
                    row = cursor.fetchone()

                if row is None:
                    return build_fallback_campus_context()

                program = normalize_program_row(row)

                cursor.execute(
                    """
                    SELECT slug, program_name, faculty, degree
                    FROM study_programs
                    WHERE is_active = 1 AND slug != %s
                    ORDER BY CASE WHEN faculty = %s THEN 0 ELSE 1 END, program_name ASC
                    LIMIT 4
                    """,
                    (program["program_slug"], program["faculty"]),
                )
                related_programs = cursor.fetchall() or []

            return {
                "program": program,
                "related_programs": related_programs,
                "directory_programs": load_program_directory(),
                "directory_stats": load_directory_stats(),
                "campus_error": None,
            }

        except (Error, RuntimeError):
            database.rollback_db()
            app.logger.exception("Data campus-detail gagal dimuat.")
            context = build_fallback_campus_context()
            context["campus_error"] = (
                "Database program studi belum siap. Halaman menampilkan data contoh."
            )
            return context


    def enrich_ticket_message_row(message_row: dict[str, Any]) -> dict[str, Any]:
        """
        Menyiapkan data pesan tiket agar mudah ditampilkan di ticket.html.

        Pesan bisa berasal dari user atau admin.
        Student membaca balasan admin melalui detail tiket di /ticket/<id>.
        """

        message = dict(message_row)
        created_at = message.get("created_at")

        if hasattr(created_at, "strftime"):
            message["created_label"] = created_at.strftime("%d/%m/%Y %H:%M")
        else:
            message["created_label"] = str(created_at or "-")

        sender_type = str(message.get("sender_type") or "user")
        message["sender_type"] = sender_type
        message["sender_label"] = (
            "Admin ComCam"
            if sender_type == "admin"
            else "Kamu"
        )

        return message


    def load_user_ticket_detail(ticket_id: int) -> dict[str, Any]:
        """
        Mengambil satu tiket milik user beserta seluruh percakapannya.

        Fungsi ini menjawab kebutuhan realistis Babak 4:
        setelah admin membalas atau menyelesaikan tiket, student bisa melihat
        balasan tersebut di halaman detail tiket.
        """

        detail_context = {
            "selected_ticket": None,
            "ticket_messages": [],
        }

        if not current_user.is_authenticated:
            return detail_context

        ensure_help_desk_tables()
        user_id = int(current_user.id)

        with database.get_cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT
                    t.id,
                    t.ticket_code,
                    t.category,
                    t.subject,
                    t.message,
                    t.priority,
                    t.status,
                    t.created_at,
                    t.updated_at,
                    COUNT(tm.id) AS message_count,
                    COALESCE(SUM(tm.sender_type = 'admin'), 0) AS admin_reply_count,
                    MAX(CASE WHEN tm.sender_type = 'admin' THEN tm.created_at END) AS last_admin_reply_at
                FROM help_tickets t
                LEFT JOIN ticket_messages tm
                    ON tm.ticket_id = t.id
                WHERE t.id = %s
                  AND t.user_id = %s
                GROUP BY
                    t.id,
                    t.ticket_code,
                    t.category,
                    t.subject,
                    t.message,
                    t.priority,
                    t.status,
                    t.created_at,
                    t.updated_at
                LIMIT 1
                """,
                (
                    ticket_id,
                    user_id,
                ),
            )

            ticket_row = cursor.fetchone()

            if not ticket_row:
                return detail_context

            cursor.execute(
                """
                SELECT
                    tm.id,
                    tm.sender_id,
                    tm.sender_type,
                    tm.message,
                    tm.created_at,
                    u.full_name AS sender_name,
                    u.email AS sender_email
                FROM ticket_messages tm
                LEFT JOIN users u
                    ON u.id = tm.sender_id
                WHERE tm.ticket_id = %s
                ORDER BY tm.created_at ASC, tm.id ASC
                """,
                (ticket_id,),
            )

            message_rows = cursor.fetchall() or []

        detail_context["selected_ticket"] = enrich_ticket_row(ticket_row)
        detail_context["ticket_messages"] = [
            enrich_ticket_message_row(row)
            for row in message_rows
        ]

        return detail_context


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
    # 4.4. HELPER MODUL ADMIN HELP DESK
    # =====================================================

    def is_current_user_admin() -> bool:
        """
        Memeriksa apakah pengguna yang sedang login memiliki role admin.

        Role berasal dari kolom users.role di database.
        Untuk membuat akun admin saat development, ubah role user
        dari phpMyAdmin: student menjadi admin.
        """

        return (
            current_user.is_authenticated
            and str(getattr(current_user, "role", "")) == "admin"
        )


    def require_admin_access():
        """
        Menjaga halaman admin agar hanya bisa dibuka oleh admin.

        Jika user biasa mencoba masuk, sistem mengembalikan user
        ke homepage dan menampilkan pesan sopan.
        """

        if is_current_user_admin():
            return None

        flash(
            "Halaman admin hanya dapat diakses oleh akun admin.",
            "error",
        )

        return redirect(
            url_for("index")
        )


    def get_admin_ticket_summary() -> dict[str, int]:
        """
        Mengambil ringkasan seluruh tiket untuk kartu statistik admin.
        """

        with database.get_cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    COALESCE(SUM(status = 'dikirim'), 0) AS submitted,
                    COALESCE(SUM(status = 'diproses'), 0) AS in_progress,
                    COALESCE(SUM(status = 'selesai'), 0) AS closed,
                    COALESCE(SUM(priority = 'high' AND status != 'selesai'), 0) AS high_priority_open
                FROM help_tickets
                """
            )

            summary = cursor.fetchone() or {}

        return {
            "total": int(summary.get("total") or 0),
            "submitted": int(summary.get("submitted") or 0),
            "in_progress": int(summary.get("in_progress") or 0),
            "closed": int(summary.get("closed") or 0),
            "high_priority_open": int(summary.get("high_priority_open") or 0),
        }


    def enrich_admin_ticket_row(ticket_row: dict[str, Any]) -> dict[str, Any]:
        """
        Menyiapkan data tiket agar mudah ditampilkan di admin.html.
        """

        ticket = enrich_ticket_row(ticket_row)

        updated_at = ticket.get("updated_at")
        if hasattr(updated_at, "strftime"):
            ticket["updated_label"] = updated_at.strftime("%d/%m/%Y %H:%M")
        else:
            ticket["updated_label"] = str(updated_at or "-")

        ticket["user_name"] = ticket.get("user_name") or "Pengguna"
        ticket["user_email"] = ticket.get("user_email") or "-"
        ticket["message_count"] = int(ticket.get("message_count") or 0)

        return ticket


    def load_admin_ticket_context() -> dict[str, Any]:
        """
        Mengambil data tiket untuk Panel Admin.

        Admin dapat memfilter tiket berdasarkan status, kategori,
        prioritas, dan kata kunci pencarian.
        """

        ensure_help_desk_tables()

        selected_status = request.args.get("status", "all").strip()
        selected_category = request.args.get("category", "all").strip()
        selected_priority = request.args.get("priority", "all").strip()
        search_query = request.args.get("q", "").strip()

        allowed_status = {"all", "dikirim", "diproses", "selesai"}
        allowed_categories = {"all"} | {item[0] for item in TICKET_CATEGORY_OPTIONS}
        allowed_priorities = {"all"} | {item[0] for item in TICKET_PRIORITY_OPTIONS}

        if selected_status not in allowed_status:
            selected_status = "all"

        if selected_category not in allowed_categories:
            selected_category = "all"

        if selected_priority not in allowed_priorities:
            selected_priority = "all"

        where_clauses: list[str] = []
        params: list[Any] = []

        if selected_status != "all":
            where_clauses.append("t.status = %s")
            params.append(selected_status)

        if selected_category != "all":
            where_clauses.append("t.category = %s")
            params.append(selected_category)

        if selected_priority != "all":
            where_clauses.append("t.priority = %s")
            params.append(selected_priority)

        if search_query:
            where_clauses.append(
                """
                (
                    t.ticket_code LIKE %s
                    OR t.subject LIKE %s
                    OR t.message LIKE %s
                    OR u.full_name LIKE %s
                    OR u.email LIKE %s
                )
                """
            )
            keyword = f"%{search_query}%"
            params.extend([keyword, keyword, keyword, keyword, keyword])

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        with database.get_cursor(dictionary=True) as cursor:
            cursor.execute(
                f"""
                SELECT
                    t.id,
                    t.ticket_code,
                    t.category,
                    t.subject,
                    t.message,
                    t.priority,
                    t.status,
                    t.created_at,
                    t.updated_at,
                    t.closed_at,
                    u.full_name AS user_name,
                    u.email AS user_email,
                    COUNT(tm.id) AS message_count
                FROM help_tickets t
                INNER JOIN users u
                    ON u.id = t.user_id
                LEFT JOIN ticket_messages tm
                    ON tm.ticket_id = t.id
                {where_sql}
                GROUP BY
                    t.id,
                    t.ticket_code,
                    t.category,
                    t.subject,
                    t.message,
                    t.priority,
                    t.status,
                    t.created_at,
                    t.updated_at,
                    t.closed_at,
                    u.full_name,
                    u.email
                ORDER BY
                    FIELD(t.status, 'dikirim', 'diproses', 'selesai'),
                    FIELD(t.priority, 'high', 'normal', 'low'),
                    t.updated_at DESC
                LIMIT 50
                """,
                tuple(params),
            )

            rows = cursor.fetchall() or []

        return {
            "admin_summary": get_admin_ticket_summary(),
            "admin_tickets": [
                enrich_admin_ticket_row(row)
                for row in rows
            ],
            "ticket_category_options": TICKET_CATEGORY_OPTIONS,
            "ticket_priority_options": TICKET_PRIORITY_OPTIONS,
            "ticket_status_labels": TICKET_STATUS_LABELS,
            "selected_status": selected_status,
            "selected_category": selected_category,
            "selected_priority": selected_priority,
            "search_query": search_query,
        }


    def validate_admin_reply_form(form_data: Any) -> tuple[str, list[str]]:
        """
        Validasi pesan balasan admin sebelum disimpan ke ticket_messages.
        """

        reply_message = str(form_data.get("reply_message", "")).strip()
        errors: list[str] = []

        if len(reply_message) < 5:
            errors.append("Balasan admin minimal 5 karakter.")

        if len(reply_message) > 2000:
            errors.append("Balasan admin maksimal 2000 karakter.")

        return reply_message, errors


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
        Route pencarian sederhana untuk Babak 5B.

        Jika kata kunci cocok dengan program studi atau nama kampus
        pada database seed realistis, user langsung diarahkan ke halaman
        campus-detail program pertama yang paling relevan.

        Search penuh dengan halaman hasil terpisah akan dibuat pada babak
        lanjutan setelah modul data kampus benar-benar final.
        """

        search_query = request.args.get("q", "").strip()
        search_focus = request.args.get("focus", "").strip()
        normalized_query = search_query.lower()

        program_keyword_map = {
            "teknik informatika": "teknik-informatika",
            "informatika": "teknik-informatika",
            "sistem informasi": "sistem-informasi",
            "manajemen": "manajemen",
            "desain komunikasi visual": "desain-komunikasi-visual",
            "dkv": "desain-komunikasi-visual",
            "ilmu komunikasi": "ilmu-komunikasi",
            "akuntansi": "akuntansi",
        }

        matched_slug = program_keyword_map.get(normalized_query)

        if matched_slug:
            return redirect(
                url_for(
                    "campus_detail_slug",
                    program_slug=matched_slug,
                )
            )

        if search_query:
            try:
                ensure_campus_tables()

                like_query = f"%{search_query}%"

                with database.get_cursor(dictionary=True) as cursor:
                    cursor.execute(
                        """
                        SELECT sp.slug
                        FROM study_programs sp
                        INNER JOIN campuses c
                            ON c.id = sp.campus_id
                        WHERE sp.is_active = 1
                          AND (
                              LOWER(sp.program_name) LIKE LOWER(%s)
                              OR LOWER(sp.faculty) LIKE LOWER(%s)
                              OR LOWER(c.campus_name) LIKE LOWER(%s)
                              OR LOWER(c.city) LIKE LOWER(%s)
                          )
                        ORDER BY
                            CASE
                                WHEN LOWER(sp.program_name) = LOWER(%s) THEN 0
                                WHEN LOWER(c.campus_name) = LOWER(%s) THEN 1
                                ELSE 2
                            END,
                            c.campus_name ASC,
                            sp.program_name ASC
                        LIMIT 1
                        """,
                        (
                            like_query,
                            like_query,
                            like_query,
                            like_query,
                            search_query,
                            search_query,
                        ),
                    )

                    row = cursor.fetchone()

                if row:
                    return redirect(
                        url_for(
                            "campus_detail_slug",
                            program_slug=row["slug"],
                        )
                    )

            except (Error, RuntimeError):
                database.rollback_db()
                app.logger.exception("Pencarian data kampus gagal.")

        search_notice = None

        if search_query:
            search_notice = (
                f"Kami belum menemukan hasil yang cocok untuk '{search_query}' karena data masih belum lengkap. "
                "Silakan coba kata kunci lain seperti nama kampus ternama, nama program studi terminat, "
                "atau bidang keilmuan yang ingin kamu cari tapi yang peminatnya banyak."
            )

            # Menjaga posisi pengguna tetap berada di bagian Program Studi
            # setelah pencarian tidak ditemukan. Tanpa ini, browser akan
            # memuat ulang halaman dari paling atas.
            if search_focus != "program-studi":
                return redirect(
                    url_for(
                        "search",
                        q=search_query,
                        focus="program-studi",
                    ) + "#program-studi"
                )

        return render_template(
            "index.html",
            **build_index_context(
                search_query=search_query,
                search_notice=search_notice,
                search_focus=search_focus,
            ),
        )
    
    @app.get("/pencarian")
    def pencarian_legacy():
        """
        Alias sementara agar link lama /pencarian tetap berjalan.
        Route utama pencarian sekarang memakai /search.
        """

        return search()


    # =====================================================
    # 5.9. HELPER BABAK 6 - PEMETAAN MINAT DAN REKOMENDASI
    # =====================================================

    RECOMMENDATION_OPTIONS = {
        "preferred_field": [
            ("teknologi", "Teknologi dan komputer"),
            ("bisnis", "Bisnis dan manajemen"),
            ("kesehatan", "Kesehatan"),
            ("teknik", "Teknik dan rekayasa"),
            ("sosial", "Sosial dan komunikasi"),
            ("desain", "Desain dan seni"),
        ],
        "favorite_subject": [
            ("matematika", "Matematika atau logika"),
            ("ekonomi", "Ekonomi atau kewirausahaan"),
            ("biologi", "Biologi atau kesehatan"),
            ("fisika", "Fisika atau teknologi"),
            ("sosial", "Sosiologi atau komunikasi"),
            ("seni", "Seni atau desain"),
        ],
        "preferred_activity": [
            ("membangun_sistem", "Membangun aplikasi atau sistem"),
            ("menganalisis_data", "Menganalisis data dan masalah"),
            ("mengelola_bisnis", "Mengelola bisnis atau organisasi"),
            ("membantu_orang", "Membantu dan melayani orang"),
            ("mendesain_visual", "Membuat desain visual"),
            ("berkomunikasi", "Berkomunikasi dan presentasi"),
        ],
        "learning_style": [
            ("praktik", "Belajar lewat praktik langsung"),
            ("analitis", "Belajar lewat analisis dan riset"),
            ("kolaboratif", "Belajar lewat diskusi tim"),
            ("kreatif", "Belajar lewat eksplorasi ide"),
        ],
        "career_goal": [
            ("software", "Karier digital atau software"),
            ("business", "Karier bisnis atau manajemen"),
            ("healthcare", "Karier kesehatan"),
            ("engineer", "Karier teknik atau industri"),
            ("communication", "Karier komunikasi atau layanan publik"),
            ("creative", "Karier kreatif"),
        ],
    }

    CATEGORY_LABELS = {
        "teknologi": "Teknologi dan Komputer",
        "bisnis": "Bisnis dan Manajemen",
        "kesehatan": "Kesehatan",
        "teknik": "Teknik dan Rekayasa",
        "sosial": "Sosial dan Komunikasi",
        "desain": "Desain dan Seni",
    }

    def ensure_recommendation_tables() -> None:
        """
        Membuat tabel Babak 6 untuk menyimpan hasil pemetaan minat.

        Tabel dibuat terpisah dari data kampus agar alur aplikasi rapi:
        - user_interest_profiles menyimpan jawaban pengguna.
        - user_recommendation_results menyimpan daftar rekomendasi hasil kalkulasi.
        """

        with database.get_cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_interest_profiles (
                    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                    user_id INT UNSIGNED NOT NULL,
                    preferred_field VARCHAR(50) NOT NULL,
                    favorite_subject VARCHAR(50) NOT NULL,
                    preferred_activity VARCHAR(50) NOT NULL,
                    learning_style VARCHAR(50) NOT NULL,
                    career_goal VARCHAR(50) NOT NULL,
                    notes TEXT DEFAULT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    KEY idx_interest_user (user_id),
                    CONSTRAINT fk_interest_user
                        FOREIGN KEY (user_id) REFERENCES users(id)
                        ON DELETE CASCADE
                ) ENGINE=InnoDB
                  DEFAULT CHARACTER SET utf8mb4
                  COLLATE utf8mb4_unicode_ci
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_recommendation_results (
                    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                    profile_id BIGINT UNSIGNED NOT NULL,
                    user_id INT UNSIGNED NOT NULL,
                    rank_order TINYINT UNSIGNED NOT NULL,
                    program_slug VARCHAR(120) NOT NULL,
                    program_name VARCHAR(160) NOT NULL,
                    campus_name VARCHAR(160) NOT NULL,
                    campus_city VARCHAR(100) DEFAULT NULL,
                    score TINYINT UNSIGNED NOT NULL DEFAULT 0,
                    reason TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    KEY idx_recommendation_user (user_id),
                    KEY idx_recommendation_profile (profile_id),
                    CONSTRAINT fk_recommendation_profile
                        FOREIGN KEY (profile_id) REFERENCES user_interest_profiles(id)
                        ON DELETE CASCADE,
                    CONSTRAINT fk_recommendation_user
                        FOREIGN KEY (user_id) REFERENCES users(id)
                        ON DELETE CASCADE
                ) ENGINE=InnoDB
                  DEFAULT CHARACTER SET utf8mb4
                  COLLATE utf8mb4_unicode_ci
                """
            )

        database.commit_db()


    def option_values(option_name: str) -> set[str]:
        """Mengambil nilai valid dari daftar pilihan form rekomendasi."""

        return {
            value
            for value, _label in RECOMMENDATION_OPTIONS.get(option_name, [])
        }


    def validate_recommendation_form(form_data: Any) -> tuple[dict[str, str], list[str]]:
        """
        Membersihkan dan memvalidasi jawaban pemetaan minat.

        Validasi dibuat eksplisit agar user tidak bisa mengirim nilai bebas
        yang tidak tersedia di pilihan antarmuka.
        """

        fields = [
            "preferred_field",
            "favorite_subject",
            "preferred_activity",
            "learning_style",
            "career_goal",
        ]

        cleaned: dict[str, str] = {}
        errors: list[str] = []

        for field in fields:
            value = str(form_data.get(field, "")).strip()
            cleaned[field] = value

            if not value:
                errors.append("Lengkapi seluruh pilihan pemetaan minat terlebih dahulu.")
                continue

            if value not in option_values(field):
                errors.append("Terdapat pilihan yang tidak valid. Silakan ulangi pemetaan minat.")

        notes = str(form_data.get("notes", "")).strip()
        cleaned["notes"] = notes[:500]

        # Hapus duplikasi pesan agar tampilan tetap rapi.
        return cleaned, list(dict.fromkeys(errors))


    def get_program_category(program_row: dict[str, Any]) -> str:
        """
        Mengelompokkan program studi berdasarkan teks nama, fakultas, dan ringkasan.

        Fungsi ini dipakai untuk seed demo. Pada versi final, kategori idealnya
        disimpan langsung di database agar lebih presisi.
        """

        text = " ".join(
            [
                str(program_row.get("program_name", "")),
                str(program_row.get("faculty", "")),
                str(program_row.get("summary", "")),
            ]
        ).lower()

        if any(keyword in text for keyword in ["informatika", "komputer", "sistem informasi", "data", "ai", "cyber"]):
            return "teknologi"
        if any(keyword in text for keyword in ["manajemen", "bisnis", "akuntansi", "ekonomi", "administrasi"]):
            return "bisnis"
        if any(keyword in text for keyword in ["kedokteran", "farmasi", "keperawatan", "gizi", "kesehatan", "psikologi"]):
            return "kesehatan"
        if any(keyword in text for keyword in ["teknik", "sipil", "industri", "mesin", "elektro", "arsitektur"]):
            return "teknik"
        if any(keyword in text for keyword in ["komunikasi", "hukum", "hubungan", "publik", "sosial", "pendidikan"]):
            return "sosial"
        if any(keyword in text for keyword in ["desain", "visual", "seni", "kreatif", "dkv"]):
            return "desain"

        return "teknologi"


    def load_recommendation_program_pool() -> list[dict[str, Any]]:
        """
        Mengambil program studi dari tabel Babak 5B.

        Jika database kampus belum siap, fungsi tetap mengembalikan fallback
        agar halaman rekomendasi tidak blank saat demo.
        """

        fallback_programs = [
            {
                "program_slug": "teknik-informatika",
                "program_name": "Teknik Informatika",
                "faculty": "Fakultas Ilmu Komputer",
                "campus_name": "Universitas Esa Unggul",
                "campus_city": "Bekasi",
                "summary": "Program untuk pemrograman, data, dan pengembangan sistem digital.",
            },
            {
                "program_slug": "sistem-informasi",
                "program_name": "Sistem Informasi",
                "faculty": "Fakultas Ilmu Komputer",
                "campus_name": "Universitas Esa Unggul",
                "campus_city": "Bekasi",
                "summary": "Program untuk sistem bisnis, analisis proses, dan teknologi informasi.",
            },
            {
                "program_slug": "manajemen",
                "program_name": "Manajemen",
                "faculty": "Fakultas Ekonomi dan Bisnis",
                "campus_name": "Universitas Esa Unggul",
                "campus_city": "Bekasi",
                "summary": "Program untuk manajemen organisasi, bisnis, pemasaran, dan kewirausahaan.",
            },
        ]

        try:
            ensure_campus_tables()

            with database.get_cursor(dictionary=True) as cursor:
                cursor.execute(
                    """
                    SELECT
                        sp.slug AS program_slug,
                        sp.program_name,
                        sp.faculty,
                        sp.summary,
                        c.campus_name,
                        c.city AS campus_city
                    FROM study_programs sp
                    INNER JOIN campuses c ON c.id = sp.campus_id
                    WHERE sp.is_active = 1
                    ORDER BY c.campus_name ASC, sp.program_name ASC
                    LIMIT 120
                    """
                )
                rows = cursor.fetchall()

            return [dict(row) for row in rows] or fallback_programs

        except (Error, RuntimeError):
            app.logger.exception("Data program untuk rekomendasi gagal dimuat.")
            return fallback_programs


    def calculate_interest_scores(cleaned_data: dict[str, str]) -> dict[str, int]:
        """
        Menghitung skor kategori berdasarkan pilihan user.

        Pendekatan ini sengaja rule-based agar mudah dijelaskan saat presentasi IMK.
        Setiap jawaban menambah skor ke bidang yang relevan.
        """

        scores = {
            "teknologi": 0,
            "bisnis": 0,
            "kesehatan": 0,
            "teknik": 0,
            "sosial": 0,
            "desain": 0,
        }

        direct_field = cleaned_data.get("preferred_field", "")
        if direct_field in scores:
            scores[direct_field] += 35

        subject_map = {
            "matematika": {"teknologi": 18, "teknik": 14, "bisnis": 8},
            "ekonomi": {"bisnis": 22, "sosial": 8},
            "biologi": {"kesehatan": 24, "sosial": 6},
            "fisika": {"teknik": 22, "teknologi": 10},
            "sosial": {"sosial": 22, "bisnis": 8},
            "seni": {"desain": 24, "sosial": 6},
        }

        activity_map = {
            "membangun_sistem": {"teknologi": 24, "teknik": 8},
            "menganalisis_data": {"teknologi": 18, "bisnis": 10},
            "mengelola_bisnis": {"bisnis": 24, "sosial": 6},
            "membantu_orang": {"kesehatan": 18, "sosial": 12},
            "mendesain_visual": {"desain": 24, "teknologi": 6},
            "berkomunikasi": {"sosial": 22, "bisnis": 6},
        }

        learning_map = {
            "praktik": {"teknik": 10, "kesehatan": 8, "teknologi": 8},
            "analitis": {"teknologi": 12, "bisnis": 8, "teknik": 8},
            "kolaboratif": {"sosial": 10, "bisnis": 8, "kesehatan": 6},
            "kreatif": {"desain": 12, "sosial": 8, "teknologi": 4},
        }

        career_map = {
            "software": {"teknologi": 25},
            "business": {"bisnis": 25},
            "healthcare": {"kesehatan": 25},
            "engineer": {"teknik": 25},
            "communication": {"sosial": 25},
            "creative": {"desain": 25},
        }

        for mapping, selected in [
            (subject_map, cleaned_data.get("favorite_subject")),
            (activity_map, cleaned_data.get("preferred_activity")),
            (learning_map, cleaned_data.get("learning_style")),
            (career_map, cleaned_data.get("career_goal")),
        ]:
            for category, point in mapping.get(selected, {}).items():
                scores[category] += point

        return scores


    def build_recommendation_results(cleaned_data: dict[str, str]) -> tuple[list[dict[str, Any]], dict[str, int]]:
        """
        Membuat daftar rekomendasi program studi dari skor kategori.
        """

        scores = calculate_interest_scores(cleaned_data)
        program_pool = load_recommendation_program_pool()
        ranked_results: list[dict[str, Any]] = []

        for program in program_pool:
            category = get_program_category(program)
            base_score = scores.get(category, 0)

            # Program dari bidang pilihan utama mendapat bonus kecil.
            if category == cleaned_data.get("preferred_field"):
                base_score += 8

            # Pastikan score tetap enak dibaca untuk user.
            final_score = max(55, min(98, base_score + 35))

            reason = (
                f"Cocok karena pilihan minatmu mengarah ke bidang "
                f"{CATEGORY_LABELS.get(category, category)}. Program ini relevan dengan "
                f"aktivitas belajar dan tujuan karier yang kamu pilih."
            )

            ranked_results.append(
                {
                    "program_slug": program.get("program_slug", "teknik-informatika"),
                    "program_name": program.get("program_name", "Teknik Informatika"),
                    "faculty": program.get("faculty", "Fakultas"),
                    "campus_name": program.get("campus_name", "Compass Campus"),
                    "campus_city": program.get("campus_city", "Indonesia"),
                    "category": category,
                    "category_label": CATEGORY_LABELS.get(category, category),
                    "score": final_score,
                    "reason": reason,
                }
            )

        ranked_results.sort(
            key=lambda item: (
                item["score"],
                item["program_name"],
            ),
            reverse=True,
        )

        # Ambil 5 hasil teratas agar tidak membuat user lelah membaca.
        top_results = ranked_results[:5]

        for index, result in enumerate(top_results, start=1):
            result["rank_order"] = index

        return top_results, scores


    def save_recommendation_result(cleaned_data: dict[str, str], results: list[dict[str, Any]]) -> int:
        """
        Menyimpan profil minat dan hasil rekomendasi user ke database.
        """

        ensure_recommendation_tables()

        with database.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_interest_profiles (
                    user_id,
                    preferred_field,
                    favorite_subject,
                    preferred_activity,
                    learning_style,
                    career_goal,
                    notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    int(current_user.id),
                    cleaned_data["preferred_field"],
                    cleaned_data["favorite_subject"],
                    cleaned_data["preferred_activity"],
                    cleaned_data["learning_style"],
                    cleaned_data["career_goal"],
                    cleaned_data.get("notes") or None,
                ),
            )
            profile_id = int(cursor.lastrowid)

            for result in results:
                cursor.execute(
                    """
                    INSERT INTO user_recommendation_results (
                        profile_id,
                        user_id,
                        rank_order,
                        program_slug,
                        program_name,
                        campus_name,
                        campus_city,
                        score,
                        reason
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        profile_id,
                        int(current_user.id),
                        int(result["rank_order"]),
                        result["program_slug"],
                        result["program_name"],
                        result["campus_name"],
                        result.get("campus_city"),
                        int(result["score"]),
                        result["reason"],
                    ),
                )

        database.commit_db()
        return profile_id


    def load_recommendation_results(profile_id: int | None = None) -> list[dict[str, Any]]:
        """Mengambil hasil rekomendasi milik user login."""

        try:
            ensure_recommendation_tables()

            with database.get_cursor(dictionary=True) as cursor:
                if profile_id is not None:
                    cursor.execute(
                        """
                        SELECT *
                        FROM user_recommendation_results
                        WHERE user_id = %s AND profile_id = %s
                        ORDER BY rank_order ASC
                        """,
                        (int(current_user.id), int(profile_id)),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT urr.*
                        FROM user_recommendation_results urr
                        INNER JOIN (
                            SELECT MAX(profile_id) AS latest_profile_id
                            FROM user_recommendation_results
                            WHERE user_id = %s
                        ) latest ON latest.latest_profile_id = urr.profile_id
                        WHERE urr.user_id = %s
                        ORDER BY urr.rank_order ASC
                        """,
                        (int(current_user.id), int(current_user.id)),
                    )

                return [dict(row) for row in cursor.fetchall()]

        except (Error, RuntimeError):
            app.logger.exception("Hasil rekomendasi gagal dimuat.")
            return []


    def load_recommendation_history() -> list[dict[str, Any]]:
        """Mengambil riwayat singkat pemetaan minat user."""

        try:
            ensure_recommendation_tables()

            with database.get_cursor(dictionary=True) as cursor:
                cursor.execute(
                    """
                    SELECT
                        uip.id,
                        uip.preferred_field,
                        uip.created_at,
                        COUNT(urr.id) AS result_count,
                        MAX(urr.score) AS best_score
                    FROM user_interest_profiles uip
                    LEFT JOIN user_recommendation_results urr
                        ON urr.profile_id = uip.id
                    WHERE uip.user_id = %s
                    GROUP BY uip.id, uip.preferred_field, uip.created_at
                    ORDER BY uip.created_at DESC
                    LIMIT 5
                    """,
                    (int(current_user.id),),
                )
                history_rows = [dict(row) for row in cursor.fetchall()]

            for row in history_rows:
                row["preferred_field_label"] = CATEGORY_LABELS.get(
                    row.get("preferred_field"),
                    row.get("preferred_field"),
                )

            return history_rows

        except (Error, RuntimeError):
            app.logger.exception("Riwayat rekomendasi gagal dimuat.")
            return []


    def build_recommendation_context(
        *,
        form_data: dict[str, str] | None = None,
        errors: list[str] | None = None,
        profile_id: int | None = None,
        scores: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        """Menyusun context template recommendation.html."""

        results = load_recommendation_results(profile_id)
        history = load_recommendation_history()

        score_items = []
        for key, value in sorted(
            (scores or calculate_interest_scores({})).items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            score_items.append(
                {
                    "key": key,
                    "label": CATEGORY_LABELS.get(key, key),
                    "value": value,
                }
            )

        return {
            "recommendation_options": RECOMMENDATION_OPTIONS,
            "category_labels": CATEGORY_LABELS,
            "form_data": form_data or {},
            "errors": errors or [],
            "results": results,
            "history": history,
            "score_items": score_items,
            "selected_profile_id": profile_id,
        }


    # =====================================================
    # 5.10. HELPER BABAK 7 - PROFIL PENGGUNA
    # =====================================================

    PROFILE_GENDER_OPTIONS = [
        ("", "Belum dipilih"),
        ("pria", "Pria"),
        ("wanita", "Wanita"),
        ("lainnya", "Lainnya"),
    ]

    PROFILE_EDUCATION_LEVEL_OPTIONS = [
        ("", "Belum dipilih"),
        ("sma", "SMA / MA"),
        ("smk", "SMK"),
        ("gap_year", "Gap year"),
        ("mahasiswa", "Sudah kuliah"),
        ("lainnya", "Lainnya"),
    ]

    PROFILE_TARGET_DEGREE_OPTIONS = [
        ("", "Belum dipilih"),
        ("d3", "D3"),
        ("d4", "D4"),
        ("s1", "S1"),
        ("s2", "S2"),
    ]

    PROFILE_CAMPUS_TYPE_OPTIONS = [
        ("", "Belum dipilih"),
        ("ptn", "PTN"),
        ("pts", "PTS"),
        ("kedinasan", "Kedinasan"),
        ("fleksibel", "Fleksibel"),
    ]

    PROFILE_BUDGET_OPTIONS = [
        ("", "Belum dipilih"),
        ("rendah", "Di bawah Rp5 juta / semester"),
        ("menengah", "Rp5 juta sampai Rp10 juta / semester"),
        ("tinggi", "Di atas Rp10 juta / semester"),
        ("beasiswa", "Mencari beasiswa"),
    ]

    PROFILE_LEARNING_OPTIONS = [
        ("", "Belum dipilih"),
        ("praktik", "Banyak praktik dan proyek"),
        ("teori", "Teori dan analisis"),
        ("visual", "Visual dan desain"),
        ("diskusi", "Diskusi dan presentasi"),
        ("campuran", "Campuran"),
    ]

    def ensure_profile_tables() -> None:
        """
        Membuat tabel profil pengguna untuk Babak 7.

        Data dasar login tetap berada di tabel users.
        Data tambahan seperti asal sekolah, kota, minat, dan preferensi
        disimpan di user_profiles agar struktur akun tetap rapi.
        """

        with database.get_cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                    user_id INT UNSIGNED NOT NULL,
                    phone_number VARCHAR(30) DEFAULT NULL,
                    date_of_birth DATE DEFAULT NULL,
                    gender ENUM('pria','wanita','lainnya') DEFAULT NULL,
                    province VARCHAR(100) DEFAULT NULL,
                    city VARCHAR(100) DEFAULT NULL,
                    address VARCHAR(255) DEFAULT NULL,
                    school_origin VARCHAR(150) DEFAULT NULL,
                    graduation_year SMALLINT UNSIGNED DEFAULT NULL,
                    education_level VARCHAR(40) DEFAULT NULL,
                    target_degree VARCHAR(20) DEFAULT NULL,
                    target_study_field VARCHAR(120) DEFAULT NULL,
                    preferred_campus_type VARCHAR(40) DEFAULT NULL,
                    preferred_location VARCHAR(120) DEFAULT NULL,
                    budget_range VARCHAR(60) DEFAULT NULL,
                    learning_preference VARCHAR(60) DEFAULT NULL,
                    career_goal VARCHAR(180) DEFAULT NULL,
                    strongest_skill VARCHAR(180) DEFAULT NULL,
                    favorite_subjects VARCHAR(180) DEFAULT NULL,
                    hobbies VARCHAR(180) DEFAULT NULL,
                    bio TEXT DEFAULT NULL,
                    notification_email TINYINT(1) NOT NULL DEFAULT 1,
                    notification_ticket TINYINT(1) NOT NULL DEFAULT 1,
                    allow_recommendation_history TINYINT(1) NOT NULL DEFAULT 1,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    UNIQUE KEY uq_user_profiles_user_id (user_id),
                    INDEX idx_user_profiles_city (city),
                    INDEX idx_user_profiles_target_degree (target_degree),
                    CONSTRAINT fk_user_profiles_user
                        FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """
            )

        database.commit_db()


    def get_default_profile_form() -> dict[str, str]:
        """Menghasilkan struktur form kosong agar template aman dibuka."""

        return {
            "full_name": getattr(current_user, "full_name", ""),
            "email": getattr(current_user, "email", ""),
            "phone_number": "",
            "date_of_birth": "",
            "gender": "",
            "province": "",
            "city": "",
            "address": "",
            "school_origin": "",
            "graduation_year": "",
            "education_level": "",
            "target_degree": "",
            "target_study_field": "",
            "preferred_campus_type": "",
            "preferred_location": "",
            "budget_range": "",
            "learning_preference": "",
            "career_goal": "",
            "strongest_skill": "",
            "favorite_subjects": "",
            "hobbies": "",
            "bio": "",
            "notification_email": "1",
            "notification_ticket": "1",
            "allow_recommendation_history": "1",
        }


    def sanitize_profile_text(value: Any, max_length: int) -> str:
        """Membersihkan input teks profil dengan batas panjang sederhana."""

        cleaned_value = str(value or "").strip()
        return cleaned_value[:max_length]


    def load_profile_row() -> dict[str, Any]:
        """
        Mengambil profil tambahan user.

        Jika user belum punya profil tambahan, sistem membuat baris kosong.
        Dengan cara ini halaman profil selalu punya data yang konsisten.
        """

        ensure_profile_tables()

        with database.get_cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM user_profiles
                WHERE user_id = %s
                LIMIT 1
                """,
                (int(current_user.id),),
            )
            profile_row = cursor.fetchone()

        if profile_row:
            return dict(profile_row)

        with database.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_profiles (user_id)
                VALUES (%s)
                """,
                (int(current_user.id),),
            )
        database.commit_db()

        with database.get_cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM user_profiles
                WHERE user_id = %s
                LIMIT 1
                """,
                (int(current_user.id),),
            )
            created_row = cursor.fetchone()

        return dict(created_row or {})


    def profile_row_to_form(profile_row: dict[str, Any]) -> dict[str, str]:
        """Mengubah row database menjadi form_data untuk template."""

        form_data = get_default_profile_form()

        for key in form_data:
            if key in {"full_name", "email"}:
                continue

            value = profile_row.get(key)

            if value is None:
                form_data[key] = ""
            elif hasattr(value, "strftime"):
                form_data[key] = value.strftime("%Y-%m-%d")
            else:
                form_data[key] = str(value)

        form_data["full_name"] = str(getattr(current_user, "full_name", ""))
        form_data["email"] = str(getattr(current_user, "email", ""))

        for flag_key in [
            "notification_email",
            "notification_ticket",
            "allow_recommendation_history",
        ]:
            form_data[flag_key] = "1" if int(profile_row.get(flag_key) or 0) == 1 else "0"

        return form_data


    def calculate_profile_completion(form_data: dict[str, str]) -> int:
        """Menghitung persentase kelengkapan profil secara sederhana."""

        important_keys = [
            "full_name",
            "phone_number",
            "city",
            "school_origin",
            "education_level",
            "target_degree",
            "target_study_field",
            "preferred_location",
            "learning_preference",
            "career_goal",
            "favorite_subjects",
            "bio",
        ]

        filled_count = sum(1 for key in important_keys if str(form_data.get(key, "")).strip())
        return round((filled_count / len(important_keys)) * 100)


    def load_profile_activity_summary() -> dict[str, Any]:
        """Mengambil ringkasan aktivitas user dari tiket dan rekomendasi."""

        summary = {
            "ticket_total": 0,
            "ticket_active": 0,
            "ticket_closed": 0,
            "recommendation_total": 0,
            "latest_recommendation_label": "Belum ada",
            "saved_programs": 0,
        }

        try:
            ensure_help_desk_tables()
            with database.get_cursor(dictionary=True) as cursor:
                cursor.execute(
                    """
                    SELECT
                        COUNT(*) AS total,
                        COALESCE(SUM(status != 'selesai'), 0) AS active_total,
                        COALESCE(SUM(status = 'selesai'), 0) AS closed_total
                    FROM help_tickets
                    WHERE user_id = %s
                    """,
                    (int(current_user.id),),
                )
                row = cursor.fetchone() or {}

            summary["ticket_total"] = int(row.get("total") or 0)
            summary["ticket_active"] = int(row.get("active_total") or 0)
            summary["ticket_closed"] = int(row.get("closed_total") or 0)

        except (Error, RuntimeError):
            app.logger.exception("Ringkasan tiket profil gagal dimuat.")

        try:
            ensure_recommendation_tables()
            with database.get_cursor(dictionary=True) as cursor:
                cursor.execute(
                    """
                    SELECT
                        COUNT(*) AS total,
                        MAX(created_at) AS latest_created_at
                    FROM user_interest_profiles
                    WHERE user_id = %s
                    """,
                    (int(current_user.id),),
                )
                row = cursor.fetchone() or {}

            summary["recommendation_total"] = int(row.get("total") or 0)
            latest_created_at = row.get("latest_created_at")

            if hasattr(latest_created_at, "strftime"):
                summary["latest_recommendation_label"] = latest_created_at.strftime("%d/%m/%Y %H:%M")

        except (Error, RuntimeError):
            app.logger.exception("Ringkasan rekomendasi profil gagal dimuat.")

        return summary


    def load_profile_recent_tickets() -> list[dict[str, Any]]:
        """Mengambil beberapa tiket terbaru untuk halaman profil."""

        try:
            ensure_help_desk_tables()
            with database.get_cursor(dictionary=True) as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        ticket_code,
                        category,
                        subject,
                        priority,
                        status,
                        created_at,
                        updated_at
                    FROM help_tickets
                    WHERE user_id = %s
                    ORDER BY updated_at DESC, created_at DESC
                    LIMIT 4
                    """,
                    (int(current_user.id),),
                )
                rows = [dict(row) for row in cursor.fetchall()]

            return [enrich_ticket_row(row) for row in rows]

        except (Error, RuntimeError):
            app.logger.exception("Tiket terbaru profil gagal dimuat.")
            return []


    def validate_profile_update_form(form_data: Any) -> tuple[dict[str, str], list[str]]:
        """Validasi form profil utama."""

        cleaned = get_default_profile_form()
        errors: list[str] = []

        cleaned["full_name"] = sanitize_profile_text(form_data.get("full_name"), 100)
        cleaned["phone_number"] = sanitize_profile_text(form_data.get("phone_number"), 30)
        cleaned["date_of_birth"] = sanitize_profile_text(form_data.get("date_of_birth"), 10)
        cleaned["gender"] = sanitize_profile_text(form_data.get("gender"), 20)
        cleaned["province"] = sanitize_profile_text(form_data.get("province"), 100)
        cleaned["city"] = sanitize_profile_text(form_data.get("city"), 100)
        cleaned["address"] = sanitize_profile_text(form_data.get("address"), 255)
        cleaned["school_origin"] = sanitize_profile_text(form_data.get("school_origin"), 150)
        cleaned["graduation_year"] = sanitize_profile_text(form_data.get("graduation_year"), 4)
        cleaned["education_level"] = sanitize_profile_text(form_data.get("education_level"), 40)
        cleaned["target_degree"] = sanitize_profile_text(form_data.get("target_degree"), 20)
        cleaned["target_study_field"] = sanitize_profile_text(form_data.get("target_study_field"), 120)
        cleaned["preferred_campus_type"] = sanitize_profile_text(form_data.get("preferred_campus_type"), 40)
        cleaned["preferred_location"] = sanitize_profile_text(form_data.get("preferred_location"), 120)
        cleaned["budget_range"] = sanitize_profile_text(form_data.get("budget_range"), 60)
        cleaned["learning_preference"] = sanitize_profile_text(form_data.get("learning_preference"), 60)
        cleaned["career_goal"] = sanitize_profile_text(form_data.get("career_goal"), 180)
        cleaned["strongest_skill"] = sanitize_profile_text(form_data.get("strongest_skill"), 180)
        cleaned["favorite_subjects"] = sanitize_profile_text(form_data.get("favorite_subjects"), 180)
        cleaned["hobbies"] = sanitize_profile_text(form_data.get("hobbies"), 180)
        cleaned["bio"] = sanitize_profile_text(form_data.get("bio"), 700)
        cleaned["notification_email"] = "1" if form_data.get("notification_email") == "1" else "0"
        cleaned["notification_ticket"] = "1" if form_data.get("notification_ticket") == "1" else "0"
        cleaned["allow_recommendation_history"] = "1" if form_data.get("allow_recommendation_history") == "1" else "0"

        if len(cleaned["full_name"]) < 3:
            errors.append("Nama lengkap minimal 3 karakter.")

        if cleaned["gender"] and cleaned["gender"] not in {"pria", "wanita", "lainnya"}:
            errors.append("Pilihan gender tidak valid.")

        if cleaned["graduation_year"]:
            if not cleaned["graduation_year"].isdigit():
                errors.append("Tahun lulus harus berupa angka.")
            else:
                graduation_year = int(cleaned["graduation_year"])
                if graduation_year < 1990 or graduation_year > 2100:
                    errors.append("Tahun lulus berada di luar rentang yang wajar.")

        return cleaned, errors


    def save_profile_update(cleaned: dict[str, str]) -> None:
        """Menyimpan perubahan profil ke users dan user_profiles."""

        ensure_profile_tables()

        graduation_year = int(cleaned["graduation_year"]) if cleaned["graduation_year"].isdigit() else None

        with database.get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET full_name = %s
                WHERE id = %s
                """,
                (
                    cleaned["full_name"],
                    int(current_user.id),
                ),
            )

            cursor.execute(
                """
                INSERT INTO user_profiles (
                    user_id,
                    phone_number,
                    date_of_birth,
                    gender,
                    province,
                    city,
                    address,
                    school_origin,
                    graduation_year,
                    education_level,
                    target_degree,
                    target_study_field,
                    preferred_campus_type,
                    preferred_location,
                    budget_range,
                    learning_preference,
                    career_goal,
                    strongest_skill,
                    favorite_subjects,
                    hobbies,
                    bio,
                    notification_email,
                    notification_ticket,
                    allow_recommendation_history
                ) VALUES (
                    %s, %s, NULLIF(%s, ''), NULLIF(%s, ''), NULLIF(%s, ''),
                    NULLIF(%s, ''), NULLIF(%s, ''), NULLIF(%s, ''), %s,
                    NULLIF(%s, ''), NULLIF(%s, ''), NULLIF(%s, ''), NULLIF(%s, ''),
                    NULLIF(%s, ''), NULLIF(%s, ''), NULLIF(%s, ''), NULLIF(%s, ''),
                    NULLIF(%s, ''), NULLIF(%s, ''), NULLIF(%s, ''), NULLIF(%s, ''),
                    %s, %s, %s
                )
                ON DUPLICATE KEY UPDATE
                    phone_number = VALUES(phone_number),
                    date_of_birth = VALUES(date_of_birth),
                    gender = VALUES(gender),
                    province = VALUES(province),
                    city = VALUES(city),
                    address = VALUES(address),
                    school_origin = VALUES(school_origin),
                    graduation_year = VALUES(graduation_year),
                    education_level = VALUES(education_level),
                    target_degree = VALUES(target_degree),
                    target_study_field = VALUES(target_study_field),
                    preferred_campus_type = VALUES(preferred_campus_type),
                    preferred_location = VALUES(preferred_location),
                    budget_range = VALUES(budget_range),
                    learning_preference = VALUES(learning_preference),
                    career_goal = VALUES(career_goal),
                    strongest_skill = VALUES(strongest_skill),
                    favorite_subjects = VALUES(favorite_subjects),
                    hobbies = VALUES(hobbies),
                    bio = VALUES(bio),
                    notification_email = VALUES(notification_email),
                    notification_ticket = VALUES(notification_ticket),
                    allow_recommendation_history = VALUES(allow_recommendation_history),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    int(current_user.id),
                    cleaned["phone_number"] or None,
                    cleaned["date_of_birth"],
                    cleaned["gender"],
                    cleaned["province"],
                    cleaned["city"],
                    cleaned["address"],
                    cleaned["school_origin"],
                    graduation_year,
                    cleaned["education_level"],
                    cleaned["target_degree"],
                    cleaned["target_study_field"],
                    cleaned["preferred_campus_type"],
                    cleaned["preferred_location"],
                    cleaned["budget_range"],
                    cleaned["learning_preference"],
                    cleaned["career_goal"],
                    cleaned["strongest_skill"],
                    cleaned["favorite_subjects"],
                    cleaned["hobbies"],
                    cleaned["bio"],
                    int(cleaned["notification_email"]),
                    int(cleaned["notification_ticket"]),
                    int(cleaned["allow_recommendation_history"]),
                ),
            )

        database.commit_db()


    def validate_profile_password_form(form_data: Any) -> tuple[dict[str, str], list[str]]:
        """Validasi form keamanan akun."""

        cleaned = {
            "current_password": str(form_data.get("current_password") or ""),
            "new_password": str(form_data.get("new_password") or ""),
            "confirm_password": str(form_data.get("confirm_password") or ""),
        }
        errors: list[str] = []

        if not cleaned["current_password"]:
            errors.append("Kata sandi saat ini wajib diisi.")

        if len(cleaned["new_password"]) < 8:
            errors.append("Kata sandi baru minimal 8 karakter.")

        if cleaned["new_password"] != cleaned["confirm_password"]:
            errors.append("Konfirmasi kata sandi baru belum sama.")

        if cleaned["current_password"] and cleaned["new_password"] and cleaned["current_password"] == cleaned["new_password"]:
            errors.append("Kata sandi baru tidak boleh sama dengan kata sandi lama.")

        return cleaned, errors


    def save_profile_password(cleaned: dict[str, str]) -> None:
        """Mengubah kata sandi user dari halaman profil."""

        with database.get_cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT password_hash
                FROM users
                WHERE id = %s
                LIMIT 1
                """,
                (int(current_user.id),),
            )
            row = cursor.fetchone()

        if not row or not check_password_hash(str(row["password_hash"]), cleaned["current_password"]):
            raise ValueError("Kata sandi saat ini tidak sesuai.")

        new_password_hash = generate_password_hash(cleaned["new_password"])

        with database.get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET password_hash = %s
                WHERE id = %s
                """,
                (
                    new_password_hash,
                    int(current_user.id),
                ),
            )

        database.commit_db()


    def build_profile_context(
        *,
        form_data: dict[str, str] | None = None,
        errors: list[str] | None = None,
    ) -> dict[str, Any]:
        """Menyusun semua data yang dibutuhkan profile.html."""

        profile_row = load_profile_row()
        active_form_data = form_data or profile_row_to_form(profile_row)
        completion = calculate_profile_completion(active_form_data)

        return {
            "form_data": active_form_data,
            "errors": errors or [],
            "profile_completion": completion,
            "activity_summary": load_profile_activity_summary(),
            "recent_tickets": load_profile_recent_tickets(),
            "recommendation_history": load_recommendation_history(),
            "gender_options": PROFILE_GENDER_OPTIONS,
            "education_level_options": PROFILE_EDUCATION_LEVEL_OPTIONS,
            "target_degree_options": PROFILE_TARGET_DEGREE_OPTIONS,
            "campus_type_options": PROFILE_CAMPUS_TYPE_OPTIONS,
            "budget_options": PROFILE_BUDGET_OPTIONS,
            "learning_options": PROFILE_LEARNING_OPTIONS,
        }


    # =====================================================
    # 6.0. ROUTE BABAK 5 - DETAIL KAMPUS DAN PROGRAM STUDI
    # =====================================================

    @app.get("/campus-detail")
    def campus_detail():
        """
        Menampilkan halaman detail program studi.

        Query opsional:
        /campus-detail?program=teknik-informatika
        """

        program_slug = request.args.get("program", DEFAULT_PROGRAM_SLUG)

        return render_template(
            "campus-detail.html",
            **load_campus_detail_context(program_slug),
        )


    @app.get("/campus-detail/<program_slug>")
    def campus_detail_slug(program_slug: str):
        """
        URL rapi untuk detail program studi.
        """

        return render_template(
            "campus-detail.html",
            **load_campus_detail_context(program_slug),
        )



    # =====================================================
    # 6.1. ROUTE BABAK 6 - PEMETAAN MINAT DAN REKOMENDASI
    # =====================================================

    @app.route("/recommendation", methods=["GET", "POST"])
    @login_required
    def recommendation():
        """
        Menampilkan dan memproses pemetaan minat.

        Halaman ini menjadi modul Babak 6. User mengisi beberapa pilihan,
        sistem menghitung kecocokan secara rule-based, lalu menampilkan
        3-5 program studi yang paling relevan.
        """

        if request.method == "POST":
            cleaned_data, errors = validate_recommendation_form(request.form)

            if errors:
                return render_template(
                    "recommendation.html",
                    **build_recommendation_context(
                        form_data=cleaned_data,
                        errors=errors,
                    ),
                )

            try:
                results, scores = build_recommendation_results(cleaned_data)
                profile_id = save_recommendation_result(cleaned_data, results)

                flash(
                    "Pemetaan minat berhasil dibuat. Lihat hasil rekomendasi di bawah.",
                    "success",
                )

                return redirect(
                    url_for("recommendation", result_id=profile_id) + "#hasil-rekomendasi"
                )

            except (Error, RuntimeError):
                database.rollback_db()
                app.logger.exception("Pemetaan minat gagal diproses.")

                return render_template(
                    "recommendation.html",
                    **build_recommendation_context(
                        form_data=cleaned_data,
                        errors=[
                            "Pemetaan minat belum bisa diproses. Silakan coba lagi beberapa saat lagi."
                        ],
                    ),
                )

        result_id_raw = request.args.get("result_id", "").strip()
        result_id = int(result_id_raw) if result_id_raw.isdigit() else None

        return render_template(
            "recommendation.html",
            **build_recommendation_context(
                profile_id=result_id,
            ),
        )


    @app.get("/recommendations")
    @login_required
    def recommendations_legacy():
        """Alias agar link /recommendations tetap aman."""

        return redirect(
            url_for("recommendation")
        )


    @app.get("/pemetaan-minat")
    @login_required
    def interest_mapping_legacy():
        """Alias agar istilah lama /pemetaan-minat tetap aman."""

        return redirect(
            url_for("recommendation")
        )



    # =====================================================
    # 6.2. ROUTE BABAK 7 - PROFIL PENGGUNA
    # =====================================================

    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        """
        Menampilkan dan memproses halaman profil pengguna.

        Babak 7 membuat akun lebih realistis:
        - data diri,
        - asal sekolah,
        - preferensi kampus,
        - minat akademik,
        - preferensi notifikasi,
        - dan keamanan password.
        """

        if request.method == "POST":
            profile_action = str(request.form.get("profile_action") or "profile").strip()

            if profile_action == "security":
                cleaned_password, password_errors = validate_profile_password_form(request.form)

                if password_errors:
                    return render_template(
                        "profile.html",
                        **build_profile_context(errors=password_errors),
                    )

                try:
                    save_profile_password(cleaned_password)
                    flash("Kata sandi berhasil diperbarui.", "success")

                    return redirect(
                        url_for("profile") + "#keamanan-akun"
                    )

                except ValueError as error:
                    return render_template(
                        "profile.html",
                        **build_profile_context(errors=[str(error)]),
                    )

                except (Error, RuntimeError):
                    database.rollback_db()
                    app.logger.exception("Perubahan kata sandi dari profil gagal.")

                    return render_template(
                        "profile.html",
                        **build_profile_context(
                            errors=["Kata sandi belum bisa diperbarui. Silakan coba lagi beberapa saat lagi."]
                        ),
                    )

            cleaned_profile, profile_errors = validate_profile_update_form(request.form)

            if profile_errors:
                return render_template(
                    "profile.html",
                    **build_profile_context(
                        form_data=cleaned_profile,
                        errors=profile_errors,
                    ),
                )

            try:
                save_profile_update(cleaned_profile)
                flash("Profil berhasil diperbarui.", "success")

                return redirect(
                    url_for("profile") + "#profil-saya"
                )

            except (Error, RuntimeError):
                database.rollback_db()
                app.logger.exception("Profil pengguna gagal diperbarui.")

                return render_template(
                    "profile.html",
                    **build_profile_context(
                        form_data=cleaned_profile,
                        errors=["Profil belum bisa disimpan. Silakan coba lagi beberapa saat lagi."],
                    ),
                )

        return render_template(
            "profile.html",
            **build_profile_context(),
        )


    @app.get("/account")
    @login_required
    def account_legacy():
        """Alias aman untuk URL akun versi umum."""

        return redirect(
            url_for("profile")
        )


    @app.get("/akun-saya")
    @login_required
    def akun_saya_legacy():
        """Alias aman untuk URL berbahasa Indonesia."""

        return redirect(
            url_for("profile")
        )


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
    @login_required
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


    @app.get("/ticket/<int:ticket_id>")
    @login_required
    def ticket_detail(ticket_id: int):
        """
        Menampilkan detail tiket milik student.

        Di sinilah student membaca balasan admin, termasuk tiket yang sudah
        ditandai selesai oleh admin.
        """

        context = load_user_ticket_context()
        detail_context = load_user_ticket_detail(ticket_id)

        if detail_context["selected_ticket"] is None:
            flash(
                "Tiket tidak ditemukan atau bukan milik akunmu.",
                "error",
            )

            return redirect(
                url_for("ticket") + "#ticket-form"
            )

        context.update(detail_context)

        return render_template(
            "ticket.html",
            **context,
        )


    @app.get("/tickets")
    def tickets_legacy():
        """
        Alias aman jika ada URL lama /tickets.
        Semua diarahkan ke halaman utama modul tiket /ticket.
        """

        return redirect(
            url_for("ticket") + "#ticket-form"
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

        # Dipakai untuk redirect ke detail tiket setelah insert sukses.
        ticket_id: int | None = None

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

        # Setelah tiket dibuat, arahkan user ke detail tiket agar pola
        # percakapan user-admin langsung terasa jelas.
        if ticket_id is not None:
            return redirect(
                url_for("ticket_detail", ticket_id=int(ticket_id)) + "#detail-tiket"
            )

        return redirect(
            url_for("ticket")
        )


    # =====================================================
    # 6.3. ROUTE PANEL ADMIN HELP DESK
    # =====================================================

    @app.get("/admin")
    @login_required
    def admin_panel():
        """
        Menampilkan Panel Admin Help Desk.

        Babak 4 dipisahkan ke file:
        - templates/admin.html
        - static/css/admin.css
        - static/js/admin.js

        Halaman ini hanya untuk user dengan role admin.
        """

        denied_response = require_admin_access()
        if denied_response is not None:
            return denied_response

        try:
            context = load_admin_ticket_context()

        except (Error, RuntimeError):
            database.rollback_db()
            app.logger.exception(
                "Panel admin gagal memuat data tiket."
            )

            flash(
                "Data admin belum dapat dimuat. Silakan coba kembali.",
                "error",
            )

            context = {
                "admin_summary": {
                    "total": 0,
                    "submitted": 0,
                    "in_progress": 0,
                    "closed": 0,
                    "high_priority_open": 0,
                },
                "admin_tickets": [],
                "ticket_category_options": TICKET_CATEGORY_OPTIONS,
                "ticket_priority_options": TICKET_PRIORITY_OPTIONS,
                "ticket_status_labels": TICKET_STATUS_LABELS,
                "selected_status": "all",
                "selected_category": "all",
                "selected_priority": "all",
                "search_query": "",
            }

        return render_template(
            "admin.html",
            **context,
        )


    @app.post("/admin/ticket/<int:ticket_id>/status")
    @login_required
    def admin_update_ticket_status(ticket_id: int):
        """
        Mengubah status tiket dari Panel Admin.
        Status yang tersedia: dikirim, diproses, selesai.
        """

        denied_response = require_admin_access()
        if denied_response is not None:
            return denied_response

        new_status = str(request.form.get("status", "")).strip()

        if new_status not in TICKET_STATUS_LABELS:
            flash("Status tiket tidak valid.", "error")

            return redirect(
                url_for("admin_panel") + "#admin-tickets"
            )

        try:
            ensure_help_desk_tables()

            with database.get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE help_tickets
                    SET
                        status = %s,
                        closed_at = CASE
                            WHEN %s = 'selesai' THEN NOW()
                            ELSE NULL
                        END
                    WHERE id = %s
                    """,
                    (
                        new_status,
                        new_status,
                        ticket_id,
                    ),
                )

            database.commit_db()
            flash("Status tiket berhasil diperbarui.", "success")

        except (Error, RuntimeError):
            database.rollback_db()
            app.logger.exception(
                "Status tiket gagal diperbarui."
            )

            flash("Status tiket belum dapat diperbarui.", "error")

        return redirect(
            url_for("admin_panel")
        )


    @app.post("/admin/ticket/<int:ticket_id>/reply")
    @login_required
    def admin_reply_ticket(ticket_id: int):
        """
        Menyimpan balasan admin ke ticket_messages.
        Saat admin membalas, status tiket otomatis menjadi diproses
        kecuali tiket sudah ditandai selesai.
        """

        denied_response = require_admin_access()
        if denied_response is not None:
            return denied_response

        reply_message, errors = validate_admin_reply_form(request.form)

        if errors:
            flash(errors[0], "error")

            return redirect(
                url_for("admin_panel") + "#admin-tickets"
            )

        try:
            ensure_help_desk_tables()

            with database.get_cursor(dictionary=True) as cursor:
                cursor.execute(
                    """
                    SELECT id, status
                    FROM help_tickets
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (ticket_id,),
                )

                ticket_row = cursor.fetchone()

            if not ticket_row:
                flash("Tiket tidak ditemukan.", "error")

                return redirect(
                    url_for("admin_panel") + "#admin-tickets"
                )

            with database.get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO ticket_messages (
                        ticket_id,
                        sender_id,
                        sender_type,
                        message
                    )
                    VALUES (%s, %s, 'admin', %s)
                    """,
                    (
                        ticket_id,
                        int(current_user.id),
                        reply_message,
                    ),
                )

                if str(ticket_row.get("status")) != "selesai":
                    cursor.execute(
                        """
                        UPDATE help_tickets
                        SET status = 'diproses'
                        WHERE id = %s
                        """,
                        (ticket_id,),
                    )

            database.commit_db()
            flash("Balasan admin berhasil dikirim.", "success")

        except (Error, RuntimeError):
            database.rollback_db()
            app.logger.exception(
                "Balasan admin gagal disimpan."
            )

            flash("Balasan belum dapat dikirim.", "error")

        return redirect(
            url_for("admin_panel")
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


    @app.get("/admin.html")
    def legacy_admin():
        """
        Mengarahkan URL admin.html menuju route admin Flask.
        """

        return redirect(
            url_for("admin_panel")
        )


    @app.get("/campus-detail.html")
    def legacy_campus_detail():
        """
        Mengarahkan URL lama campus-detail.html menuju route Flask Babak 5.
        """

        return redirect(
            url_for("campus_detail")
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

        # Mencegah halaman login, index, ticket, dan admin dipulihkan
        # sebagai tampilan putih/stale ketika user memakai tombol Back browser.
        # Browser akan memuat ulang HTML terbaru dari Flask.
        if response.mimetype == "text/html":
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

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