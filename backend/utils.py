from typing import Dict, Any, List, Tuple
import datetime
import json

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

def get_market_metadata(ticker: str) -> Dict[str, Any]:
    """
    Fetch market data (RVOL and Price History) for a ticker via yfinance.
    """
    import yfinance as yf
    try:
        # IDX tickers need .JK suffix
        symbol = f"{ticker.upper()}.JK"
        stock = yf.Ticker(symbol)
        
        # Get history for the last 30 days to calculate 20-day average volume
        hist = stock.history(period="1mo")
        if hist.empty:
            return {"rvol": 1.0, "price_history": []}
            
        # 20-day average volume
        avg_vol_20 = hist['Volume'].tail(20).mean()
        current_vol = hist['Volume'].iloc[-1]
        rvol = current_vol / avg_vol_20 if avg_vol_20 > 0 else 1.0
        
        # Last 5 days close prices
        price_history = hist['Close'].tail(5).tolist()
        
        return {
            "rvol": float(round(rvol, 2)),
            "price_history": [float(round(p, 2)) for p in price_history]
        }
    except Exception as e:
        print(f"Error fetching market data for {ticker}: {e}")
        return {"rvol": 1.0, "price_history": []}

def calculate_score(transaction: Dict[str, Any], db=None) -> Tuple[int, List[str]]:
    """
    Implements the Smart Scoring System with reason breakdown.
    """
    score = 0
    reasons = []
    t_type = str(transaction.get("transaction_type", "BUY")).upper()
    role = normalize_role(transaction.get("role", ""))
    value = float(transaction.get("value", 0))
    ticker = transaction.get("ticker", "")
    t_date = transaction.get("date")

    if t_type == "GIFT":
        return 0, ["Gift/Inheritance (0)"]

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
        r_weight = role_weights.get(role, 0)
        if r_weight > 0:
            score += r_weight
            reasons.append(f"{role.replace('_', ' ')} Buy (+{r_weight})")

        # Value Weight
        if value >= 10_000_000_000:
            score += 5
            reasons.append("Ultra Large Value (+5)")
        elif value >= 5_000_000_000:
            score += 4
            reasons.append("Very Large Value (+4)")
        elif value >= 1_000_000_000:
            score += 3
            reasons.append("Large Value (+3)")
        elif value >= 500_000_000:
            score += 2
            reasons.append("Significant Value (+2)")
        elif value >= 100_000_000:
            score += 1
            reasons.append("Standard Value (+1)")
        
        # Bonus Modifiers
        if transaction.get("direct_ownership", True):
            score += 1
            reasons.append("Direct Ownership (+1)")
            
        if transaction.get("ownership_change_pct", 0) > 0.1:
            score += 2
            reasons.append("Significant Stake Increase (+2)")
        
        # Double-Conviction (Buyback)
        if transaction.get("is_buyback", False):
            score += 3
            reasons.append("Double-Conviction: Coincides with Buyback (+3)")
            
        # RVOL Modifiers
        rvol = transaction.get("rvol", 1.0)
        if rvol >= 2.0:
            score += 2
            reasons.append(f"High RVOL {rvol}x (+2)")
        
        # Cluster Buy Logic
        if db and ticker and t_date:
            from .models import InsiderTransaction
            seven_days_ago = t_date - datetime.timedelta(days=7)
            
            other_insiders_count = db.query(InsiderTransaction.insider_name).filter(
                InsiderTransaction.ticker == ticker,
                InsiderTransaction.transaction_type == "BUY",
                InsiderTransaction.date >= seven_days_ago,
                InsiderTransaction.date <= t_date,
                InsiderTransaction.insider_name != transaction.get("insider_name")
            ).distinct().count()
            
            total_insiders = other_insiders_count + 1
            
            if total_insiders >= 3:
                score += 5
                reasons.append(f"Strong Cluster: {total_insiders} Insiders (+5)")
            elif total_insiders == 2:
                score += 3
                reasons.append("Small Cluster: 2 Insiders (+3)")
            
    elif t_type == "SELL":
        score -= 2
        reasons.append("Insider Sell (-2)")
        if role in ["DIREKTUR_UTAMA", "PENGENDALI"]:
            score -= 1
            reasons.append("Key Management Sell (-1)")
        if value >= 5_000_000_000:
            score -= 2
            reasons.append("Large Value Sell (-2)")

    return score, reasons
