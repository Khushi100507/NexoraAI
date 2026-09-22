from typing import Any, Dict


class CustomerAgent:

    """
    Specialized agent responsible for customer intelligence.

    Responsibilities:
    - Analyze customer population
    - Detect active/inactive customer patterns
    - Identify customer concentration
    - Detect customer growth/retention signals
    - Produce structured customer decisions

    The agent does not execute business actions.
    """

    def __init__(self, analytics_engine):
        self.engine = analytics_engine

    def analyze(
        self,
        period="this_month"
    ) -> Dict[str, Any]:

        self.engine.refresh()

        customers = self.engine.customers

        if customers is None or customers.empty:
            return {
                "agent": "CustomerAgent",
                "domain": "customers",
                "status": "NO_DATA",
                "period": period,
                "decisions": [],
                "summary": {
                    "total_customers": 0
                }
            }

        total_customers = len(customers)

        active_customers = self._active_customers(
            customers
        )

        inactive_customers = (
            total_customers - active_customers
        )

        active_rate = (
            active_customers / total_customers * 100
            if total_customers
            else 0
        )

        decisions = []

        if active_rate < 50:

            decisions.append({
                "action_type":
                    "CUSTOMER_RETENTION",

                "domain":
                    "customers",

                "title":
                    "Investigate customer inactivity",

                "priority":
                    "HIGH",

                "risk":
                    "LOW",

                "approval":
                    "NOT_REQUIRED",

                "expected_impact":
                    75,

                "reason":
                    (
                        f"Only {active_rate:.2f}% "
                        "of customers are currently "
                        "classified as active."
                    ),

                "evidence": [
                    f"Total customers: {total_customers:,}",
                    f"Active customers: {active_customers:,}",
                    f"Inactive customers: {inactive_customers:,}",
                    f"Active customer rate: {active_rate:.2f}%"
                ],

                "recommended_next_step":
                    (
                        "Identify inactive customer "
                        "segments and investigate "
                        "retention opportunities."
                    ),

                "agent":
                    "CustomerAgent",

                "agent_status":
                    "ANALYZED",

                "status":
                    "PROPOSED"
            })

        elif active_rate < 70:

            decisions.append({
                "action_type":
                    "CUSTOMER_GROWTH_ANALYSIS",

                "domain":
                    "customers",

                "title":
                    "Analyze customer engagement",

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
                        f"Customer activity rate is "
                        f"{active_rate:.2f}%, indicating "
                        "an opportunity to improve "
                        "customer engagement."
                    ),

                "evidence": [
                    f"Total customers: {total_customers:,}",
                    f"Active customers: {active_customers:,}",
                    f"Inactive customers: {inactive_customers:,}",
                    f"Active customer rate: {active_rate:.2f}%"
                ],

                "recommended_next_step":
                    (
                        "Analyze customer segments "
                        "and identify opportunities "
                        "to increase repeat activity."
                    ),

                "agent":
                    "CustomerAgent",

                "agent_status":
                    "ANALYZED",

                "status":
                    "PROPOSED"
            })

        return {
            "agent": "CustomerAgent",
            "domain": "customers",
            "status": "ANALYZED",
            "period": period,
            "decisions": decisions,
            "summary": {
                "total_customers":
                    total_customers,

                "active_customers":
                    active_customers,

                "inactive_customers":
                    inactive_customers,

                "active_rate":
                    round(
                        active_rate,
                        2
                    ),

                "decision_count":
                    len(decisions)
            }
        }

    def _active_customers(
        self,
        customers
    ):

        possible_columns = [
            "status",
            "customer_status",
            "activity_status"
        ]

        status_column = None

        for column in possible_columns:

            if column in customers.columns:
                status_column = column
                break

        if status_column:

            values = (
                customers[status_column]
                .astype(str)
                .str.lower()
                .str.strip()
            )

            return int(
                values.isin(
                    [
                        "active",
                        "1",
                        "true"
                    ]
                ).sum()
            )

        # If the customer dataset does not contain
        # an activity/status column, use all customers
        # as the currently available customer population.
        return len(customers)