import math

class SuggestionAgent:
    """Agent that analyzes prediction and clustering results to provide actionable recommendations and cost estimation."""
    
    def run(self, risk_score: int, total_reviews: int, clusters: list, mismatches: list) -> dict:
        """Runs the suggestion engine, heuristically building suggestions based on risk score and data."""
        
        # Build Listing Improvements based on text factors and mismatches
        listing_improvements = []
        if mismatches:
            listing_improvements.append("Address the listing discrepancies found by the AI (e.g. materials, dimensions)")
            listing_improvements.append("Improve product title clarity to match customer expectations")
        if risk_score > 50:
            listing_improvements.append("Add highly detailed size chart and lifestyle images to reduce fit/expectation confusion")
            listing_improvements.append("Include a product overview video demonstrating real-world usage")
        else:
            listing_improvements.append("Add additional contextual product images")
            listing_improvements.append("Refine product description to highlight key selling points and minimize minor confusion")

        # Build Customer Expectation Fixes based on cluster themes
        expectation_fixes = []
        if clusters:
            for c in clusters[:2]:
                theme = c["theme"] if isinstance(c, dict) else c.theme
                expectation_fixes.append(f"Act on common complaints about: {theme.lower()}")
        if not expectation_fixes:
            expectation_fixes = [
                "Address mixed customer feedback systematically",
                "Ensure actual packaging reflects the marketed quality"
            ]

        # Build Seller Optimization
        seller_optimization = [
            "Use better packaging materials to prevent transit damage",
            "Optimize inventory stocking levels based on return probability",
            "Add a comparison chart with similar products to help buyers make informed decisions"
        ]

        # Cost Estimation (Heuristic scaling based on total_reviews and risk_score)
        base_factor = max(100, total_reviews * 2) * (risk_score / 100.0)
        
        return {
            "suggestions": {
                "listing_improvements": listing_improvements,
                "customer_expectation_fixes": expectation_fixes,
                "seller_optimization": seller_optimization
            },
            "cost_estimation": {
                "return_cost_breakdown": {
                    "logistics": int(base_factor * 150),
                    "refunds": int(base_factor * 200),
                    "warehouse": int(base_factor * 80),
                    "restocking": int(base_factor * 50)
                },
                "potential_savings": {
                    "better_images": int(base_factor * 70),
                    "clear_description": int(base_factor * 60),
                    "size_chart": int(base_factor * 40),
                    "better_packaging": int(base_factor * 30)
                }
            }
        }
