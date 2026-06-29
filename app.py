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
                url_for("ticket")
            )

        if request.path.startswith("/admin"):
            flash(
                "Sesi formulir admin sudah berakhir. Muat ulang halaman, lalu coba kembali.",
                "error",
            )

            return redirect(
                url_for("admin_panel")
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
                url_for("ticket")
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
                url_for("ticket_detail", ticket_id=int(ticket_id))
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
                url_for("admin_panel")
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
                url_for("admin_panel")
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
                    url_for("admin_panel")
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