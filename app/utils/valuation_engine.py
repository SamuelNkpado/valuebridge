# This is the core valuation logic from FR3.3

INDUSTRY_MULTIPLES = {
    "Technology": 4.0,
    "Food & Beverage": 2.5,
    "Retail": 2.0,
    "Manufacturing": 2.5,
    "Healthcare": 3.5,
    "Education": 3.0,
    "Agriculture": 2.0,
    "Real Estate": 3.0,
    "Finance": 3.5,
    "Other": 2.0,
}


def calculate_asset_based(total_assets: float, total_liabilities: float) -> float:
    """Net Asset Value = Assets - Liabilities"""
    if not total_assets or not total_liabilities:
        return 0.0
    return max(total_assets - total_liabilities, 0)


def calculate_income_based(profit: float, growth_rate: float = 0.10) -> float:
    """DCF simplified = Profit / (Discount Rate - Growth Rate)"""
    if not profit:
        return 0.0
    discount_rate = 0.20  # 20% discount rate for Nigerian SMEs
    if discount_rate <= growth_rate:
        growth_rate = 0.05
    return profit / (discount_rate - growth_rate)


def calculate_market_multiples(annual_revenue: float, industry: str) -> float:
    """Value = Revenue × Industry Multiple"""
    if not annual_revenue:
        return 0.0
    multiple = INDUSTRY_MULTIPLES.get(industry, 2.0)
    return annual_revenue * multiple


def calculate_combined(
    asset_value: float, income_value: float, market_value: float
) -> float:
    """Weighted average of all three methods"""
    values = [v for v in [asset_value, income_value, market_value] if v > 0]
    if not values:
        return 0.0
    return sum(values) / len(values)
