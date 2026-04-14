-- Clio M1 初始化脚本：7张核心表 + 索引
-- PostgreSQL 16

-- 1. users 表
CREATE TABLE IF NOT EXISTS users (
    id            BIGSERIAL PRIMARY KEY,
    email         VARCHAR(255) NOT NULL,
    username      VARCHAR(100),
    password_hash VARCHAR(255),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- 2. conversations 表
CREATE TABLE IF NOT EXISTS conversations (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title         VARCHAR(500),
    status        VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_conv_user_id    ON conversations (user_id);
CREATE INDEX IF NOT EXISTS idx_conv_updated_at ON conversations (updated_at DESC);

-- 3. messages 表
CREATE TABLE IF NOT EXISTS messages (
    id              BIGSERIAL PRIMARY KEY,
    conversation_id  BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL,
    content         TEXT,
    token_count     INTEGER,
    model           VARCHAR(100),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_msg_conv_id_created ON messages (conversation_id, created_at);

-- 4. fact_check_reports 表
CREATE TABLE IF NOT EXISTS fact_check_reports (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status      VARCHAR(20) NOT NULL DEFAULT 'pending',
    source_text TEXT,
    result_text TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_fcr_user_id ON fact_check_reports (user_id);
CREATE INDEX IF NOT EXISTS idx_fcr_status  ON fact_check_reports (status);

-- 5. fact_check_items 表
CREATE TABLE IF NOT EXISTS fact_check_items (
    id          BIGSERIAL PRIMARY KEY,
    report_id   BIGINT NOT NULL REFERENCES fact_check_reports(id) ON DELETE CASCADE,
    claim       TEXT,
    verdict     VARCHAR(50),
    explanation TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_fci_report_id ON fact_check_items (report_id);

-- 6. feedbacks 表
CREATE TABLE IF NOT EXISTS feedbacks (
    id          BIGSERIAL PRIMARY KEY,
    message_id  BIGINT REFERENCES messages(id) ON DELETE SET NULL,
    user_id     BIGINT REFERENCES users(id) ON DELETE CASCADE,
    rating      VARCHAR(20),
    comment     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_fb_msg_id ON feedbacks (message_id);

-- 7. analytics_events 表
CREATE TABLE IF NOT EXISTS analytics_events (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT REFERENCES users(id) ON DELETE SET NULL,
    event_type  VARCHAR(100) NOT NULL,
    event_data  JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ae_type_created ON analytics_events (event_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ae_user_created ON analytics_events (user_id, created_at DESC);
