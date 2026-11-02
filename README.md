# Task-Manager

API de gestion de tâches (FastAPI, SQLAlchemy, Alembic) avec authentification JWT.

## Développement local

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env          # puis remplacer les secrets
.venv/bin/pytest
```

Avec Docker (API + PostgreSQL) :

```bash
docker compose up -d --build
```

## Déploiement sur Vercel

L'API tourne sur Vercel comme une fonction Python, avec une base PostgreSQL Neon
ajoutée depuis le Marketplace Vercel. Le HTTPS est fourni automatiquement sur
`https://<projet>.vercel.app`.

### Étapes

1. Pousser le dépôt sur GitHub.
2. Sur [vercel.com](https://vercel.com) : **Add New → Project**, importer `Wendy-EMS/Task-Manager`.
   Vercel détecte FastAPI grâce à `app/main.py`. Laisser les réglages par défaut.
3. Dans le projet : **Storage → Neon** (offre gratuite), puis connecter la base à
   l'environnement **Production**. Vercel ajoute `DATABASE_URL` (connexion via le pooler) et
   `DATABASE_URL_UNPOOLED` (connexion directe).
4. **Settings → Environment Variables**, environnement **Production**, en cochant **Sensitive** :

   | Variable | Valeur |
   | --- | --- |
   | `JWT_SECRET` | sortie de `python3 -c "import secrets; print(secrets.token_urlsafe(48))"` |
   | `CORS_ORIGINS` | `https://<projet>.vercel.app` |
   | `JWT_EXPIRE_MINUTES` | `30` |

5. **Deployments → Redeploy**. Pendant le build, `scripts/migrate.py` applique les migrations
   Alembic sur la base de production via `DATABASE_URL_UNPOOLED`.

Les secrets restent dans Vercel : le fichier `.env` n'est jamais envoyé (voir `.gitignore` et
`.vercelignore`).

### Tester la production

Avec curl :

```bash
sh scripts/smoke_test.sh https://<projet>.vercel.app
```

Le script vérifie `/health`, l'inscription, la connexion, le refus sans jeton (401), puis
crée, liste, lit, remplace et supprime une tâche.

Avec Postman :

1. Importer `postman/tasks.postman_collection.json`, `postman/local.postman_environment.json`
   et `postman/production.postman_environment.json`.
2. Dans l'environnement **Tâches - production**, mettre l'URL du projet dans `base_url`.
3. Sélectionner cet environnement et lancer la collection avec le **Collection Runner**.
   La connexion enregistre le jeton dans `token`, la création enregistre l'id dans `task_id`.

### Limites

- Chaque requête peut tourner sur une instance différente : la limitation de débit
  (`slowapi`) garde ses compteurs en mémoire, donc par instance.
- Les déploiements de preview n'appliquent pas les migrations : seule la production modifie
  la base.
- L'offre gratuite de Neon est limitée (1 Go de stockage, temps de calcul mensuel plafonné),
  et la base se met en veille quand elle n'est pas utilisée : la première requête après une
  pause est plus lente.
