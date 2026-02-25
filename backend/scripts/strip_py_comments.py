from __future__ import annotations

import io
import os
import sys
import fnmatch
import tokenize
import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Options:
    root: Path
    dry_run: bool = True
    include_glob: str = "*.py"
    exclude_globs: tuple[str, ...] = (
        "**/.venv/**",
        "**/venv/**",
        "**/__pycache__/**",
        "**/.git/**",
        "**/.pytest_cache/**",
        "**/alembic/versions/**",  # часто лучше не трогать миграции
        "**/alembic/env.py",
        "**/check_models.py",
        
    )
    encoding: str = "utf-8"


def _matches_any_glob(path_posix: str, globs: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(path_posix, g) for g in globs)


def remove_hash_comments_preserve_strings(src: str, *, encoding: str = "utf-8") -> str:
    """
    Removes only '#' comments (tokenize.COMMENT). Does NOT touch strings,
    so triple-quoted prompt templates remain intact.
    """
    out_tokens: list[tokenize.TokenInfo] = []
    reader = io.BytesIO(src.encode(encoding)).readline

    for tok in tokenize.tokenize(reader):
        if tok.type == tokenize.COMMENT:
            continue
        out_tokens.append(tok)

    return tokenize.untokenize(out_tokens).decode(encoding)


def iter_python_files(opts: Options):
    for path in opts.root.rglob(opts.include_glob):
        posix = path.as_posix()
        if _matches_any_glob(posix, opts.exclude_globs):
            continue
        if path.is_file():
            yield path


def process_file(path: Path, opts: Options) -> bool:
    original = path.read_text(encoding=opts.encoding)

    cleaned = remove_hash_comments_preserve_strings(original, encoding=opts.encoding)

    if cleaned == original:
        return False

    if opts.dry_run:
        print(f"[DRY] would update: {path}")
        return True

    path.write_text(cleaned, encoding=opts.encoding)
    print(f"[OK] updated: {path}")
    return True


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("root", nargs="?", default=None)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv[1:])

    root = Path(args.root) if args.root else Path.cwd()
    dry_run = not bool(args.apply)

    opts = Options(root=root, dry_run=dry_run)

    changed = 0
    scanned = 0
    for f in iter_python_files(opts):
        scanned += 1
        if process_file(f, opts):
            changed += 1

    print(f"Scanned: {scanned}, changed: {changed}, mode: {'DRY-RUN' if dry_run else 'APPLY'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))