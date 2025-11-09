-- Migration: Add Prospects Management Tables
-- Created: 2025-01-09
-- Description: Adds tables for prospect management, communications, activities, and import tracking

-- ============================================================================
-- CREATE ENUM TYPES
-- ============================================================================

CREATE TYPE prospectstatus AS ENUM ('NEW', 'CONTACTED', 'QUALIFIED', 'NEGOTIATION', 'CONVERTED', 'LOST');
CREATE TYPE prospectpriority AS ENUM ('HOT', 'WARM', 'COLD');
CREATE TYPE prospectsource AS ENUM ('IMPORT', 'MANUAL', 'REFERRAL', 'WEBSITE', 'EVENT', 'OTHER');

-- ============================================================================
-- CREATE PROSPECTS TABLE
-- ============================================================================

CREATE TABLE prospects (
    id SERIAL PRIMARY KEY,

    -- Basic Information
    full_name VARCHAR NOT NULL,
    email VARCHAR,
    phone VARCHAR,
    alternate_phone VARCHAR,
    company VARCHAR,
    designation VARCHAR,

    -- Lead Qualification
    status prospectstatus NOT NULL DEFAULT 'NEW',
    priority prospectpriority NOT NULL DEFAULT 'WARM',
    estimated_portfolio_value DOUBLE PRECISION,
    interested_services JSON,

    -- Source Tracking
    source prospectsource NOT NULL DEFAULT 'MANUAL',
    import_batch_id VARCHAR,
    import_file_name VARCHAR,
    import_date TIMESTAMP WITH TIME ZONE,
    referral_source VARCHAR,

    -- Assignment
    assigned_to_id INTEGER REFERENCES users(id),

    -- Conversion Tracking
    converted_to_customer_id INTEGER REFERENCES customers(id),
    converted_at TIMESTAMP WITH TIME ZONE,
    converted_by_id INTEGER REFERENCES users(id),

    -- Contact Tracking
    first_contact_date TIMESTAMP WITH TIME ZONE,
    last_contact_date TIMESTAMP WITH TIME ZONE,
    next_follow_up_date TIMESTAMP WITH TIME ZONE,
    contact_attempts INTEGER DEFAULT 0,

    -- Additional Data
    notes TEXT,
    tags JSON,
    custom_fields JSON,

    -- Standard Fields
    created_by_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- CREATE INDEXES FOR PROSPECTS
-- ============================================================================

CREATE INDEX idx_prospects_full_name ON prospects(full_name);
CREATE INDEX idx_prospects_email ON prospects(email);
CREATE INDEX idx_prospects_phone ON prospects(phone);
CREATE INDEX idx_prospects_company ON prospects(company);
CREATE INDEX idx_prospects_status ON prospects(status);
CREATE INDEX idx_prospects_priority ON prospects(priority);
CREATE INDEX idx_prospects_source ON prospects(source);
CREATE INDEX idx_prospects_import_batch_id ON prospects(import_batch_id);
CREATE INDEX idx_prospects_assigned_to_id ON prospects(assigned_to_id);
CREATE INDEX idx_prospects_last_contact_date ON prospects(last_contact_date);
CREATE INDEX idx_prospects_next_follow_up_date ON prospects(next_follow_up_date);
CREATE INDEX idx_prospects_created_at ON prospects(created_at);

-- ============================================================================
-- CREATE PROSPECT COMMUNICATIONS TABLE
-- ============================================================================

CREATE TABLE prospect_communications (
    id SERIAL PRIMARY KEY,
    prospect_id INTEGER NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),

    communication_type communicationtype NOT NULL,
    subject VARCHAR,
    content TEXT NOT NULL,
    duration_minutes INTEGER,

    communication_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_prospect_communications_prospect_id ON prospect_communications(prospect_id);
CREATE INDEX idx_prospect_communications_communication_date ON prospect_communications(communication_date);

-- ============================================================================
-- CREATE PROSPECT ACTIVITIES TABLE
-- ============================================================================

CREATE TABLE prospect_activities (
    id SERIAL PRIMARY KEY,
    prospect_id INTEGER NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),

    action VARCHAR NOT NULL,
    description VARCHAR NOT NULL,
    changes JSON,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_prospect_activities_prospect_id ON prospect_activities(prospect_id);
CREATE INDEX idx_prospect_activities_created_at ON prospect_activities(created_at);

-- ============================================================================
-- CREATE IMPORT BATCHES TABLE
-- ============================================================================

CREATE TABLE import_batches (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR UNIQUE NOT NULL,
    file_name VARCHAR NOT NULL,
    file_size INTEGER,

    total_records INTEGER NOT NULL,
    successful_imports INTEGER DEFAULT 0,
    failed_imports INTEGER DEFAULT 0,
    errors JSON,

    imported_by_id INTEGER NOT NULL REFERENCES users(id),
    mapping_used JSON,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_import_batches_batch_id ON import_batches(batch_id);
CREATE INDEX idx_import_batches_created_at ON import_batches(created_at);

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE prospects IS 'Stores potential customers (leads) before conversion to active customers';
COMMENT ON TABLE prospect_communications IS 'Tracks all communications with prospects';
COMMENT ON TABLE prospect_activities IS 'Audit trail for prospect changes and activities';
COMMENT ON TABLE import_batches IS 'Tracks bulk import operations for prospects';

COMMENT ON COLUMN prospects.custom_fields IS 'Flexible JSON field for storing additional data from imports that doesnt fit the schema';
COMMENT ON COLUMN prospects.tags IS 'JSON array of tags for categorization';
COMMENT ON COLUMN prospects.interested_services IS 'JSON array of services the prospect is interested in';
