from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from empirical.public_data_backbone import data_backbone_status


def test_secom_public_case_contains_model_challenger_review():
    case = data_backbone_status()["case_study"]
    model = case["yield_excursion_model"]
    names = {row["model"] for row in model["model_comparison"]}
    assert {"constant_prevalence_baseline", "nearest_centroid_challenger", "class_balanced_logistic_champion"} <= names
    assert model["selected_model"] == "class_balanced_logistic_champion"
