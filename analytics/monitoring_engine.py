from datetime import datetime
from typing import Any, Dict


class MonitoringEngine:

    def __init__(self, analytics_engine):
        self.engine = analytics_engine
        self.monitoring_log = []

    # =========================================================
    # MONITOR EXECUTED ACTION
    # =========================================================

    def monitor(
        self,
        verification_result: Dict[str, Any]
    ) -> Dict[str, Any]:

        if verification_result.get("status") != "VERIFIED":

            result = {
                "success": False,
                "status": "MONITORING_BLOCKED",
                "message": (
                    "Monitoring cannot continue because "
                    "execution was not verified."
                )
            }

            self.monitoring_log.append(result)

            return result

        action_type = verification_result.get(
            "action_type"
        )

        if action_type == "RESTOCK":

            result = self._monitor_restock(
                verification_result
            )

        else:

            result = self._monitor_generic_action(
                verification_result
            )

        self.monitoring_log.append(result)

        return result

    # =========================================================
    # MONITOR RESTOCK
    # =========================================================

    def _monitor_restock(
        self,
        verification_result: Dict[str, Any]
    ) -> Dict[str, Any]:

        product = verification_result.get(
            "product"
        )

        current_stock = verification_result.get(
            "actual_stock"
        )

        inventory = self.engine.inventory

        rows = inventory[
            inventory["product"] == product
        ]

        if rows.empty:

            return {
                "success": False,
                "status": "MONITORING_FAILED",
                "product": product,
                "message": (
                    f"Product {product} was not found "
                    "during monitoring."
                )
            }

        row = rows.iloc[0]

        reorder_level = int(
            row.get(
                "reorder_level",
                0
            )
        )

        if current_stock <= reorder_level:

            state = "REQUIRES_REPLANNING"

            message = (
                f"{product} remains at or below "
                "the reorder level after restocking."
            )

        else:

            state = "STABLE"

            message = (
                f"{product} stock is currently healthy "
                "after the restock."
            )

        return {
            "success": True,
            "status": "MONITORED",
            "action_type": "RESTOCK",
            "product": product,
            "current_stock": current_stock,
            "reorder_level": reorder_level,
            "state": state,
            "replan_required": (
                state == "REQUIRES_REPLANNING"
            ),
            "message": message,
            "monitored_at": datetime.utcnow().isoformat()
        }

    # =========================================================
    # GENERIC ACTION MONITORING
    # =========================================================

    def _monitor_generic_action(
        self,
        verification_result: Dict[str, Any]
    ) -> Dict[str, Any]:

        return {
            "success": True,
            "status": "MONITORED",
            "action_type": verification_result.get(
                "action_type"
            ),
            "state": "STABLE",
            "replan_required": False,
            "message": (
                "Action completed and remains "
                "under monitoring."
            ),
            "monitored_at": datetime.utcnow().isoformat()
        }

    # =========================================================
    # MONITORING HISTORY
    # =========================================================

    def get_monitoring_log(self):

        return self.monitoring_log.copy()