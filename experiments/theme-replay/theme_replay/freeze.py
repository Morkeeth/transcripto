"""Freeze the Stage 0 synthetic corpus. Never reads private transcript roots."""

from __future__ import annotations

import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

from .citations import flatten_episode
from .schema import FORBIDDEN_PATH_MARKERS, HARNESSES, KINDS, REQUIRED_EPISODE, REQUIRED_EVENT


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf8")).hexdigest()


def load_episodes(path: Path) -> list[dict]:
    rows = []
    for raw in path.read_text(encoding="utf8").splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        rows.append(row)
    return rows


def assert_stage0(episodes: list[dict]) -> None:
    dumped = json.dumps(episodes)
    for marker in FORBIDDEN_PATH_MARKERS:
        if marker in dumped:
            raise ValueError(f"private-path marker {marker} is not allowed in Stage 0")
    if len(episodes) != 12:
        raise ValueError(f"Stage 0 needs 12 episodes, got {len(episodes)}")
    ids = [row["episode_id"] for row in episodes]
    if len(set(ids)) != 12:
        raise ValueError("episode ids must be unique")
    for row in episodes:
        for key in REQUIRED_EPISODE:
            if key not in row:
                raise ValueError(f"{row.get('episode_id')} missing {key}")
        if row["provenance"] != "synthetic":
            raise ValueError(f"{row['episode_id']} is not synthetic")
        if row["harness"] not in HARNESSES:
            raise ValueError(f"{row['episode_id']} has unknown harness")
        if row["kind"] not in KINDS:
            raise ValueError(f"{row['episode_id']} has unknown kind")
        for event in row["events"]:
            for key in REQUIRED_EVENT:
                if key not in event:
                    raise ValueError(f"{row['episode_id']} event missing {key}")
    counts = Counter((row["harness"], row["kind"]) for row in episodes)
    for harness in HARNESSES:
        for kind in KINDS:
            if counts[(harness, kind)] != 1:
                raise ValueError(f"need one {harness} {kind} episode")


def freeze(
    source: Path,
    out: Path,
    question: str,
    prompt: str,
    protocol: dict,
) -> dict:
    episodes = load_episodes(source)
    assert_stage0(episodes)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "episodes.jsonl"
    shutil.copyfile(source, dest)
    indexed = []
    for row in episodes:
        indexed.append(
            {
                "episode_id": row["episode_id"],
                "harness": row["harness"],
                "kind": row["kind"],
                "provenance": row["provenance"],
                "open": row.get("open"),
                "lines": flatten_episode(row),
                "events": row["events"],
            }
        )
    (out / "question.txt").write_text(question.rstrip() + "\n", encoding="utf8")
    (out / "analysis-prompt.txt").write_text(prompt.rstrip() + "\n", encoding="utf8")
    (out / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n", encoding="utf8")
    (out / "corpus-index.json").write_text(
        json.dumps({"episodes": indexed}, indent=2) + "\n",
        encoding="utf8",
    )
    manifest = {
        "stage": 0,
        "n": 12,
        "harnesses": {name: 4 for name in HARNESSES},
        "kinds": {name: 3 for name in KINDS},
        "question": question.strip(),
        "files": {
            "episodes.jsonl": sha256_file(dest),
            "question.txt": sha256_file(out / "question.txt"),
            "analysis-prompt.txt": sha256_file(out / "analysis-prompt.txt"),
            "protocol.json": sha256_file(out / "protocol.json"),
            "corpus-index.json": sha256_file(out / "corpus-index.json"),
        },
        "private_transcripts": False,
    }
    (out / "dataset-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf8")
    return manifest
