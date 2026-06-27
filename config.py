"""
=========================================================
COMPASS CAMPUS — CONFIG.PY

File ini bertugas:
1. Membaca konfigurasi dari file .env
2. Menyediakan konfigurasi Flask
3. Menyediakan konfigurasi database MySQL
4. Mengatur keamanan session pengguna
=========================================================
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv


# =========================================================
# 1. MENENTUKAN LOKASI FOLDER PROYEK
# =========================================================

# Lokasi folder tempat config.py berada.
BASE_DIR = Path(__file__).resolve().parent

# Lokasi file .env.
ENV_FILE = BASE_DIR / ".env"

# Membaca seluruh variabel dari file .env.
load_dotenv(ENV_FILE)


# =========================================================
# 2. FUNGSI MEMBACA NILAI BOOLEAN
# =========================================================

def get_env_boolean(
    variable_name: str,
    default: bool = False,
) -> bool:
    """
    Mengubah nilai string dari .env menjadi boolean.

    Nilai berikut dianggap True:
    true, 1, yes, on

    Contoh:
    FLASK_DEBUG=True
    """

    value = os.getenv(variable_name)

    if value is None:
        return default

    return value.strip().lower() in {
        "true",
        "1",
        "yes",
        "on",
    }


# =========================================================
# 3. KONFIGURASI UTAMA FLASK
# =========================================================

class Config:
    """
    Konfigurasi utama aplikasi Compass Campus.
    """

    # -----------------------------------------------------
    # Konfigurasi keamanan Flask
    # -----------------------------------------------------

    SECRET_KEY = os.getenv(
        "FLASK_SECRET_KEY",
        "",
    )

    DEBUG = get_env_boolean(
        "FLASK_DEBUG",
        default=False,
    )

    # Cookie session tidak dapat dibaca melalui JavaScript.
    SESSION_COOKIE_HTTPONLY = True

    # Membantu mengurangi risiko CSRF.
    SESSION_COOKIE_SAMESITE = "Lax"

    # Secure dibuat False karena proyek masih menggunakan
    # localhost tanpa HTTPS.
    # Saat website memakai HTTPS, ubah menjadi True.
    SESSION_COOKIE_SECURE = False

    # Session login dapat bertahan selama tujuh hari.
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)


    # -----------------------------------------------------
    # Konfigurasi database MySQL XAMPP
    # -----------------------------------------------------

    DB_HOST = os.getenv(
        "DB_HOST",
        "127.0.0.1",
    )

    DB_PORT = int(
        os.getenv(
            "DB_PORT",
            "3306",
        )
    )

    DB_USER = os.getenv(
        "DB_USER",
        "root",
    )

    DB_PASSWORD = os.getenv(
        "DB_PASSWORD",
        "",
    )

    DB_NAME = os.getenv(
        "DB_NAME",
        "help_desk_comcam",
    )


    # -----------------------------------------------------
    # Konfigurasi tambahan aplikasi
    # -----------------------------------------------------

    # Batas maksimum unggahan sebesar 5 MB.
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # Mempertahankan urutan data JSON.
    JSON_SORT_KEYS = False


# =========================================================
# 4. VALIDASI KONFIGURASI
# =========================================================

def validate_configuration() -> None:
    """
    Memastikan konfigurasi penting sudah tersedia.

    Fungsi ini nantinya dipanggil oleh app.py saat aplikasi
    mulai dijalankan.
    """

    if not Config.SECRET_KEY:
        raise RuntimeError(
            "FLASK_SECRET_KEY belum diisi pada file .env."
        )

    if not Config.DB_NAME:
        raise RuntimeError(
            "DB_NAME belum diisi pada file .env."
        )

# =====================================================
# 5. KONFIGURASI CSRF
# =====================================================

# Mengaktifkan perlindungan seluruh request POST.
WTF_CSRF_ENABLED = True

# Token berlaku selama satu jam.
WTF_CSRF_TIME_LIMIT = timedelta(hours=1)