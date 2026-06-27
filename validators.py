"""
=========================================================
COMPASS CAMPUS — VALIDATORS.PY

File ini bertugas:
1. Membersihkan input dari form
2. Memvalidasi nama lengkap
3. Memvalidasi dan menormalisasi email
4. Memvalidasi kata sandi
5. Memeriksa konfirmasi kata sandi
6. Memvalidasi form register
7. Memvalidasi form login
8. Memvalidasi form forgot-password

PENTING:
- Validasi JavaScript hanya membantu tampilan pengguna.
- Seluruh input wajib divalidasi kembali oleh Python.
- Password tidak pernah dicetak atau disimpan di file ini.
=========================================================
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from email_validator import (
    EmailNotValidError,
    validate_email as validate_email_library,
)


# =========================================================
# 1. KONSTANTA VALIDASI
# =========================================================

MIN_FULL_NAME_LENGTH = 3
MAX_FULL_NAME_LENGTH = 100

MAX_EMAIL_LENGTH = 150

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


# =========================================================
# 2. FUNGSI DASAR PEMBERSIHAN INPUT
# =========================================================

def clean_text(value: Any) -> str:
    """
    Mengubah input menjadi string dan menghapus spasi
    di awal maupun akhir.

    Args:
        value:
            Nilai dari form.

    Returns:
        str:
            Teks yang sudah dibersihkan.
    """

    if value is None:
        return ""

    return str(value).strip()


def normalize_full_name(value: Any) -> str:
    """
    Membersihkan nama dan menggabungkan spasi berlebihan.

    Contoh:
        "  Marcell   Wijaya  "
        menjadi:
        "Marcell Wijaya"
    """

    full_name = clean_text(value)

    return " ".join(full_name.split())


# =========================================================
# 3. VALIDASI NAMA LENGKAP
# =========================================================

def validate_full_name(value: Any) -> tuple[str, str | None]:
    """
    Memvalidasi nama lengkap pengguna.

    Returns:
        tuple:
            (
                nama_yang_sudah_dibersihkan,
                pesan_error_atau_None
            )
    """

    full_name = normalize_full_name(value)

    if not full_name:
        return "", "Nama lengkap wajib diisi."

    if len(full_name) < MIN_FULL_NAME_LENGTH:
        return (
            full_name,
            "Nama lengkap minimal terdiri dari 3 karakter.",
        )

    if len(full_name) > MAX_FULL_NAME_LENGTH:
        return (
            full_name,
            "Nama lengkap maksimal terdiri dari 100 karakter.",
        )

    # Karakter nama yang diperbolehkan:
    # - Huruf
    # - Spasi
    # - Tanda titik
    # - Apostrof
    # - Tanda hubung

    allowed_special_characters = {
        " ",
        ".",
        "'",
        "’",
        "-",
    }

    for character in full_name:
        if (
            not character.isalpha()
            and character not in allowed_special_characters
        ):
            return (
                full_name,
                "Nama lengkap hanya boleh berisi huruf, "
                "spasi, titik, apostrof, atau tanda hubung.",
            )

    alphabetic_character_count = sum(
        character.isalpha()
        for character in full_name
    )

    if alphabetic_character_count < 2:
        return (
            full_name,
            "Masukkan nama lengkap yang valid.",
        )

    return full_name, None

# =========================================================
# 4. VALIDASI EMAIL
# =========================================================

def validate_email_address(
    value: Any,
) -> tuple[str, str | None]:
    """
    Memvalidasi format email dan menghasilkan email
    yang sudah dinormalisasi.

    Pemeriksaan DNS tidak digunakan karena proyek masih
    dijalankan secara lokal dan tidak mengirim email.

    Returns:
        tuple:
            (
                email_normal,
                pesan_error_atau_None
            )
    """

    email = clean_text(value)

    if not email:
        return "", "Email wajib diisi."

    if len(email) > MAX_EMAIL_LENGTH:
        return (
            email,
            "Email maksimal terdiri dari 150 karakter.",
        )

    try:
        email_information = validate_email_library(
            email,
            check_deliverability=False,
        )

        normalized_email = email_information.normalized

    except EmailNotValidError:
        return (
            email,
            "Masukkan format email yang valid.",
        )

    if len(normalized_email) > MAX_EMAIL_LENGTH:
        return (
            normalized_email,
            "Email maksimal terdiri dari 150 karakter.",
        )

    return normalized_email, None


# =========================================================
# 5. VALIDASI KATA SANDI
# =========================================================

def validate_password(
    value: Any,
    *,
    field_name: str = "Kata sandi",
) -> tuple[str, str | None]:
    """
    Memvalidasi kata sandi baru atau kata sandi register.

    Password tidak di-strip karena spasi dapat menjadi
    bagian dari kata sandi pengguna.

    Args:
        value:
            Kata sandi dari form.

        field_name:
            Nama field untuk pesan kesalahan.

    Returns:
        tuple:
            (
                password,
                pesan_error_atau_None
            )
    """

    if value is None:
        password = ""
    else:
        password = str(value)

    if not password:
        return "", f"{field_name} wajib diisi."

    if password.strip() == "":
        return (
            password,
            f"{field_name} tidak boleh hanya berisi spasi.",
        )

    if len(password) < MIN_PASSWORD_LENGTH:
        return (
            password,
            f"{field_name} minimal terdiri dari "
            f"{MIN_PASSWORD_LENGTH} karakter.",
        )

    if len(password) > MAX_PASSWORD_LENGTH:
        return (
            password,
            f"{field_name} maksimal terdiri dari "
            f"{MAX_PASSWORD_LENGTH} karakter.",
        )

    prohibited_characters = {
        "\n",
        "\r",
        "\t",
        "\0",
    }

    if any(
        character in password
        for character in prohibited_characters
    ):
        return (
            password,
            f"{field_name} mengandung karakter yang "
            "tidak diperbolehkan.",
        )

    return password, None


# =========================================================
# 6. VALIDASI PASSWORD UNTUK LOGIN
# =========================================================

def validate_login_password(
    value: Any,
) -> tuple[str, str | None]:
    """
    Memastikan kata sandi login telah diisi.

    Pemeriksaan benar atau salahnya password tidak dilakukan
    di sini. Password akan dibandingkan dengan password_hash
    oleh auth.py.
    """

    if value is None:
        password = ""
    else:
        password = str(value)

    if not password:
        return "", "Kata sandi wajib diisi."

    if len(password) > MAX_PASSWORD_LENGTH:
        return (
            password,
            "Kata sandi maksimal terdiri dari "
            f"{MAX_PASSWORD_LENGTH} karakter.",
        )

    return password, None


# =========================================================
# 7. VALIDASI KONFIRMASI PASSWORD
# =========================================================

def validate_password_confirmation(
    password: str,
    confirmation_value: Any,
) -> tuple[str, str | None]:
    """
    Memastikan konfirmasi kata sandi telah diisi
    dan sama dengan kata sandi utama.
    """

    if confirmation_value is None:
        confirmation = ""
    else:
        confirmation = str(confirmation_value)

    if not confirmation:
        return (
            "",
            "Konfirmasi kata sandi wajib diisi.",
        )

    if confirmation != password:
        return (
            confirmation,
            "Konfirmasi kata sandi tidak sama.",
        )

    return confirmation, None


# =========================================================
# 8. VALIDASI CHECKBOX PERSETUJUAN
# =========================================================

def validate_agreement(value: Any) -> str | None:
    """
    Memastikan checkbox persetujuan pada register
    telah dicentang.
    """

    accepted_values = {
        "1",
        "true",
        "yes",
        "on",
        "accepted",
    }

    agreement_value = clean_text(value).lower()

    if agreement_value not in accepted_values:
        return (
            "Kamu harus menyetujui Syarat dan Ketentuan "
            "serta Kebijakan Privasi."
        )

    return None


# =========================================================
# 9. VALIDASI FORM REGISTER
# =========================================================

def validate_register_form(
    form_data: Mapping[str, Any],
) -> tuple[dict[str, str], dict[str, str]]:
    """
    Memvalidasi seluruh data dari halaman register.

    Field HTML yang digunakan:
    - full_name
    - email
    - password
    - confirm_password
    - agreement

    Returns:
        tuple:
            (
                data_yang_sudah_dibersihkan,
                kumpulan_error
            )
    """

    errors: dict[str, str] = {}
    cleaned_data: dict[str, str] = {}

    full_name, full_name_error = validate_full_name(
        form_data.get("full_name")
    )

    email, email_error = validate_email_address(
        form_data.get("email")
    )

    password, password_error = validate_password(
        form_data.get("password"),
        field_name="Kata sandi",
    )

    _, confirmation_error = validate_password_confirmation(
        password,
        form_data.get("confirm_password"),
    )

    agreement_error = validate_agreement(
        form_data.get("agreement")
    )

    if full_name_error:
        errors["full_name"] = full_name_error

    if email_error:
        errors["email"] = email_error

    if password_error:
        errors["password"] = password_error

    if confirmation_error:
        errors["confirm_password"] = confirmation_error

    if agreement_error:
        errors["agreement"] = agreement_error

    cleaned_data["full_name"] = full_name
    cleaned_data["email"] = email
    cleaned_data["password"] = password

    return cleaned_data, errors


# =========================================================
# 10. VALIDASI FORM LOGIN
# =========================================================

def validate_login_form(
    form_data: Mapping[str, Any],
) -> tuple[dict[str, str], dict[str, str]]:
    """
    Memvalidasi data dari halaman login.

    Field HTML yang digunakan:
    - email
    - password
    """

    errors: dict[str, str] = {}
    cleaned_data: dict[str, str] = {}

    email, email_error = validate_email_address(
        form_data.get("email")
    )

    password, password_error = validate_login_password(
        form_data.get("password")
    )

    if email_error:
        errors["email"] = email_error

    if password_error:
        errors["password"] = password_error

    cleaned_data["email"] = email
    cleaned_data["password"] = password

    return cleaned_data, errors


# =========================================================
# 11. VALIDASI FORM FORGOT PASSWORD
# =========================================================

def validate_forgot_password_form(
    form_data: Mapping[str, Any],
) -> tuple[dict[str, str], dict[str, str]]:
    """
    Memvalidasi data dari halaman forgot-password.

    Field HTML yang digunakan:
    - email
    - new_password
    - confirm_password
    """

    errors: dict[str, str] = {}
    cleaned_data: dict[str, str] = {}

    email, email_error = validate_email_address(
        form_data.get("email")
    )

    new_password, password_error = validate_password(
        form_data.get("new_password"),
        field_name="Kata sandi baru",
    )

    _, confirmation_error = validate_password_confirmation(
        new_password,
        form_data.get("confirm_password"),
    )

    if email_error:
        errors["email"] = email_error

    if password_error:
        errors["new_password"] = password_error

    if confirmation_error:
        errors["confirm_password"] = confirmation_error

    cleaned_data["email"] = email
    cleaned_data["new_password"] = new_password

    return cleaned_data, errors


# =========================================================
# 12. MENGAMBIL PESAN ERROR PERTAMA
# =========================================================

def get_first_error(
    errors: Mapping[str, str],
    default_message: str = "Periksa kembali data yang dimasukkan.",
) -> str:
    """
    Mengambil pesan error pertama untuk ditampilkan
    sebagai alert pada halaman.
    """

    if not errors:
        return default_message

    return next(iter(errors.values()))


# =========================================================
# 13. MEMERIKSA HASIL VALIDASI
# =========================================================

def validation_is_successful(
    errors: Mapping[str, str],
) -> bool:
    """
    Menghasilkan True apabila tidak ada pesan kesalahan.
    """

    return not bool(errors)