"""
=========================================================
COMPASS CAMPUS — DATABASE.PY

File ini bertugas:
1. Membuat koneksi Flask dengan MySQL XAMPP
2. Menyediakan koneksi selama satu request
3. Menyediakan cursor database yang aman digunakan
4. Melakukan commit dan rollback transaksi
5. Menutup koneksi secara otomatis
6. Menyediakan perintah pengujian koneksi database
=========================================================
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator

import click
import mysql.connector

from flask import Flask, current_app, g
from mysql.connector import Error
from mysql.connector.connection import MySQLConnection
from mysql.connector.cursor import MySQLCursor


# =========================================================
# 1. MEMBUAT KONEKSI MYSQL
# =========================================================

def create_database_connection() -> MySQLConnection:
    """
    Membuat koneksi baru menuju database MySQL XAMPP.

    Konfigurasi koneksi diambil dari Flask config yang
    sebelumnya telah membaca file .env melalui config.py.

    Returns:
        MySQLConnection:
            Objek koneksi MySQL yang aktif.

    Raises:
        RuntimeError:
            Jika MySQL tidak dapat dihubungi.
    """

    try:
        connection = mysql.connector.connect(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
            database=current_app.config["DB_NAME"],

            # Memastikan teks Indonesia dan simbol
            # tersimpan dengan benar.
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",

            # Commit dilakukan secara sengaja oleh backend.
            autocommit=False,

            # Membatasi waktu menunggu koneksi.
            connection_timeout=10,
        )

        return connection

    except Error as error:
        current_app.logger.exception(
            "Koneksi menuju database MySQL gagal."
        )

        raise RuntimeError(
            "Database tidak dapat dihubungkan. "
            "Pastikan MySQL XAMPP aktif dan konfigurasi "
            "pada file .env sudah benar."
        ) from error


# =========================================================
# 2. MENGAMBIL KONEKSI DATABASE
# =========================================================

def get_db() -> MySQLConnection:
    """
    Mengambil koneksi database untuk request yang sedang aktif.

    Koneksi disimpan pada objek Flask `g`, sehingga tidak perlu
    membuat koneksi baru setiap kali menjalankan query dalam
    request yang sama.

    Returns:
        MySQLConnection:
            Koneksi MySQL yang aktif.
    """

    database_connection = g.get("database_connection")

    # Membuat koneksi jika belum tersedia.
    if database_connection is None:
        database_connection = create_database_connection()

        g.database_connection = database_connection

        return database_connection

    # Mencoba menghubungkan ulang jika koneksi sebelumnya putus.
    try:
        if not database_connection.is_connected():
            database_connection.reconnect(
                attempts=2,
                delay=1,
            )

    except Error as error:
        current_app.logger.exception(
            "Koneksi database terputus dan gagal disambungkan ulang."
        )

        raise RuntimeError(
            "Koneksi database terputus. "
            "Silakan coba beberapa saat lagi."
        ) from error

    return database_connection


# =========================================================
# 3. MENUTUP KONEKSI DATABASE
# =========================================================

def close_db(error: BaseException | None = None) -> None:
    """
    Menutup koneksi database setelah request Flask selesai.

    Parameter `error` disediakan karena Flask secara otomatis
    mengirimkan informasi error ke fungsi teardown.
    """

    database_connection = g.pop(
        "database_connection",
        None,
    )

    if database_connection is None:
        return

    try:
        if database_connection.is_connected():
            database_connection.close()

    except Error:
        current_app.logger.exception(
            "Terjadi masalah saat menutup koneksi database."
        )


# =========================================================
# 4. MEMBUAT CURSOR DATABASE
# =========================================================

@contextmanager
def get_cursor(
    *,
    dictionary: bool = False,
    buffered: bool = True,
) -> Generator[MySQLCursor, None, None]:
    """
    Membuat cursor dan menutupnya secara otomatis setelah dipakai.

    Args:
        dictionary:
            Jika True, hasil query berbentuk dictionary.

            Contoh:
            {
                "id": 1,
                "email": "user@example.com"
            }

        buffered:
            Jika True, hasil query dibaca ke buffer agar cursor
            dapat digunakan dengan lebih aman.

    Yields:
        MySQLCursor:
            Cursor MySQL yang siap digunakan.
    """

    database_connection = get_db()

    cursor = database_connection.cursor(
        dictionary=dictionary,
        buffered=buffered,
    )

    try:
        yield cursor

    finally:
        cursor.close()


# =========================================================
# 5. COMMIT DAN ROLLBACK
# =========================================================

def commit_db() -> None:
    """
    Menyimpan perubahan INSERT, UPDATE, atau DELETE
    secara permanen ke database.
    """

    database_connection = get_db()

    database_connection.commit()


def rollback_db() -> None:
    """
    Membatalkan perubahan apabila query database gagal.
    """

    database_connection = get_db()

    database_connection.rollback()


# =========================================================
# 6. PENGUJIAN KONEKSI
# =========================================================

def test_database_connection() -> dict[str, Any]:
    """
    Menguji koneksi dan mengambil informasi database aktif.

    Returns:
        dict:
            Nama database, versi MySQL, dan jumlah pengguna.
    """

    with get_cursor(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT
                DATABASE() AS database_name,
                VERSION() AS mysql_version
            """
        )

        database_information = cursor.fetchone()

        cursor.execute(
            """
            SELECT COUNT(*) AS total_users
            FROM users
            """
        )

        users_information = cursor.fetchone()

    return {
        "database_name": (
            database_information["database_name"]
            if database_information
            else None
        ),
        "mysql_version": (
            database_information["mysql_version"]
            if database_information
            else None
        ),
        "total_users": (
            users_information["total_users"]
            if users_information
            else 0
        ),
    }


# =========================================================
# 7. PERINTAH TERMINAL UNTUK MENGUJI DATABASE
# =========================================================

@click.command("test-db")
def test_db_command() -> None:
    """
    Perintah terminal:

    flask --app app test-db
    """

    try:
        information = test_database_connection()

        click.echo(
            "Koneksi database Compass Campus berhasil."
        )

        click.echo(
            f"Database : {information['database_name']}"
        )

        click.echo(
            f"MySQL    : {information['mysql_version']}"
        )

        click.echo(
            f"Pengguna : {information['total_users']}"
        )

    except RuntimeError as error:
        raise click.ClickException(
            str(error)
        ) from error

    except Error as error:
        current_app.logger.exception(
            "Pengujian database gagal."
        )

        raise click.ClickException(
            f"Query database gagal: {error}"
        ) from error


# =========================================================
# 8. MENDAFTARKAN DATABASE KE APLIKASI FLASK
# =========================================================

def init_app(app: Flask) -> None:
    """
    Menghubungkan fungsi database dengan aplikasi Flask.

    Fungsi ini nanti dipanggil dari app.py:

        database.init_app(app)
    """

    # Menutup koneksi setiap application context selesai.
    app.teardown_appcontext(close_db)

    # Menambahkan perintah `test-db` ke Flask CLI.
    app.cli.add_command(test_db_command)