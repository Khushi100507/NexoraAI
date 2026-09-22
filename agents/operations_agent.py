from typing import Any, Dict, List


class OperationsAgent:

    def __init__(self, analytics_engine):
        self.engine = analytics_engine

    def analyze(
        self,
        decisions: List[Dict[str, Any]],
        period="this_month"
    ) -> Dict[str, Any]:

        self.engine.refresh()

        if not decisions:
            return {
                "agent": "OperationsAgent",
                "domain": "operations",
                "status": "ANALYZED",
                "period": period,
                "decisions": [],
                "summary": {
                    "input_decisions": 0,
                    "high_priority_decisions": 0,
                    "cross_domain_risks": 0,
                    "decision_count": 0
                }
            }

        high_priority = [
            item
            for item in decisions
            if item.get("priority")
            in ["CRITICAL", "HIGH"]
        ]

        domains = set(
            item.get("domain")
            for item in decisions
            if item.get("domain")
        )

        cross_domain_risks = 0
        operational_decisions = []

        # -------------------------------------------------
        # Cross-domain operational pressure
        # -------------------------------------------------

        if (
            "inventory" in domains
            and "sales" in domains
        ):

            cross_domain_risks += 1

            operational_decisions.append({
                "action_type":
                    "OPERATIONS_COORDINATION",

                "domain":
                    "operations",

                "title":
                    "Coordinate inventory and sales operations",

                "priority":
                    "HIGH",

                "risk":
                    "MEDIUM",

                "approval":
                    "NOT_REQUIRED",

                "expected_impact":
                    85,

                "reason":
                    (
                        "Sales activity and inventory pressure "
                        "are occurring simultaneously."
                    ),

                "evidence": [
                    "Sales intelligence detected business activity.",
                    "Inventory intelligence detected stock pressure."
                ],

                "recommended_next_step":
                    (
                        "Coordinate replenishment with demand "
                        "signals and prioritize products with "
                        "the highest operational risk."
                    ),

                "agent":
                    "OperationsAgent",

                "agent_status":
                    "ANALYZED",

                "status":
                    "PROPOSED"
            })

        # -------------------------------------------------
        # Multiple high-priority operational decisions
        # -------------------------------------------------

        if len(high_priority) >= 3:

            cross_domain_risks += 1

            operational_decisions.append({
                "action_type":
                    "OPERATIONS_PRIORITIZATION",

                "domain":
                    "operations",

                "title":
                    "Prioritize high-impact operational actions",

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
                        f"{len(high_priority)} high-priority "
                        "business decisions require coordinated "
                        "operational attention."
                    ),

                "evidence": [
                    (
                        f"High-priority decisions: "
                        f"{len(high_priority)}"
                    ),
                    (
                        f"Active business domains: "
                        f"{', '.join(sorted(domains))}"
                    )
                ],

                "recommended_next_step":
                    (
                        "Prioritize decisions by business impact, "
                        "risk and dependency before execution."
                    ),

                "agent":
                    "OperationsAgent",

                "agent_status":
                    "ANALYZED",

                "status":
                    "PROPOSED"
            })

        return {
            "agent": "OperationsAgent",
            "domain": "operations",
            "status": "ANALYZED",
            "period": period,
            "decisions": operational_decisions,
            "summary": {
                "input_decisions": len(decisions),
                "high_priority_decisions": len(high_priority),
                "cross_domain_risks": cross_domain_risks,
                "decision_count": len(
                    operational_decisions
                )
            }
        }