/* =========================================================
   COMPASS CAMPUS — DATABASE SCHEMA

   Nama database : help_desk_comcam
   Digunakan untuk:
   1. Registrasi pengguna
   2. Login pengguna
   3. Perubahan kata sandi
   4. Penyimpanan informasi akun

   Catatan keamanan:
   - Password asli tidak pernah disimpan.
   - Password disimpan dalam kolom password_hash.
   - Proses hashing akan dilakukan oleh Flask/Python.
   ========================================================= */


/* =========================================================
   1. MEMBUAT DATABASE JIKA BELUM TERSEDIA
   ========================================================= */

CREATE DATABASE IF NOT EXISTS help_desk_comcam
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;


/* Memilih database yang akan digunakan */
USE help_desk_comcam;


/* =========================================================
   2. MEMBUAT TABEL USERS
   ========================================================= */

CREATE TABLE IF NOT EXISTS users (

    /* ID unik setiap pengguna */
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,

    /* Nama lengkap pengguna */
    full_name VARCHAR(100) NOT NULL,

    /* Email pengguna untuk login */
    email VARCHAR(150) NOT NULL,

    /*
       Password yang sudah di-hash oleh Flask.
       Jangan pernah menyimpan password asli.
    */
    password_hash VARCHAR(255) NOT NULL,

    /*
       Peran akun:
       student = pengguna biasa/calon mahasiswa
       admin   = pengelola sistem
    */
    role ENUM('student', 'admin')
        NOT NULL
        DEFAULT 'student',

    /*
       Status akun:
       1 = akun aktif
       0 = akun dinonaktifkan
    */
    is_active TINYINT(1)
        NOT NULL
        DEFAULT 1,

    /*
       Menyimpan waktu login terakhir.
       Nilainya masih NULL jika pengguna belum pernah login.
    */
    last_login_at DATETIME
        DEFAULT NULL,

    /*
       Menyimpan waktu terakhir password diganti.
       Nilainya diperbarui saat forgot-password berhasil.
    */
    password_changed_at DATETIME
        DEFAULT NULL,

    /* Waktu akun dibuat */
    created_at TIMESTAMP
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    /* Waktu data akun terakhir diperbarui */
    updated_at TIMESTAMP
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    /* Menentukan primary key */
    PRIMARY KEY (id),

    /*
       Email harus unik.
       Dua pengguna tidak boleh memakai email yang sama.
    */
    UNIQUE KEY uq_users_email (email),

    /* Index untuk mempercepat pencarian berdasarkan status */
    INDEX idx_users_active (is_active),

    /* Index untuk mempercepat pencarian berdasarkan role */
    INDEX idx_users_role (role)

) ENGINE=InnoDB
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;


/* =========================================================
   3. MEMBUAT TABEL AUTH_LOGS
   ========================================================= */

/*
   Tabel ini mencatat aktivitas autentikasi penting, seperti:
   - Register berhasil
   - Login berhasil
   - Login gagal
   - Perubahan password

   Tabel ini tidak menyimpan password pengguna.
*/

CREATE TABLE IF NOT EXISTS auth_logs (

    /* ID unik setiap catatan aktivitas */
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    /*
       ID pengguna yang melakukan aktivitas.
       Dapat bernilai NULL apabila login gagal karena
       email tidak terdaftar.
    */
    user_id INT UNSIGNED DEFAULT NULL,

    /*
       Email disimpan untuk membantu pencatatan login gagal.
       Tidak digunakan sebagai pengganti relasi user_id.
    */
    email VARCHAR(150) DEFAULT NULL,

    /*
       Jenis aktivitas autentikasi.
    */
    activity_type ENUM(
        'register_success',
        'register_failed',
        'login_success',
        'login_failed',
        'password_changed',
        'logout'
    ) NOT NULL,

    /* Informasi tambahan yang aman untuk dicatat */
    description VARCHAR(255) DEFAULT NULL,

    /*
       Alamat IP pengguna.
       Panjang 45 karakter mendukung IPv4 dan IPv6.
    */
    ip_address VARCHAR(45) DEFAULT NULL,

    /* Informasi browser atau perangkat */
    user_agent VARCHAR(255) DEFAULT NULL,

    /* Waktu aktivitas terjadi */
    created_at TIMESTAMP
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),

    /* Index agar riwayat pengguna lebih cepat dicari */
    INDEX idx_auth_logs_user_id (user_id),

    /* Index untuk pencarian berdasarkan email */
    INDEX idx_auth_logs_email (email),

    /* Index untuk pencarian berdasarkan jenis aktivitas */
    INDEX idx_auth_logs_activity (activity_type),

    /* Index untuk pencarian berdasarkan waktu */
    INDEX idx_auth_logs_created_at (created_at),

    /*
       Relasi ke tabel users.
       Jika akun dihapus, user_id pada log menjadi NULL
       agar riwayat sistem tetap tersimpan.
    */
    CONSTRAINT fk_auth_logs_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL

) ENGINE=InnoDB
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;


/* =========================================================
   4. MEMBUAT VIEW INFORMASI PENGGUNA
   ========================================================= */

/*
   View ini menampilkan informasi pengguna tanpa password_hash.
   Dapat dipakai oleh halaman admin atau dashboard nanti.
*/

CREATE OR REPLACE VIEW user_public_information AS
SELECT
    id,
    full_name,
    email,
    role,
    is_active,
    last_login_at,
    password_changed_at,
    created_at,
    updated_at
FROM users;


/* =========================================================
   5. VERIFIKASI STRUKTUR
   ========================================================= */

/*
   Query berikut akan menampilkan tabel yang berhasil dibuat.
*/

SHOW TABLES;


/*
   Menampilkan struktur tabel users.
*/

DESCRIBE users;


/*
   Menampilkan struktur tabel auth_logs.
*/

DESCRIBE auth_logs;