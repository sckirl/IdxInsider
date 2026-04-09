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

def calculate_score(transaction: Dict[str, Any], db=None) -> int:
    """
    Implements the Smart Scoring System as defined in DATA_SCHEMA.md.
    """
    score = 0
    t_type = str(transaction.get("transaction_type", "BUY")).upper()
    role = normalize_role(transaction.get("role", ""))
    value = float(transaction.get("value", 0))
    ticker = transaction.get("ticker", "")
    t_date = transaction.get("date")

    if t_type == "GIFT":
        return 0

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
            
        if transaction.get("ownership_change_pct", 0) > 0.1:
            score += 2
        
        # Cluster Buy Logic
        if db and ticker and t_date:
            from .models import InsiderTransaction
            import datetime
            seven_days_ago = t_date - datetime.timedelta(days=7)
            
            # Count distinct insiders who bought this ticker in the last 7 days
            other_insiders_count = db.query(InsiderTransaction.insider_name).filter(
                InsiderTransaction.ticker == ticker,
                InsiderTransaction.transaction_type == "BUY",
                InsiderTransaction.date >= seven_days_ago,
                InsiderTransaction.date <= t_date,
                InsiderTransaction.insider_name != transaction.get("insider_name")
            ).distinct().count()
            
            # Total unique insiders including the current one
            total_insiders = other_insiders_count + 1
            
            if total_insiders >= 3:
                score += 5
            elif total_insiders == 2:
                score += 3
            
    elif t_type == "SELL":
        score -= 2
        if role in ["DIREKTUR_UTAMA", "PENGENDALI"]:
            score -= 1
        if value >= 5_000_000_000:
            score -= 2

    return score
