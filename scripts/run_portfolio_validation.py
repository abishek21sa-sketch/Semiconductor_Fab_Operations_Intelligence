from __future__ import annotations

import json
from pathlib import Path

from fabops import __release__, __version__
from fabops.research.portfolio_validation import portfolio_validation


def main():
    result = portfolio_validation(seed=117, replications=8, lot_count=12)
    out = {
        "release": __release__,
        "version": __version__,
        "status": "PASS" if result["hypothesis"]["reject_at_0_05"] else "REVIEW",
        "research_validation": result,
    }
    target = Path(__file__).resolve().parents[1] / "docs" / "validation" / "portfolio_release_validation.json"
    target.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    print(f"PORTFOLIO_RESEARCH_VALIDATION={out['status']}")


if __name__ == "__main__":
    main()
