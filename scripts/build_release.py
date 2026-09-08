from __future__ import annotations

import hashlib
import json
import re
import tomllib
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)

project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
version = project["version"]
init_text = (ROOT / "src" / "fabops" / "__init__.py").read_text(encoding="utf-8")
release_match = re.search(r'__release__\s*=\s*["\']([^"\']+)', init_text)
version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)', init_text)
release = release_match.group(1) if release_match else "UNSPECIFIED_RELEASE"
package_version = version_match.group(1) if version_match else None
if package_version != version:
    raise RuntimeError(f"version mismatch: pyproject={version}, fabops={package_version}")

EXCLUDE_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "dist", ".mypy_cache", ".ruff_cache"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".db", ".sqlite", ".sqlite3"}
EXCLUDE_NAMES = {"MANIFEST_RELEASE.json"}


def excluded(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return True
    if any(part.endswith(".egg-info") for part in rel.parts):
        return True
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return True
    if path.name in EXCLUDE_NAMES:
        return True
    return False


files = [p for p in sorted(ROOT.rglob("*")) if p.is_file() and not excluded(p)]
manifest = {
    "release": release,
    "version": version,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "evidence_boundary": "Source release for synthetic/reference portfolio validation; not production fab deployment.",
    "file_count": len(files),
    "files": [],
}
for p in files:
    rel = p.relative_to(ROOT).as_posix()
    data = p.read_bytes()
    manifest["files"].append({"path": rel, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})

manifest_path = ROOT / "MANIFEST_RELEASE.json"
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
files.append(manifest_path)

out = DIST / f"Semiconductor_Fab_Operations_Intelligence_{release}_{version}_SOURCE.zip"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
    for p in sorted(files):
        zf.write(p, Path(ROOT.name) / p.relative_to(ROOT))

digest = hashlib.sha256(out.read_bytes()).hexdigest()
sha_path = out.with_suffix(out.suffix + ".sha256")
sha_path.write_text(f"{digest}  {out.name}\n", encoding="utf-8")

print(json.dumps({"release": release, "version": version, "zip": str(out), "sha256": digest, "files": len(files)}, indent=2))
