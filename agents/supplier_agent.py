from typing import Any, Dict


class SupplierAgent:

    def __init__(self, analytics_engine):
        self.engine = analytics_engine

    def analyze(self, period="this_month") -> Dict[str, Any]:

        self.engine.refresh()

        suppliers = self.engine.suppliers

        if suppliers is None or suppliers.empty:
            return {
                "agent": "SupplierAgent",
                "domain": "suppliers",
                "status": "NO_DATA",
                "period": period,
                "decisions": [],
                "summary": {
                    "supplier_count": 0,
                    "decision_count": 0
                }
            }

        supplier_count = len(suppliers)
        decisions = []

        # -----------------------------------------------
        # Detect supplier status / performance columns
        # -----------------------------------------------

        status_column = None

        for column in [
            "status",
            "supplier_status",
            "availability",
            "supplier_availability"
        ]:
            if column in suppliers.columns:
                status_column = column
                break

        risk_count = 0

        if status_column:

            values = (
                suppliers[status_column]
                .astype(str)
                .str.lower()
                .str.strip()
            )

            risky = values.isin([
                "inactive",
                "unavailable",
                "delayed",
                "at_risk",
                "risk",
                "critical"
            ])

            risk_count = int(risky.sum())

            if risk_count > 0:

                risk_percentage = (
                    risk_count / supplier_count * 100
                    if supplier_count
                    else 0
                )

                priority = (
                    "HIGH"
                    if risk_percentage >= 20
                    else "MEDIUM"
                )

                decisions.append({
                    "action_type":
                        "SUPPLIER_INVESTIGATION",

                    "domain":
                        "suppliers",

                    "title":
                        "Investigate supplier risk",

                    "priority":
                        priority,

                    "risk":
                        "MEDIUM",

                    "approval":
                        "NOT_REQUIRED",

                    "expected_impact":
                        70,

                    "reason":
                        (
                            f"{risk_count} of "
                            f"{supplier_count} suppliers "
                            f"show potential supply risk."
                        ),

                    "evidence": [
                        f"Total suppliers: {supplier_count}",
                        f"Risky suppliers: {risk_count}",
                        (
                            f"Risk percentage: "
                            f"{risk_percentage:.2f}%"
                        )
                    ],

                    "recommended_next_step":
                        (
                            "Review supplier availability, "
                            "delivery reliability and "
                            "inventory dependencies."
                        ),

                    "agent":
                        "SupplierAgent",

                    "agent_status":
                        "ANALYZED",

                    "status":
                        "PROPOSED"
                })

        # -----------------------------------------------
        # Check supplier quantity / capacity information
        # -----------------------------------------------

        capacity_column = None

        for column in [
            "capacity",
            "available_capacity",
            "supply_capacity",
            "quantity"
        ]:
            if column in suppliers.columns:
                capacity_column = column
                break

        low_capacity_count = 0

        if capacity_column:

            try:

                values = suppliers[
                    capacity_column
                ].astype(float)

                low_capacity_count = int(
                    (values <= 20).sum()
                )

                if (
                    low_capacity_count > 0
                    and not decisions
                ):

                    decisions.append({
                        "action_type":
                            "SUPPLIER_CAPACITY_ANALYSIS",

                        "domain":
                            "suppliers",

                        "title":
                            "Analyze low supplier capacity",

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
                                f"{low_capacity_count} suppliers "
                                "have low available capacity."
                            ),

                        "evidence": [
                            f"Total suppliers: {supplier_count}",
                            (
                                f"Low-capacity suppliers: "
                                f"{low_capacity_count}"
                            )
                        ],

                        "recommended_next_step":
                            (
                                "Review supplier capacity and "
                                "identify alternative suppliers "
                                "for critical products."
                            ),

                        "agent":
                            "SupplierAgent",

                        "agent_status":
                            "ANALYZED",

                        "status":
                            "PROPOSED"
                    })

            except (ValueError, TypeError):
                pass

        return {
            "agent": "SupplierAgent",
            "domain": "suppliers",
            "status": "ANALYZED",
            "period": period,
            "decisions": decisions,
            "summary": {
                "supplier_count": supplier_count,
                "risk_count": risk_count,
                "low_capacity_count": low_capacity_count,
                "decision_count": len(decisions)
            }
        }