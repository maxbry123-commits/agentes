"""CLI for skills management.

This module allows listing and creating skills directly
via the command line. Skills are additional procedures stored in the
plugins directory. When called without a subcommand,
a short help message is displayed.

Examples:

.. code-block:: bash

    # List skills
    python -m jarvis.skills.cli list

    # Create a new skill
    python -m jarvis.skills.cli create "Research blog article" --triggers research blog

"""

from __future__ import annotations

import argparse
import sys

from cognithor.config import load_config
from cognithor.skills.manager import create_skill, list_skills
from cognithor.utils.logging import get_logger

log = get_logger(__name__)


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="jarvis-skills",
        description="Jarvis Skills Manager -- Skills erstellen und verwalten",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list command
    _list_parser = subparsers.add_parser("list", help="Verfügbare Skills auflisten")

    # create command
    create_parser = subparsers.add_parser("create", help="Neuen Skill (Prozedur) anlegen")
    create_parser.add_argument("name", help="Name des neuen Skills")
    create_parser.add_argument(
        "--triggers",
        nargs="*",
        default=[],
        help="Trigger-Schlüsselwörter, die den Skill aktivieren",
    )

    # search command
    search_parser = subparsers.add_parser("search", help="Skills in einem Remote-Repository suchen")
    search_parser.add_argument("query", help="Suchbegriff für Skills")
    search_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximale Anzahl von Ergebnissen",
    )

    # install command
    install_parser = subparsers.add_parser(
        "install", help="Skill aus einem Remote-Repository installieren"
    )
    install_parser.add_argument(
        "name",
        help="Name des Skills, der installiert werden soll",
    )
    install_parser.add_argument(
        "--repo",
        default=None,
        help="Optional: URL des Skill-Repositorys (nicht unterstützt im Stub)",
    )

    args = parser.parse_args(argv)

    # Load configuration to determine the skills directory
    config = load_config()
    skills_path = config.cognithor_home / config.plugins.skills_dir

    if args.command == "list":
        skills = list_skills(skills_path)
        if not skills:
            print("Keine Skills installiert.")
        else:
            print("Installierte Skills:")
            for skill in skills:
                print(f" - {skill}")

    elif args.command == "create":
        try:
            path = create_skill(skills_path, args.name, args.triggers)
        except FileExistsError as exc:
            log.error("skill_create_failed", name=args.name, error=str(exc))
            sys.exit(1)
        else:
            print(f"Skill '{args.name}' erstellt: {path}")

    elif args.command == "search":
        from cognithor.skills.manager import search_remote_skills

        results = search_remote_skills(args.query, limit=args.limit)
        if not results:
            print("Keine Ergebnisse gefunden oder Remote-Suche nicht verfügbar.")
        else:
            print("Gefundene Skills:")
            for name in results:
                print(f" - {name}")

    elif args.command == "install":
        from cognithor.skills.manager import install_remote_skill

        path = install_remote_skill(skills_path, args.name, args.repo)
        print(f"Skill '{args.name}' installiert: {path}")


if __name__ == "__main__":  # pragma: no cover
    main()
