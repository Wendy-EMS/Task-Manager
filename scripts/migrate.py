import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    if os.environ.get("VERCEL_ENV") != "production":
        print("Migrations ignorées : seul le déploiement de production modifie la base.")
        return 0

    # Les migrations ont besoin d'une connexion directe, sans le pooler de Neon.
    direct_url = os.environ.get("DATABASE_URL_UNPOOLED")
    if direct_url:
        os.environ["DATABASE_URL"] = direct_url
    if not os.environ.get("DATABASE_URL"):
        print("DATABASE_URL est absente : connecte la base Neon au projet Vercel.")
        return 1

    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)

    from alembic.config import main as alembic_main

    alembic_main(argv=["upgrade", "head"])
    print("Migrations appliquées.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
