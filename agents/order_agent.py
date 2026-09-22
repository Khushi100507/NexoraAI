from typing import Any, Dict


class OrderAgent:

    def __init__(self, analytics_engine):
        self.engine = analytics_engine

    def analyze(self, period="this_month") -> Dict[str, Any]:

        self.engine.refresh()

        orders = self.engine.orders

        if orders is None or orders.empty:
            return {
                "agent": "OrderAgent",
                "domain": "orders",
                "status": "NO_DATA",
                "period": period,
                "decisions": [],
                "summary": {
                    "order_count": 0,
                    "decision_count": 0
                }
            }

        # -------------------------------------------------
        # Filter orders for the requested business period
        # -------------------------------------------------

        date_column = None

        for column in [
            "date",
            "order_date",
            "created_at",
            "timestamp"
        ]:
            if column in orders.columns:
                date_column = column
                break

        if date_column is None:
            period_data = orders.copy()

        else:
            order_dates = orders[date_column]

            try:
                order_dates = order_dates.astype("datetime64[ns]")
            except Exception:
                order_dates = __import__(
                    "pandas"
                ).to_datetime(
                    order_dates,
                    errors="coerce",
                    format="mixed"
                )

            period_data = orders.copy()
            period_data["_agent_date"] = order_dates

            # Current month
            if period == "this_month":

                latest_date = (
                    period_data["_agent_date"]
                    .dropna()
                    .max()
                )

                if latest_date is not None:

                    period_data = period_data[
                        (
                            period_data["_agent_date"].dt.year
                            == latest_date.year
                        )
                        &
                        (
                            period_data["_agent_date"].dt.month
                            == latest_date.month
                        )
                    ]

            # Previous month
            elif period == "last_month":

                latest_date = (
                    period_data["_agent_date"]
                    .dropna()
                    .max()
                )

                if latest_date is not None:

                    year = latest_date.year
                    month = latest_date.month - 1

                    if month == 0:
                        month = 12
                        year -= 1

                    period_data = period_data[
                        (
                            period_data["_agent_date"].dt.year
                            == year
                        )
                        &
                        (
                            period_data["_agent_date"].dt.month
                            == month
                        )
                    ]

            # YYYY-MM
            elif len(str(period)) == 7 and str(period)[4] == "-":

                try:
                    year = int(str(period)[:4])
                    month = int(str(period)[5:7])

                    period_data = period_data[
                        (
                            period_data["_agent_date"].dt.year
                            == year
                        )
                        &
                        (
                            period_data["_agent_date"].dt.month
                            == month
                        )
                    ]

                except ValueError:
                    pass

            # YYYY
            elif str(period).isdigit() and len(str(period)) == 4:

                year = int(period)

                period_data = period_data[
                    period_data["_agent_date"].dt.year
                    == year
                ]

            if "_agent_date" in period_data.columns:
                period_data = period_data.drop(
                    columns=["_agent_date"]
                )

        if period_data.empty:
            return {
                "agent": "OrderAgent",
                "domain": "orders",
                "status": "NO_DATA",
                "period": period,
                "decisions": [],
                "summary": {
                    "order_count": 0,
                    "decision_count": 0
                }
            }

        order_count = len(period_data)

        decisions = []

        # -------------------------------------------------
        # Detect order status
        # -------------------------------------------------

        cancellation_column = None

        for column in [
            "status",
            "order_status",
            "order_statuses"
        ]:
            if column in period_data.columns:
                cancellation_column = column
                break

        cancellation_rate = 0.0

        if cancellation_column:

            status_values = (
                period_data[cancellation_column]
                .astype(str)
                .str.lower()
                .str.strip()
            )

            cancelled = status_values.isin([
                "cancelled",
                "canceled",
                "cancel",
                "cancelled_order"
            ]).sum()

            cancellation_rate = (
                cancelled / order_count * 100
                if order_count
                else 0
            )

            if cancellation_rate >= 10:

                decisions.append({
                    "action_type":
                        "ORDER_INVESTIGATION",

                    "domain":
                        "orders",

                    "title":
                        "Investigate high order cancellation rate",

                    "priority":
                        "HIGH",

                    "risk":
                        "LOW",

                    "approval":
                        "NOT_REQUIRED",

                    "expected_impact":
                        70,

                    "reason":
                        (
                            f"Order cancellation rate is "
                            f"{cancellation_rate:.2f}%."
                        ),

                    "evidence": [
                        f"Orders: {order_count}",
                        (
                            f"Cancellation rate: "
                            f"{cancellation_rate:.2f}%"
                        )
                    ],

                    "recommended_next_step":
                        (
                            "Investigate cancellation reasons, "
                            "inventory availability and "
                            "fulfillment issues."
                        ),

                    "agent":
                        "OrderAgent",

                    "agent_status":
                        "ANALYZED",

                    "status":
                        "PROPOSED"
                })

        return {
            "agent": "OrderAgent",
            "domain": "orders",
            "status": "ANALYZED",
            "period": period,
            "decisions": decisions,
            "summary": {
                "order_count": order_count,
                "cancellation_rate": round(
                    cancellation_rate,
                    2
                ),
                "decision_count": len(
                    decisions
                )
            }
        }