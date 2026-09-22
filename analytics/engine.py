from pathlib import Path

import pandas as pd

from analytics.time_intelligence import TimeIntelligence


DATA = Path(__file__).resolve().parents[1] / "data"


class AnalyticsEngine:

    def __init__(self):
        self.refresh()

    # =========================================================
    # DATA REFRESH
    # =========================================================

    def refresh(self):

        self.sales = pd.read_csv(
            DATA / "sales.csv"
        )

        self.orders = pd.read_csv(
            DATA / "orders.csv"
        )

        self.customers = pd.read_csv(
            DATA / "customers.csv"
        )

        self.products = pd.read_csv(
            DATA / "products.csv"
        )

        self.inventory = pd.read_csv(
            DATA / "inventory.csv"
        )

        self.finance = pd.read_csv(
            DATA / "finance.csv"
        )

        self.marketing = pd.read_csv(
            DATA / "marketing.csv"
        )

        self.suppliers = pd.read_csv(
            DATA / "suppliers.csv"
        )

        # -----------------------------------------------------
        # DATE CLEANING
        # -----------------------------------------------------

        self.sales["date"] = pd.to_datetime(
            self.sales["date"],
            format="mixed"
        )

        self.orders["date"] = pd.to_datetime(
            self.orders["date"],
            format="mixed"
        )

        self.finance["date"] = pd.to_datetime(
            self.finance["date"],
            format="mixed"
        )

        self.marketing["date"] = pd.to_datetime(
            self.marketing["date"],
            format="mixed"
        )

        # -----------------------------------------------------
        # TIME INTELLIGENCE
        # -----------------------------------------------------

        self.time = TimeIntelligence(
            self.sales
        )

    # =========================================================
    # BUSINESS OVERVIEW
    # =========================================================

    def overview(self):

        current = self.time.summary(
            "this_month"
        )

        previous = self.time.summary(
            "last_month"
        )

        current_revenue = current["revenue"]
        previous_revenue = previous["revenue"]

        if previous_revenue:

            growth = (
                (
                    current_revenue
                    -
                    previous_revenue
                )
                /
                previous_revenue
            ) * 100

        else:

            growth = 0

        return {

            "period": current["period"],

            "start": current["start"],

            "end": current["end"],

            "revenue": current["revenue"],

            "previous_revenue": previous["revenue"],

            "revenue_growth": round(
                growth,
                2
            ),

            "units": current["units"],

            "orders": current["orders"],

            "customers": current["customers"],

            "profit": current["profit"],

            "expenses": current["expenses"],

            "low_stock_items": int(
                (
                    self.inventory["stock"]
                    <= self.inventory["reorder_level"]
                ).sum()
            ),

            "at_risk_customers": int(
                (
                    self.customers["risk_score"]
                    >= 70
                ).sum()
            )
        }

    # =========================================================
    # PERIOD SUMMARY
    # =========================================================

    def period_summary(self, period):

        return self.time.summary(
            period
        )

    # =========================================================
    # PERIOD COMPARISON
    # =========================================================

    def compare_periods(
        self,
        current_period,
        previous_period
    ):

        comparison = self.time.compare(
            current_period,
            previous_period
        )

        current = comparison["current"]
        previous = comparison["previous"]

        # -----------------------------------------------------
        # METRIC CHANGES
        # -----------------------------------------------------

        def percentage_change(
            current_value,
            previous_value
        ):

            if previous_value == 0:

                if current_value == 0:
                    return 0.0

                return None

            return round(
                (
                    (
                        current_value
                        -
                        previous_value
                    )
                    /
                    previous_value
                ) * 100,
                2
            )

        metric_changes = {

            "revenue": percentage_change(
                current["revenue"],
                previous["revenue"]
            ),

            "orders": percentage_change(
                current["orders"],
                previous["orders"]
            ),

            "customers": percentage_change(
                current["customers"],
                previous["customers"]
            ),

            "units": percentage_change(
                current["units"],
                previous["units"]
            ),

            "profit": percentage_change(
                current["profit"],
                previous["profit"]
            ),

            "expenses": percentage_change(
                current["expenses"],
                previous["expenses"]
            )
        }

        # -----------------------------------------------------
        # GET SALES FOR BOTH PERIODS
        # -----------------------------------------------------

        current_sales, _ = self.time.filter_sales(
            current_period
        )

        previous_sales, _ = self.time.filter_sales(
            previous_period
        )

        # -----------------------------------------------------
        # PRODUCT MOVEMENT
        # -----------------------------------------------------

        current_products = (
            current_sales
            .groupby("product")["revenue"]
            .sum()
            .rename("current_revenue")
        )

        previous_products = (
            previous_sales
            .groupby("product")["revenue"]
            .sum()
            .rename("previous_revenue")
        )

        product_movement = pd.concat(
            [
                current_products,
                previous_products
            ],
            axis=1
        ).fillna(0)

        product_movement["revenue_change"] = (
            product_movement["current_revenue"]
            -
            product_movement["previous_revenue"]
        )

        product_movement["revenue_change_percent"] = (
            product_movement.apply(
                lambda row: percentage_change(
                    row["current_revenue"],
                    row["previous_revenue"]
                ),
                axis=1
            )
        )

        product_movement = (
            product_movement
            .reset_index()
            .rename(
                columns={
                    "index": "product"
                }
            )
            .sort_values(
                "revenue_change",
                ascending=False
            )
        )

        # -----------------------------------------------------
        # REGIONAL MOVEMENT
        # -----------------------------------------------------

        current_regions = (
            current_sales
            .groupby("region")["revenue"]
            .sum()
            .rename("current_revenue")
        )

        previous_regions = (
            previous_sales
            .groupby("region")["revenue"]
            .sum()
            .rename("previous_revenue")
        )

        regional_movement = pd.concat(
            [
                current_regions,
                previous_regions
            ],
            axis=1
        ).fillna(0)

        regional_movement["revenue_change"] = (
            regional_movement["current_revenue"]
            -
            regional_movement["previous_revenue"]
        )

        regional_movement["revenue_change_percent"] = (
            regional_movement.apply(
                lambda row: percentage_change(
                    row["current_revenue"],
                    row["previous_revenue"]
                ),
                axis=1
            )
        )

        regional_movement = (
            regional_movement
            .reset_index()
            .rename(
                columns={
                    "index": "region"
                }
            )
            .sort_values(
                "revenue_change",
                ascending=False
            )
        )

        # -----------------------------------------------------
        # PRODUCT DRIVER
        # -----------------------------------------------------

        if not product_movement.empty:

            largest_product = (
                product_movement.iloc[0]
            )

            largest_product_name = (
                largest_product["product"]
            )

            largest_product_change = float(
                largest_product["revenue_change"]
            )

        else:

            largest_product_name = None
            largest_product_change = 0

        # -----------------------------------------------------
        # REGIONAL DRIVER
        # -----------------------------------------------------

        if not regional_movement.empty:

            largest_region = (
                regional_movement.iloc[0]
            )

            largest_region_name = (
                largest_region["region"]
            )

            largest_region_change = float(
                largest_region["revenue_change"]
            )

        else:

            largest_region_name = None
            largest_region_change = 0

        # -----------------------------------------------------
        # BUSINESS DRIVER
        # -----------------------------------------------------

        revenue_change = metric_changes["revenue"]

        units_change = metric_changes["units"]

        orders_change = metric_changes["orders"]

        if revenue_change is None:

            business_driver = (
                "Revenue could not be compared because "
                "the previous period had no revenue."
            )

        elif revenue_change > 0:

            if (
                units_change is not None
                and units_change > revenue_change
            ):

                business_driver = (
                    f"Revenue increased by "
                    f"{revenue_change:.2f}%, while units "
                    f"increased by {units_change:.2f}%. "
                    f"This indicates that higher sales volume "
                    f"was an important contributor to the "
                    f"revenue change."
                )

            else:

                business_driver = (
                    f"Revenue increased by "
                    f"{revenue_change:.2f}%."
                )

        elif revenue_change < 0:

            if (
                units_change is not None
                and units_change < revenue_change
            ):

                business_driver = (
                    f"Revenue decreased by "
                    f"{abs(revenue_change):.2f}%, while units "
                    f"also declined by "
                    f"{abs(units_change):.2f}%. "
                    f"This indicates that lower sales volume "
                    f"was an important contributor to the "
                    f"revenue decline."
                )

            else:

                business_driver = (
                    f"Revenue decreased by "
                    f"{abs(revenue_change):.2f}%."
                )

        else:

            business_driver = (
                "Revenue remained approximately unchanged "
                "between the selected periods."
            )

        # -----------------------------------------------------
        # PRODUCT / REGION EVIDENCE
        # -----------------------------------------------------

        driver_details = []

        if (
            largest_product_name is not None
            and largest_product_change != 0
        ):

            if largest_product_change > 0:

                driver_details.append(
                    f"{largest_product_name} contributed "
                    f"the largest absolute product-level "
                    f"revenue increase."
                )

            else:

                driver_details.append(
                    f"{largest_product_name} had the largest "
                    f"absolute product-level revenue movement."
                )

        if (
            largest_region_name is not None
            and largest_region_change != 0
        ):

            if largest_region_change > 0:

                driver_details.append(
                    f"{largest_region_name} contributed "
                    f"the largest absolute regional "
                    f"revenue increase."
                )

            else:

                driver_details.append(
                    f"{largest_region_name} had the largest "
                    f"absolute regional revenue movement."
                )

        if driver_details:

            business_driver = (
                business_driver
                + " "
                + " ".join(driver_details)
            )

        # -----------------------------------------------------
        # PRODUCT OUTPUT
        # -----------------------------------------------------

        product_output = []

        for _, row in product_movement.iterrows():

            product_output.append({

                "product": row["product"],

                "current_revenue": round(
                    float(
                        row["current_revenue"]
                    ),
                    2
                ),

                "previous_revenue": round(
                    float(
                        row["previous_revenue"]
                    ),
                    2
                ),

                "revenue_change": round(
                    float(
                        row["revenue_change"]
                    ),
                    2
                ),

                "revenue_change_percent": (
                    row["revenue_change_percent"]
                )
            })

        # -----------------------------------------------------
        # REGIONAL OUTPUT
        # -----------------------------------------------------

        regional_output = []

        for _, row in regional_movement.iterrows():

            regional_output.append({

                "region": row["region"],

                "current_revenue": round(
                    float(
                        row["current_revenue"]
                    ),
                    2
                ),

                "previous_revenue": round(
                    float(
                        row["previous_revenue"]
                    ),
                    2
                ),

                "revenue_change": round(
                    float(
                        row["revenue_change"]
                    ),
                    2
                ),

                "revenue_change_percent": (
                    row["revenue_change_percent"]
                )
            })

        comparison["metric_changes"] = metric_changes

        comparison["product_movement"] = (
            product_output
        )

        comparison["regional_movement"] = (
            regional_output
        )

        comparison["business_driver"] = (
            business_driver
        )

        comparison["driver_summary"] = {

            "largest_product": (
                largest_product_name
            ),

            "largest_product_change": round(
                largest_product_change,
                2
            ),

            "largest_region": (
                largest_region_name
            ),

            "largest_region_change": round(
                largest_region_change,
                2
            ),

            "revenue_change_percent": (
                revenue_change
            ),

            "units_change_percent": (
                units_change
            ),

            "orders_change_percent": (
                orders_change
            )
        }

        return comparison

    # =========================================================
    # SALES PERFORMANCE
    # =========================================================

    def sales_performance(
        self,
        period="this_month"
    ):

        sales, resolved = self.time.filter_sales(
            period
        )

        top = (
            sales
            .groupby(
                "product",
                as_index=False
            )
            .agg(
                revenue=("revenue", "sum"),
                units=("units", "sum")
            )
            .sort_values(
                "revenue",
                ascending=False
            )
            .head(10)
        )

        regions = (
            sales
            .groupby(
                "region",
                as_index=False
            )["revenue"]
            .sum()
            .sort_values(
                "revenue",
                ascending=False
            )
        )

        daily = (
            sales
            .groupby(
                "date",
                as_index=False
            )["revenue"]
            .sum()
            .sort_values(
                "date"
            )
        )

        return {

            "period": resolved["label"],

            "start": str(
                resolved["start"]
            ),

            "end": str(
                resolved["end"]
            ),

            "top_products": top.to_dict(
                "records"
            ),

            "regions": regions.to_dict(
                "records"
            ),

            "daily": [
                {
                    "date": str(
                        row.date.date()
                    ),

                    "revenue": round(
                        float(row.revenue),
                        2
                    )
                }

                for row in daily.itertuples()
            ]
        }

    # =========================================================
    # BUSINESS INSIGHTS
    # =========================================================

    def insights(self):

        overview = self.overview()

        output = []

        # -----------------------------------------------------
        # REVENUE SIGNAL
        # -----------------------------------------------------

        if overview["revenue_growth"] < -5:

            output.append({

                "severity": "high",

                "domain": "sales",

                "title": "Revenue decline detected",

                "summary": (
                    f"Revenue is down "
                    f"{abs(overview['revenue_growth']):.1f}% "
                    f"compared with last month."
                ),

                "recommendation": (
                    "Investigate product, region, inventory, "
                    "customer and marketing drivers."
                )
            })

        elif overview["revenue_growth"] > 5:

            output.append({

                "severity": "positive",

                "domain": "sales",

                "title": "Revenue growth detected",

                "summary": (
                    f"Revenue increased "
                    f"{overview['revenue_growth']:.1f}% "
                    f"compared with last month."
                ),

                "recommendation": (
                    "Identify the strongest products and regions "
                    "and evaluate scaling opportunities."
                )
            })

        # -----------------------------------------------------
        # INVENTORY SIGNALS
        # -----------------------------------------------------

        low_stock = self.inventory[
            self.inventory["stock"]
            <= self.inventory["reorder_level"]
        ]

        for row in low_stock.head(8).itertuples():

            output.append({

                "severity": "high",

                "domain": "inventory",

                "title": (
                    f"Low stock: {row.product}"
                ),

                "summary": (
                    f"{row.stock} units remain against "
                    f"reorder level {row.reorder_level}."
                ),

                "recommendation": (
                    f"Prepare a replenishment plan "
                    f"for {row.product}."
                )
            })

        # -----------------------------------------------------
        # ORDER CANCELLATION SIGNAL
        # -----------------------------------------------------

        cancellation_rate = (
            self.orders["status"]
            .eq("cancelled")
            .mean()
            * 100
        )

        if cancellation_rate > 8:

            output.append({

                "severity": "medium",

                "domain": "orders",

                "title": "Elevated cancellation rate",

                "summary": (
                    f"Cancellation rate is "
                    f"{cancellation_rate:.1f}%."
                ),

                "recommendation": (
                    "Investigate cancellation reasons, "
                    "delivery performance and inventory availability."
                )
            })

        return output

    # =========================================================
    # INVENTORY INTELLIGENCE
    # =========================================================

    def inventory_intelligence(self):

        self.refresh()

        sales = self.sales.copy()

        inventory = self.inventory.copy()

        if sales.empty or inventory.empty:
            return []

        # -----------------------------------------------------
        # DATE CLEANING
        # -----------------------------------------------------

        sales["date"] = pd.to_datetime(
            sales["date"],
            format="mixed",
            errors="coerce"
        )

        sales = sales.dropna(
            subset=["date"]
        )

        if sales.empty:
            return []

        # -----------------------------------------------------
        # NUMERIC CLEANING
        # -----------------------------------------------------

        sales["units"] = pd.to_numeric(
            sales["units"],
            errors="coerce"
        ).fillna(0)

        inventory["stock"] = pd.to_numeric(
            inventory["stock"],
            errors="coerce"
        ).fillna(0)

        inventory["reorder_level"] = pd.to_numeric(
            inventory["reorder_level"],
            errors="coerce"
        ).fillna(0)

        # -----------------------------------------------------
        # RECENT DEMAND
        # -----------------------------------------------------

        latest_date = sales["date"].max()

        recent_start = (
            latest_date
            - pd.Timedelta(days=30)
        )

        recent_sales = sales[
            sales["date"] >= recent_start
        ]

        # IMPORTANT:
        # Demand is based on actual units sold,
        # not number of transaction rows.

        demand = (
            recent_sales
            .groupby("product")["units"]
            .sum()
            .reset_index(
                name="recent_demand"
            )
        )

        # -----------------------------------------------------
        # MERGE INVENTORY + DEMAND
        # -----------------------------------------------------

        result = inventory.merge(
            demand,
            on="product",
            how="left"
        )

        result["recent_demand"] = (
            result["recent_demand"]
            .fillna(0)
        )

        # -----------------------------------------------------
        # DAILY DEMAND
        # -----------------------------------------------------

        result["daily_demand"] = (
            result["recent_demand"] / 30
        )

        # -----------------------------------------------------
        # DAYS OF STOCK
        # -----------------------------------------------------

        def calculate_days_of_stock(row):

            daily_demand = row["daily_demand"]

            stock = row["stock"]

            if daily_demand > 0:

                return stock / daily_demand

            return float("inf")

        result["days_of_stock"] = result.apply(
            calculate_days_of_stock,
            axis=1
        )

        # -----------------------------------------------------
        # STOCK GAP
        # -----------------------------------------------------

        result["stock_gap"] = (
            result["reorder_level"]
            -
            result["stock"]
        ).clip(
            lower=0
        )

        # -----------------------------------------------------
        # PRIORITY
        # -----------------------------------------------------

        def calculate_priority(row):

            stock = row["stock"]

            reorder = row["reorder_level"]

            days = row["days_of_stock"]

            if stock <= 0:
                return "CRITICAL"

            if days < 7:
                return "CRITICAL"

            if stock <= reorder:
                return "HIGH"

            if days < 14:
                return "MEDIUM"

            return "LOW"

        result["priority"] = result.apply(
            calculate_priority,
            axis=1
        )

        # -----------------------------------------------------
        # RECOMMENDED QUANTITY
        # -----------------------------------------------------

        target_stock = result[
            [
                "reorder_level",
                "recent_demand"
            ]
        ].max(
            axis=1
        )

        result["recommended_quantity"] = (
            target_stock
            -
            result["stock"]
        ).clip(
            lower=0
        )

        result["recommended_quantity"] = (
            result["recommended_quantity"]
            .round()
            .astype(int)
        )

        # -----------------------------------------------------
        # REMOVE LOW PRIORITY
        # -----------------------------------------------------

        result = result[
            result["priority"] != "LOW"
        ].copy()

        if result.empty:
            return []

        # -----------------------------------------------------
        # PRIORITY ORDER
        # -----------------------------------------------------

        priority_order = {

            "CRITICAL": 0,

            "HIGH": 1,

            "MEDIUM": 2
        }

        result["_priority_order"] = (
            result["priority"]
            .map(priority_order)
        )

        result = result.sort_values(
            by=[
                "_priority_order",
                "days_of_stock"
            ],
            ascending=[
                True,
                True
            ]
        )

        # -----------------------------------------------------
        # RETURN CLEAN DATA
        # -----------------------------------------------------

        output = []

        for _, row in result.iterrows():

            days_of_stock = row[
                "days_of_stock"
            ]

            if pd.isna(days_of_stock):

                days_of_stock = 0

            if days_of_stock == float("inf"):

                days_of_stock = 999999

            output.append({

                "product": row["product"],

                "stock": int(
                    row["stock"]
                ),

                "reorder_level": int(
                    row["reorder_level"]
                ),

                "recent_demand": round(
                    float(
                        row["recent_demand"]
                    ),
                    2
                ),

                "daily_demand": round(
                    float(
                        row["daily_demand"]
                    ),
                    2
                ),

                "days_of_stock": round(
                    float(days_of_stock),
                    2
                ),

                "stock_gap": int(
                    row["stock_gap"]
                ),

                "priority": row["priority"],

                "recommended_quantity": int(
                    row["recommended_quantity"]
                )
            })

        return output

    # =========================================================
    # BUSINESS DIAGNOSIS
    # =========================================================

    def diagnosis(
        self,
        period="this_month"
    ):

        # =====================================================
        # SELECTED PERIOD
        # =====================================================

        current = self.time.summary(
            period
        )

        # -----------------------------------------------------
        # PREVIOUS PERIOD
        # -----------------------------------------------------

        previous_period = "last_month"

        comparison = self.compare_periods(
            period,
            previous_period
        )

        # =====================================================
        # SALES EVIDENCE
        # =====================================================

        sales, resolved = self.time.filter_sales(
            period
        )

        if not sales.empty:

            top_products = (
                sales
                .groupby(
                    "product"
                )["revenue"]
                .sum()
                .sort_values(
                    ascending=False
                )
                .head(5)
            )

        else:

            top_products = pd.Series(
                dtype=float
            )

        if not sales.empty:

            top_regions = (
                sales
                .groupby(
                    "region"
                )["revenue"]
                .sum()
                .sort_values(
                    ascending=False
                )
            )

        else:

            top_regions = pd.Series(
                dtype=float
            )

        # =====================================================
        # INVENTORY EVIDENCE
        # =====================================================

        low_stock = self.inventory[
            self.inventory["stock"]
            <= self.inventory["reorder_level"]
        ].copy()

        inventory_intelligence = (
            self.inventory_intelligence()
        )

        # =====================================================
        # PERIOD DATES
        # =====================================================

        period_start = pd.Timestamp(
            resolved["start"]
        )

        period_end = pd.Timestamp(
            resolved["end"]
        )

        # =====================================================
        # ORDER EVIDENCE
        # =====================================================

        period_orders = self.orders[
            (
                self.orders["date"]
                >= period_start
            )
            &
            (
                self.orders["date"]
                <= period_end
            )
        ].copy()

        if not period_orders.empty:

            cancellation_rate = (
                period_orders["status"]
                .eq("cancelled")
                .mean()
                * 100
            )

        else:

            cancellation_rate = 0.0

        # =====================================================
        # CUSTOMER EVIDENCE
        # =====================================================

        customer_count = int(
            current["customers"]
        )

        # =====================================================
        # MARKETING EVIDENCE
        # =====================================================

        period_marketing = self.marketing[
            (
                self.marketing["date"]
                >= period_start
            )
            &
            (
                self.marketing["date"]
                <= period_end
            )
        ].copy()

        marketing_evidence = {

            "records": int(
                len(
                    period_marketing
                )
            )
        }

        if not period_marketing.empty:

            numeric_columns = (
                period_marketing
                .select_dtypes(
                    include="number"
                )
                .columns
                .tolist()
            )

            for column in numeric_columns:

                # Conversion rate is a derived metric.
                # Do NOT sum individual conversion rates.

                if column == "conversion_rate":
                    continue

                marketing_evidence[
                    column
                ] = round(
                    float(
                        period_marketing[
                            column
                        ].sum()
                    ),
                    2
                )

            # -------------------------------------------------
            # CORRECT CONVERSION RATE
            # -------------------------------------------------

            total_leads = marketing_evidence.get(
                "leads",
                0
            )

            total_conversions = marketing_evidence.get(
                "conversions",
                0
            )

            if total_leads > 0:

                marketing_evidence[
                    "conversion_rate"
                ] = round(
                    (
                        total_conversions
                        /
                        total_leads
                    ) * 100,
                    2
                )

            else:

                marketing_evidence[
                    "conversion_rate"
                ] = 0.0

        # =====================================================
        # FINANCE EVIDENCE
        # =====================================================

        period_finance = self.finance[
            (
                self.finance["date"]
                >= period_start
            )
            &
            (
                self.finance["date"]
                <= period_end
            )
        ].copy()

        finance_evidence = {

            "records": int(
                len(
                    period_finance
                )
            )
        }

        if not period_finance.empty:

            numeric_columns = (
                period_finance
                .select_dtypes(
                    include="number"
                )
                .columns
                .tolist()
            )

            for column in numeric_columns:

                finance_evidence[
                    column
                ] = round(
                    float(
                        period_finance[
                            column
                        ].sum()
                    ),
                    2
                )

        # =====================================================
        # FINAL DIAGNOSIS DATA
        # =====================================================

        return {

            "period": {

                "label": resolved["label"],

                "start": str(
                    resolved["start"]
                ),

                "end": str(
                    resolved["end"]
                )
            },

            "overview": current,

            "comparison": comparison,

            "sales_evidence": {

                "top_products": (
                    top_products
                    .round(2)
                    .to_dict()
                ),

                "top_regions": (
                    top_regions
                    .round(2)
                    .to_dict()
                )
            },

            "order_evidence": {

                "orders": int(
                    current["orders"]
                ),

                "cancellation_rate": round(
                    float(
                        cancellation_rate
                    ),
                    2
                )
            },

            "customer_evidence": {

                "customers": customer_count
            },

            "inventory_evidence": {

                "low_stock_items": (
                    low_stock[
                        [
                            "product",
                            "stock",
                            "reorder_level"
                        ]
                    ]
                    .to_dict(
                        "records"
                    )
                ),

                "intelligence": (
                    inventory_intelligence
                )
            },

            "marketing_evidence": (
                marketing_evidence
            ),

            "finance_evidence": (
                finance_evidence
            ),

            "investigation": (
                "NEXORAAI has collected sales, order, "
                "customer, inventory, marketing and "
                "finance evidence for the selected period. "
                "This evidence will be used by the diagnosis "
                "and decision layers to determine business "
                "drivers and recommended actions."
            )
        }

    # =========================================================
    # QUESTION CONTEXT
    # =========================================================

    def question_context(self):

        return {

            "overview": self.overview(),

            "sales": self.sales_performance(
                "this_month"
            ),

            "insights": self.insights(),

            "diagnosis": self.diagnosis()
        }

    # =========================================================
    # EXECUTE RESTOCK
    # =========================================================

    def execute_restock(
        self,
        product,
        quantity
    ):

        self.refresh()

        mask = self.inventory[
            "product"
        ].eq(product)

        if not mask.any():

            return {

                "success": False,

                "message": "Product not found."
            }

        index = self.inventory.index[
            mask
        ][0]

        old_stock = int(
            self.inventory.at[
                index,
                "stock"
            ]
        )

        quantity = int(
            quantity
        )

        if quantity <= 0:

            return {

                "success": False,

                "message": (
                    "Quantity must be greater than zero."
                )
            }

        new_stock = (
            old_stock
            +
            quantity
        )

        self.inventory.at[
            index,
            "stock"
        ] = new_stock

        self.inventory.to_csv(
            DATA / "inventory.csv",
            index=False
        )

        return {

            "success": True,

            "product": product,

            "old_stock": old_stock,

            "new_stock": new_stock,

            "quantity_added": quantity,

            "verified": (
                new_stock
                ==
                old_stock + quantity
            )
        }