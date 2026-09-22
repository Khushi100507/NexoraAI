from typing import Any, Dict


class MarketingAgent:

    def __init__(self, analytics_engine):
        self.engine = analytics_engine

    def analyze(self, period="this_month") -> Dict[str, Any]:

        self.engine.refresh()

        marketing = self.engine.marketing

        if marketing is None or marketing.empty:
            return {
                "agent": "MarketingAgent",
                "domain": "marketing",
                "status": "NO_DATA",
                "period": period,
                "decisions": [],
                "summary": {
                    "leads": 0,
                    "conversions": 0,
                    "conversion_rate": 0,
                    "spend": 0,
                    "decision_count": 0
                }
            }

        # -------------------------------------------------
        # Find date column
        # -------------------------------------------------

        date_column = None

        for column in [
            "date",
            "marketing_date",
            "campaign_date",
            "created_at",
            "timestamp"
        ]:
            if column in marketing.columns:
                date_column = column
                break

        period_data = marketing.copy()

        if date_column:

            import pandas as pd

            dates = pd.to_datetime(
                period_data[date_column],
                errors="coerce",
                format="mixed"
            )

            if period == "this_month":

                latest = dates.dropna().max()

                if pd.notna(latest):

                    period_data = period_data[
                        (dates.dt.year == latest.year)
                        &
                        (dates.dt.month == latest.month)
                    ]

            elif period == "last_month":

                latest = dates.dropna().max()

                if pd.notna(latest):

                    year = latest.year
                    month = latest.month - 1

                    if month == 0:
                        month = 12
                        year -= 1

                    period_data = period_data[
                        (dates.dt.year == year)
                        &
                        (dates.dt.month == month)
                    ]

            elif (
                len(str(period)) == 7
                and str(period)[4] == "-"
            ):

                try:

                    year = int(str(period)[:4])
                    month = int(str(period)[5:7])

                    period_data = period_data[
                        (dates.dt.year == year)
                        &
                        (dates.dt.month == month)
                    ]

                except ValueError:
                    pass

            elif (
                str(period).isdigit()
                and len(str(period)) == 4
            ):

                year = int(period)

                period_data = period_data[
                    dates.dt.year == year
                ]

        if period_data.empty:

            return {
                "agent": "MarketingAgent",
                "domain": "marketing",
                "status": "NO_DATA",
                "period": period,
                "decisions": [],
                "summary": {
                    "leads": 0,
                    "conversions": 0,
                    "conversion_rate": 0,
                    "spend": 0,
                    "decision_count": 0
                }
            }

        # -------------------------------------------------
        # Detect columns
        # -------------------------------------------------

        def find_column(names):

            for name in names:
                if name in period_data.columns:
                    return name

            return None

        leads_column = find_column([
            "leads",
            "lead_count",
            "total_leads"
        ])

        conversions_column = find_column([
            "conversions",
            "conversion",
            "converted"
        ])

        spend_column = find_column([
            "spend",
            "marketing_spend",
            "ad_spend",
            "cost"
        ])

        leads = (
            float(period_data[leads_column].sum())
            if leads_column
            else 0
        )

        conversions = (
            float(period_data[conversions_column].sum())
            if conversions_column
            else 0
        )

        spend = (
            float(period_data[spend_column].sum())
            if spend_column
            else 0
        )

        conversion_rate = (
            conversions / leads * 100
            if leads > 0
            else 0
        )

        decisions = []

        # -------------------------------------------------
        # Marketing intelligence
        # -------------------------------------------------

        if conversion_rate < 5 and leads > 0:

            decisions.append({
                "action_type":
                    "MARKETING_OPTIMIZATION",

                "domain":
                    "marketing",

                "title":
                    "Optimize low-converting marketing",

                "priority":
                    "HIGH",

                "risk":
                    "MEDIUM",

                "approval":
                    "REQUIRED",

                "expected_impact":
                    75,

                "reason":
                    (
                        f"Marketing conversion rate is "
                        f"{conversion_rate:.2f}%."
                    ),

                "evidence": [
                    f"Leads: {leads:,.0f}",
                    f"Conversions: {conversions:,.0f}",
                    (
                        f"Conversion rate: "
                        f"{conversion_rate:.2f}%"
                    ),
                    f"Marketing spend: ₹{spend:,.2f}"
                ],

                "recommended_next_step":
                    (
                        "Identify underperforming campaigns "
                        "and evaluate budget allocation, "
                        "audience targeting and conversion "
                        "performance."
                    ),

                "agent":
                    "MarketingAgent",

                "agent_status":
                    "ANALYZED",

                "status":
                    "PROPOSED"
            })

        elif conversion_rate < 15 and leads > 0:

            decisions.append({
                "action_type":
                    "MARKETING_ANALYSIS",

                "domain":
                    "marketing",

                "title":
                    "Analyze marketing conversion performance",

                "priority":
                    "MEDIUM",

                "risk":
                    "LOW",

                "approval":
                    "NOT_REQUIRED",

                "expected_impact":
                    55,

                "reason":
                    (
                        f"Marketing conversion rate is "
                        f"{conversion_rate:.2f}%."
                    ),

                "evidence": [
                    f"Leads: {leads:,.0f}",
                    f"Conversions: {conversions:,.0f}",
                    (
                        f"Conversion rate: "
                        f"{conversion_rate:.2f}%"
                    ),
                    f"Marketing spend: ₹{spend:,.2f}"
                ],

                "recommended_next_step":
                    (
                        "Review campaign-level performance "
                        "and identify opportunities to "
                        "increase conversion efficiency."
                    ),

                "agent":
                    "MarketingAgent",

                "agent_status":
                    "ANALYZED",

                "status":
                    "PROPOSED"
            })

        return {
            "agent": "MarketingAgent",
            "domain": "marketing",
            "status": "ANALYZED",
            "period": period,
            "decisions": decisions,
            "summary": {
                "leads": round(leads, 2),
                "conversions": round(conversions, 2),
                "conversion_rate": round(
                    conversion_rate,
                    2
                ),
                "spend": round(spend, 2),
                "decision_count": len(decisions)
            }
        }