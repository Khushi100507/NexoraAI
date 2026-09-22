from typing import Any, Dict


class InventoryAgent:

    def __init__(self, analytics_engine):
        self.engine = analytics_engine

    def analyze(self) -> Dict[str, Any]:

        self.engine.refresh()

        inventory_data = self.engine.inventory_intelligence()

        # inventory_intelligence() returns a list
        # of inventory risk records.
        if isinstance(inventory_data, list):
            risks = inventory_data
        else:
            risks = inventory_data.get("risks", [])

        decisions = []

        for item in risks:

            priority = item.get(
                "risk_level",
                item.get(
                    "priority",
                    "MEDIUM"
                )
            )

            priority = str(
                priority
            ).upper()

            if priority not in [
                "CRITICAL",
                "HIGH",
                "MEDIUM",
                "LOW"
            ]:
                priority = "MEDIUM"

            product = item.get(
                "product",
                "Unknown Product"
            )

            stock = item.get(
                "stock",
                0
            )

            reorder_level = item.get(
                "reorder_level",
                0
            )

            days_of_stock = item.get(
                "days_of_stock",
                0
            )

            recommended_quantity = item.get(
                "recommended_restock",
                item.get(
                    "recommended_quantity",
                    item.get(
                        "recommended",
                        0
                    )
                )
            )

            try:
                days_of_stock = float(
                    days_of_stock
                )
            except (
                ValueError,
                TypeError
            ):
                days_of_stock = 0.0

            try:
                recommended_quantity = int(
                    recommended_quantity
                )
            except (
                ValueError,
                TypeError
            ):
                recommended_quantity = 0

            if priority == "CRITICAL":
                risk = "HIGH"
                expected_impact = 95

            elif priority == "HIGH":
                risk = "MEDIUM"
                expected_impact = 80

            else:
                risk = "LOW"
                expected_impact = 60

            if days_of_stock > 0:

                reason = (
                    f"{product} has only "
                    f"{days_of_stock:.2f} days of stock "
                    "remaining at current demand."
                )

            else:

                reason = (
                    f"{product} is below its "
                    "operational inventory threshold."
                )

            decisions.append({

                "action_type":
                    "RESTOCK",

                "domain":
                    "inventory",

                "title":
                    f"Restock {product}",

                "priority":
                    priority,

                "risk":
                    risk,

                "approval":
                    "REQUIRED",

                "expected_impact":
                    expected_impact,

                "reason":
                    reason,

                "evidence": [
                    f"Product: {product}",
                    f"Current stock: {stock}",
                    f"Reorder level: {reorder_level}",
                    (
                        f"Days of stock: "
                        f"{days_of_stock:.2f}"
                    ),
                    (
                        f"Recommended restock: "
                        f"{recommended_quantity}"
                    )
                ],

                "recommended_next_step":
                    (
                        f"Restock {product} by "
                        f"{recommended_quantity} units "
                        "after human approval."
                    ),

                "product":
                    product,

                "quantity":
                    recommended_quantity,

                "agent":
                    "InventoryAgent",

                "agent_status":
                    "ANALYZED",

                "status":
                    "PROPOSED"
            })

        return {

            "agent":
                "InventoryAgent",

            "domain":
                "inventory",

            "status":
                "ANALYZED",

            "decisions":
                decisions,

            "summary": {

                "total_inventory_items":
                    (
                        inventory_data.get(
                            "total_inventory_items",
                            0
                        )
                        if isinstance(
                            inventory_data,
                            dict
                        )
                        else len(
                            inventory_data
                        )
                    ),

                "risk_count":
                    len(risks),

                "critical_risks":
                    sum(
                        1
                        for item in risks
                        if str(
                            item.get(
                                "risk_level",
                                item.get(
                                    "priority",
                                    ""
                                )
                            )
                        ).upper()
                        == "CRITICAL"
                    ),

                "high_risks":
                    sum(
                        1
                        for item in risks
                        if str(
                            item.get(
                                "risk_level",
                                item.get(
                                    "priority",
                                    ""
                                )
                            )
                        ).upper()
                        == "HIGH"
                    ),

                "decision_count":
                    len(decisions)
            }
        }

    def get_restock_candidates(self):

        result = self.analyze()

        return result.get(
            "decisions",
            []
        )