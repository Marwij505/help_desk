/* =========================================================
   COMPASS CAMPUS - SCHEMA-4 PATCH BABAK 4
   STUDENT TICKET DETAIL + REMEMBER ME FIX

   Fungsi file:
   1. Menyediakan view untuk melihat balasan admin dari sisi student.
   2. Tidak menghapus data lama.
   3. Aman dijalankan setelah schema-2.sql dan schema-3.sql.

   Catatan:
   - Tidak ada tabel baru wajib.
   - Percakapan tetap memakai tabel ticket_messages.
   - Student membaca balasan admin lewat route /ticket/<id>.
   ========================================================= */

USE help_desk_comcam;

/* ---------------------------------------------------------
   Pastikan tabel utama Babak 3 tetap tersedia.
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
   View ringkas agar balasan admin bisa dicek dari phpMyAdmin.
   Backend tetap memakai query langsung di app.py.
   --------------------------------------------------------- */

CREATE OR REPLACE VIEW user_ticket_reply_summary AS
SELECT
    t.id,
    t.user_id,
    t.ticket_code,
    t.subject,
    t.category,
    t.priority,
    t.status,
    t.created_at,
    t.updated_at,
    t.closed_at,
    COUNT(tm.id) AS total_messages,
    COALESCE(SUM(tm.sender_type = 'admin'), 0) AS total_admin_replies,
    MAX(CASE WHEN tm.sender_type = 'admin' THEN tm.created_at END) AS last_admin_reply_at
FROM help_tickets t
LEFT JOIN ticket_messages tm
    ON tm.ticket_id = t.id
GROUP BY
    t.id,
    t.user_id,
    t.ticket_code,
    t.subject,
    t.category,
    t.priority,
    t.status,
    t.created_at,
    t.updated_at,
    t.closed_at;

/* ---------------------------------------------------------
   Cara cek cepat:

   SELECT *
   FROM user_ticket_reply_summary
   ORDER BY updated_at DESC;
   --------------------------------------------------------- */
