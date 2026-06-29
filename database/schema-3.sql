/* =========================================================
   COMPASS CAMPUS - SCHEMA-3 BABAK 4 ADMIN HELP DESK

   Fungsi file:
   1. Menyiapkan view tambahan untuk Panel Admin.
   2. Menjaga tabel Babak 3 tetap aman jika file dijalankan ulang.
   3. Memberi catatan cara menjadikan user sebagai admin.

   Jalankan di phpMyAdmin setelah schema-2.sql.
   ========================================================= */

USE help_desk_comcam;

/* ---------------------------------------------------------
   Pastikan tabel tiket Babak 3 tetap tersedia.
   --------------------------------------------------------- */

CREATE TABLE IF NOT EXISTS help_tickets (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    ticket_code VARCHAR(24) NOT NULL,
    category ENUM('program_studi','pemetaan_minat','akun','data_kampus','lainnya') NOT NULL DEFAULT 'lainnya',
    subject VARCHAR(120) NOT NULL,
    message TEXT NOT NULL,
    priority ENUM('low','normal','high') NOT NULL DEFAULT 'normal',
    status ENUM('dikirim','diproses','selesai') NOT NULL DEFAULT 'dikirim',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
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
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ticket_messages (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    ticket_id BIGINT UNSIGNED NOT NULL,
    sender_id INT UNSIGNED DEFAULT NULL,
    sender_type ENUM('user','admin','system') NOT NULL DEFAULT 'user',
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
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

/* ---------------------------------------------------------
   View untuk memudahkan inspeksi tiket dari sisi admin.
   Backend Flask tetap memakai query langsung agar lebih fleksibel.
   --------------------------------------------------------- */

CREATE OR REPLACE VIEW admin_ticket_overview AS
SELECT
    t.id,
    t.ticket_code,
    t.category,
    t.subject,
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
GROUP BY
    t.id,
    t.ticket_code,
    t.category,
    t.subject,
    t.priority,
    t.status,
    t.created_at,
    t.updated_at,
    t.closed_at,
    u.full_name,
    u.email;

/* ---------------------------------------------------------
   Cara membuat akun admin saat development:

   1. Register akun biasa lewat website.
   2. Buka phpMyAdmin.
   3. Jalankan contoh query berikut dengan email akunmu.

   UPDATE users
   SET role = 'admin'
   WHERE email = 'email_kamu@gmail.com';
   --------------------------------------------------------- */
