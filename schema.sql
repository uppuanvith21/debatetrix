CREATE DATABASE IF NOT EXISTS debatetrix CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE debatetrix;

CREATE TABLE IF NOT EXISTS fact_check_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    source_name VARCHAR(160) NOT NULL,
    source_region VARCHAR(40) NOT NULL,
    source_reliability INT NOT NULL,
    title VARCHAR(700) NOT NULL,
    summary TEXT NULL,
    url VARCHAR(1200) NOT NULL,
    published_at VARCHAR(80) NULL,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags VARCHAR(500) NULL,
    UNIQUE KEY uniq_source_url (source_name, url(700)),
    INDEX idx_source_region (source_region),
    INDEX idx_title (title(255))
);
