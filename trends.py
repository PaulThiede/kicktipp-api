import requests
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
import math

load_dotenv()
API_KEY = os.getenv("API_KEY")


options = ["soccer_germany_bundesliga"]
liga_completer = WordCompleter(options, ignore_case=True)

leagueKey = prompt("Wähle eine Liga: ", completer=liga_completer)

url = f'https://api.the-odds-api.com/v4/sports/{leagueKey}/odds'

now = datetime.now(timezone.utc)
future = now + timedelta(days=7)

print(f"{now.year}-{now.month:02d}-{now.day:02d}T{now.hour:02d}:{now.minute:02d}:{now.second:02d}Z")


params = {  
    "apiKey": API_KEY,
    "regions": "eu",
    "markets": "h2h",
    "commenceTimeFrom": f"{now.year}-{now.month:02d}-{now.day:02d}T{now.hour:02d}:{now.minute:02d}:{now.second:02d}Z",
    "commenceTimeTo": f"{future.year}-{future.month:02d}-{future.day:02d}T{future.hour:02d}:{future.minute:02d}:{future.second:02d}Z",
}

response = requests.get(url, params=params)

if (response.status_code != 200):
    print("Fehler bei der Anfrage:", response.status_code, response.text)
    exit()

data = response.json()

def poisson_pmf(lam, k):
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def predict_match(home_odds, away_odds, draw_odds):
    # 1. Quoten in Wahrscheinlichkeiten umrechnen
    home_prob = 1 / home_odds
    draw_prob = 1 / draw_odds
    away_prob = 1 / away_odds

    total_prob = home_prob + draw_prob + away_prob
    home_prob /= total_prob
    draw_prob /= total_prob
    away_prob /= total_prob

    # 2. Erwartete Gesamtzahl an Toren schätzen
    base_goals = 2.5
    factor = 1.0
    diff = abs(home_prob - away_prob)
    expected_goals = base_goals + factor * diff

    # 3. Erwartete Tore auf Heim/Auswärts aufteilen
    total_win_prob = home_prob + away_prob
    expected_home_goals = expected_goals * (home_prob / total_win_prob)
    expected_away_goals = expected_goals * (away_prob / total_win_prob)

    # 4. Poisson-Verteilung für mögliche Ergebnisse
    score_probs = {}
    max_goals = 5
    for h in range(max_goals + 1):
        p_home = poisson(h, expected_home_goals)
        for a in range(max_goals + 1):
            p_away = poisson(a, expected_away_goals)
            score = f"{h}:{a}"
            score_probs[score] = p_home * p_away

    # 5. Wahrscheinlichstes Ergebnis zurückgeben
    best_result = max(score_probs.items(), key=lambda x: x[1])
    return best_result[0]

def poisson(k, lamb):
    return (lamb ** k) * math.exp(-lamb) / math.factorial(k)


for match in data:
    # We select the first bookmaker to get our quotes
    bookmaker = match["bookmakers"][0]
    outcome = bookmaker["markets"][0]["outcomes"]

    tip = predict_match(outcome[0]["price"], outcome[1]["price"], outcome[2]["price"])
    print(f"Bester Tipp: {outcome[0]['name']} - {outcome[1]['name']} {tip} ({outcome[0]['price']} - {outcome[1]['price']})")

