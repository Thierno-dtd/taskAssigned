#!/usr/bin/env python3
"""
Smoke-test automatique de l'API SEEG Intervention.

Teste, en une seule exécution, tous les endpoints principaux : login,
lecture (GET) sur chaque ressource, et vérifie qu'un accès sans token est
bien rejeté (401). Affiche un tableau récapitulatif pass/fail, pas besoin
de cliquer un par un dans Swagger.

Usage :
    pip install requests
    python test_api_smoke.py
    python test_api_smoke.py --base-url http://127.0.0.1:8000/api/v1 --username admin --password admin123

Prérequis : le serveur doit tourner, et un compte doit exister (ex: via
`python manage.py seed_data` : admin / admin123).
"""
import argparse
import sys

try:
    import requests
except ImportError:
    print("Ce script a besoin de 'requests' : pip install requests")
    sys.exit(1)


def color(text, code):
    return f"\033[{code}m{text}\033[0m"


def check(method, path, token=None, expected=(200,), json_body=None,
          allow_statuses=None, description=None):
    """Fait une requête et retourne (ok, status_code, detail)."""
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    url = f"{BASE_URL}{path}"
    try:
        resp = requests.request(method, url, headers=headers, json=json_body, timeout=10)
    except requests.exceptions.ConnectionError:
        return False, None, "Connexion refusée (le serveur tourne-t-il ?)"
    ok_statuses = allow_statuses if allow_statuses else expected
    ok = resp.status_code in ok_statuses
    return ok, resp.status_code, (description or "")


def main():
    global BASE_URL
    parser = argparse.ArgumentParser(description="Smoke-test de l'API SEEG Intervention")
    parser.add_argument('--base-url', default='http://127.0.0.1:8000/api/v1')
    parser.add_argument('--username', default='admin')
    parser.add_argument('--password', default='admin123')
    args = parser.parse_args()
    BASE_URL = args.base_url.rstrip('/')

    results = []

    def record(name, ok, status, detail=""):
        results.append((name, ok, status, detail))
        mark = color("PASS", "92") if ok else color("FAIL", "91")
        print(f"  [{mark}] {name:<45} -> {status}  {detail}")

    print(f"\n=== Smoke-test API : {BASE_URL} ===\n")

    # --- 1. Endpoints publics (pas de token requis) ---
    print("-- Endpoints publics --")
    ok, status, _ = check('GET', '/../health/', expected=(200, 503))
    record("GET /api/health/ (hors /v1, volontaire)", ok, status)

    # --- 2. Sécurité : accès sans token doit être refusé ---
    print("\n-- Sécurité (sans token, doit être rejeté) --")
    ok, status, _ = check('GET', '/taches/', expected=(401,))
    record("GET /taches/ sans token -> 401 attendu", ok, status)

    # --- 3. Login ---
    print("\n-- Authentification --")
    resp = requests.post(f"{BASE_URL}/auth/login/", json={
        'username': args.username, 'password': args.password
    }, timeout=10)
    login_ok = resp.status_code == 200 and 'access' in resp.json()
    record("POST /auth/login/", login_ok, resp.status_code)
    if not login_ok:
        print(color("\nImpossible de continuer sans authentification valide.", "91"))
        print(f"Réponse: {resp.text[:300]}")
        print_summary(results)
        sys.exit(1)

    token = resp.json()['access']

    ok, status, _ = check('GET', '/auth/me/', token=token, expected=(200, 404))
    record("GET /auth/me/ (profil courant, si existant)", ok, status)

    # --- 4. Tâches / semaines ---
    print("\n-- Tâches & semaines --")
    for name, method, path in [
        ("Liste des semaines", 'GET', '/semaines/'),
        ("Liste des tâches", 'GET', '/taches/'),
        ("Mes tâches (agent connecté)", 'GET', '/mes-taches/'),
        ("Liste des imports Excel (lots)", 'GET', '/import/lots/'),
    ]:
        ok, status, _ = check(method, path, token=token, expected=(200,))
        record(f"{method} {path} — {name}", ok, status)

    # --- 5. Rapports ---
    print("\n-- Rapports --")
    for name, method, path in [
        ("Liste des rapports", 'GET', '/rapports/'),
        ("Mes rapports", 'GET', '/mes-rapports/'),
    ]:
        ok, status, _ = check(method, path, token=token, expected=(200,))
        record(f"{method} {path} — {name}", ok, status)

    # --- 6. Notifications ---
    print("\n-- Notifications --")
    for name, method, path in [
        ("Liste des notifications", 'GET', '/notifications/'),
        ("Compteur non-lues", 'GET', '/notifications/non-lues/count/'),
    ]:
        ok, status, _ = check(method, path, token=token, expected=(200,))
        record(f"{method} {path} — {name}", ok, status)

    # --- 7. Dashboard / stats ---
    print("\n-- Statistiques (dashboard) --")
    for name, method, path in [
        ("Stats générales", 'GET', '/stats/'),
        ("Stats semaine courante", 'GET', '/stats/semaine/'),
        ("Stats par agent", 'GET', '/stats/agents/'),
        ("Stats raisons de non-exécution", 'GET', '/stats/raisons/'),
    ]:
        ok, status, _ = check(method, path, token=token, expected=(200,))
        record(f"{method} {path} — {name}", ok, status)

    # --- 8. Carte / GPS ---
    print("\n-- Carte & GPS --")
    for name, method, path in [
        ("Tâches sur la carte", 'GET', '/map/taches/'),
        ("Suivi des agents", 'GET', '/agents/tracking/'),
    ]:
        ok, status, _ = check(method, path, token=token, expected=(200,))
        record(f"{method} {path} — {name}", ok, status)

    # --- 9. Export Excel ---
    print("\n-- Export Excel --")
    ok, status, _ = check('GET', '/export/taches/', token=token, expected=(200,))
    record("GET /export/taches/ (fichier xlsx)", ok, status)
    ok, status, _ = check('GET', '/export/agents/', token=token, expected=(200,))
    record("GET /export/agents/ (fichier xlsx)", ok, status)

    print_summary(results)


def print_summary(results):
    total = len(results)
    passed = sum(1 for _, ok, _, _ in results if ok)
    failed = total - passed
    print(f"\n=== Résumé : {passed}/{total} OK", end="")
    if failed:
        print(color(f" — {failed} échec(s)", "91"))
        print("\nÉchecs :")
        for name, ok, status, detail in results:
            if not ok:
                print(f"  - {name} (status: {status}) {detail}")
        sys.exit(1)
    else:
        print(color(" — tout est vert !", "92"))
        sys.exit(0)


if __name__ == '__main__':
    main()
