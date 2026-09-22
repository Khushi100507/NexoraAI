from datetime import datetime, date
import calendar
import pandas as pd


class TimeIntelligence:

    def __init__(self, sales_data):
        self.sales = sales_data.copy()

        # Sales data contains mixed date formats.
        # format="mixed" allows pandas to correctly parse
        # both YYYY-MM-DD and YYYY-MM-DD HH:MM:SS.
        self.sales["date"] = pd.to_datetime(
            self.sales["date"],
            format="mixed"
        )

        self.min_date = self.sales["date"].min().date()
        self.max_date = self.sales["date"].max().date()

    # ---------------------------------------------------------
    # BASIC PERIOD HELPERS
    # ---------------------------------------------------------

    def _month_range(self, year, month):

        start = date(
            year,
            month,
            1
        )

        last_day = calendar.monthrange(
            year,
            month
        )[1]

        end = date(
            year,
            month,
            last_day
        )

        return start, end

    # ---------------------------------------------------------
    # RESOLVE PERIOD
    # ---------------------------------------------------------

    def resolve(self, period):

        period = period.lower().strip()

        today = self.max_date

        # -----------------------------
        # TODAY
        # -----------------------------

        if period == "today":

            return {
                "label": "Today",
                "start": today,
                "end": today
            }

        # -----------------------------
        # YESTERDAY
        # -----------------------------

        if period == "yesterday":

            day = today - pd.Timedelta(days=1)

            return {
                "label": "Yesterday",
                "start": day,
                "end": day
            }

        # -----------------------------
        # THIS MONTH
        # -----------------------------

        if period == "this_month":

            start, end = self._month_range(
                today.year,
                today.month
            )

            return {
                "label": "This month",
                "start": start,
                "end": end
            }

        # -----------------------------
        # LAST MONTH
        # -----------------------------

        if period == "last_month":

            if today.month == 1:

                year = today.year - 1
                month = 12

            else:

                year = today.year
                month = today.month - 1

            start, end = self._month_range(
                year,
                month
            )

            return {
                "label": "Last month",
                "start": start,
                "end": end
            }

        # -----------------------------
        # THIS YEAR
        # -----------------------------

        if period == "this_year":

            return {
                "label": "This year",
                "start": date(
                    today.year,
                    1,
                    1
                ),
                "end": date(
                    today.year,
                    12,
                    31
                )
            }

        # -----------------------------
        # LAST YEAR
        # -----------------------------

        if period == "last_year":

            year = today.year - 1

            return {
                "label": "Last year",
                "start": date(
                    year,
                    1,
                    1
                ),
                "end": date(
                    year,
                    12,
                    31
                )
            }

        # -----------------------------
        # SPECIFIC YEAR
        # Example: 2026
        # -----------------------------

        if period.isdigit() and len(period) == 4:

            year = int(period)

            return {
                "label": str(year),
                "start": date(
                    year,
                    1,
                    1
                ),
                "end": date(
                    year,
                    12,
                    31
                )
            }

        # -----------------------------
        # SPECIFIC MONTH
        # Example: 2026-03
        # -----------------------------

        try:

            parsed = datetime.strptime(
                period,
                "%Y-%m"
            )

            start, end = self._month_range(
                parsed.year,
                parsed.month
            )

            return {
                "label": parsed.strftime("%B %Y"),
                "start": start,
                "end": end
            }

        except ValueError:
            pass

        raise ValueError(
            f"Unsupported time period: {period}"
        )

    # ---------------------------------------------------------
    # FILTER SALES
    # ---------------------------------------------------------

    def filter_sales(self, period):

        resolved = self.resolve(period)

        start = pd.Timestamp(
            resolved["start"]
        )

        end = pd.Timestamp(
            resolved["end"]
        )

        filtered = self.sales[
            (self.sales["date"] >= start)
            &
            (self.sales["date"] <= end)
        ].copy()

        return filtered, resolved

    # ---------------------------------------------------------
    # PERIOD SUMMARY
    # ---------------------------------------------------------

    def summary(self, period):

        sales, resolved = self.filter_sales(
            period
        )

        return {
            "period": resolved["label"],

            "start": str(
                resolved["start"]
            ),

            "end": str(
                resolved["end"]
            ),

            "revenue": round(
                float(
                    sales["revenue"].sum()
                ),
                2
            ),

            "units": int(
                sales["units"].sum()
            ),

            "orders": int(
                sales["order_id"].nunique()
            ),

            "customers": int(
                sales["customer_id"].nunique()
            ),

            "profit": round(
                float(
                    sales["profit"].sum()
                ),
                2
            ),

            "expenses": round(
                float(
                    sales["expense"].sum()
                ),
                2
            )
        }

    # ---------------------------------------------------------
    # COMPARE TWO PERIODS
    # ---------------------------------------------------------

    def compare(
        self,
        current_period,
        previous_period
    ):

        current = self.summary(
            current_period
        )

        previous = self.summary(
            previous_period
        )

        current_revenue = current[
            "revenue"
        ]

        previous_revenue = previous[
            "revenue"
        ]

        if previous_revenue:

            revenue_change = (
                (
                    current_revenue
                    -
                    previous_revenue
                )
                /
                previous_revenue
            ) * 100

        else:

            revenue_change = 0

        return {
            "current": current,
            "previous": previous,
            "revenue_change_percent": round(
                revenue_change,
                2
            )
        }