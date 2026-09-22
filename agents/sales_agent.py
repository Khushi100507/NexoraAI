from typing import Any, Dict, List

from analytics.root_cause import RootCauseEngine


class SalesAgent:

    """
    Specialized agent responsible for sales intelligence.

    Responsibilities:
    - Detect significant revenue changes
    - Analyze unit and order movement
    - Identify product-level sales drivers
    - Identify regional sales drivers
    - Produce evidence-backed sales decisions

    The agent does NOT execute business actions.
    """

    def __init__(self, analytics_engine):
        self.engine = analytics_engine
        self.root_cause_engine = RootCauseEngine(
            analytics_engine
        )

    def analyze(
        self,
        period="this_month"
    ) -> Dict[str, Any]:

        diagnosis = self.root_cause_engine.analyze(
            period
        )

        root_causes = diagnosis.get(
            "root_causes",
            []
        )

        revenue_change = None
        units_change = None
        orders_change = None

        product_driver = None
        regional_driver = None

        for cause in root_causes:

            cause_type = cause.get(
                "type"
            )

            evidence = cause.get(
                "evidence",
                []
            )

            if cause_type == "sales_volume":

                revenue_change = self._extract_percentage(
                    evidence,
                    "Revenue change:"
                )

                units_change = self._extract_percentage(
                    evidence,
                    "Units change:"
                )

            elif cause_type == "order_volume":

                orders_change = self._extract_percentage(
                    evidence,
                    "Order change:"
                )

            elif cause_type == "products":

                product_driver = cause

            elif cause_type == "regions":

                regional_driver = cause

        event = self._classify_event(
            revenue_change
        )

        drivers = []

        if revenue_change is not None:

            drivers.append({
                "type": "revenue",
                "change": revenue_change
            })

        if units_change is not None:

            drivers.append({
                "type": "units",
                "change": units_change
            })

        if orders_change is not None:

            drivers.append({
                "type": "orders",
                "change": orders_change
            })

        if product_driver:

            drivers.append({
                "type": "product",
                "evidence":
                    product_driver.get(
                        "evidence",
                        []
                    )
            })

        if regional_driver:

            drivers.append({
                "type": "region",
                "evidence":
                    regional_driver.get(
                        "evidence",
                        []
                    )
            })

        decisions = self._build_decisions(
            event=event,
            revenue_change=revenue_change,
            units_change=units_change,
            orders_change=orders_change
        )

        return {
            "agent": "SalesAgent",
            "domain": "sales",
            "status": "ANALYZED",
            "period": diagnosis.get(
                "period"
            ),
            "business_event":
                diagnosis.get(
                    "business_event"
                ),
            "event_type":
                event,
            "drivers":
                drivers,
            "decisions":
                decisions,
            "summary": {
                "revenue_change":
                    revenue_change,
                "units_change":
                    units_change,
                "orders_change":
                    orders_change,
                "decision_count":
                    len(decisions)
            }
        }

    def _build_decisions(
        self,
        event,
        revenue_change,
        units_change,
        orders_change
    ) -> List[Dict[str, Any]]:

        decisions = []

        if (
            event == "GROWTH"
            and revenue_change is not None
            and revenue_change > 10
            and units_change is not None
            and units_change > 10
        ):

            evidence = [

                f"Revenue change: "
                f"{revenue_change:.2f}%",

                f"Units change: "
                f"{units_change:.2f}%"

            ]

            if orders_change is not None:

                evidence.append(
                    f"Order change: "
                    f"{orders_change:.2f}%"
                )

            decisions.append({

                "action_type":
                    "GROWTH_ANALYSIS",

                "domain":
                    "sales",

                "title":
                    "Analyze high-growth sales drivers",

                "priority":
                    "MEDIUM",

                "risk":
                    "LOW",

                "approval":
                    "NOT_REQUIRED",

                "expected_impact":
                    65,

                "reason":
                    (
                        f"Revenue increased by "
                        f"{revenue_change:.2f}% and "
                        f"units increased by "
                        f"{units_change:.2f}%."
                    ),

                "evidence":
                    evidence,

                "recommended_next_step":
                    (
                        "Identify high-performing "
                        "products, regions and "
                        "customer segments that "
                        "can be scaled."
                    ),

                "agent":
                    "SalesAgent",

                "agent_status":
                    "ANALYZED",

                "status":
                    "PROPOSED"

            })

        elif (
            event == "DECLINE"
            and revenue_change is not None
            and revenue_change < -10
        ):

            evidence = [

                f"Revenue change: "
                f"{revenue_change:.2f}%"

            ]

            if units_change is not None:

                evidence.append(
                    f"Units change: "
                    f"{units_change:.2f}%"
                )

            if orders_change is not None:

                evidence.append(
                    f"Order change: "
                    f"{orders_change:.2f}%"
                )

            decisions.append({

                "action_type":
                    "SALES_INVESTIGATION",

                "domain":
                    "sales",

                "title":
                    "Investigate revenue decline",

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
                        f"Revenue declined by "
                        f"{abs(revenue_change):.2f}%."
                    ),

                "evidence":
                    evidence,

                "recommended_next_step":
                    (
                        "Investigate product, "
                        "regional, customer, "
                        "inventory and marketing "
                        "drivers before executing "
                        "corrective action."
                    ),

                "agent":
                    "SalesAgent",

                "agent_status":
                    "ANALYZED",

                "status":
                    "PROPOSED"

            })

        return decisions

    def _classify_event(
        self,
        revenue_change
    ):

        if revenue_change is None:

            return "UNKNOWN"

        if revenue_change > 10:

            return "GROWTH"

        if revenue_change < -10:

            return "DECLINE"

        return "STABLE"

    def _extract_percentage(
        self,
        evidence,
        prefix
    ):

        for line in evidence:

            if not line.startswith(prefix):

                continue

            try:

                return float(
                    line.split(":")[1]
                    .replace("%", "")
                    .strip()
                )

            except (
                ValueError,
                IndexError
            ):

                return None

        return None