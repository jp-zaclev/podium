# podium.py
import requests
from bs4 import BeautifulSoup
import re
import unicodedata
from typing import List, Dict
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

# Chemin du fichier config (injecté par main.py)
CONFIG_PATH = "config_rewards_champ.txt"  # Par défaut

# === CLÉS AUTORISÉES DANS CONFIG ===
ALLOWED_KEYS = {"URLS", "CATEGORY", "RANK", "PRIZE", "CONDITION", "ORDER"}

# === NETTOYAGE NOM FICHIER ===
def clean_filename(name: str) -> str:
    name = ''.join(c for c in unicodedata.normalize('NFD', name)
                   if unicodedata.category(c) != 'Mn')
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F\'"]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    name = re.sub(r'_+-_', '_', name)
    if len(name) > 100:
        name = name[:100]
    return name if name else "Tournoi_Inconnu"

# === EXTRACTION DONNÉES TOURNOI ===
def extract_tournament_data(url: str) -> tuple[List[Dict], str]:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'width': '800'})
        if not table:
            raise ValueError("Tableau non trouvé.")
        title_row = table.find('tr', class_='papi_titre')
        if title_row:
            full_text = title_row.find('td').get_text(strip=True)
            tournament_name = re.split(r'\s*Classement|ronde|Ronde|après|Résultats', full_text, maxsplit=1)[0].strip()
            tournament_name = tournament_name.rstrip(' -–—').strip()
        else:
            tournament_name = "Tournoi Inconnu"
        rows = table.find_all('tr', class_=re.compile(r'papi_liste_[fc]'))
        players = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 9: continue
            try:
                rank = int(cols[0].get_text(strip=True))
                name_tag = cols[2].find('a')
                name = name_tag.get_text(strip=True) if name_tag else cols[2].get_text(strip=True).strip()
                cat_full = cols[4].get_text(strip=True)
                
                club_raw = cols[7].get_text(separator=' ', strip=True)  # Confirmé correct
                club = re.sub(r'\s+', ' ', club_raw.replace('\xa0', ' ')).strip() or "Club inconnu"
                points_text = cols[8].get_text(strip=True)
                points = float(points_text.replace('½', '.5'))
                category = cat_full[:-1].upper() if cat_full and cat_full[-1] in 'MFmf' else cat_full.upper()
                genre = cat_full[-1].upper() if cat_full and cat_full[-1] in 'MFmf' else None
                # Dans la boucle des joueurs
                elo_text = cols[3].get_text(strip=True)
                elo = int(elo_text) if elo_text.isdigit() else 0
                players.append({
                    'rank': rank, 'name': name, 'category': category,
                    'genre': genre, 'points': points, 'club': club,
                    'elo': elo
                })
            except:
                continue
        return sorted(players, key=lambda x: x['rank']), tournament_name
    except Exception as e:
        print(f"[ERREUR] Échec traitement URL {url} : {e}")
        return None, None

# === CHARGEMENT CONFIG AVEC DÉTECTION DES LIGNES SANS ':' ===
def load_reward_rules(filename: str) -> tuple[List[Dict], List[str]]:
    rules = []
    current = {}
    urls = []
    line_num = 0

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                original_line = line
                line = line.strip()

                # === LIGNE VIDE OU COMMENTAIRE ===
                if not line or line.startswith('#'):
                    if current:
                        if validate_and_add_rule(current, rules, line_num):
                            current = {}
                        else:
                            current = {}
                    continue

                # === LIGNE SANS ':' → ERREUR DE SYNTAXE ===
                if ':' not in original_line:
                    print(f"[ERREUR] Ligne {line_num} → Syntaxe invalide : manque ':' → '{line}'")
                    continue

                # === CLÉ:VALEUR ===
                k, v = original_line.split(':', 1)
                key = k.strip().upper()
                value = v.strip()

                # === CLÉ INVALIDE ===
                if key not in ALLOWED_KEYS:
                    print(f"[ERREUR] Ligne {line_num} → Mot-clé invalide ignoré : '{key}'")
                    continue

                # === URLS ===
                if key == "URLS":
                    raw_urls = [u.strip() for u in value.split('|') if u.strip()]
                    for u in raw_urls:
                        if u.startswith("https://echecs.asso.fr"):
                            urls.append(u)
                        else:
                            print(f"[AVERTISSEMENT] URL invalide ignorée (ligne {line_num}) : {u}")
                else:
                    current[key] = value

            # Dernière règle
            if current:
                validate_and_add_rule(current, rules, line_num)

    except FileNotFoundError:
        print(f"[ERREUR] Fichier config '{filename}' introuvable.")
        exit(1)
    except Exception as e:
        print(f"[ERREUR] Erreur lecture config : {e}")
        exit(1)

    if not urls:
        print("[ERREUR] Aucune URL valide dans le fichier config.")
        exit(1)

    print(f"[INFO] {len(urls)} URLs valides chargées.")
    print(f"[INFO] {len(rules)} règles valides chargées.")
    return rules, urls
# === CLÉS AUTORISÉES (TOUT EN FRANÇAIS) ===
ALLOWED_KEYS = {"URLS", "CATEGORIE", "RANG", "PRIX", "CONDITION", "ORDRE"}

# === VALIDATION D'UNE RÈGLE ===
def validate_and_add_rule(rule_dict: Dict, rules_list: List[Dict], line_num: int) -> bool:
    required = ["CATEGORIE", "RANG", "PRIX"]   # ← PRIX au lieu de PRIZE
    missing = [k for k in required if k not in rule_dict]
    if missing:
        print(f"[ERREUR] Règle ignorée (ligne ~{line_num}) → clés manquantes : {', '.join(missing)}")
        return False
    rules_list.append(rule_dict.copy())
    return True
    
# === ÉVALUATION CONDITION ===
def evaluate_condition(player: Dict, condition: str) -> bool:
    """
    Évalue une condition sur un joueur.
    Supporte :
    - category == "cad"
    - genre == "f"
    - elo < 1500
    - elo >= 1200
    - category == "cad" et genre == "f"
    - category == "min" ou elo > 1000
    """
    if not condition or condition.strip().lower() == 'none':
        return True

    # Nettoyage
    condition = condition.strip()
    if ' et ' in condition.lower():
        parts = [p.strip() for p in condition.split(' et ')]
        return all(evaluate_single_cond(player, p) for p in parts)
    if ' ou ' in condition.lower():
        parts = [p.strip() for p in condition.split(' ou ')]
        return any(evaluate_single_cond(player, p) for p in parts)

    return evaluate_single_cond(player, condition)


def evaluate_single_cond(player: Dict, cond: str) -> bool:
    """Évalue une condition unique (ex: elo < 1500)"""
    cond = cond.strip()

    # Égalité de chaîne (insensible à la casse)
    if '==' in cond:
        key, value = [x.strip().strip('"\'') for x in cond.split('==', 1)]
        player_val = str(player.get(key, '')).strip()
        return player_val.upper() == value.upper()

    # Comparaisons numériques : <, <=, >, >=
    for op in ['<', '<=', '>', '>=']:
        if op in cond:
            try:
                key, value = [x.strip() for x in cond.split(op, 1)]
                player_val = player.get(key, 0)
                if not isinstance(player_val, (int, float)):
                    player_val = 0
                value = float(value)
                if op == '<':  return player_val < value
                if op == '<=': return player_val <= value
                if op == '>':  return player_val > value
                if op == '>=': return player_val >= value
            except:
                return False
    return False

# === ATTRIBUTION RÉCOMPENSES (FRANÇAIS) ===
def assign_rewards(players: List[Dict], rules: List[Dict]) -> List[Dict]:
    awards = []
    for rule in rules:
        cat = rule['CATEGORIE']
        prizes = [p.strip() for p in rule['PRIX'].split('|')]   # ← PRIX
        cond = rule.get('CONDITION', 'none').strip()
        rank_str = rule['RANG'].strip().lower()                 # ← RANG
        order = int(rule.get('ORDRE', 999))                     # ← ORDRE

        eligible = [p for p in players if evaluate_condition(p, cond)]
        if not eligible: continue
        eligible.sort(key=lambda x: (-x['points'], x['rank']))

        if rank_str == 'best':
            if eligible:
                w = eligible[0]
                awards.append({'category': cat, 'place': prizes[0], 'player': w['name'],
                               'prize': prizes[0], 'rank': w['rank'], 'points': w['points'],
                               'club': w['club'], 'order': order})
            continue

        try:
            if '-' in rank_str:
                _, end = map(int, rank_str.split('-'))
            else:
                end = int(rank_str)
        except:
            print(f"[AVERTISSEMENT] RANG invalide ignoré dans règle '{cat}'")
            continue

        winners = eligible[:end]
        for i, w in enumerate(winners):
            if i >= len(prizes): break
            place_prize = prizes[i]
            awards.append({'category': cat, 'place': place_prize, 'player': w['name'],
                           'prize': place_prize, 'rank': w['rank'], 'points': w['points'],
                           'club': w['club'], 'order': order})
    return awards
# === GÉNÉRATION PDF UNIQUE ===
def generate_pdf_all(awards_per_tournament: List[tuple[str, str, List[Dict]]], output_file: str):
    doc = SimpleDocTemplate(output_file, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Tournament', fontSize=16, leading=20, spaceAfter=10, alignment=1, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='Url', fontSize=11, leading=14, spaceAfter=15, alignment=1, fontName='Helvetica-Oblique'))
    styles.add(ParagraphStyle(name='Category', fontSize=14, leading=18, spaceAfter=12, alignment=1, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='Award', fontSize=11, leading=14, spaceAfter=6, fontName='Helvetica'))
    story = []
    for idx, (tournament_name, url, awards) in enumerate(awards_per_tournament):
        if idx > 0:
            story.append(PageBreak())
        story.append(Paragraph(tournament_name, styles['Tournament']))
        story.append(Paragraph(f"<link href='{url}'>URL : {url}</link>", styles['Url']))
        story.append(Paragraph("Palmarès des Récompenses", styles['Title']))
        story.append(Spacer(1, 0.5*cm))
        last_order = None
        for a in sorted(awards, key=lambda x: (x['order'], x['rank'])):
            if a['order'] != last_order:
                story.append(Paragraph(a['category'].upper(), styles['Category']))
                last_order = a['order']
            text = f"<b>{a['place']}</b> : <b>{a['player']}</b> - <i>{a['club']}</i> - (Clt {a['rank']}, {a['points']} pts)"
            story.append(Paragraph(text, styles['Award']))
    doc.build(story)
    print(f"PDF unique généré : {output_file}")

# === GÉNÉRATION TXT UNIQUE ===
def generate_text_all(awards_per_tournament: List[tuple[str, str, List[Dict]]], output_file: str):
    with open(output_file, 'w', encoding='utf-8') as f:
        for idx, (tournament_name, url, awards) in enumerate(awards_per_tournament):
            if idx > 0:
                f.write("\n" + "="*50 + " FIN TOURNOI " + "="*50 + "\n\n")
            f.write(f"=== {tournament_name} ===\n")
            f.write(f"URL : {url}\n\n")
            last_order = None
            for a in sorted(awards, key=lambda x: (x['order'], x['rank'])):
                if a['order'] != last_order:
                    f.write(f"\n[{a['category'].upper()}]\n")
                    last_order = a['order']
                f.write(f"  {a['place']} : {a['player']} - {a['club']} - (Clt {a['rank']}, {a['points']} pts)\n")
            f.write("\n=== Fin du palmarès ===\n")
    print(f"Fichier texte unique généré : {output_file}")

# === MAIN ===
def main():
    rules, urls = load_reward_rules(CONFIG_PATH)
    awards_per_tournament = []
    for i, url in enumerate(urls, start=1):
        print(f"\n[Traitement tournoi {i}/{len(urls)}] : {url}")
        players, tournament_name = extract_tournament_data(url)
        if players is None:
            print(f"[ERREUR] Tournoi ignoré – passage au suivant.")
            continue
        awards = assign_rewards(players, rules)
        awards_per_tournament.append((tournament_name, url, awards))
        print(f"  → {tournament_name} traité.")
    if not awards_per_tournament:
        print("[ERREUR] Aucun tournoi traité avec succès.")
        return
    generate_pdf_all(awards_per_tournament, "palmares.pdf")
    generate_text_all(awards_per_tournament, "palmares.txt")
    print("\n=== TOUS LES FICHIERS GÉNÉRÉS ===")
    print("  → palmares.pdf")
    print("  → palmares.txt")

if __name__ == "__main__":
    main()
