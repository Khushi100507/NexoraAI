import json
from datetime import datetime

from database.db import SessionLocal, Operation

from analytics.decision_engine import DecisionEngine
from analytics.risk_engine import RiskEngine
from analytics.execution_engine import ExecutionEngine
from analytics.verification_engine import VerificationEngine
from analytics.monitoring_engine import MonitoringEngine
from analytics.replanning_engine import ReplanningEngine


class Orchestrator:

    def __init__(self, engine):

        self.engine = engine

        self.decision_engine = DecisionEngine(
            engine
        )

        self.risk_engine = RiskEngine()

        self.execution_engine = ExecutionEngine(
            engine
        )

        self.verification_engine = VerificationEngine(
            engine
        )

        self.monitoring_engine = MonitoringEngine(
            engine
        )

        self.replanning_engine = ReplanningEngine(
            engine
        )

    # =========================================================
    # MONITOR / GENERATE OPERATIONS
    # =========================================================

    def monitor(
        self,
        period="this_month"
    ):

        self.engine.refresh()

        decisions = self.decision_engine.decide(
            period
        )

        assessed = self.risk_engine.assess(
            decisions["decisions"]
        )

        db = SessionLocal()

        try:

            created = []
            updated = []

            for decision in assessed["decisions"]:

                risk_assessment = decision.get(
                    "risk_assessment",
                    {}
                )

                approval = risk_assessment.get(
                    "approval"
                )

                if approval == "REQUIRED":

                    result = self._sync_database_operation(
                        db,
                        decision,
                        risk_assessment
                    )

                    if result:

                        operation = result["operation"]

                        serialized = self.serialize(
                            operation
                        )

                        if result["action"] == "created":

                            created.append(
                                serialized
                            )

                        elif result["action"] == "updated":

                            updated.append(
                                serialized
                            )

                else:

                    self._execute_automatic_action(
                        decision,
                        risk_assessment
                    )

            db.commit()

            return {

                "success": True,

                "period": period,

                "business_event":
                    decisions.get(
                        "business_event"
                    ),

                "created":
                    created,

                "updated":
                    updated,

                "summary": {

                    "decisions":
                        len(
                            assessed["decisions"]
                        ),

                    "approval_required":
                        sum(
                            1
                            for item
                            in assessed["decisions"]
                            if item.get(
                                "risk_assessment",
                                {}
                            ).get(
                                "approval"
                            ) == "REQUIRED"
                        ),

                    "created_operations":
                        len(created),

                    "updated_operations":
                        len(updated)
                }
            }

        finally:

            db.close()

    # =========================================================
    # SYNCHRONIZE DATABASE OPERATION
    # =========================================================

    def _sync_database_operation(
        self,
        db,
        decision,
        risk_assessment
    ):

        action_type = decision.get(
            "action_type",
            ""
        )

        product = decision.get(
            "product"
        )

        title = decision.get(
            "title",
            "NEXORAAI Operation"
        )

        # -----------------------------------------------------
        # FIND EXISTING ACTIVE OPERATION
        # -----------------------------------------------------

        existing = None

        if product:

            existing = (
                db.query(Operation)
                .filter(
                    Operation.status.in_(
                        [
                            "pending_approval",
                            "approved"
                        ]
                    )
                )
                .filter(
                    Operation.title.contains(
                        str(product)
                    )
                )
                .first()
            )

        else:

            existing = (
                db.query(Operation)
                .filter(
                    Operation.status.in_(
                        [
                            "pending_approval",
                            "approved"
                        ]
                    )
                )
                .filter(
                    Operation.title == title
                )
                .first()
            )

        # -----------------------------------------------------
        # DOMAIN
        # -----------------------------------------------------

        domain_map = {

            "RESTOCK":
                "inventory",

            "GROWTH_ANALYSIS":
                "sales",

            "SALES_INVESTIGATION":
                "sales",

            "ORDER_INVESTIGATION":
                "orders",

            "MARKETING_OPTIMIZATION":
                "marketing"
        }

        domain = domain_map.get(
            action_type,
            "business"
        )

        # -----------------------------------------------------
        # PAYLOAD
        # -----------------------------------------------------

        payload = {

            "action_type":
                action_type,

            "product":
                product,

            "quantity":
                decision.get(
                    "quantity"
                ),

            "priority":
                decision.get(
                    "priority"
                ),

            "risk_score":
                risk_assessment.get(
                    "risk_score"
                ),

            "risk_level":
                risk_assessment.get(
                    "risk_level"
                ),

            "expected_impact":
                decision.get(
                    "expected_impact"
                ),

            "evidence":
                decision.get(
                    "evidence",
                    []
                ),

            "recommended_next_step":
                decision.get(
                    "recommended_next_step"
                )
        }

        # -----------------------------------------------------
        # UPDATE EXISTING OPERATION
        # -----------------------------------------------------

        if existing:

            existing.action = action_type

            existing.domain = domain

            existing.title = title

            existing.reason = decision.get(
                "reason",
                "NEXORAAI generated this operation."
            )

            existing.payload = json.dumps(
                payload
            )

            existing.risk = risk_assessment.get(
                "risk_level",
                decision.get(
                    "risk",
                    "MEDIUM"
                )
            )

            return {
                "action":
                    "updated",

                "operation":
                    existing
            }

        # -----------------------------------------------------
        # CREATE NEW OPERATION
        # -----------------------------------------------------

        operation = Operation(

            action=action_type,

            domain=domain,

            title=title,

            reason=decision.get(
                "reason",
                "NEXORAAI generated this operation."
            ),

            payload=json.dumps(
                payload
            ),

            risk=risk_assessment.get(
                "risk_level",
                decision.get(
                    "risk",
                    "MEDIUM"
                )
            ),

            status="pending_approval"
        )

        db.add(
            operation
        )

        db.flush()

        return {
            "action":
                "created",

            "operation":
                operation
        }

    # =========================================================
    # AUTOMATIC ACTIONS
    # =========================================================

    def _execute_automatic_action(
        self,
        decision,
        risk_assessment
    ):

        if risk_assessment.get(
            "approval"
        ) == "REQUIRED":

            return None

        risk_assessment[
            "execution_status"
        ] = "READY_FOR_EXECUTION"

        request = {

            "approval_request": {

                "status":
                    "APPROVED",

                "request_id":
                    (
                        "AUTO-"
                        +
                        datetime.utcnow().strftime(
                            "%Y%m%d%H%M%S%f"
                        )
                    )
            },

            "risk_assessment":
                risk_assessment,

            "action_type":
                decision.get(
                    "action_type"
                ),

            "title":
                decision.get(
                    "title"
                ),

            "product":
                decision.get(
                    "product"
                ),

            "quantity":
                decision.get(
                    "quantity",
                    0
                )
        }

        try:

            execution = (
                self.execution_engine.execute(
                    request
                )
            )

            if not execution.get(
                "success"
            ):

                return execution

            verification = (
                self.verification_engine.verify(
                    execution
                )
            )

            if verification.get(
                "status"
            ) != "VERIFIED":

                return verification

            monitoring = (
                self.monitoring_engine.monitor(
                    verification
                )
            )

            if monitoring.get(
                "replan_required"
            ):

                return (
                    self.replanning_engine.replan(
                        monitoring
                    )
                )

            return monitoring

        except Exception as exc:

            return {
                "success":
                    False,

                "error":
                    str(exc)
            }

    # =========================================================
    # LIST OPERATIONS
    # =========================================================

    def items(self):

        db = SessionLocal()

        try:

            operations = (
                db.query(Operation)
                .order_by(
                    Operation.id.desc()
                )
                .limit(100)
                .all()
            )

            return [
                self.serialize(
                    operation
                )
                for operation in operations
            ]

        finally:

            db.close()

    # =========================================================
    # SERIALIZE OPERATION
    # =========================================================

    def serialize(
        self,
        operation
    ):

        try:

            payload = json.loads(
                operation.payload
            )

        except Exception:

            payload = {}

        return {

            "id":
                operation.id,

            "action":
                operation.action,

            "domain":
                operation.domain,

            "title":
                operation.title,

            "reason":
                operation.reason,

            "payload":
                payload,

            "risk":
                operation.risk,

            "status":
                operation.status,

            "created_at":
                (
                    operation.created_at.isoformat()
                    if operation.created_at
                    else None
                ),

            "completed_at":
                (
                    operation.completed_at.isoformat()
                    if operation.completed_at
                    else None
                ),

            "verification":
                operation.verification
        }

    # =========================================================
    # APPROVE / REJECT
    # =========================================================

    def status(
        self,
        op_id,
        status
    ):

        allowed = {

            "approved":
                "approved",

            "rejected":
                "rejected"
        }

        new_status = allowed.get(
            status
        )

        if not new_status:

            return None

        db = SessionLocal()

        try:

            operation = db.get(
                Operation,
                op_id
            )

            if not operation:

                return None

            if operation.status != "pending_approval":

                return self.serialize(
                    operation
                )

            operation.status = new_status

            db.commit()

            db.refresh(
                operation
            )

            return self.serialize(
                operation
            )

        finally:

            db.close()

    # =========================================================
    # EXECUTE APPROVED OPERATION
    # =========================================================

    def execute(
        self,
        op_id
    ):

        db = SessionLocal()

        try:

            operation = db.get(
                Operation,
                op_id
            )

            if not operation:

                return None

            if operation.status != "approved":

                return {
                    "error":
                        "Operation must be approved before execution."
                }

            payload = json.loads(
                operation.payload
            )

            action_type = payload.get(
                "action_type",
                operation.action
            )

            risk_assessment = {

                "approval":
                    "REQUIRED",

                "risk_level":
                    operation.risk,

                "execution_status":
                    "READY_FOR_EXECUTION"
            }

            request = {

                "approval_request": {

                    "status":
                        "APPROVED",

                    "request_id":
                        f"DB-{operation.id}"
                },

                "risk_assessment":
                    risk_assessment,

                "action_type":
                    action_type,

                "title":
                    operation.title,

                "product":
                    payload.get(
                        "product"
                    ),

                "quantity":
                    payload.get(
                        "quantity",
                        0
                    )
            }

            execution = (
                self.execution_engine.execute(
                    request
                )
            )

            if not execution.get(
                "success"
            ):

                operation.status = "failed"

                operation.verification = json.dumps(
                    execution
                )

                db.commit()

                db.refresh(
                    operation
                )

                return self.serialize(
                    operation
                )

            verification = (
                self.verification_engine.verify(
                    execution
                )
            )

            monitoring = None

            if verification.get(
                "status"
            ) == "VERIFIED":

                monitoring = (
                    self.monitoring_engine.monitor(
                        verification
                    )
                )

            replanning = None

            if (
                monitoring
                and monitoring.get(
                    "replan_required"
                )
            ):

                replanning = (
                    self.replanning_engine.replan(
                        monitoring
                    )
                )

            if verification.get(
                "status"
            ) == "VERIFIED":

                operation.status = "completed"

                operation.completed_at = (
                    datetime.utcnow()
                )

            else:

                operation.status = "failed"

            operation.verification = json.dumps({

                "execution":
                    execution,

                "verification":
                    verification,

                "monitoring":
                    monitoring,

                "replanning":
                    replanning
            })

            db.commit()

            db.refresh(
                operation
            )

            return self.serialize(
                operation
            )

        except Exception as exc:

            operation.status = "failed"

            operation.verification = json.dumps({

                "error":
                    str(exc)

            })

            db.commit()

            db.refresh(
                operation
            )

            return self.serialize(
                operation
            )

        finally:

            db.close()