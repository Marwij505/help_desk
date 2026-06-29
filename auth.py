"""
=========================================================
COMPASS CAMPUS — AUTH.PY

File ini bertugas:
1. Menampilkan halaman login
2. Memproses login pengguna
3. Menampilkan halaman register
4. Memproses pendaftaran akun
5. Memproses perubahan kata sandi
6. Membuat dan menghapus session login
7. Mencatat aktivitas autentikasi
8. Menghubungkan Flask-Login dengan tabel users

PENTING:
- Password asli tidak pernah disimpan ke database.
- Password disimpan dalam bentuk hash.
- Seluruh input divalidasi ulang oleh Python.
- Query database menggunakan parameterized query.
=========================================================
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from urllib.parse import urljoin, urlsplit

from flask import (
    Blueprint,
    Flask,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from mysql.connector import Error, IntegrityError
from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from database import (
    commit_db,
    get_cursor,
    rollback_db,
)
from validators import (
    get_first_error,
    validate_forgot_password_form,
    validate_login_form,
    validate_register_form,
)


# =========================================================
# 1. BLUEPRINT DAN FLASK-LOGIN
# =========================================================

auth_bp = Blueprint(
    "auth",
    __name__,
)

login_manager = LoginManager()

# Halaman tujuan ketika pengguna belum login.
login_manager.login_view = "auth.login"

# Pesan bawaan Flask-Login.
login_manager.login_message = (
    "Silakan masuk terlebih dahulu untuk mengakses halaman tersebut."
)

login_manager.login_message_category = "error"


# =========================================================
# 2. MODEL USER UNTUK SESSION FLASK-LOGIN
# =========================================================

class User(UserMixin):
    """
    Representasi pengguna untuk Flask-Login.

    Class ini bukan tabel database baru.
    Data tetap berasal dari tabel users di MySQL.
    """

    def __init__(
        self,
        *,
        user_id: int,
        full_name: str,
        email: str,
        role: str,
        is_active: bool,
    ) -> None:
        self.id = user_id
        self.full_name = full_name
        self.email = email
        self.role = role
        self._is_active = bool(is_active)

    @property
    def is_active(self) -> bool:
        """
        Mengembalikan status aktif pengguna.
        """

        return self._is_active


# =========================================================
# 3. MEMBUAT OBJEK USER DARI HASIL DATABASE
# =========================================================

def create_user_from_row(
    user_row: dict[str, Any],
) -> User:
    """
    Mengubah hasil query dictionary menjadi objek User.
    """

    return User(
        user_id=int(user_row["id"]),
        full_name=str(user_row["full_name"]),
        email=str(user_row["email"]),
        role=str(user_row["role"]),
        is_active=bool(user_row["is_active"]),
    )


# =========================================================
# 4. MEMUAT USER DARI SESSION
# =========================================================

@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    """
    Mengambil pengguna berdasarkan ID yang tersimpan
    pada session Flask-Login.

    Fungsi ini otomatis dipanggil pada setiap request
    ketika pengguna sudah login.
    """

    try:
        numeric_user_id = int(user_id)

    except (TypeError, ValueError):
        return None

    try:
        with get_cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    full_name,
                    email,
                    role,
                    is_active
                FROM users
                WHERE id = %s
                LIMIT 1
                """,
                (numeric_user_id,),
            )

            user_row = cursor.fetchone()

    except (Error, RuntimeError):
        current_app.logger.exception(
            "Gagal memuat pengguna dari session."
        )

        return None

    if not user_row:
        return None

    # Pengguna yang dinonaktifkan tidak boleh
    # mempertahankan session login.
    if not bool(user_row["is_active"]):
        return None

    return create_user_from_row(user_row)


# =========================================================
# 5. PENANGANAN PENGGUNA YANG BELUM LOGIN
# =========================================================

@login_manager.unauthorized_handler
def handle_unauthorized():
    """
    Mengarahkan pengguna ke login jika mencoba membuka
    halaman yang membutuhkan autentikasi.
    """

    next_destination = request.path

    return redirect(
        url_for(
            "auth.login",
            required="1",
            next=next_destination,
        )
    )


# =========================================================
# 6. INFORMASI REQUEST UNTUK AUTH LOG
# =========================================================

def get_client_ip_address() -> str | None:
    """
    Mengambil alamat IP pengguna.

    Untuk penggunaan localhost, nilai biasanya:
    127.0.0.1
    """

    return request.remote_addr


def get_user_agent() -> str | None:
    """
    Mengambil informasi browser dan perangkat pengguna.
    """

    user_agent = request.user_agent.string

    if not user_agent:
        return None

    # Kolom database maksimal 255 karakter.
    return user_agent[:255]


# =========================================================
# 7. MENYIMPAN AUTH LOG
# =========================================================

def insert_auth_log(
    *,
    activity_type: str,
    user_id: int | None = None,
    email: str | None = None,
    description: str | None = None,
) -> None:
    """
    Menambahkan aktivitas ke tabel auth_logs.

    Fungsi ini tidak melakukan commit secara otomatis,
    sehingga dapat menjadi bagian dari transaksi utama.
    """

    safe_description = (
        description[:255]
        if description
        else None
    )

    with get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO auth_logs (
                user_id,
                email,
                activity_type,
                description,
                ip_address,
                user_agent
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                email,
                activity_type,
                safe_description,
                get_client_ip_address(),
                get_user_agent(),
            ),
        )


def safely_record_auth_log(
    *,
    activity_type: str,
    user_id: int | None = None,
    email: str | None = None,
    description: str | None = None,
) -> None:
    """
    Menyimpan log secara aman tanpa mengganggu proses utama.

    Digunakan terutama untuk mencatat login gagal.
    """

    try:
        insert_auth_log(
            activity_type=activity_type,
            user_id=user_id,
            email=email,
            description=description,
        )

        commit_db()

    except (Error, RuntimeError):
        try:
            rollback_db()
        except (Error, RuntimeError):
            pass

        current_app.logger.exception(
            "Aktivitas autentikasi gagal dicatat."
        )


# =========================================================
# 8. MEMERIKSA TUJUAN REDIRECT
# =========================================================

def is_safe_redirect_destination(
    destination: str | None,
) -> bool:
    """
    Mencegah redirect menuju website luar.

    Parameter `next` hanya diperbolehkan menuju halaman
    dalam aplikasi Compass Campus.
    """

    if not destination:
        return False

    reference_url = urlsplit(request.host_url)

    destination_url = urlsplit(
        urljoin(
            request.host_url,
            destination,
        )
    )

    return (
        destination_url.scheme in {"http", "https"}
        and reference_url.netloc
        == destination_url.netloc
    )


# =========================================================
# 9. HALAMAN REGISTER
# =========================================================

@auth_bp.route(
    "/register",
    methods=["GET", "POST"],
)
def register():
    """
    Menampilkan dan memproses halaman registrasi.
    """

    # Pengguna yang sudah login tidak perlu register lagi.
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "GET":
        return render_template(
            "register.html",
            error=None,
            success=None,
        )

    # -----------------------------------------------------
    # Validasi data register
    # -----------------------------------------------------

    cleaned_data, errors = validate_register_form(
        request.form
    )

    if errors:
        return (
            render_template(
                "register.html",
                error=get_first_error(errors),
                success=None,
                form_data={
                    "full_name": cleaned_data.get(
                        "full_name",
                        "",
                    ),
                    "email": cleaned_data.get(
                        "email",
                        "",
                    ),
                },
            ),
            400,
        )

    full_name = cleaned_data["full_name"]
    email = cleaned_data["email"]
    password = cleaned_data["password"]

    try:
        # -------------------------------------------------
        # Memeriksa email yang sudah terdaftar
        # -------------------------------------------------

        with get_cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    email
                FROM users
                WHERE email = %s
                LIMIT 1
                """,
                (email,),
            )

            existing_user = cursor.fetchone()

        if existing_user:
            safely_record_auth_log(
                activity_type="register_failed",
                user_id=int(existing_user["id"]),
                email=email,
                description=(
                    "Pendaftaran ditolak karena email "
                    "sudah terdaftar."
                ),
            )

            return (
                render_template(
                    "register.html",
                    error=(
                        "Email tersebut sudah terdaftar. "
                        "Silakan masuk menggunakan akunmu."
                    ),
                    success=None,
                    form_data={
                        "full_name": full_name,
                        "email": email,
                    },
                ),
                409,
            )

        # -------------------------------------------------
        # Membuat hash password
        # -------------------------------------------------

        password_hash = generate_password_hash(
            password
        )

        # -------------------------------------------------
        # Menyimpan akun baru
        # -------------------------------------------------

        with get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (
                    full_name,
                    email,
                    password_hash,
                    role,
                    is_active
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    full_name,
                    email,
                    password_hash,
                    "student",
                    1,
                ),
            )

            new_user_id = cursor.lastrowid

        if new_user_id is None:
            raise RuntimeError(
                "ID pengguna baru tidak berhasil dibuat."
            )

        # Pencatatan register berhasil berada
        # dalam transaksi yang sama.
        insert_auth_log(
            activity_type="register_success",
            user_id=int(new_user_id),
            email=email,
            description="Akun pengguna berhasil dibuat.",
        )

        commit_db()

    except IntegrityError:
        rollback_db()

        current_app.logger.warning(
            "Pendaftaran menggunakan email duplikat: %s",
            email,
        )

        return (
            render_template(
                "register.html",
                error=(
                    "Email tersebut sudah terdaftar. "
                    "Silakan gunakan email lain."
                ),
                success=None,
                form_data={
                    "full_name": full_name,
                    "email": email,
                },
            ),
            409,
        )

    except (Error, RuntimeError):
        rollback_db()

        current_app.logger.exception(
            "Proses registrasi pengguna gagal."
        )

        return (
            render_template(
                "register.html",
                error=(
                    "Pendaftaran belum dapat diproses. "
                    "Silakan coba kembali beberapa saat lagi."
                ),
                success=None,
                form_data={
                    "full_name": full_name,
                    "email": email,
                },
            ),
            500,
        )

    # Registrasi berhasil dan diarahkan menuju login.
    return redirect(
        url_for(
            "auth.login",
            registered="1",
        )
    )


# =========================================================
# 10. HALAMAN LOGIN
# =========================================================

@auth_bp.route(
    "/login",
    methods=["GET", "POST"],
)
def login():
    """
    Menampilkan dan memproses halaman login.
    """

    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "GET":
        success_message = None
        error_message = None

        if request.args.get("registered") == "1":
            success_message = (
                "Akun berhasil dibuat. "
                "Silakan masuk menggunakan akun barumu."
            )

        elif request.args.get("password_changed") == "1":
            success_message = (
                "Kata sandi berhasil diperbarui. "
                "Silakan masuk menggunakan kata sandi baru."
            )

        elif request.args.get("logout") == "1":
            success_message = (
                "Kamu berhasil keluar dari akun."
            )

        if request.args.get("required") == "1":
            error_message = (
                "Silakan masuk terlebih dahulu untuk "
                "mengakses halaman tersebut."
            )

        return render_template(
            "login.html",
            error=error_message,
            success=success_message,
        )

    # -----------------------------------------------------
    # Validasi form login
    # -----------------------------------------------------

    cleaned_data, errors = validate_login_form(
        request.form
    )

    if errors:
        return (
            render_template(
                "login.html",
                error=get_first_error(errors),
                success=None,
                form_data={
                    "email": cleaned_data.get(
                        "email",
                        "",
                    ),
                },
            ),
            400,
        )

    email = cleaned_data["email"]
    password = cleaned_data["password"]

    try:
        # -------------------------------------------------
        # Mengambil akun berdasarkan email
        # -------------------------------------------------

        with get_cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    full_name,
                    email,
                    password_hash,
                    role,
                    is_active
                FROM users
                WHERE email = %s
                LIMIT 1
                """,
                (email,),
            )

            user_row = cursor.fetchone()

        # -------------------------------------------------
        # Email tidak terdaftar
        # -------------------------------------------------

        if not user_row:
            safely_record_auth_log(
                activity_type="login_failed",
                email=email,
                description=(
                    "Login gagal karena email "
                    "tidak terdaftar."
                ),
            )

            return (
                render_template(
                    "login.html",
                    error="Email tidak terdaftar.",
                    success=None,
                    form_data={
                        "email": email,
                    },
                ),
                401,
            )

        user_id = int(user_row["id"])

        # -------------------------------------------------
        # Akun dinonaktifkan
        # -------------------------------------------------

        if not bool(user_row["is_active"]):
            safely_record_auth_log(
                activity_type="login_failed",
                user_id=user_id,
                email=email,
                description=(
                    "Login gagal karena akun tidak aktif."
                ),
            )

            return (
                render_template(
                    "login.html",
                    error=(
                        "Akun ini sedang tidak aktif. "
                        "Silakan hubungi tim bantuan."
                    ),
                    success=None,
                    form_data={
                        "email": email,
                    },
                ),
                403,
            )

        # -------------------------------------------------
        # Password salah
        # -------------------------------------------------

        password_is_correct = check_password_hash(
            str(user_row["password_hash"]),
            password,
        )

        if not password_is_correct:
            safely_record_auth_log(
                activity_type="login_failed",
                user_id=user_id,
                email=email,
                description=(
                    "Login gagal karena kata sandi salah."
                ),
            )

            return (
                render_template(
                    "login.html",
                    error="Kata sandi yang dimasukkan salah.",
                    success=None,
                    form_data={
                        "email": email,
                    },
                ),
                401,
            )

        # -------------------------------------------------
        # Membuat session login
        # -------------------------------------------------

        user = create_user_from_row(user_row)

        remember_value = str(
            request.form.get("remember", "")
        ).strip().lower()

        remember_user = remember_value in {
            "1",
            "true",
            "yes",
            "on",
        }

        login_was_successful = login_user(
            user,
            remember=remember_user,
            duration=timedelta(days=7),
            fresh=True,
        )

        if not login_was_successful:
            return (
                render_template(
                    "login.html",
                    error=(
                        "Session login tidak berhasil dibuat."
                    ),
                    success=None,
                    form_data={
                        "email": email,
                    },
                ),
                500,
            )

        session.permanent = remember_user

        # -------------------------------------------------
        # Memperbarui login terakhir
        # -------------------------------------------------

        with get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET last_login_at = NOW()
                WHERE id = %s
                """,
                (user_id,),
            )

        insert_auth_log(
            activity_type="login_success",
            user_id=user_id,
            email=email,
            description="Pengguna berhasil masuk.",
        )

        commit_db()

    except (Error, RuntimeError):
        rollback_db()

        # Jika session sempat terbentuk sebelum query gagal,
        # session tersebut dibersihkan kembali.
        if current_user.is_authenticated:
            logout_user()

        current_app.logger.exception(
            "Proses login pengguna gagal."
        )

        return (
            render_template(
                "login.html",
                error=(
                    "Login belum dapat diproses. "
                    "Silakan coba kembali beberapa saat lagi."
                ),
                success=None,
                form_data={
                    "email": email,
                },
            ),
            500,
        )

    # -----------------------------------------------------
    # Menentukan halaman tujuan setelah login
    # -----------------------------------------------------

    next_destination = request.args.get("next")

    if is_safe_redirect_destination(
        next_destination
    ):
        return redirect(next_destination)

    return redirect(
        url_for("index")
    )


# =========================================================
# 11. HALAMAN FORGOT PASSWORD
# =========================================================

@auth_bp.route(
    "/forgot-password",
    methods=["GET", "POST"],
)
def forgot_password():
    """
    Menampilkan dan memproses perubahan kata sandi.

    Catatan:
    Metode ini digunakan untuk demonstrasi lokal.
    Versi publik sebaiknya menggunakan token reset
    dan verifikasi email.
    """

    if request.method == "GET":
        return render_template(
            "forgot-password.html",
            error=None,
            success=None,
        )

    # -----------------------------------------------------
    # Validasi form forgot-password
    # -----------------------------------------------------

    cleaned_data, errors = (
        validate_forgot_password_form(
            request.form
        )
    )

    if errors:
        return (
            render_template(
                "forgot-password.html",
                error=get_first_error(errors),
                success=None,
                form_data={
                    "email": cleaned_data.get(
                        "email",
                        "",
                    ),
                },
            ),
            400,
        )

    email = cleaned_data["email"]
    new_password = cleaned_data["new_password"]

    try:
        # -------------------------------------------------
        # Mencari pengguna berdasarkan email
        # -------------------------------------------------

        with get_cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    email,
                    password_hash,
                    is_active
                FROM users
                WHERE email = %s
                LIMIT 1
                """,
                (email,),
            )

            user_row = cursor.fetchone()

        if not user_row:
            return (
                render_template(
                    "forgot-password.html",
                    error=(
                        "Email tidak ditemukan pada sistem."
                    ),
                    success=None,
                    form_data={
                        "email": email,
                    },
                ),
                404,
            )

        user_id = int(user_row["id"])

        if not bool(user_row["is_active"]):
            return (
                render_template(
                    "forgot-password.html",
                    error=(
                        "Akun ini sedang tidak aktif. "
                        "Silakan hubungi tim bantuan."
                    ),
                    success=None,
                    form_data={
                        "email": email,
                    },
                ),
                403,
            )

        # -------------------------------------------------
        # Mencegah penggunaan password lama
        # -------------------------------------------------

        password_is_unchanged = check_password_hash(
            str(user_row["password_hash"]),
            new_password,
        )

        if password_is_unchanged:
            return (
                render_template(
                    "forgot-password.html",
                    error=(
                        "Kata sandi baru tidak boleh sama "
                        "dengan kata sandi sebelumnya."
                    ),
                    success=None,
                    form_data={
                        "email": email,
                    },
                ),
                400,
            )

        # -------------------------------------------------
        # Membuat hash password baru
        # -------------------------------------------------

        new_password_hash = generate_password_hash(
            new_password
        )

        # -------------------------------------------------
        # Memperbarui database
        # -------------------------------------------------

        with get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET
                    password_hash = %s,
                    password_changed_at = NOW()
                WHERE id = %s
                """,
                (
                    new_password_hash,
                    user_id,
                ),
            )

        insert_auth_log(
            activity_type="password_changed",
            user_id=user_id,
            email=email,
            description=(
                "Kata sandi pengguna berhasil diperbarui."
            ),
        )

        commit_db()

    except (Error, RuntimeError):
        rollback_db()

        current_app.logger.exception(
            "Perubahan kata sandi gagal."
        )

        return (
            render_template(
                "forgot-password.html",
                error=(
                    "Kata sandi belum dapat diperbarui. "
                    "Silakan coba kembali beberapa saat lagi."
                ),
                success=None,
                form_data={
                    "email": email,
                },
            ),
            500,
        )

    # Jika pengguna sedang login menggunakan akun yang sama,
    # session lama dihapus setelah password diganti.
    if (
        current_user.is_authenticated
        and int(current_user.id) == user_id
    ):
        # Jangan memanggil session.clear() setelah logout_user().
        # Flask-Login perlu menyimpan tanda penghapusan remember cookie
        # di session agar cookie Remember Me benar-benar dibersihkan.
        logout_user()

    return redirect(
        url_for(
            "auth.login",
            password_changed="1",
        )
    )


# =========================================================
# 12. LOGOUT
# =========================================================

@auth_bp.route(
    "/logout",
    methods=["GET", "POST"],
)
@login_required
def logout():
    """
    Menghapus session login pengguna.
    """

    user_id = int(current_user.id)
    email = str(current_user.email)

    safely_record_auth_log(
        activity_type="logout",
        user_id=user_id,
        email=email,
        description="Pengguna keluar dari akun.",
    )

    # Penting: jangan panggil session.clear() setelah logout_user().
    # Jika user login dengan Remember Me, session.clear() akan menghapus
    # tanda internal Flask-Login untuk membersihkan remember cookie.
    logout_user()

    return redirect(
        url_for(
            "auth.login",
            logout="1",
        )
    )


# =========================================================
# 13. MENDAFTARKAN AUTH KE FLASK
# =========================================================

def init_app(app: Flask) -> None:
    """
    Menghubungkan Flask-Login dan auth blueprint
    dengan aplikasi utama.

    Fungsi ini nanti dipanggil dari app.py:

        auth.init_app(app)
    """

    login_manager.init_app(app)

    app.register_blueprint(auth_bp)