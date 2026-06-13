-- Schema Supabase para Football Data
-- Executar no SQL Editor do Supabase

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Ligas/Competições
CREATE TABLE IF NOT EXISTS leagues (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('League', 'Cup')),
    logo TEXT,
    current_season INTEGER,
    coverage_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Melhores Marcadores
CREATE TABLE IF NOT EXISTS top_scorers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    league_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    player_name TEXT NOT NULL,
    player_photo TEXT,
    team_name TEXT NOT NULL,
    team_logo TEXT,
    goals INTEGER NOT NULL,
    assists INTEGER DEFAULT 0,
    appearances INTEGER NOT NULL,
    minutes INTEGER NOT NULL,
    rating NUMERIC(3,2),
    penalties_scored INTEGER DEFAULT 0,
    penalties_total INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(league_id, season, rank)
);

-- Classificação
CREATE TABLE IF NOT EXISTS standings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    league_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    team_name TEXT NOT NULL,
    team_logo TEXT,
    played INTEGER NOT NULL,
    win INTEGER NOT NULL,
    draw INTEGER NOT NULL,
    lose INTEGER NOT NULL,
    goals_for INTEGER NOT NULL,
    goals_against INTEGER NOT NULL,
    goal_diff INTEGER NOT NULL,
    points INTEGER NOT NULL,
    form TEXT,
    status TEXT,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(league_id, season, rank)
);

-- Estatísticas de Jogo (equipas)
CREATE TABLE IF NOT EXISTS fixture_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fixture_id INTEGER NOT NULL,
    team_name TEXT NOT NULL,
    is_home BOOLEAN NOT NULL,
    metric TEXT NOT NULL,
    value TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(fixture_id, team_name, metric)
);

-- Estatísticas de Jogadores por Jogo
CREATE TABLE IF NOT EXISTS player_match_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fixture_id INTEGER NOT NULL,
    team_name TEXT NOT NULL,
    player_name TEXT NOT NULL,
    player_photo TEXT,
    position TEXT,
    minutes INTEGER,
    rating NUMERIC(3,2),
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    shots_total INTEGER DEFAULT 0,
    shots_on_target INTEGER DEFAULT 0,
    passes_total INTEGER DEFAULT 0,
    passes_accuracy INTEGER DEFAULT 0,
    duels_total INTEGER DEFAULT 0,
    duels_won INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(fixture_id, player_name)
);

-- Previsões
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fixture_id INTEGER NOT NULL UNIQUE,
    winner_name TEXT,
    percent_home TEXT,
    percent_draw TEXT,
    percent_away TEXT,
    advice TEXT,
    comparison_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Histórico H2H
CREATE TABLE IF NOT EXISTS h2h_matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_home_id INTEGER NOT NULL,
    team_away_id INTEGER NOT NULL,
    fixture_date DATE NOT NULL,
    league_name TEXT,
    home_team_name TEXT NOT NULL,
    home_team_logo TEXT,
    away_team_name TEXT NOT NULL,
    away_team_logo TEXT,
    goals_home INTEGER,
    goals_away INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(team_home_id, team_away_id, fixture_date)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_top_scorers_league_season ON top_scorers(league_id, season);
CREATE INDEX IF NOT EXISTS idx_standings_league_season ON standings(league_id, season);
CREATE INDEX IF NOT EXISTS idx_fixture_stats_fixture ON fixture_stats(fixture_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_fixture ON player_match_stats(fixture_id);
CREATE INDEX IF NOT EXISTS idx_predictions_fixture ON predictions(fixture_id);
CREATE INDEX IF NOT EXISTS idx_h2h_teams ON h2h_matches(team_home_id, team_away_id);

-- RLS (Row Level Security) - opcional
-- ALTER TABLE leagues ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Public read" ON leagues FOR SELECT USING (true);
-- Repetir para outras tabelas se necessário