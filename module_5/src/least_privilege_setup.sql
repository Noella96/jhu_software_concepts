-- ==============================================================================
-- Module 5: Database Hardening & Least-Privilege Role Configuration
-- Johns Hopkins University - Software Concepts (EN.605.601)
-- ==============================================================================
-- This SQL script establishes a hardened, least-privilege PostgreSQL user
-- ('gradcafe_app_user') adhering to the Principle of Least Privilege (PoLP).
--
-- Security Controls Implemented:
-- 1. Non-Superuser: Role lacks SUPERUSER, CREATEDB, and CREATEROLE permissions.
-- 2. Scoped Access: Grants only CONNECT on database and USAGE on schema public.
-- 3. Restricted DML: Only SELECT, INSERT, and UPDATE permissions on 'applicants'.
-- 4. Destructive DDL Prohibited: Role CANNOT DROP, ALTER, or TRUNCATE tables.
-- ==============================================================================

-- Step 1: Create the application user if it does not already exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'gradcafe_app_user') THEN
        CREATE ROLE gradcafe_app_user WITH LOGIN PASSWORD 'gradcafe_secure_pass_2026';
    END IF;
END
$$;

-- Step 2: Revoke all default public permissions for defensive isolation
REVOKE ALL ON DATABASE gradcafe_db FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;

-- Step 3: Grant connection and schema usage to the dedicated app user
GRANT CONNECT ON DATABASE gradcafe_db TO gradcafe_app_user;
GRANT USAGE ON SCHEMA public TO gradcafe_app_user;

-- Step 4: Grant minimal required Data Manipulation Language (DML) privileges
-- Read analytics, insert scraped entries, and update standardized fields
GRANT SELECT, INSERT, UPDATE ON TABLE applicants TO gradcafe_app_user;

-- Step 5: Explicitly ensure destructive permissions remain denied
-- Note: PostgreSQL roles by default cannot DROP or ALTER tables they do not own.
-- Verifying ownership remains with the DBA/superuser account:
ALTER TABLE applicants OWNER TO postgres;

-- Verification Query: Inspect granted permissions
SELECT 
    grantee, 
    table_name, 
    privilege_type 
FROM information_schema.role_table_grants 
WHERE grantee = 'gradcafe_app_user';
