-- Migration: V001_initial_schema.sql
-- Description: Initial database schema with all tables, indexes, and seed data
-- Created: 2026-03-14
-- Author: Digital FTE Team

-- This migration creates the complete CRM database schema for the Digital FTE system

-- Source the main schema file
\i ../../schema.sql

-- Migration complete
SELECT 'Migration V001_initial_schema completed successfully' AS status;
