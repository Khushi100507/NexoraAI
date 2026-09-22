from typing import Any, Dict, List


class RiskEngine:

    def __init__(self):
        pass

    def assess(
        self,
        decisions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:

        assessed_decisions = []

        for decision in decisions:

            assessed = self._assess_decision(
                decision
            )

            assessed_decisions.append(
                assessed
            )

        return {
            "decisions": assessed_decisions,
            "summary": self._summary(
                assessed_decisions
            )
        }

    def _assess_decision(
        self,
        decision: Dict[str, Any]
    ) -> Dict[str, Any]:

        action_type = decision.get(
            "action_type",
            "UNKNOWN"
        )

        priority = decision.get(
            "priority",
            "LOW"
        )

        requested_approval = decision.get(
            "approval",
            "REQUIRED"
        )

        risk_level = decision.get(
            "risk",
            "MEDIUM"
        )

        risk_score = 50
        risk_reasons = []

        # -------------------------------------------------
        # Inventory RESTOCK
        # -------------------------------------------------

        if action_type == "RESTOCK":

            risk_score = 70

            risk_reasons.append(
                "Inventory replenishment changes physical stock levels."
            )

            approval_status = "REQUIRED"
            execution_mode = "HUMAN_APPROVAL"

            if priority == "CRITICAL":

                risk_score = 85
                risk_level = "HIGH"

                risk_reasons.append(
                    "Critical inventory condition requires controlled execution."
                )

            elif priority == "HIGH":

                risk_score = 70
                risk_level = "MEDIUM"

                risk_reasons.append(
                    "Inventory is below the operational threshold."
                )

        # -------------------------------------------------
        # Sales analysis
        # -------------------------------------------------

        elif action_type == "SALES_INVESTIGATION":

            risk_score = 20
            risk_level = "LOW"

            approval_status = "NOT_REQUIRED"
            execution_mode = "AUTOMATIC"

            risk_reasons.append(
                "Investigation does not directly change business data."
            )

        elif action_type == "GROWTH_ANALYSIS":

            risk_score = 15
            risk_level = "LOW"

            approval_status = "NOT_REQUIRED"
            execution_mode = "AUTOMATIC"

            risk_reasons.append(
                "Analysis is informational and does not directly execute a business action."
            )

        # -------------------------------------------------
        # Customer analysis
        # -------------------------------------------------

        elif action_type in [
            "CUSTOMER_RETENTION",
            "CUSTOMER_GROWTH_ANALYSIS"
        ]:

            risk_score = 20
            risk_level = "LOW"

            approval_status = "NOT_REQUIRED"
            execution_mode = "AUTOMATIC"

            risk_reasons.append(
                "Customer analysis does not directly modify customer data."
            )

        # -------------------------------------------------
        # Order analysis
        # -------------------------------------------------

        elif action_type == "ORDER_INVESTIGATION":

            risk_score = 25
            risk_level = "LOW"

            approval_status = "NOT_REQUIRED"
            execution_mode = "AUTOMATIC"

            risk_reasons.append(
                "Order investigation does not directly modify orders."
            )

        # -------------------------------------------------
        # Finance analysis
        # -------------------------------------------------

        elif action_type in [
            "MARGIN_ANALYSIS",
            "FINANCE_INVESTIGATION"
        ]:

            risk_score = 20
            risk_level = "LOW"

            approval_status = "NOT_REQUIRED"
            execution_mode = "AUTOMATIC"

            risk_reasons.append(
                "Financial analysis is informational and does not directly modify financial records."
            )

        # -------------------------------------------------
        # Marketing analysis
        # -------------------------------------------------

        elif action_type == "MARKETING_ANALYSIS":

            risk_score = 20
            risk_level = "LOW"

            approval_status = "NOT_REQUIRED"
            execution_mode = "AUTOMATIC"

            risk_reasons.append(
                "Marketing analysis does not directly change marketing spending."
            )

        elif action_type == "MARKETING_OPTIMIZATION":

            risk_score = 60
            risk_level = "MEDIUM"

            approval_status = "REQUIRED"
            execution_mode = "HUMAN_APPROVAL"

            risk_reasons.append(
                "Marketing optimization may change business spending."
            )

        # -------------------------------------------------
        # Supplier analysis
        # -------------------------------------------------

        elif action_type in [
            "SUPPLIER_INVESTIGATION",
            "SUPPLIER_CAPACITY_ANALYSIS"
        ]:

            risk_score = 25
            risk_level = "LOW"

            approval_status = "NOT_REQUIRED"
            execution_mode = "AUTOMATIC"

            risk_reasons.append(
                "Supplier analysis does not directly modify supplier records."
            )

        # -------------------------------------------------
        # Operations analysis
        # -------------------------------------------------

        elif action_type in [
            "OPERATIONS_COORDINATION",
            "OPERATIONS_PRIORITIZATION"
        ]:

            risk_score = 30
            risk_level = "LOW"

            approval_status = "NOT_REQUIRED"
            execution_mode = "AUTOMATIC"

            risk_reasons.append(
                "Operational coordination is analytical and does not directly modify business data."
            )

        # -------------------------------------------------
        # Unknown action
        # -------------------------------------------------

        else:

            risk_score = 50
            risk_level = "MEDIUM"

            approval_status = "REQUIRED"
            execution_mode = "HUMAN_APPROVAL"

            risk_reasons.append(
                "Unknown action type requires human review before execution."
            )

        # -------------------------------------------------
        # Respect the agent's explicit approval requirement
        # -------------------------------------------------

        if requested_approval == "REQUIRED":

            approval_status = "REQUIRED"
            execution_mode = "HUMAN_APPROVAL"

        elif requested_approval == "NOT_REQUIRED":

            approval_status = "NOT_REQUIRED"
            execution_mode = "AUTOMATIC"

        # -------------------------------------------------
        # Normalize risk level from score
        # -------------------------------------------------

        if risk_score >= 80:

            risk_level = "HIGH"

        elif risk_score >= 50:

            risk_level = "MEDIUM"

        else:

            risk_level = "LOW"

        # -------------------------------------------------
        # Execution state
        # -------------------------------------------------

        if approval_status == "REQUIRED":

            execution_status = "WAITING_FOR_APPROVAL"

        else:

            execution_status = "READY_FOR_EXECUTION"

        result = decision.copy()

        result["risk_assessment"] = {

            "risk_score":
                risk_score,

            "risk_level":
                risk_level,

            "reasons":
                risk_reasons,

            "approval":
                approval_status,

            "execution_mode":
                execution_mode,

            "execution_status":
                execution_status
        }

        return result

    def _summary(
        self,
        decisions: List[Dict[str, Any]]
    ):

        high_risk = sum(
            1
            for item in decisions
            if item["risk_assessment"]["risk_level"]
            == "HIGH"
        )

        medium_risk = sum(
            1
            for item in decisions
            if item["risk_assessment"]["risk_level"]
            == "MEDIUM"
        )

        low_risk = sum(
            1
            for item in decisions
            if item["risk_assessment"]["risk_level"]
            == "LOW"
        )

        approval_required = sum(
            1
            for item in decisions
            if item["risk_assessment"]["approval"]
            == "REQUIRED"
        )

        ready_for_execution = sum(
            1
            for item in decisions
            if item["risk_assessment"]["execution_status"]
            == "READY_FOR_EXECUTION"
        )

        waiting_for_approval = sum(
            1
            for item in decisions
            if item["risk_assessment"]["execution_status"]
            == "WAITING_FOR_APPROVAL"
        )

        return {
            "total_decisions":
                len(decisions),

            "high_risk":
                high_risk,

            "medium_risk":
                medium_risk,

            "low_risk":
                low_risk,

            "approval_required":
                approval_required,

            "ready_for_execution":
                ready_for_execution,

            "waiting_for_approval":
                waiting_for_approval
        }