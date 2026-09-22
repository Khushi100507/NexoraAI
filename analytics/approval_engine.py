from datetime import datetime
from typing import Any, Dict, List


class ApprovalEngine:

    def __init__(self):

        self.audit_log = []

    # =========================================================
    # CREATE APPROVAL REQUESTS
    # =========================================================

    def create_requests(
        self,
        decisions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:

        requests = []

        for index, decision in enumerate(
            decisions,
            start=1
        ):

            risk = decision.get(
                "risk_assessment",
                {}
            )

            approval = risk.get(
                "approval",
                decision.get(
                    "approval",
                    "REQUIRED"
                )
            )

            request = decision.copy()

            # -------------------------------------------------
            # HUMAN APPROVAL REQUIRED
            # -------------------------------------------------

            if approval == "REQUIRED":

                request["approval_request"] = {

                    "request_id":
                        f"APR-{index:04d}",

                    "status":
                        "PENDING",

                    "created_at":
                        datetime.utcnow().isoformat(),

                    "approved_by":
                        None,

                    "approved_at":
                        None,

                    "rejected_by":
                        None,

                    "rejected_at":
                        None,

                    "rejection_reason":
                        None
                }

            # -------------------------------------------------
            # AUTOMATIC ACTION
            # -------------------------------------------------

            else:

                request["approval_request"] = {

                    "request_id":
                        f"AUTO-{index:04d}",

                    "status":
                        "NOT_REQUIRED",

                    "created_at":
                        datetime.utcnow().isoformat(),

                    "approved_by":
                        "SYSTEM",

                    "approved_at":
                        datetime.utcnow().isoformat(),

                    "rejected_by":
                        None,

                    "rejected_at":
                        None,

                    "rejection_reason":
                        None
                }

                risk["execution_status"] = (
                    "READY_FOR_EXECUTION"
                )

                risk["execution_mode"] = (
                    "AUTOMATIC"
                )

                request["risk_assessment"] = risk

            requests.append(
                request
            )

        return {

            "requests":
                requests,

            "summary":
                self._summary(
                    requests
                )
        }

    # =========================================================
    # APPROVE REQUEST
    # =========================================================

    def approve(
        self,
        request: Dict[str, Any],
        approved_by: str = "human"
    ) -> Dict[str, Any]:

        approval = request.get(
            "approval_request",
            {}
        )

        if approval.get(
            "status"
        ) != "PENDING":

            return {

                "success":
                    False,

                "message":
                    (
                        "Only pending approval "
                        "requests can be approved."
                    ),

                "request":
                    request
            }

        now = datetime.utcnow().isoformat()

        approval["status"] = (
            "APPROVED"
        )

        approval["approved_by"] = (
            approved_by
        )

        approval["approved_at"] = (
            now
        )

        request["status"] = (
            "APPROVED"
        )

        risk = request.get(
            "risk_assessment",
            {}
        )

        risk["execution_status"] = (
            "READY_FOR_EXECUTION"
        )

        risk["execution_mode"] = (
            "APPROVED_EXECUTION"
        )

        request["risk_assessment"] = (
            risk
        )

        self._record_audit(
            request=request,
            action="APPROVED",
            actor=approved_by
        )

        return {

            "success":
                True,

            "message":
                (
                    "Approval granted. "
                    "Action is ready for execution."
                ),

            "request":
                request
        }

    # =========================================================
    # REJECT REQUEST
    # =========================================================

    def reject(
        self,
        request: Dict[str, Any],
        rejected_by: str = "human",
        reason: str = "Rejected by reviewer."
    ) -> Dict[str, Any]:

        approval = request.get(
            "approval_request",
            {}
        )

        if approval.get(
            "status"
        ) != "PENDING":

            return {

                "success":
                    False,

                "message":
                    (
                        "Only pending approval "
                        "requests can be rejected."
                    ),

                "request":
                    request
            }

        now = datetime.utcnow().isoformat()

        approval["status"] = (
            "REJECTED"
        )

        approval["rejected_by"] = (
            rejected_by
        )

        approval["rejected_at"] = (
            now
        )

        approval["rejection_reason"] = (
            reason
        )

        request["status"] = (
            "REJECTED"
        )

        risk = request.get(
            "risk_assessment",
            {}
        )

        risk["execution_status"] = (
            "BLOCKED"
        )

        risk["execution_mode"] = (
            "REJECTED"
        )

        request["risk_assessment"] = (
            risk
        )

        self._record_audit(
            request=request,
            action="REJECTED",
            actor=rejected_by,
            reason=reason
        )

        return {

            "success":
                True,

            "message":
                (
                    "Action rejected and blocked "
                    "from execution."
                ),

            "request":
                request
        }

    # =========================================================
    # AUDIT LOG
    # =========================================================

    def _record_audit(
        self,
        request: Dict[str, Any],
        action: str,
        actor: str,
        reason: str = None
    ):

        approval = request.get(
            "approval_request",
            {}
        )

        self.audit_log.append({

            "request_id":
                approval.get(
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

            "action":
                action,

            "actor":
                actor,

            "reason":
                reason,

            "timestamp":
                datetime.utcnow().isoformat()
        })

    # =========================================================
    # AUDIT HISTORY
    # =========================================================

    def get_audit_log(self):

        return self.audit_log.copy()

    # =========================================================
    # SUMMARY
    # =========================================================

    def _summary(
        self,
        requests: List[Dict[str, Any]]
    ):

        pending = sum(

            1

            for request in requests

            if request.get(
                "approval_request",
                {}
            ).get(
                "status"
            ) == "PENDING"
        )

        approved = sum(

            1

            for request in requests

            if request.get(
                "approval_request",
                {}
            ).get(
                "status"
            ) == "APPROVED"
        )

        rejected = sum(

            1

            for request in requests

            if request.get(
                "approval_request",
                {}
            ).get(
                "status"
            ) == "REJECTED"
        )

        automatic = sum(

            1

            for request in requests

            if request.get(
                "approval_request",
                {}
            ).get(
                "status"
            ) == "NOT_REQUIRED"
        )

        return {

            "total_requests":
                len(requests),

            "pending":
                pending,

            "approved":
                approved,

            "rejected":
                rejected,

            "automatic":
                automatic
        }