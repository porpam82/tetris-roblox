# Football Data Frontend — Primeira Liga

Frontend simples em HTML/JS para visualizar dados de futebol da Primeira Liga portuguesa, consumindo dados armazenados no **Supabase** (populados via API-Football Free Tier).

## 🔗 Demo
[GitHub Pages](https://porpam82.github.io/tetris-roblox/) — *Ative GitHub Pages nas settings do repo*

## 📊 Dados Disponíveis

| Aba | Descrição | Fonte |
|-----|-----------|-------|
| **Melhores Marcadores** | Top 20 da época 2024/25 | `top_scorers` |
| **Classificação** | Tabela final 2024/25 | `standings` |
| **Estatísticas de Jogo** | Porto 3-0 Moreirense (team + players) | `fixture_stats`, `player_match_stats` |
| **Previsões** | Modelo multi-matchup (Poisson, H2H, etc.) | `predictions` |
| **Histórico H2H** | Últimos 7 Porto vs Moreirense | `h2h_matches` |
| **Ligas Portuguesas** | 11 competições disponíveis no Free Tier | `leagues` |

## 🏗️ Arquitetura

```
API-Football (Free Tier) → Python ETL → Supabase → Frontend (HTML/JS)
```

- **API**: `https://v3.football.api-sports.io` (header `x-apisports-key`)
- **Free Tier**: 100 req/dia, todas as ligas/endpoints, sem live data
- **Supabase**: Self-hosted em `https://supabase.porpamtech.com`

## 🚀 Como Usar

### 1. Clonar e abrir localmente
```bash
git clone https://github.com/porpam82/tetris-roblox.git
cd tetris-roblox
# Abrir index.html no browser (ou servir com python -m http.server)
```

### 2. Popular Supabase (ETL)
```bash
cd scripts
pip install -r requirements.txt
python populate_supabase.py --api-key SUA_API_KEY --season 2024 --league 94
```

### 3. Configurar Supabase
Edite `index.html` e substitua as variáveis:
```js
const SUPABASE_URL = 'https://supabase.porpamtech.com';
const SUPABASE_ANON_KEY = 'SUA_ANON_KEY_AQUI';
```

## 📁 Estrutura

```
tetris-roblox/
├── index.html          # Frontend principal (single-file)
├── README.md           # Este ficheiro
└── scripts/
    ├── populate_supabase.py    # ETL principal
    ├── requirements.txt
    └── schema.sql              # DDL das tabelas
```

## 🔑 API-Football Free Tier

| Limite | Valor |
|--------|-------|
| Requests/dia | 100 |
| Ligas | Todas (incl. Portugal: 94, 95, 96, 97, 550, 865, 948, 457–460) |
| Endpoints | Fixtures, Players, Predictions, Standings, Stats, H2H |
| Live data | ❌ Não incluído |
| Odds/Injuries | ❌ Não incluído |

## 📋 Tabelas Supabase

```sql
leagues              -- Competições (id, name, type, logo, season, coverage)
top_scorers          -- Marcadores (league_id, season, rank, player, team, goals...)
standings            -- Classificação (league_id, season, rank, team, W/D/L, GF/GA, pts)
fixture_stats        -- Métricas de jogo (fixture_id, team, is_home, metric, value)
player_match_stats   -- Stats por jogador/jogo (fixture_id, player, pos, mins, rating, goals...)
predictions          -- Previsões multi-modelo (fixture_id, winner, %, advice, JSON)
h2h_matches          -- Histórico direto (team_home, team_away, date, league, score)
```

## ⚠️ Limitações Conhecidas

- **Época 2025**: Free Tier não retorna dados para season=2025 (Erro 429/403)
- **Rate limit**: 100 req/dia — planeie o ETL com cache
- **Live data**: Indisponível no Free Tier
- **Odds/Injuries**: Requer plano pago

## 📝 Licença

MIT — Use à vontade para análise pessoal/educacional.
