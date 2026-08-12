-- ============================================================================
-- Create the dedicated READ-ONLY execution role.
-- This is the account used to execute LLM-generated (approved) queries.
-- It has SELECT-only privileges and no write / DDL / admin rights.
-- The role password here is a DEFAULT for local docker development; in real
-- deployments use docker secrets / injection.
-- ============================================================================

DO $$
BEGIN
   IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nlsql_readonly') THEN
      CREATE ROLE nlsql_readonly LOGIN PASSWORD 'NLSQL_READONLY_PASSWORD';
   END IF;
END
$$;

GRANT CONNECT ON DATABASE nlsql TO nlsql_readonly;
GRANT USAGE ON SCHEMA public TO nlsql_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO nlsql_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO nlsql_readonly;

-- Revoke broad/public write+DML rights so read-only is the effective boundary.
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE CREATE, USAGE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO PUBLIC;
