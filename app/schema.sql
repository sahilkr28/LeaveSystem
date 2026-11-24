-- Smart Campus Hostel & Leave Management System
-- Database Schema for PostgreSQL & SQLite Compatibility

-- 1. Leave Applications Table
CREATE TABLE IF NOT EXISTS leaves (
    id SERIAL PRIMARY KEY,
    student_name VARCHAR(100) NOT NULL,
    roll_number VARCHAR(50) NOT NULL,
    hostel_block VARCHAR(50) NOT NULL,
    room_number VARCHAR(20) NOT NULL,
    contact_number VARCHAR(20) NOT NULL,
    parent_contact VARCHAR(20) NOT NULL,
    leave_type VARCHAR(20) NOT NULL, -- 'Day Leave' or 'Night Leave'
    start_date VARCHAR(20) NOT NULL,
    out_time VARCHAR(10) NOT NULL,
    expected_return_date VARCHAR(20) NOT NULL,
    expected_return_time VARCHAR(10) NOT NULL, -- For Day Leave: <= 21:00 (9:00 PM)
    destination VARCHAR(255),
    reason TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending', -- 'Pending', 'Approved', 'Rejected'
    warden_remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Room Maintenance Tickets Table
CREATE TABLE IF NOT EXISTS maintenance_tickets (
    id SERIAL PRIMARY KEY,
    student_name VARCHAR(100) NOT NULL,
    roll_number VARCHAR(50) NOT NULL,
    hostel_block VARCHAR(50) NOT NULL,
    room_number VARCHAR(20) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'Electrical', 'Plumbing', 'Wi-Fi', 'Carpentry', 'Other'
    urgency VARCHAR(20) NOT NULL DEFAULT 'Medium', -- 'Low', 'Medium', 'High', 'Emergency'
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending', -- 'Pending', 'In Progress', 'Resolved'
    warden_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_leaves_roll_number ON leaves (roll_number);
CREATE INDEX IF NOT EXISTS idx_leaves_status ON leaves (status);
CREATE INDEX IF NOT EXISTS idx_leaves_created_at ON leaves (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_tickets_category ON maintenance_tickets (category);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON maintenance_tickets (status);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON maintenance_tickets (created_at DESC);

-- Sample Initial University ERP Records
INSERT INTO leaves (
    student_name, roll_number, hostel_block, room_number, 
    contact_number, parent_contact, leave_type, start_date, 
    out_time, expected_return_date, expected_return_time, 
    destination, reason, status, warden_remarks, created_at
) VALUES 
(
    'Aarav Sharma', '21BCE1042', 'Block A (Aryabhatta)', 'A-304',
    '+91-9876543210', '+91-9876500001', 'Day Leave', '2026-11-25',
    '15:00', '2026-11-25', '20:30',
    'City Central Library', 'Attending IEEE research seminar and reference book issue', 'Pending', NULL, CURRENT_TIMESTAMP
),
(
    'Rohan Verma', '21BIT0892', 'Block B (Vidyasagar)', 'B-112',
    '+91-9811223344', '+91-9811220000', 'Night Leave', '2026-11-28',
    '08:00', '2026-11-30', '20:00',
    'Home - Sector 14, Gurugram', 'Family wedding ceremony. Parent letter verified.', 'Approved', 'Parent confirmed via registered phone call.', CURRENT_TIMESTAMP
),
(
    'Devika Nair', '22BME0341', 'Block C (Gargi)', 'C-208',
    '+91-9744332211', '+91-9744330000', 'Day Leave', '2026-11-24',
    '16:30', '2026-11-24', '20:45',
    'University Medical Centre', 'Dental checkup and routine health follow-up', 'Approved', 'Allowed till 21:00 strictly.', CURRENT_TIMESTAMP
);

INSERT INTO maintenance_tickets (
    student_name, roll_number, hostel_block, room_number,
    category, urgency, description, status, warden_notes, created_at
) VALUES 
(
    'Siddharth Malhotra', '21BCE1105', 'Block A (Aryabhatta)', 'A-214',
    'Electrical', 'High', 'Ceiling fan regulator short-circuit and main switch sparking.', 'Pending', NULL, CURRENT_TIMESTAMP
),
(
    'Kunal Deshmukh', '22BIT0412', 'Block B (Vidyasagar)', 'B-405',
    'Wi-Fi', 'Medium', 'Hostel LAN port loose; Wi-Fi access point dropping connection continuously.', 'In Progress', 'Assigned to Campus IT Services ticket #IT-4921.', CURRENT_TIMESTAMP
),
(
    'Meera Iyer', '21ECE0198', 'Block C (Gargi)', 'C-102',
    'Plumbing', 'Emergency', 'Bathroom tap valve leakage causing water accumulation near doorway.', 'Resolved', 'Replaced washer valve on 24-Nov morning. Tested OK.', CURRENT_TIMESTAMP
);
