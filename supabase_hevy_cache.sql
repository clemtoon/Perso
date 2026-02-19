-- Run this in Supabase SQL Editor (Dashboard → SQL Editor) to create the cache table.
-- Required only when using Supabase for storage (SUPABASE_URL + SUPABASE_KEY in .env).

CREATE TABLE IF NOT EXISTS hevy_cache (
  api_key_hash TEXT PRIMARY KEY,
  user_json TEXT NOT NULL,
  workouts_json TEXT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
