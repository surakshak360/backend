-- Surakshak360 Supabase PostgreSQL Database Migration Schema
-- Copy and paste this script into your Supabase Dashboard -> SQL Editor and click RUN.

-- Clean up any existing legacy tables
DROP TABLE IF EXISTS public.evidence CASCADE;
DROP TABLE IF EXISTS public.cases CASCADE;
DROP TABLE IF EXISTS public.users CASCADE;

-- 1. Create Users Table
CREATE TABLE public.users (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    phone TEXT UNIQUE,
    email TEXT UNIQUE,
    password_hash TEXT,
    role TEXT NOT NULL DEFAULT 'citizen',
    language TEXT DEFAULT 'en',
    is_verified BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Create Cases Table
CREATE TABLE public.cases (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    reporter_id TEXT,
    type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    priority TEXT NOT NULL DEFAULT 'medium',
    source TEXT NOT NULL DEFAULT 'web',
    summary TEXT,
    location JSONB,
    risk_score FLOAT DEFAULT 0.0,
    assigned_officer TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Create Evidence Table
CREATE TABLE public.evidence (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    case_id TEXT NOT NULL,
    type TEXT NOT NULL,
    file_id TEXT,
    file_name TEXT,
    text_content TEXT,
    ml_results JSONB,
    intelligence_output JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Create Indexes for High Performance
CREATE INDEX idx_cases_type ON public.cases(type);
CREATE INDEX idx_cases_status ON public.cases(status);
CREATE INDEX idx_cases_priority ON public.cases(priority);
CREATE INDEX idx_cases_created_at ON public.cases(created_at DESC);
CREATE INDEX idx_evidence_case_id ON public.evidence(case_id);

-- Enable Row Level Security (RLS)
ALTER TABLE public.cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Allow Public/Anon Access for Testing & API Gateway
CREATE POLICY "Allow public read access on cases" ON public.cases FOR SELECT USING (true);
CREATE POLICY "Allow public insert access on cases" ON public.cases FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update access on cases" ON public.cases FOR UPDATE USING (true);

CREATE POLICY "Allow public read access on evidence" ON public.evidence FOR SELECT USING (true);
CREATE POLICY "Allow public insert access on evidence" ON public.evidence FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public access on users" ON public.users FOR ALL USING (true);
