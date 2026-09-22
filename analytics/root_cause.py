from typing import Any, Dict, List


class RootCauseEngine:

    def __init__(self, analytics_engine):
        self.engine = analytics_engine

    # =========================================================
    # MAIN DIAGNOSIS
    # =========================================================

    def analyze(
        self,
        period="this_month"
    ):

        evidence = self.engine.diagnosis(
            period
        )

        candidates = []

        # -----------------------------------------------------
        # 1. SALES / VOLUME DRIVER
        # -----------------------------------------------------

        candidates.extend(
            self._analyze_sales_volume(
                evidence
            )
        )

        # -----------------------------------------------------
        # 2. PRODUCT DRIVER
        # -----------------------------------------------------

        candidates.extend(
            self._analyze_products(
                evidence
            )
        )

        # -----------------------------------------------------
        # 3. REGIONAL DRIVER
        # -----------------------------------------------------

        candidates.extend(
            self._analyze_regions(
                evidence
            )
        )

        # -----------------------------------------------------
        # 4. INVENTORY DRIVER
        # -----------------------------------------------------

        candidates.extend(
            self._analyze_inventory(
                evidence
            )
        )

        # -----------------------------------------------------
        # 5. MARKETING DRIVER
        # -----------------------------------------------------

        candidates.extend(
            self._analyze_marketing(
                evidence
            )
        )

        # -----------------------------------------------------
        # 6. ORDER DRIVER
        # -----------------------------------------------------

        candidates.extend(
            self._analyze_orders(
                evidence
            )
        )

        # -----------------------------------------------------
        # 7. FINANCE CONTEXT
        # -----------------------------------------------------

        candidates.extend(
            self._analyze_finance(
                evidence
            )
        )

        # -----------------------------------------------------
        # SORT BY IMPACT
        # -----------------------------------------------------

        impact_order = {

            "HIGH": 0,

            "MEDIUM": 1,

            "LOW": 2
        }

        candidates.sort(
            key=lambda item: (
                impact_order.get(
                    item["impact"],
                    99
                ),
                -item["confidence"]
            )
        )

        # -----------------------------------------------------
        # OVERALL BUSINESS EVENT
        # -----------------------------------------------------

        event = self._business_event(
            evidence
        )

        return {

            "period": evidence["period"],

            "business_event": event,

            "root_causes": candidates,

            "evidence_summary": {

                "revenue": evidence[
                    "overview"
                ]["revenue"],

                "units": evidence[
                    "overview"
                ]["units"],

                "orders": evidence[
                    "overview"
                ]["orders"],

                "customers": evidence[
                    "overview"
                ]["customers"]
            }
        }

    # =========================================================
    # BUSINESS EVENT
    # =========================================================

    def _business_event(
        self,
        evidence
    ):

        changes = evidence[
            "comparison"
        ]["metric_changes"]

        revenue_change = changes.get(
            "revenue"
        )

        if revenue_change is None:

            return (
                "Revenue could not be compared "
                "with the previous period."
            )

        if revenue_change > 0:

            return (
                f"Revenue increased by "
                f"{revenue_change:.2f}% "
                f"compared with the previous period."
            )

        if revenue_change < 0:

            return (
                f"Revenue decreased by "
                f"{abs(revenue_change):.2f}% "
                f"compared with the previous period."
            )

        return (
            "Revenue remained approximately "
            "unchanged compared with the "
            "previous period."
        )

    # =========================================================
    # SALES / VOLUME ANALYSIS
    # =========================================================

    def _analyze_sales_volume(
        self,
        evidence
    ):

        changes = evidence[
            "comparison"
        ]["metric_changes"]

        revenue_change = changes.get(
            "revenue"
        )

        units_change = changes.get(
            "units"
        )

        orders_change = changes.get(
            "orders"
        )

        if revenue_change is None:
            return []

        causes = []

        # -----------------------------------------------------
        # REVENUE UP
        # -----------------------------------------------------

        if revenue_change > 0:

            if (
                units_change is not None
                and units_change > 0
            ):

                causes.append({

                    "type": "sales_volume",

                    "title": (
                        "Higher sales volume "
                        "contributed to revenue growth"
                    ),

                    "description": (
                        f"Revenue increased by "
                        f"{revenue_change:.2f}% while "
                        f"units increased by "
                        f"{units_change:.2f}%."
                    ),

                    "evidence": [

                        f"Revenue change: "
                        f"{revenue_change:.2f}%",

                        f"Units change: "
                        f"{units_change:.2f}%"
                    ],

                    "impact": "HIGH",

                    "confidence": 0.90
                })

            if (
                orders_change is not None
                and orders_change > 0
            ):

                causes.append({

                    "type": "order_volume",

                    "title": (
                        "Higher order volume "
                        "supported revenue growth"
                    ),

                    "description": (
                        f"Orders increased by "
                        f"{orders_change:.2f}%."
                    ),

                    "evidence": [

                        f"Order change: "
                        f"{orders_change:.2f}%"
                    ],

                    "impact": "MEDIUM",

                    "confidence": 0.82
                })

        # -----------------------------------------------------
        # REVENUE DOWN
        # -----------------------------------------------------

        elif revenue_change < 0:

            if (
                units_change is not None
                and units_change < 0
            ):

                causes.append({

                    "type": "sales_volume",

                    "title": (
                        "Lower sales volume "
                        "contributed to revenue decline"
                    ),

                    "description": (
                        f"Revenue declined by "
                        f"{abs(revenue_change):.2f}% "
                        f"while units declined by "
                        f"{abs(units_change):.2f}%."
                    ),

                    "evidence": [

                        f"Revenue change: "
                        f"{revenue_change:.2f}%",

                        f"Units change: "
                        f"{units_change:.2f}%"
                    ],

                    "impact": "HIGH",

                    "confidence": 0.90
                })

            if (
                orders_change is not None
                and orders_change < 0
            ):

                causes.append({

                    "type": "order_volume",

                    "title": (
                        "Lower order volume "
                        "contributed to revenue decline"
                    ),

                    "description": (
                        f"Orders declined by "
                        f"{abs(orders_change):.2f}%."
                    ),

                    "evidence": [

                        f"Order change: "
                        f"{orders_change:.2f}%"
                    ],

                    "impact": "MEDIUM",

                    "confidence": 0.82
                })

        return causes

    # =========================================================
    # PRODUCT ANALYSIS
    # =========================================================

    def _analyze_products(
        self,
        evidence
    ):

        products = evidence[
            "comparison"
        ].get(
            "product_movement",
            []
        )

        if not products:
            return []

        top = products[0]

        change = top.get(
            "revenue_change",
            0
        )

        if change == 0:
            return []

        direction = (
            "increase"
            if change > 0
            else "decrease"
        )

        causes = [

            {

                "type": "product_driver",

                "title": (
                    f"Product-level revenue "
                    f"{direction}"
                ),

                "description": (
                    f"{top['product']} had the "
                    f"largest absolute product-level "
                    f"revenue movement."
                ),

                "evidence": [

                    f"Product: "
                    f"{top['product']}",

                    f"Current revenue: "
                    f"₹{top['current_revenue']:,.2f}",

                    f"Previous revenue: "
                    f"₹{top['previous_revenue']:,.2f}",

                    f"Revenue change: "
                    f"₹{top['revenue_change']:,.2f}"
                ],

                "impact": "HIGH",

                "confidence": 0.88
            }

        ]

        return causes

    # =========================================================
    # REGION ANALYSIS
    # =========================================================

    def _analyze_regions(
        self,
        evidence
    ):

        regions = evidence[
            "comparison"
        ].get(
            "regional_movement",
            []
        )

        if not regions:
            return []

        top = regions[0]

        change = top.get(
            "revenue_change",
            0
        )

        if change == 0:
            return []

        direction = (
            "growth"
            if change > 0
            else "decline"
        )

        return [

            {

                "type": "regional_driver",

                "title": (
                    f"Regional {direction} detected"
                ),

                "description": (
                    f"{top['region']} had the "
                    f"largest absolute regional "
                    f"revenue movement."
                ),

                "evidence": [

                    f"Region: "
                    f"{top['region']}",

                    f"Current revenue: "
                    f"₹{top['current_revenue']:,.2f}",

                    f"Previous revenue: "
                    f"₹{top['previous_revenue']:,.2f}",

                    f"Revenue change: "
                    f"₹{top['revenue_change']:,.2f}"
                ],

                "impact": "HIGH",

                "confidence": 0.84
            }
        ]

    # =========================================================
    # INVENTORY ANALYSIS
    # =========================================================

    def _analyze_inventory(
        self,
        evidence
    ):

        inventory = evidence[
            "inventory_evidence"
        ].get(
            "intelligence",
            []
        )

        causes = []

        for item in inventory:

            if item["priority"] != "CRITICAL":
                continue

            days = item[
                "days_of_stock"
            ]

            causes.append({

                "type": "inventory_risk",

                "title": (
                    f"Critical inventory risk: "
                    f"{item['product']}"
                ),

                "description": (
                    f"{item['product']} has only "
                    f"{days:.2f} days of stock "
                    f"remaining at current demand."
                ),

                "evidence": [

                    f"Current stock: "
                    f"{item['stock']} units",

                    f"Recent 30-day demand: "
                    f"{item['recent_demand']:.0f} units",

                    f"Daily demand: "
                    f"{item['daily_demand']:.2f} units",

                    f"Days of stock: "
                    f"{days:.2f}",

                    f"Recommended replenishment: "
                    f"{item['recommended_quantity']} units"
                ],

                "impact": "HIGH",

                "confidence": 0.95
            })

        return causes

    # =========================================================
    # MARKETING ANALYSIS
    # =========================================================

    def _analyze_marketing(
        self,
        evidence
    ):

        marketing = evidence[
            "marketing_evidence"
        ]

        leads = marketing.get(
            "leads",
            0
        )

        conversions = marketing.get(
            "conversions",
            0
        )

        conversion_rate = marketing.get(
            "conversion_rate",
            0
        )

        if leads <= 0:
            return []

        if conversion_rate >= 10:

            title = (
                "Marketing is generating "
                "measurable conversion"
            )

            impact = "MEDIUM"

            confidence = 0.75

        else:

            title = (
                "Marketing conversion "
                "is relatively weak"
            )

            impact = "MEDIUM"

            confidence = 0.72

        return [

            {

                "type": "marketing_driver",

                "title": title,

                "description": (
                    f"Marketing generated "
                    f"{leads:,.0f} leads and "
                    f"{conversions:,.0f} conversions "
                    f"at a {conversion_rate:.2f}% "
                    f"conversion rate."
                ),

                "evidence": [

                    f"Leads: "
                    f"{leads:,.0f}",

                    f"Conversions: "
                    f"{conversions:,.0f}",

                    f"Conversion rate: "
                    f"{conversion_rate:.2f}%",

                    f"Spend: "
                    f"₹{marketing.get('spend', 0):,.2f}"
                ],

                "impact": impact,

                "confidence": confidence
            }
        ]

    # =========================================================
    # ORDER ANALYSIS
    # =========================================================

    def _analyze_orders(
        self,
        evidence
    ):

        order_data = evidence[
            "order_evidence"
        ]

        cancellation_rate = order_data.get(
            "cancellation_rate",
            0
        )

        if cancellation_rate < 5:

            return []

        if cancellation_rate >= 10:

            impact = "HIGH"

            confidence = 0.88

        else:

            impact = "MEDIUM"

            confidence = 0.75

        return [

            {

                "type": "order_risk",

                "title": (
                    "Order cancellation risk detected"
                ),

                "description": (
                    f"Order cancellation rate is "
                    f"{cancellation_rate:.2f}%."
                ),

                "evidence": [

                    f"Cancellation rate: "
                    f"{cancellation_rate:.2f}%",

                    f"Orders: "
                    f"{order_data.get('orders', 0)}"
                ],

                "impact": impact,

                "confidence": confidence
            }
        ]

    # =========================================================
    # FINANCE ANALYSIS
    # =========================================================

    def _analyze_finance(
        self,
        evidence
    ):

        finance = evidence[
            "finance_evidence"
        ]

        revenue = finance.get(
            "revenue",
            0
        )

        expense = finance.get(
            "expense",
            finance.get(
                "expenses",
                0
            )
        )

        profit = finance.get(
            "profit",
            0
        )

        if revenue <= 0:
            return []

        margin = (
            profit / revenue
        ) * 100

        return [

            {

                "type": "finance_context",

                "title": (
                    "Financial performance context"
                ),

                "description": (
                    f"Finance records show "
                    f"₹{revenue:,.2f} revenue, "
                    f"₹{expense:,.2f} expense and "
                    f"₹{profit:,.2f} profit."
                ),

                "evidence": [

                    f"Revenue: "
                    f"₹{revenue:,.2f}",

                    f"Expense: "
                    f"₹{expense:,.2f}",

                    f"Profit: "
                    f"₹{profit:,.2f}",

                    f"Profit margin: "
                    f"{margin:.2f}%"
                ],

                "impact": "MEDIUM",

                "confidence": 0.90
            }
        ]