from typing import Any, Dict, List

from analytics.root_cause import RootCauseEngine

from agents.inventory_agent import InventoryAgent
from agents.sales_agent import SalesAgent
from agents.customer_agent import CustomerAgent
from agents.order_agent import OrderAgent
from agents.finance_agent import FinanceAgent
from agents.marketing_agent import MarketingAgent
from agents.supplier_agent import SupplierAgent
from agents.operations_agent import OperationsAgent


class DecisionEngine:

    def __init__(self, analytics_engine):

        self.engine = analytics_engine

        self.root_cause_engine = RootCauseEngine(
            analytics_engine
        )

        self.inventory_agent = InventoryAgent(
            analytics_engine
        )

        self.sales_agent = SalesAgent(
            analytics_engine
        )

        self.customer_agent = CustomerAgent(
            analytics_engine
        )

        self.order_agent = OrderAgent(
            analytics_engine
        )

        self.finance_agent = FinanceAgent(
            analytics_engine
        )

        self.marketing_agent = MarketingAgent(
            analytics_engine
        )

        self.supplier_agent = SupplierAgent(
            analytics_engine
        )

        self.operations_agent = OperationsAgent(
            analytics_engine
        )

    def decide(
        self,
        period: str = "this_month"
    ) -> Dict[str, Any]:

        self.engine.refresh()

        root_cause = self.root_cause_engine.analyze(
            period
        )

        all_decisions: List[Dict[str, Any]] = []

        # -------------------------------------------------
        # 1. Inventory Intelligence
        # -------------------------------------------------

        inventory_result = (
            self.inventory_agent.analyze()
        )

        inventory_decisions = (
            inventory_result.get(
                "decisions",
                []
            )
        )

        all_decisions.extend(
            inventory_decisions
        )

        # -------------------------------------------------
        # 2. Sales Intelligence
        # -------------------------------------------------

        sales_result = (
            self.sales_agent.analyze(
                period
            )
        )

        sales_decisions = (
            sales_result.get(
                "decisions",
                []
            )
        )

        all_decisions.extend(
            sales_decisions
        )

        # -------------------------------------------------
        # 3. Customer Intelligence
        # -------------------------------------------------

        customer_result = (
            self.customer_agent.analyze(
                period
            )
        )

        customer_decisions = (
            customer_result.get(
                "decisions",
                []
            )
        )

        all_decisions.extend(
            customer_decisions
        )

        # -------------------------------------------------
        # 4. Order Intelligence
        # -------------------------------------------------

        order_result = (
            self.order_agent.analyze(
                period
            )
        )

        order_decisions = (
            order_result.get(
                "decisions",
                []
            )
        )

        all_decisions.extend(
            order_decisions
        )

        # -------------------------------------------------
        # 5. Finance Intelligence
        # -------------------------------------------------

        finance_result = (
            self.finance_agent.analyze(
                period
            )
        )

        finance_decisions = (
            finance_result.get(
                "decisions",
                []
            )
        )

        all_decisions.extend(
            finance_decisions
        )

        # -------------------------------------------------
        # 6. Marketing Intelligence
        # -------------------------------------------------

        marketing_result = (
            self.marketing_agent.analyze(
                period
            )
        )

        marketing_decisions = (
            marketing_result.get(
                "decisions",
                []
            )
        )

        all_decisions.extend(
            marketing_decisions
        )

        # -------------------------------------------------
        # 7. Supplier Intelligence
        # -------------------------------------------------

        supplier_result = (
            self.supplier_agent.analyze(
                period
            )
        )

        supplier_decisions = (
            supplier_result.get(
                "decisions",
                []
            )
        )

        all_decisions.extend(
            supplier_decisions
        )

        # -------------------------------------------------
        # 8. Operations Intelligence
        #
        # OperationsAgent receives decisions from all
        # specialist agents and creates cross-domain
        # operational decisions.
        # -------------------------------------------------

        operations_result = (
            self.operations_agent.analyze(
                all_decisions,
                period
            )
        )

        operations_decisions = (
            operations_result.get(
                "decisions",
                []
            )
        )

        all_decisions.extend(
            operations_decisions
        )

        # -------------------------------------------------
        # Attach common metadata
        # -------------------------------------------------

        for decision in all_decisions:

            decision.setdefault(
                "status",
                "PROPOSED"
            )

            decision.setdefault(
                "period",
                period
            )

        # -------------------------------------------------
        # Sort decisions
        # -------------------------------------------------

        priority_order = {
            "CRITICAL": 0,
            "HIGH": 1,
            "MEDIUM": 2,
            "LOW": 3
        }

        all_decisions.sort(
            key=lambda item: (
                priority_order.get(
                    item.get(
                        "priority",
                        "LOW"
                    ),
                    3
                ),
                -float(
                    item.get(
                        "expected_impact",
                        0
                    )
                )
            )
        )

        # -------------------------------------------------
        # Summary
        # -------------------------------------------------

        summary = {
            "total_decisions":
                len(all_decisions),

            "critical":
                sum(
                    1
                    for item in all_decisions
                    if item.get("priority")
                    == "CRITICAL"
                ),

            "high":
                sum(
                    1
                    for item in all_decisions
                    if item.get("priority")
                    == "HIGH"
                ),

            "medium":
                sum(
                    1
                    for item in all_decisions
                    if item.get("priority")
                    == "MEDIUM"
                ),

            "low":
                sum(
                    1
                    for item in all_decisions
                    if item.get("priority")
                    == "LOW"
                ),

            "approval_required":
                sum(
                    1
                    for item in all_decisions
                    if item.get("approval")
                    == "REQUIRED"
                ),

            "inventory_agent_decisions":
                len(inventory_decisions),

            "sales_agent_decisions":
                len(sales_decisions),

            "customer_agent_decisions":
                len(customer_decisions),

            "order_agent_decisions":
                len(order_decisions),

            "finance_agent_decisions":
                len(finance_decisions),

            "marketing_agent_decisions":
                len(marketing_decisions),

            "supplier_agent_decisions":
                len(supplier_decisions),

            "operations_agent_decisions":
                len(operations_decisions)
        }

        return {
            "success": True,

            "period": period,

            "business_event":
                root_cause.get(
                    "business_event"
                ),

            "decisions":
                all_decisions,

            "summary":
                summary
        }