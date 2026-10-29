"""从受控基础 SVG 生成已批准色板；--check 只校验，不写资源。"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "ui" / "family-ui-final" / "icon-provenance.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    icons = ROOT / "resources" / "icons"
    expected_paths = set()
    for name, spec in manifest["icons"].items():
        source = icons / f"{name}.svg"
        raw = source.read_bytes()
        # The repository enforces LF. Older Windows worktrees can retain CRLF;
        # provenance hashes identify Git bytes, while rendering preserves the
        # local source's endings for an exact variant byte comparison.
        if sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != spec["source_sha256"]:
            raise ValueError(f"基础图标需重新审查来源：{source.name}")
        for color in spec["colors"]:
            target = icons / "tinted" / f"{name}-{color}.svg"
            expected_paths.add(target)
            rendered = raw.replace(b'currentColor', f"#{color}".encode("ascii"))
            if args.check:
                if target.read_bytes() != rendered:
                    raise ValueError(f"色板变体漂移：{target.name}")
            else:
                target.write_bytes(rendered)
    if set((icons / "tinted").glob("*.svg")) != expected_paths:
        raise ValueError("存在未登记或缺失的色板变体")
    print(f"family icon variants: PASS ({len(expected_paths)} SVGs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
