/* =========================================================
   COMPASS CAMPUS - SCHEMA-5 BABAK 5 CAMPUS DETAIL

   Fungsi file:
   1. Membuat tabel campuses.
   2. Membuat tabel study_programs.
   3. Mengisi data awal Universitas Esa Unggul dan beberapa prodi contoh.
   4. Aman dijalankan berulang karena memakai IF NOT EXISTS dan INSERT IGNORE.

   Jalankan setelah schema-2.sql, schema-3.sql, dan schema-4.sql.
   ========================================================= */

USE help_desk_comcam;

CREATE TABLE IF NOT EXISTS campuses (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    slug VARCHAR(120) NOT NULL,
    campus_name VARCHAR(160) NOT NULL,
    city VARCHAR(100) NOT NULL,
    address VARCHAR(255) DEFAULT NULL,
    website VARCHAR(180) DEFAULT NULL,
    campus_type VARCHAR(100) DEFAULT NULL,
    description TEXT DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_campuses_slug (slug)
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS study_programs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    campus_id BIGINT UNSIGNED NOT NULL,
    slug VARCHAR(120) NOT NULL,
    program_name VARCHAR(160) NOT NULL,
    faculty VARCHAR(160) NOT NULL,
    degree VARCHAR(40) NOT NULL DEFAULT 'S1',
    accreditation VARCHAR(80) DEFAULT 'Dalam pendataan',
    learning_mode VARCHAR(80) DEFAULT 'Reguler',
    duration VARCHAR(80) DEFAULT '8 Semester',
    tuition_range VARCHAR(180) DEFAULT NULL,
    summary TEXT NOT NULL,
    curriculum_points TEXT DEFAULT NULL,
    career_paths TEXT DEFAULT NULL,
    skills TEXT DEFAULT NULL,
    facilities TEXT DEFAULT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_study_programs_slug (slug),
    INDEX idx_study_programs_campus_id (campus_id),
    INDEX idx_study_programs_faculty (faculty),
    INDEX idx_study_programs_active (is_active),
    CONSTRAINT fk_study_programs_campus
        FOREIGN KEY (campus_id)
        REFERENCES campuses(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT IGNORE INTO campuses (
    id,
    slug,
    campus_name,
    city,
    address,
    website,
    campus_type,
    description
)
VALUES (
    1,
    'universitas-esa-unggul',
    'Universitas Esa Unggul',
    'Bekasi',
    'Harapan Indah, Bekasi',
    'https://www.esaunggul.ac.id',
    'Perguruan Tinggi Swasta',
    'Kampus dengan pilihan program studi lintas bidang yang dapat dijelajahi oleh calon mahasiswa baru.'
);

INSERT IGNORE INTO study_programs (
    campus_id,
    slug,
    program_name,
    faculty,
    degree,
    accreditation,
    learning_mode,
    duration,
    tuition_range,
    summary,
    curriculum_points,
    career_paths,
    skills,
    facilities
)
VALUES
(
    1,
    'teknik-informatika',
    'Teknik Informatika',
    'Fakultas Ilmu Komputer',
    'S1',
    'Baik Sekali',
    'Reguler',
    '8 Semester',
    'Informasi biaya mengikuti kebijakan kampus',
    'Program studi untuk mahasiswa yang tertarik pada pemrograman, rekayasa perangkat lunak, kecerdasan buatan, data, dan pengembangan sistem digital.',
    'Dasar pemrograman dan struktur data;Basis data dan analisis sistem;Rekayasa perangkat lunak;Jaringan komputer dan keamanan;Kecerdasan buatan dan data science',
    'Software Developer;Backend Developer;Data Analyst;AI Engineer;System Analyst',
    'Problem solving;Logika algoritma;Pemrograman;Analisis data;Kolaborasi tim',
    'Laboratorium komputer;Akses pembelajaran digital;Dukungan dosen dan konselor akademik;Kegiatan pengembangan minat mahasiswa'
),
(
    1,
    'sistem-informasi',
    'Sistem Informasi',
    'Fakultas Ilmu Komputer',
    'S1',
    'Baik Sekali',
    'Reguler',
    '8 Semester',
    'Informasi biaya mengikuti kebijakan kampus',
    'Program studi yang menghubungkan teknologi, proses bisnis, analisis sistem, dan kebutuhan organisasi.',
    'Analisis proses bisnis;Perancangan sistem informasi;Basis data;Manajemen proyek TI;Enterprise system',
    'Business Analyst;System Analyst;IT Project Officer;Product Owner;Database Administrator',
    'Analisis kebutuhan;Komunikasi bisnis;Pemodelan sistem;Manajemen data;Dokumentasi sistem',
    'Laboratorium komputer;Studi kasus bisnis digital;Simulasi proyek sistem;Akses materi digital'
),
(
    1,
    'manajemen',
    'Manajemen',
    'Fakultas Ekonomi dan Bisnis',
    'S1',
    'Baik Sekali',
    'Reguler',
    '8 Semester',
    'Informasi biaya mengikuti kebijakan kampus',
    'Program studi untuk memahami pengelolaan organisasi, bisnis, pemasaran, sumber daya manusia, dan strategi.',
    'Pengantar manajemen;Manajemen pemasaran;Manajemen keuangan;Manajemen SDM;Kewirausahaan',
    'Management Trainee;Marketing Officer;HR Officer;Business Development;Entrepreneur',
    'Kepemimpinan;Analisis bisnis;Komunikasi;Perencanaan strategi;Negosiasi',
    'Kelas diskusi;Studi kasus bisnis;Kegiatan kewirausahaan;Bimbingan akademik'
),
(
    1,
    'desain-komunikasi-visual',
    'Desain Komunikasi Visual',
    'Fakultas Desain dan Industri Kreatif',
    'S1',
    'Dalam pendataan',
    'Reguler',
    '8 Semester',
    'Informasi biaya mengikuti kebijakan kampus',
    'Program studi untuk pengguna yang menyukai desain, visual branding, ilustrasi, media digital, dan komunikasi visual.',
    'Dasar desain;Tipografi;Ilustrasi digital;Branding;Desain UI dan media interaktif',
    'Graphic Designer;UI Designer;Brand Designer;Illustrator;Creative Content Designer',
    'Kreativitas visual;Komposisi;Penggunaan software desain;Storytelling visual;Riset pengguna',
    'Studio desain;Perangkat desain digital;Galeri karya;Pendampingan portofolio'
),
(
    1,
    'ilmu-komunikasi',
    'Ilmu Komunikasi',
    'Fakultas Ilmu Komunikasi',
    'S1',
    'Baik Sekali',
    'Reguler',
    '8 Semester',
    'Informasi biaya mengikuti kebijakan kampus',
    'Program studi untuk memahami strategi komunikasi, media, public relations, konten, dan komunikasi digital.',
    'Dasar komunikasi;Public relations;Komunikasi digital;Produksi konten;Riset media',
    'Public Relations Officer;Content Strategist;Social Media Specialist;Media Planner;Communication Officer',
    'Public speaking;Menulis;Riset audiens;Produksi konten;Manajemen komunikasi',
    'Studio media;Ruang praktik komunikasi;Kegiatan produksi konten;Bimbingan portofolio'
),
(
    1,
    'akuntansi',
    'Akuntansi',
    'Fakultas Ekonomi dan Bisnis',
    'S1',
    'Baik Sekali',
    'Reguler',
    '8 Semester',
    'Informasi biaya mengikuti kebijakan kampus',
    'Program studi untuk mempelajari pencatatan keuangan, audit, perpajakan, dan pelaporan bisnis.',
    'Akuntansi dasar;Akuntansi keuangan;Perpajakan;Audit;Sistem informasi akuntansi',
    'Accounting Staff;Auditor;Tax Officer;Finance Officer;Budget Analyst',
    'Ketelitian;Analisis angka;Etika profesi;Pelaporan keuangan;Penggunaan software akuntansi',
    'Laboratorium akuntansi;Studi kasus laporan keuangan;Simulasi pajak;Bimbingan akademik'
);

CREATE OR REPLACE VIEW campus_program_overview AS
SELECT
    sp.id,
    sp.slug AS program_slug,
    sp.program_name,
    sp.faculty,
    sp.degree,
    sp.accreditation,
    sp.learning_mode,
    sp.duration,
    c.campus_name,
    c.city,
    c.campus_type
FROM study_programs sp
INNER JOIN campuses c
    ON c.id = sp.campus_id
WHERE sp.is_active = 1;

/* ---------------------------------------------------------
   Contoh cek cepat:

   SELECT *
   FROM campus_program_overview
   ORDER BY faculty, program_name;
   --------------------------------------------------------- */
