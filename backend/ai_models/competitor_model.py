import json
import math
from pathlib import Path
from typing import Dict, Any, List, Optional

# Lightweight competitor analysis model with JSON-configured weights
# Avoids heavy ML dependencies; suitable for t2.micro

DEFAULT_WEIGHTS = {
    "intercept": -0.5,
    "estimated_value_log": 0.35,
    "category_risk": 0.6,
    "deadline_urgency": 0.4,
    "emd_ratio": -0.25,
    "location_factor": 0.15
}

CATEGORY_RISK = {
    "IT Services": 0.6,
    "Construction": 0.8,
    "Medical Equipment": 0.5,
    "Office Supplies": 0.3,
    "Consulting": 0.4
}

LOCATION_FACTOR = {
    "New Delhi": 0.2,
    "Mumbai": 0.25,
    "Bangalore": 0.22,
    "Chennai": 0.18,
    "Kolkata": 0.15,
    "Hyderabad": 0.2
}

DEFAULT_COMPETITORS = [
    {"name": "TechCorp Solutions", "base_win_rate": 0.65, "avg_margin": 0.125},
    {"name": "Global Vendors Ltd", "base_win_rate": 0.55, "avg_margin": 0.15},
    {"name": "Prime Suppliers", "base_win_rate": 0.45, "avg_margin": 0.18},
]


def sigmoid(x: float) -> float:
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


class SimpleCompetitorModel:
    def __init__(self, weights_path: Optional[Path] = None, competitors_path: Optional[Path] = None):
        self.weights = DEFAULT_WEIGHTS.copy()
        self.competitors = DEFAULT_COMPETITORS.copy()
        if weights_path and weights_path.exists():
            try:
                self.weights.update(json.loads(weights_path.read_text()))
            except Exception:
                pass
        if competitors_path and competitors_path.exists():
            try:
                self.competitors = json.loads(competitors_path.read_text())
            except Exception:
                pass

    def _featureize(self, tender: Dict[str, Any]) -> Dict[str, float]:
        est_val = float(tender.get("estimated_value", 0.0))
        emd = float(tender.get("emd_amount", 0.0))
        category = tender.get("category", "IT Services")
        location = tender.get("location", "New Delhi")

        # deadline_urgency: closer deadline => higher value
        deadline = tender.get("submission_deadline")
        published = tender.get("published_date")
        days_window = 30.0
        urgency = 0.5
        try:
            # If strings, API caller converts to datetime in server before calling model
            if deadline and published:
                delta_days = max(1.0, (deadline - published).days)
                urgency = max(0.0, min(1.0, (days_window - delta_days) / days_window))
        except Exception:
            pass

        features = {
            "estimated_value_log": math.log10(max(est_val, 1.0)),
            "emd_ratio": (emd / est_val) if est_val > 0 else 0.0,
            "category_risk": CATEGORY_RISK.get(category, 0.4),
            "location_factor": LOCATION_FACTOR.get(location, 0.15),
            "deadline_urgency": urgency,
        }
        return features

    def _base_score(self, features: Dict[str, float]) -> float:
        s = self.weights.get("intercept", 0.0)
        for k, v in features.items():
            s += self.weights.get(k, 0.0) * v
        return sigmoid(s)

    def predict(self, tender: Dict[str, Any]) -> List[Dict[str, Any]]:
        feats = self._featureize(tender)
        base = self._base_score(feats)

        out: List[Dict[str, Any]] = []
        for comp in self.competitors:
            name = comp.get("name", "Unknown")
            win_rate = float(comp.get("base_win_rate", 0.5))
            margin = float(comp.get("avg_margin", 0.15))

            # Adjust score: aggressive pricing gets higher threat when base is high
            pricing_factor = 1.0 - min(max(margin, 0.0), 0.4)  # 0.0..0.4 -> 1.0..0.6
            score = base * (0.5 + 0.5 * win_rate) * (0.7 + 0.3 * pricing_factor)
            score = max(0.0, min(1.0, score))

            if score >= 0.66:
                threat = "high"
            elif score >= 0.4:
                threat = "medium"
            else:
                threat = "low"

            out.append({
                "name": name,
                "win_rate": round(win_rate*100, 1),
                "avg_margin": round(margin*100, 1),
                "threat": threat,
                "threat_score": round(score, 3)
            })
        return out


def analyze_market(competitors: List[Dict[str, Any]]) -> str:
    highs = [c for c in competitors if c["threat"] == "high"]
    meds = [c for c in competitors if c["threat"] == "medium"]
    if len(highs) >= 2:
        return "Highly competitive market with multiple aggressive players. Consider differentiation and post-warranty support emphasis."
    if len(highs) == 1 and len(meds) >= 1:
        return "Moderately competitive: one aggressive leader and following challengers. Pricing discipline and value-adds recommended."
    if len(meds) >= 2:
        return "Balanced competition. Competitive pricing with quality focus likely to succeed."
    return "Low immediate threat. Focus on compliance and timely submission to maximize success chances."
