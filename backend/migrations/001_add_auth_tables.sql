-- EV Navigation System - Database Migration
-- Phase 1: User Authentication & Favorite Routes
-- Created: 2025-11-30

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Create indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Create favorite_routes table  
CREATE TABLE IF NOT EXISTS favorite_routes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    route_name VARCHAR(200) NOT NULL,
    start_address VARCHAR(500),
    end_address VARCHAR(500),
    start_lat VARCHAR(50),
    start_lon VARCHAR(50),
    end_lat VARCHAR(50),
    end_lon VARCHAR(50),
    vehicle_id INTEGER,
    vehicle_range_km INTEGER,
    battery_capacity_kwh INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, route_name)
);

-- Create indexes for favorite_routes table
CREATE INDEX IF NOT EXISTS idx_favorite_routes_user_id ON favorite_routes(user_id);

-- Add comment to tables
COMMENT ON TABLE users IS 'User accounts for authentication';
COMMENT ON TABLE favorite_routes IS 'User saved favorite routes';

-- Display created tables
SELECT 'Migration completed successfully!' AS status;
SELECT 'Created tables: users, favorite_routes' AS info;
