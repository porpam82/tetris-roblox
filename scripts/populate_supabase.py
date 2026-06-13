#!/usr/bin/env python3
"""
ETL Script: API-Football → Supabase
Popula as tabelas no Supabase a partir da API-Football Free Tier.
"""
import os
import sys
import time
import argparse
import requests
from pathlib import Path
from typing import Optional
from datetime import datetime

try:
    from supabase import create_client, Client
except ImportError:
    print("Erro: instale dependências → pip install supabase requests python-dotenv")
    sys.exit(1)

# Configurações
API_BASE = "https://v3.football.api-sports.io"
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://supabase.porpamtech.com")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

session = requests.Session()


def get_api_key() -> str:
    """Obtém API key do argumento ou env."""
    key = os.getenv("API_FOOTBALL_KEY")
    if not key:
        print("Erro: defina API_FOOTBALL_KEY no .env ou passe --api-key")
        sys.exit(1)
    return key


def api_get(endpoint: str, params: dict = None, api_key: str = None) -> Optional[dict]:
    """Chamada à API-Football com rate limit handling."""
    headers = {"x-apisports-key": api_key}
    url = f"{API_BASE}{endpoint}"
    try:
        resp = session.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code == 429:
            print(f"  ⚠️ Rate limited (429) — aguardando 60s...")
            time.sleep(60)
            return api_get(endpoint, params, api_key)
        resp.raise_for_status()
        data = resp.json()
        if data.get("errors"):
            print(f"  ❌ API Error: {data['errors']}")
            return None
        return data
    except requests.RequestException as e:
        print(f"  ❌ Erro na request: {e}")
        return None


def get_supabase() -> Client:
    """Cria cliente Supabase."""
    if not SUPABASE_KEY:
        print("Erro: defina SUPABASE_ANON_KEY no .env")
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def upsert_leagues(sb: Client, api_key: str):
    """Busca e guarda ligas portuguesas."""
    print("📋 A buscar ligas de Portugal...")
    data = api_get("/leagues", {"country": "Portugal"}, api_key)
    if not data or not data.get("response"):
        print("  Sem dados de ligas")
        return

    leagues = []
    for l in data["response"]:
        league = l["league"]
        country = l["country"]
        coverage = l.get("coverage", {})
        leagues.append({
            "id": league["id"],
            "name": league["name"],
            "type": league["type"],
            "logo": league.get("logo"),
            "current_season": league.get("season"),
            "coverage_json": coverage
        })

    # Upsert
    for lg in leagues:
        sb.table("leagues").upsert(lg, on_conflict="id").execute()
    print(f"  ✅ {len(leagues)} ligas guardadas")


def upsert_top_scorers(sb: Client, api_key: str, league_id: int, season: int):
    """Busca e guarda melhores marcadores."""
    print(f"⚽ A buscar top scorers league={league_id} season={season}...")
    data = api_get("/players/topscorers", {"league": league_id, "season": season}, api_key)
    if not data or not data.get("response"):
        print("  Sem dados de marcadores")
        return

    scorers = []
    for p in data["response"]:
        player = p["player"]
        stats = p["statistics"][0] if p.get("statistics") else {}
        team = stats.get("team", {})
        games = stats.get("games", {})
        goals = stats.get("goals", {})
        penalties = stats.get("penalty", {})

        scorers.append({
            "league_id": league_id,
            "season": season,
            "rank": p.get("rank", 0),
            "player_name": player.get("name", "Unknown"),
            "player_photo": player.get("photo"),
            "team_name": team.get("name", "Unknown"),
            "team_logo": team.get("logo"),
            "goals": goals.get("total", 0) or 0,
            "assists": goals.get("assists", 0) or 0,
            "appearances": games.get("appearences", 0) or 0,
            "minutes": games.get("minutes", 0) or 0,
            "rating": float(games.get("rating", 0) or 0),
            "penalties_scored": penalties.get("scored", 0) or 0,
            "penalties_total": penalties.get("total", 0) or 0
        })

    for s in scorers:
        sb.table("top_scorers").upsert(s, on_conflict="league_id,season,rank").execute()
    print(f"  ✅ {len(scorers)} marcadores guardados")


def upsert_standings(sb: Client, api_key: str, league_id: int, season: int):
    """Busca e guarda classificação."""
    print(f"📊 A buscar standings league={league_id} season={season}...")
    data = api_get("/standings", {"league": league_id, "season": season}, api_key)
    if not data or not data.get("response"):
        print("  Sem dados de classificação")
        return

    standings = []
    for s in data["response"][0].get("league", {}).get("standings", [[]])[0]:
        standings.append({
            "league_id": league_id,
            "season": season,
            "rank": s["rank"],
            "team_name": s["team"]["name"],
            "team_logo": s["team"].get("logo"),
            "played": s["all"]["played"],
            "win": s["all"]["win"],
            "draw": s["all"]["draw"],
            "lose": s["all"]["lose"],
            "goals_for": s["all"]["goals"]["for"],
            "goals_against": s["all"]["goals"]["against"],
            "goal_diff": s["goalsDiff"],
            "points": s["points"],
            "form": s.get("form", ""),
            "status": s.get("status", ""),
            "description": s.get("description", "")
        })

    for st in standings:
        sb.table("standings").upsert(st, on_conflict="league_id,season,rank").execute()
    print(f"  ✅ {len(standings)} equipas na classificação")


def upsert_fixture_stats(sb: Client, api_key: str, fixture_id: int):
    """Busca e guarda estatísticas de um jogo."""
    print(f"📈 A buscar fixture stats fixture={fixture_id}...")
    data = api_get("/fixtures/statistics", {"fixture": fixture_id}, api_key)
    if not data or not data.get("response"):
        print("  Sem estatísticas")
        return

    stats = []
    for team_stat in data["response"]:
        team = team_stat["team"]
        for stat in team_stat["statistics"]:
            stats.append({
                "fixture_id": fixture_id,
                "team_name": team["name"],
                "is_home": team["id"] == data["response"][0]["team"]["id"] if data["response"] else True,
                "metric": stat["type"],
                "value": str(stat["value"]) if stat["value"] is not None else "-"
            })

    for st in stats:
        sb.table("fixture_stats").upsert(st, on_conflict="fixture_id,team_name,metric").execute()
    print(f"  ✅ {len(stats)} métricas guardadas")


def upsert_player_match_stats(sb: Client, api_key: str, fixture_id: int):
    """Busca e guarda stats de jogadores num jogo."""
    print(f"👥 A buscar player stats fixture={fixture_id}...")
    data = api_get("/fixtures/players", {"fixture": fixture_id}, api_key)
    if not data or not data.get("response"):
        print("  Sem stats de jogadores")
        return

    players = []
    for team_players in data["response"]:
        team = team_players["team"]
        for p in team_players["players"]:
            player = p["player"]
            stats = p["statistics"][0] if p.get("statistics") else {}
            games = stats.get("games", {})
            goals = stats.get("goals", {})
            shots = stats.get("shots", {})
            passes = stats.get("passes", {})
            duels = stats.get("duels", {})

            players.append({
                "fixture_id": fixture_id,
                "team_name": team["name"],
                "player_name": player.get("name", "Unknown"),
                "player_photo": player.get("photo"),
                "position": games.get("position"),
                "minutes": games.get("minutes"),
                "rating": float(games.get("rating", 0) or 0),
                "goals": goals.get("total", 0) or 0,
                "assists": goals.get("assists", 0) or 0,
                "shots_total": shots.get("total", 0) or 0,
                "shots_on_target": shots.get("on", 0) or 0,
                "passes_total": passes.get("total", 0) or 0,
                "passes_accuracy": passes.get("accuracy", 0) or 0,
                "duels_total": duels.get("total", 0) or 0,
                "duels_won": duels.get("won", 0) or 0
            })

    for pl in players:
        sb.table("player_match_stats").upsert(pl, on_conflict="fixture_id,player_name").execute()
    print(f"  ✅ {len(players)} jogadores guardados")


def upsert_predictions(sb: Client, api_key: str, fixture_id: int):
    """Busca e guarda previsões."""
    print(f"🔮 A buscar predictions fixture={fixture_id}...")
    data = api_get("/predictions", {"fixture": fixture_id}, api_key)
    if not data or not data.get("response"):
        print("  Sem previsões")
        return

    for p in data["response"]:
        predictions = p.get("predictions", {})
        comparison = p.get("comparison", {})
        sb.table("predictions").upsert({
            "fixture_id": fixture_id,
            "winner_name": predictions.get("winner", {}).get("name"),
            "percent_home": predictions.get("percent", {}).get("home"),
            "percent_draw": predictions.get("percent", {}).get("draw"),
            "percent_away": predictions.get("percent", {}).get("away"),
            "advice": predictions.get("advice"),
            "comparison_json": comparison
        }, on_conflict="fixture_id").execute()
    print("  ✅ Previsões guardadas")


def upsert_h2h(sb: Client, api_key: str, h2h: str, limit: int = 10):
    """Busca e guarda histórico H2H (ex: '525-453')."""
    print(f"📜 A buscar H2H {h2h}...")
    data = api_get("/fixtures/headtohead", {"h2h": h2h, "limit": limit}, api_key)
    if not data or not data.get("response"):
        print("  Sem H2H")
        return

    matches = []
    for m in data["response"]:
        fixture = m["fixture"]
        league = m["league"]
        teams = m["teams"]
        goals = m["goals"]
        matches.append({
            "team_home_id": teams["home"]["id"],
            "team_away_id": teams["away"]["id"],
            "fixture_date": fixture["date"][:10],
            "league_name": league["name"],
            "home_team_name": teams["home"]["name"],
            "home_team_logo": teams["home"].get("logo"),
            "away_team_name": teams["away"]["name"],
            "away_team_logo": teams["away"].get("logo"),
            "goals_home": goals["home"],
            "goals_away": goals["away"]
        })

    for m in matches:
        sb.table("h2h_matches").upsert(m, on_conflict="team_home_id,team_away_id,fixture_date").execute()
    print(f"  ✅ {len(matches)} jogos H2H guardados")


def main():
    parser = argparse.ArgumentParser(description="ETL API-Football → Supabase")
    parser.add_argument("--api-key", help="API-Football key (ou env API_FOOTBALL_KEY)")
    parser.add_argument("--league", type=int, default=94, help="League ID (default: 94 Primeira Liga)")
    parser.add_argument("--season", type=int, default=2024, help="Season (default: 2024)")
    parser.add_argument("--fixture", type=int, help="Fixture ID para stats/players/predictions")
    parser.add_argument("--h2h", help="H2H pair ex: '525-453'")
    parser.add_argument("--all", action="store_true", help="Executa tudo (ligas, scorers, standings)")
    args = parser.parse_args()

    api_key = args.api_key or os.getenv("API_FOOTBALL_KEY")
    if not api_key:
        print("Erro: forneça --api-key ou defina API_FOOTBALL_KEY")
        sys.exit(1)

    sb = get_supabase()
    print(f"🔗 Conectado a Supabase: {SUPABASE_URL}")
    print(f"🔑 API-Football key: {api_key[:8]}...")
    print()

    if args.all or not any([args.fixture, args.h2h]):
        upsert_leagues(sb, api_key)
        upsert_top_scorers(sb, api_key, args.league, args.season)
        upsert_standings(sb, api_key, args.league, args.season)

    if args.fixture:
        upsert_fixture_stats(sb, api_key, args.fixture)
        upsert_player_match_stats(sb, api_key, args.fixture)
        upsert_predictions(sb, api_key, args.fixture)

    if args.h2h:
        upsert_h2h(sb, api_key, args.h2h)

    print("\n✅ ETL concluído!")


if __name__ == "__main__":
    main()