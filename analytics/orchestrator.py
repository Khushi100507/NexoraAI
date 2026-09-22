from typing import Any, Dict

from analytics.decision_engine import DecisionEngine
from analytics.risk_engine import RiskEngine
from analytics.approval_engine import ApprovalEngine
from analytics.execution_engine import ExecutionEngine
from analytics.verification_engine import VerificationEngine
from analytics.monitoring_engine import MonitoringEngine
from analytics.replanning_engine import ReplanningEngine


class Orchestrator:

    def __init__(self, analytics_engine):

        self.engine = analytics_engine

        self.decision_engine = DecisionEngine(
            analytics_engine
        )

        self.risk_engine = RiskEngine()

        self.approval_engine = ApprovalEngine()

        self.execution_engine = ExecutionEngine(
            analytics_engine
        )

        self.verification_engine = VerificationEngine(
            analytics_engine
        )

        self.monitoring_engine = MonitoringEngine(
            analytics_engine
        )

        self.replanning_engine = ReplanningEngine(
            analytics_engine
        )

    # =========================================================
    # RUN AUTONOMOUS BUSINESS CYCLE
    # =========================================================

    def run(
        self,
        period: str = "this_month"
    ) -> Dict[str, Any]:

        # -----------------------------------------------------
        # STEP 1 — DECISION
        # -----------------------------------------------------

        decisions = self.decision_engine.decide(
            period
        )

        # -----------------------------------------------------
        # STEP 2 — RISK ASSESSMENT
        # -----------------------------------------------------

        assessed = self.risk_engine.assess(
            decisions["decisions"]
        )

        # -----------------------------------------------------
        # STEP 3 — APPROVAL REQUESTS
        # -----------------------------------------------------

        approval_requests = (
            self.approval_engine.create_requests(
                assessed["decisions"]
            )
        )

        pending_requests = (
            approval_requests["requests"]
        )

        # -----------------------------------------------------
        # STEP 4 — SEPARATE ACTIONS
        # -----------------------------------------------------

        automatic_actions = []
        approval_required = []

        for request in pending_requests:

            risk_assessment = request.get(
                "risk_assessment",
                {}
            )

            approval = risk_assessment.get(
                "approval"
            )

            if approval == "REQUIRED":

                approval_required.append(
                    request
                )

            else:

                automatic_actions.append(
                    request
                )

        # -----------------------------------------------------
        # STEP 5 — EXECUTE AUTOMATIC ACTIONS
        # -----------------------------------------------------

        execution_results = []

        for request in automatic_actions:

            risk_assessment = request.get(
                "risk_assessment",
                {}
            )

            risk_assessment[
                "execution_status"
            ] = "READY_FOR_EXECUTION"

            request[
                "risk_assessment"
            ] = risk_assessment

            executed = self.execution_engine.execute(
                request
            )

            execution_results.append(
                executed
            )

        # -----------------------------------------------------
        # STEP 6 — VERIFICATION
        # -----------------------------------------------------

        verification_results = []

        for execution in execution_results:

            if execution.get("success"):

                verified = (
                    self.verification_engine.verify(
                        execution
                    )
                )

                verification_results.append(
                    verified
                )

        # -----------------------------------------------------
        # STEP 7 — MONITORING
        # -----------------------------------------------------

        monitoring_results = []

        for verification in verification_results:

            if verification.get(
                "status"
            ) == "VERIFIED":

                monitored = (
                    self.monitoring_engine.monitor(
                        verification
                    )
                )

                monitoring_results.append(
                    monitored
                )

        # -----------------------------------------------------
        # STEP 8 — REPLANNING
        # -----------------------------------------------------

        replanning_results = []

        for monitoring in monitoring_results:

            if monitoring.get(
                "replan_required"
            ):

                replanned = (
                    self.replanning_engine.replan(
                        monitoring
                    )
                )

                replanning_results.append(
                    replanned
                )

        # -----------------------------------------------------
        # FINAL RESULT
        # -----------------------------------------------------

        return {

            "success": True,

            "period": period,

            "decisions": decisions,

            "risk_assessment": assessed,

            "approval_requests": approval_requests,

            "automatic_actions": automatic_actions,

            "approval_required": approval_required,

            "execution_results": execution_results,

            "verification_results": verification_results,

            "monitoring_results": monitoring_results,

            "replanning_results": replanning_results,

            "summary": {

                "total_decisions": len(
                    decisions["decisions"]
                ),

                "approval_required": len(
                    approval_required
                ),

                "automatic_actions": len(
                    automatic_actions
                ),

                "executed": len(
                    execution_results
                ),

                "verified": len(
                    verification_results
                ),

                "monitored": len(
                    monitoring_results
                ),

                "replanned": len(
                    replanning_results
                )
            }
        }

    # =========================================================
    # GET COMPONENTS
    # =========================================================

    def get_components(self):

        return {

            "decision_engine":
                self.decision_engine,

            "risk_engine":
                self.risk_engine,

            "approval_engine":
                self.approval_engine,

            "execution_engine":
                self.execution_engine,

            "verification_engine":
                self.verification_engine,

            "monitoring_engine":
                self.monitoring_engine,

            "replanning_engine":
                self.replanning_engine
        }