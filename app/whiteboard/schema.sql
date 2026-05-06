-- Schema for Whiteboard Save States
CREATE TABLE IF NOT EXISTS whiteboard_save_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    whiteboard_id UUID NOT NULL REFERENCES whiteboards(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    data JSONB NOT NULL,
    size_bytes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for per-room pruning logic
CREATE INDEX idx_whiteboard_save_states_room_date ON whiteboard_save_states(whiteboard_id, created_at ASC);

-- Pruning Logic (Example for Backend Implementation)
-- To be called before a new save to ensure the 20-save-per-room limit (Option 2)
-- DELETE FROM whiteboard_save_states 
-- WHERE whiteboard_id = :room_id 
-- AND id NOT IN (
--     SELECT id FROM whiteboard_save_states 
--     WHERE whiteboard_id = :room_id 
--     ORDER BY created_at DESC 
--     LIMIT 19
-- );
