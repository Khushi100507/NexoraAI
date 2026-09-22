from datetime import datetime
from typing import Any, Dict


class ExecutionEngine:

    def __init__(self, analytics_engine):

        self.engine = analytics_engine

        self.execution_log = []

    # =========================================================
    # MAIN EXECUTION
    # =========================================================

    def execute(
        self,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:

        approval_request = request.get(
            "approval_request",
            {}
        )

        approval_status = approval_request.get(
            "status"
        )

        risk_assessment = request.get(
            "risk_assessment",
            {}
        )

        execution_status = risk_assessment.get(
            "execution_status"
        )

        # -----------------------------------------------------
        # APPROVAL CHECK
        # -----------------------------------------------------

        approval_required = (
            risk_assessment.get(
                "approval"
            )
            == "REQUIRED"
        )

        if approval_required:

            if approval_status != "APPROVED":

                return {
                    "success": False,
                    "status": "BLOCKED",
                    "message":
                        "Action cannot be executed without approval.",
                    "request":
                        request
                }

        # -----------------------------------------------------
        # EXECUTION STATE CHECK
        # -----------------------------------------------------

        if execution_status != "READY_FOR_EXECUTION":

            return {
                "success": False,
                "status": "BLOCKED",
                "message":
                    "Action is not ready for execution.",
                "request":
                    request
            }

        action_type = request.get(
            "action_type"
        )

        try:

            # -------------------------------------------------
            # PHYSICAL INVENTORY ACTION
            # -------------------------------------------------

            if action_type == "RESTOCK":

                result = self._execute_restock(
                    request
                )

            # -------------------------------------------------
            # ANALYTICAL / AUTOMATIC ACTIONS
            # -------------------------------------------------

            elif action_type in [

                "GROWTH_ANALYSIS",

                "SALES_INVESTIGATION",

                "ORDER_INVESTIGATION",

                "CUSTOMER_RETENTION",

                "CUSTOMER_GROWTH_ANALYSIS",

                "FINANCE_INVESTIGATION",

                "MARGIN_ANALYSIS",

                "MARKETING_ANALYSIS",

                "MARKETING_OPTIMIZATION",

                "SUPPLIER_INVESTIGATION",

                "SUPPLIER_CAPACITY_ANALYSIS",

                "OPERATIONS_COORDINATION",

                "OPERATIONS_PRIORITIZATION"

            ]:

                result = self._execute_analysis(
                    request
                )

            # -------------------------------------------------
            # UNKNOWN ACTION
            # -------------------------------------------------

            else:

                return {
                    "success": False,
                    "status": "FAILED",
                    "message":
                        (
                            "Unsupported action type: "
                            f"{action_type}"
                        ),
                    "request":
                        request
                }

            # -------------------------------------------------
            # MARK COMPLETED
            # -------------------------------------------------

            request["status"] = "COMPLETED"

            risk_assessment[
                "execution_status"
            ] = "COMPLETED"

            risk_assessment[
                "execution_mode"
            ] = "EXECUTED"

            request[
                "risk_assessment"
            ] = risk_assessment

            request[
                "execution_result"
            ] = result

            self._record_execution(
                request
            )

            return {

                "success":
                    True,

                "status":
                    "COMPLETED",

                "message":
                    "Action executed successfully.",

                "request":
                    request
            }

        except Exception as error:

            request["status"] = "FAILED"

            risk_assessment[
                "execution_status"
            ] = "FAILED"

            request[
                "risk_assessment"
            ] = risk_assessment

            request[
                "execution_result"
            ] = {
                "error":
                    str(error)
            }

            self._record_execution(
                request
            )

            return {

                "success":
                    False,

                "status":
                    "FAILED",

                "message":
                    "Action execution failed.",

                "error":
                    str(error),

                "request":
                    request
            }

    # =========================================================
    # RESTOCK EXECUTION
    # =========================================================

    def _execute_restock(
        self,
        request: Dict[str, Any]
    ):

        product = request.get(
            "product"
        )

        quantity = int(
            request.get(
                "quantity",
                0
            )
        )

        if not product:

            raise ValueError(
                "Restock request is missing product."
            )

        if quantity <= 0:

            raise ValueError(
                "Restock quantity must be greater than zero."
            )

        result = self.engine.execute_restock(
            product=product,
            quantity=quantity
        )

        return {

            "action":
                "RESTOCK",

            "product":
                product,

            "quantity":
                quantity,

            "result":
                result,

            "executed_at":
                datetime.utcnow().isoformat()
        }

    # =========================================================
    # ANALYTICAL / NON-MUTATING EXECUTION
    # =========================================================

    def _execute_analysis(
        self,
        request: Dict[str, Any]
    ):

        action_type = request.get(
            "action_type"
        )

        return {

            "action":
                action_type,

            "message":
                (
                    "Analysis or operational coordination "
                    "was executed and recorded. "
                    "No physical business data was modified."
                ),

            "executed_at":
                datetime.utcnow().isoformat()
        }

    # =========================================================
    # EXECUTION LOG
    # =========================================================

    def _record_execution(
        self,
        request: Dict[str, Any]
    ):

        approval_request = request.get(
            "approval_request",
            {}
        )

        self.execution_log.append({

            "request_id":
                approval_request.get(
                    "request_id"
                ),

            "action_type":
                request.get(
                    "action_type"
                ),

            "title":
                request.get(
                    "title"
                ),

            "status":
                request.get(
                    "status"
                ),

            "timestamp":
                datetime.utcnow().isoformat()
        })

    # =========================================================
    # GET EXECUTION LOG
    # =========================================================

    def get_execution_log(self):

        return self.execution_log.copy()