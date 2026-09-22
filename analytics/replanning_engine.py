from datetime import datetime
from typing import Any, Dict


class ReplanningEngine:

    def __init__(self, analytics_engine):
        self.engine = analytics_engine
        self.replanning_log = []

    # =========================================================
    # REPLAN
    # =========================================================

    def replan(
        self,
        monitoring_result: Dict[str, Any]
    ) -> Dict[str, Any]:

        if monitoring_result.get("status") != "MONITORED":

            result = {
                "success": False,
                "status": "REPLAN_BLOCKED",
                "message": (
                    "Replanning requires a valid "
                    "monitoring result."
                )
            }

            self.replanning_log.append(result)

            return result

        if not monitoring_result.get(
            "replan_required",
            False
        ):

            result = {
                "success": True,
                "status": "NO_REPLAN_REQUIRED",
                "message": (
                    "Business state is stable. "
                    "No new plan is required."
                ),
                "replan_required": False,
                "new_plan": None,
                "created_at": datetime.utcnow().isoformat()
            }

            self.replanning_log.append(result)

            return result

        action_type = monitoring_result.get(
            "action_type"
        )

        if action_type == "RESTOCK":

            plan = self._replan_restock(
                monitoring_result
            )

        else:

            plan = self._replan_generic(
                monitoring_result
            )

        result = {
            "success": True,
            "status": "REPLAN_CREATED",
            "replan_required": True,
            "new_plan": plan,
            "created_at": datetime.utcnow().isoformat()
        }

        self.replanning_log.append(result)

        return result

    # =========================================================
    # RESTOCK REPLAN
    # =========================================================

    def _replan_restock(
        self,
        monitoring_result: Dict[str, Any]
    ) -> Dict[str, Any]:

        product = monitoring_result.get(
            "product"
        )

        current_stock = monitoring_result.get(
            "current_stock",
            0
        )

        reorder_level = monitoring_result.get(
            "reorder_level",
            0
        )

        additional_quantity = max(
            reorder_level * 2 - current_stock,
            0
        )

        if additional_quantity <= 0:

            additional_quantity = reorder_level

        return {
            "action_type": "RESTOCK",
            "product": product,
            "quantity": int(
                additional_quantity
            ),
            "priority": "HIGH",
            "reason": (
                f"{product} remains at or below "
                "the reorder level after the previous "
                "restock."
            ),
            "requires_risk_assessment": True,
            "requires_approval": True
        }

    # =========================================================
    # GENERIC REPLAN
    # =========================================================

    def _replan_generic(
        self,
        monitoring_result: Dict[str, Any]
    ) -> Dict[str, Any]:

        return {
            "action_type": monitoring_result.get(
                "action_type"
            ),
            "priority": "MEDIUM",
            "reason": (
                "The previous action did not fully "
                "resolve the monitored condition."
            ),
            "requires_risk_assessment": True,
            "requires_approval": True
        }

    # =========================================================
    # REPLANNING HISTORY
    # =========================================================

    def get_replanning_log(self):

        return self.replanning_log.copy()