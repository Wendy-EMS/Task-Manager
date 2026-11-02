#!/bin/sh
# Vérifie l'API déployée de bout en bout.
# Usage : sh scripts/smoke_test.sh https://mon-projet.vercel.app
set -eu

if [ $# -ne 1 ]; then
    echo "Usage : $0 <base_url>" >&2
    exit 2
fi

BASE_URL="${1%/}"
EMAIL="smoke-$(date +%s)@example.com"
PASSWORD="motdepasse-smoke"
BODY="$(mktemp)"
trap 'rm -f "$BODY"' EXIT

# call <code attendu> <méthode> <chemin> [corps JSON] [jeton]
call() {
    expected="$1"
    method="$2"
    path="$3"
    data="${4:-}"
    token="${5:-}"

    set -- -sS -o "$BODY" -w '%{http_code}' -X "$method" "$BASE_URL$path"
    if [ -n "$data" ]; then
        set -- "$@" -H "Content-Type: application/json" -d "$data"
    fi
    if [ -n "$token" ]; then
        set -- "$@" -H "Authorization: Bearer $token"
    fi

    code="$(curl "$@")"
    if [ "$code" != "$expected" ]; then
        echo "ÉCHEC  $method $path : attendu $expected, reçu $code" >&2
        cat "$BODY" >&2
        echo >&2
        exit 1
    fi
    echo "OK     $method $path -> $code"
}

json_field() {
    python3 -c "import json, sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])" "$BODY" "$1"
}

call 200 GET /health
call 201 POST /auth/register "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}"
call 200 POST /auth/login "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}"
TOKEN="$(json_field access_token)"

call 401 GET /tasks
call 201 POST /tasks '{"title": "Tester la production", "priority": "high"}' "$TOKEN"
TASK_ID="$(json_field id)"

call 200 GET "/tasks?skip=0&limit=10" "" "$TOKEN"
call 200 GET "/tasks/$TASK_ID" "" "$TOKEN"
call 200 PUT "/tasks/$TASK_ID" '{"title": "Tester la production", "done": true, "priority": "high"}' "$TOKEN"
call 204 DELETE "/tasks/$TASK_ID" "" "$TOKEN"
call 404 GET "/tasks/$TASK_ID" "" "$TOKEN"

echo "Tous les tests sont passés sur $BASE_URL"
