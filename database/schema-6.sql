-- =========================================================
-- COMPASS CAMPUS - SCHEMA BABAK 6
-- Modul: Pemetaan Minat dan Rekomendasi Program Studi
-- =========================================================

CREATE TABLE IF NOT EXISTS user_interest_profiles (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    preferred_field VARCHAR(50) NOT NULL,
    favorite_subject VARCHAR(50) NOT NULL,
    preferred_activity VARCHAR(50) NOT NULL,
    learning_style VARCHAR(50) NOT NULL,
    career_goal VARCHAR(50) NOT NULL,
    notes TEXT DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_interest_user (user_id),
    CONSTRAINT fk_interest_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_recommendation_results (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    profile_id BIGINT UNSIGNED NOT NULL,
    user_id INT UNSIGNED NOT NULL,
    rank_order TINYINT UNSIGNED NOT NULL,
    program_slug VARCHAR(120) NOT NULL,
    program_name VARCHAR(160) NOT NULL,
    campus_name VARCHAR(160) NOT NULL,
    campus_city VARCHAR(100) DEFAULT NULL,
    score TINYINT UNSIGNED NOT NULL DEFAULT 0,
    reason TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_recommendation_user (user_id),
    KEY idx_recommendation_profile (profile_id),
    CONSTRAINT fk_recommendation_profile
        FOREIGN KEY (profile_id) REFERENCES user_interest_profiles(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_recommendation_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
