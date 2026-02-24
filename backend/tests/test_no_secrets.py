"""Проверка репозитория на случайный коммит секретов.

Тест консервативный: ловит очевидные паттерны утечек ключей.
"""

import pathlib
import re


def test_no_api_secrets_committed():
    repo_root = pathlib.Path(__file__).resolve().parents[2]

    # Паттерны для выявления типичных утечек секретов (консервативно, чтобы не было ложных срабатываний)
    patterns = [
        re.compile(r"\bgsk_[A-Za-z0-9]{10,}\b"),
        re.compile(r"\bapi_key\s*=\s*\"[^\"\n]{10,}\""),
        re.compile(r"\bapi_key\s*=\s*'[^'\n]{10,}'"),
    ]

    excluded_dirs = {
        ".git",
        "proc",
        "sys",
        "dev",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        "dist",
        "build",
    }

    excluded_files = {
        # Не сканируем env файлы (они должны быть gitignored), чтобы не ловить локальные ложные падения.
        ".env",
        ".env.local",
        ".env.development.local",
        ".env.test.local",
        ".env.production.local",
    }

    for path in repo_root.rglob("*"):
        if any(part in excluded_dirs for part in path.parts):
            continue
        if path.is_dir():
            continue
        if path.name in excluded_files:
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf"}:
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for pat in patterns:
            m = pat.search(content)
            if m:
                rel = path.relative_to(repo_root)
                raise AssertionError(
                    f"Potential secret detected in {rel}: matched {pat.pattern}: {m.group(0)[:32]}..."
                )
