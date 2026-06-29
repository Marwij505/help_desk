/* =========================================================
   COMPASS CAMPUS - SCHEMA-2 BABAK 3 TICKETING

   Jalankan file ini di phpMyAdmin jika database lama sudah ada.
   File ini hanya menambahkan tabel Help Desk Ticketing.
   Aman dijalankan lebih dari satu kali karena memakai IF NOT EXISTS.
   ========================================================= */

USE help_desk_comcam;

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

CREATE OR REPLACE VIEW user_ticket_summary AS
SELECT
    user_id,
    COUNT(*) AS total_tickets,
    SUM(status != 'selesai') AS active_tickets,
    SUM(status = 'dikirim') AS submitted_tickets,
    SUM(status = 'diproses') AS in_progress_tickets,
    SUM(status = 'selesai') AS closed_tickets
FROM help_tickets
GROUP BY user_id;
