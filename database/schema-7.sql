/* =========================================================
   COMPASS CAMPUS - SCHEMA-7 BABAK 7 PROFIL PENGGUNA

   File ini menambahkan tabel profil tambahan untuk user.
   Tabel users tetap dipakai untuk login, email, role, dan password.
   ========================================================= */

USE help_desk_comcam;

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
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
