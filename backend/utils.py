from typing import Dict, Any

def normalize_role(role_str: str) -> str:
    if not role_str:
        return "OTHERS"
    role_str = role_str.upper()
    if any(x in role_str for x in ["PRESIDEN DIREKTUR", "DIREKTUR UTAMA", "CEO"]):
        return "DIREKTUR_UTAMA"
    if "DIREKTUR" in role_str:
        return "DIREKTUR"
    if any(x in role_str for x in ["PRESIDEN KOMISARIS", "KOMISARIS UTAMA"]):
        return "KOMISARIS_UTAMA"
    if "KOMISARIS" in role_str:
        return "KOMISARIS"
    if any(x in role_str for x in ["PENGENDALI"]):
        return "PENGENDALI"
    if any(x in role_str for x in ["UTAMA"]):
        return "PEMEGANG_SAHAM_UTAMA"
    return "OTHERS"

def calculate_score(transaction: Dict[str, Any]) -> int:
    """
    Implements the Smart Scoring System as defined in DATA_SCHEMA.md.
    """
    score = 0
    t_type = str(transaction.get("transaction_type", "BUY")).upper()
    role = normalize_role(transaction.get("role", ""))
    value = float(transaction.get("value", 0))

    if t_type == "BUY":
        # Role Weight
        role_weights = {
            "DIREKTUR_UTAMA": 5,
            "KOMISARIS_UTAMA": 4,
            "DIREKTUR": 3,
            "PENGENDALI": 3,
            "KOMISARIS": 2,
            "PEMEGANG_SAHAM_UTAMA": 1,
            "OTHERS": 0
        }
        score += role_weights.get(role, 0)

        # Value Weight
        if value >= 10_000_000_000:
            score += 5
        elif value >= 5_000_000_000:
            score += 4
        elif value >= 1_000_000_000:
            score += 3
        elif value >= 500_000_000:
            score += 2
        elif value >= 100_000_000:
            score += 1
        
        # Bonus Modifiers
        if transaction.get("direct_ownership", True):
            score += 1
            
    elif t_type == "SELL":
        score -= 2
        if role in ["DIREKTUR_UTAMA", "PENGENDALI"]:
            score -= 1
        if value >= 5_000_000_000:
            score -= 2

    return score
