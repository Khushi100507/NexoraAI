from datetime import datetime
from typing import Any, Dict


class VerificationEngine:

    def __init__(self, analytics_engine):
        self.engine = analytics_engine
        self.verification_log = []

    # =========================================================
    # VERIFY EXECUTION
    # =========================================================

    def verify(
        self,
        execution_result: Dict[str, Any]
    ) -> Dict[str, Any]:

        if execution_result.get("status") != "COMPLETED":

            return {
                "success": False,
                "status": "FAILED",
                "message": (
                    "Execution was not completed, "
                    "so verification cannot proceed."
                ),
                "verification": None
            }

        request = execution_result.get(
            "request",
            {}
        )

        action_type = request.get(
            "action_type"
        )

        if action_type == "RESTOCK":

            result = self._verify_restock(
                request
            )

        else:

            result = self._verify_non_inventory_action(
                request
            )

        self.verification_log.append(result)

        return result

    # =========================================================
    # VERIFY RESTOCK
    # =========================================================

    def _verify_restock(
        self,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:

        product = request.get(
            "product"
        )

        quantity = int(
            request.get(
                "quantity",
                0
            )
        )

        execution_result = request.get(
            "execution_result",
            {}
        )

        execution_data = execution_result.get(
            "result",
            {}
        )

        old_stock = execution_data.get(
            "old_stock"
        )

        expected_stock = None

        if old_stock is not None:

            expected_stock = (
                int(old_stock)
                + quantity
            )

        actual_stock = self._get_current_stock(
            product
        )

        verified = (
            expected_stock is not None
            and actual_stock == expected_stock
        )

        if verified:

            status = "VERIFIED"

            message = (
                f"Restock verified successfully. "
                f"{product} stock is now "
                f"{actual_stock} units."
            )

        else:

            status = "FAILED"

            message = (
                f"Restock verification failed. "
                f"Expected stock: {expected_stock}, "
                f"actual stock: {actual_stock}."
            )

        return {
            "success": verified,
            "status": status,
            "action_type": "RESTOCK",
            "product": product,
            "quantity": quantity,
            "old_stock": old_stock,
            "expected_stock": expected_stock,
            "actual_stock": actual_stock,
            "verified": verified,
            "message": message,
            "verified_at": datetime.utcnow().isoformat()
        }

    # =========================================================
    # GET CURRENT STOCK
    # =========================================================

    def _get_current_stock(
        self,
        product: str
    ):

        inventory = self.engine.inventory

        if inventory is None:

            raise ValueError(
                "Inventory data is unavailable."
            )

        rows = inventory[
            inventory["product"] == product
        ]

        if rows.empty:

            raise ValueError(
                f"Product not found in inventory: {product}"
            )

        return int(
            rows.iloc[0]["stock"]
        )

    # =========================================================
    # VERIFY NON-INVENTORY ACTION
    # =========================================================

    def _verify_non_inventory_action(
        self,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:

        return {
            "success": True,
            "status": "VERIFIED",
            "action_type": request.get(
                "action_type"
            ),
            "verified": True,
            "message": (
                "Action was recorded successfully. "
                "No physical business data was modified."
            ),
            "verified_at": datetime.utcnow().isoformat()
        }

    # =========================================================
    # VERIFICATION HISTORY
    # =========================================================

    def get_verification_log(self):

        return self.verification_log.copy()