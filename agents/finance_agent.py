from typing import Any, Dict


class FinanceAgent:

    def __init__(self, analytics_engine):
        self.engine = analytics_engine

    def analyze(self, period="this_month") -> Dict[str, Any]:

        self.engine.refresh()

        finance = self.engine.finance

        if finance is None or finance.empty:
            return {
                "agent": "FinanceAgent",
                "domain": "finance",
                "status": "NO_DATA",
                "period": period,
                "decisions": [],
                "summary": {
                    "revenue": 0,
                    "expense": 0,
                    "profit": 0,
                    "margin": 0,
                    "decision_count": 0
                }
            }

        # Find date column
        date_column = None

        for column in [
            "date",
            "finance_date",
            "transaction_date",
            "created_at",
            "timestamp"
        ]:
            if column in finance.columns:
                date_column = column
                break

        period_data = finance.copy()

        if date_column:

            import pandas as pd

            dates = pd.to_datetime(
                period_data[date_column],
                errors="coerce",
                format="mixed"
            )

            period_data["_finance_date"] = dates

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
                "agent": "FinanceAgent",
                "domain": "finance",
                "status": "NO_DATA",
                "period": period,
                "decisions": [],
                "summary": {
                    "revenue": 0,
                    "expense": 0,
                    "profit": 0,
                    "margin": 0,
                    "decision_count": 0
                }
            }

        # -------------------------------------------------
        # Detect financial columns
        # -------------------------------------------------

        revenue_column = None
        expense_column = None
        profit_column = None

        for column in [
            "revenue",
            "sales",
            "income",
            "total_revenue"
        ]:
            if column in period_data.columns:
                revenue_column = column
                break

        for column in [
            "expense",
            "expenses",
            "cost",
            "total_expense"
        ]:
            if column in period_data.columns:
                expense_column = column
                break

        for column in [
            "profit",
            "net_profit",
            "gross_profit"
        ]:
            if column in period_data.columns:
                profit_column = column
                break

        revenue = (
            float(period_data[revenue_column].sum())
            if revenue_column
            else 0
        )

        expense = (
            float(period_data[expense_column].sum())
            if expense_column
            else 0
        )

        if profit_column:
            profit = float(
                period_data[profit_column].sum()
            )
        else:
            profit = revenue - expense

        margin = (
            (profit / revenue) * 100
            if revenue
            else 0
        )

        decisions = []

        # -------------------------------------------------
        # Financial pressure detection
        # -------------------------------------------------

        if margin < 10 and revenue > 0:

            decisions.append({
                "action_type":
                    "FINANCE_INVESTIGATION",

                "domain":
                    "finance",

                "title":
                    "Investigate low profit margin",

                "priority":
                    "HIGH",

                "risk":
                    "MEDIUM",

                "approval":
                    "NOT_REQUIRED",

                "expected_impact":
                    80,

                "reason":
                    (
                        f"Profit margin is only "
                        f"{margin:.2f}%."
                    ),

                "evidence": [
                    f"Revenue: ₹{revenue:,.2f}",
                    f"Expense: ₹{expense:,.2f}",
                    f"Profit: ₹{profit:,.2f}",
                    f"Profit margin: {margin:.2f}%"
                ],

                "recommended_next_step":
                    (
                        "Investigate major cost drivers, "
                        "product profitability and "
                        "operational expenses."
                    ),

                "agent":
                    "FinanceAgent",

                "agent_status":
                    "ANALYZED",

                "status":
                    "PROPOSED"
            })

        elif margin < 20 and revenue > 0:

            decisions.append({
                "action_type":
                    "MARGIN_ANALYSIS",

                "domain":
                    "finance",

                "title":
                    "Analyze moderate profit margin",

                "priority":
                    "MEDIUM",

                "risk":
                    "LOW",

                "approval":
                    "NOT_REQUIRED",

                "expected_impact":
                    60,

                "reason":
                    (
                        f"Current profit margin is "
                        f"{margin:.2f}%."
                    ),

                "evidence": [
                    f"Revenue: ₹{revenue:,.2f}",
                    f"Expense: ₹{expense:,.2f}",
                    f"Profit: ₹{profit:,.2f}",
                    f"Profit margin: {margin:.2f}%"
                ],

                "recommended_next_step":
                    (
                        "Review cost structure and "
                        "identify opportunities to "
                        "improve profitability."
                    ),

                "agent":
                    "FinanceAgent",

                "agent_status":
                    "ANALYZED",

                "status":
                    "PROPOSED"
            })

        return {
            "agent": "FinanceAgent",
            "domain": "finance",
            "status": "ANALYZED",
            "period": period,
            "decisions": decisions,
            "summary": {
                "revenue": round(revenue, 2),
                "expense": round(expense, 2),
                "profit": round(profit, 2),
                "margin": round(margin, 2),
                "decision_count": len(decisions)
            }
        }