import os
import json
import re

import pandas as pd

try:
    from groq import Groq
except Exception:
    Groq = None


# =========================================================
# TIME PERIOD DETECTION
# =========================================================

MONTHS = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12"
}


def detect_period(question):

    q = question.lower().strip()

    if "this month" in q:
        return "this_month"

    if "last month" in q or "previous month" in q:
        return "last_month"

    if "this year" in q:
        return "this_year"

    if "last year" in q or "previous year" in q:
        return "last_year"

    if "yesterday" in q:
        return "yesterday"

    if "today" in q:
        return "today"

    for month_name, month_number in MONTHS.items():

        pattern = rf"\b{month_name}\s*,?\s*(20\d{{2}})\b"

        match = re.search(pattern, q)

        if match:
            return f"{match.group(1)}-{month_number}"

    match = re.search(
        r"\b(20\d{2})-(0[1-9]|1[0-2])\b",
        q
    )

    if match:
        return f"{match.group(1)}-{match.group(2)}"

    match = re.search(
        r"\b(20\d{2})\b",
        q
    )

    if match:
        return match.group(1)

    return None


# =========================================================
# COMPARISON DETECTION
# =========================================================

def detect_comparison(question):

    q = question.lower().strip()

    match = re.search(
        r"(.+?)\s+(?:vs\.?|versus|with)\s+(.+)",
        q
    )

    if match:

        left = detect_period(match.group(1))
        right = detect_period(match.group(2))

        if left and right:
            return left, right

    if "compare" in q:

        periods = []

        for month_name, month_number in MONTHS.items():

            pattern = rf"\b{month_name}\s*,?\s*(20\d{{2}})\b"

            for match in re.finditer(pattern, q):

                periods.append(
                    f"{match.group(1)}-{month_number}"
                )

        for match in re.finditer(
            r"\b20\d{2}\b",
            q
        ):

            year = match.group(0)

            if year not in periods:
                periods.append(year)

        if len(periods) >= 2:
            return periods[0], periods[1]

    return None


# =========================================================
# FORMAT PERIOD SUMMARY
# =========================================================

def format_period_summary(summary):

    return (
        f"### {summary['period']} Business Report\n\n"
        f"**Period:** {summary['start']} → {summary['end']}\n\n"
        f"**Revenue:** ₹{summary['revenue']:,.2f}\n\n"
        f"**Units sold:** {summary['units']:,}\n\n"
        f"**Orders:** {summary['orders']:,}\n\n"
        f"**Customers:** {summary['customers']:,}\n\n"
        f"**Profit:** ₹{summary['profit']:,.2f}\n\n"
        f"**Expenses:** ₹{summary['expenses']:,.2f}"
    )


# =========================================================
# HISTORICAL MONTHLY ANALYSIS
# =========================================================

def historical_monthly_sales(engine):

    sales = engine.sales.copy()

    if sales.empty:
        return pd.DataFrame()

    sales["date"] = pd.to_datetime(
        sales["date"],
        format="mixed",
        errors="coerce"
    )

    sales = sales.dropna(subset=["date"])

    if sales.empty:
        return pd.DataFrame()

    sales["month"] = (
        sales["date"]
        .dt.to_period("M")
        .astype(str)
    )

    monthly = (
        sales
        .groupby("month")
        .agg(
            revenue=("revenue", "sum"),
            units=("units", "sum")
        )
        .reset_index()
        .sort_values("month")
    )

    monthly["previous_revenue"] = monthly["revenue"].shift(1)

    monthly["revenue_change"] = (
        monthly["revenue"]
        - monthly["previous_revenue"]
    )

    monthly["revenue_change_percent"] = (
        monthly["revenue_change"]
        / monthly["previous_revenue"]
        * 100
    )

    monthly.loc[
        monthly["previous_revenue"] == 0,
        "revenue_change_percent"
    ] = None

    monthly["previous_units"] = monthly["units"].shift(1)

    monthly["units_change"] = (
        monthly["units"]
        - monthly["previous_units"]
    )

    monthly["units_change_percent"] = (
        monthly["units_change"]
        / monthly["previous_units"]
        * 100
    )

    monthly.loc[
        monthly["previous_units"] == 0,
        "units_change_percent"
    ] = None

    return monthly


# =========================================================
# HISTORICAL DECLINE DETECTION
# =========================================================

def find_largest_sales_decline(engine):

    monthly = historical_monthly_sales(engine)

    if monthly.empty:
        return None

    declines = monthly[
        monthly["revenue_change"] < 0
    ].copy()

    if declines.empty:
        return None

    row = declines.loc[
        declines["revenue_change"].idxmin()
    ]

    return row.to_dict()


# =========================================================
# HISTORICAL MONTH DETAILS
# =========================================================

def historical_month_details(engine, month):

    sales = engine.sales.copy()

    sales["date"] = pd.to_datetime(
        sales["date"],
        format="mixed",
        errors="coerce"
    )

    sales = sales.dropna(subset=["date"])

    sales["month"] = (
        sales["date"]
        .dt.to_period("M")
        .astype(str)
    )

    current = sales[
        sales["month"] == month
    ].copy()

    if current.empty:
        return None

    month_period = pd.Period(month, freq="M")

    previous_month = str(month_period - 1)

    previous = sales[
        sales["month"] == previous_month
    ].copy()

    # -----------------------------------------------------
    # PRODUCT MOVEMENT
    # -----------------------------------------------------

    current_products = (
        current
        .groupby("product")["revenue"]
        .sum()
    )

    previous_products = (
        previous
        .groupby("product")["revenue"]
        .sum()
    )

    product_movement = pd.concat(
        [
            current_products.rename("current"),
            previous_products.rename("previous")
        ],
        axis=1
    ).fillna(0)

    product_movement["change"] = (
        product_movement["current"]
        - product_movement["previous"]
    )

    product_movement["change_percent"] = (
        product_movement["change"]
        / product_movement["previous"]
        * 100
    )

    product_movement.loc[
        product_movement["previous"] == 0,
        "change_percent"
    ] = None

    product_movement = (
        product_movement
        .reset_index()
        .sort_values("change", ascending=True)
    )

    # -----------------------------------------------------
    # REGION MOVEMENT
    # -----------------------------------------------------

    current_regions = (
        current
        .groupby("region")["revenue"]
        .sum()
    )

    previous_regions = (
        previous
        .groupby("region")["revenue"]
        .sum()
    )

    region_movement = pd.concat(
        [
            current_regions.rename("current"),
            previous_regions.rename("previous")
        ],
        axis=1
    ).fillna(0)

    region_movement["change"] = (
        region_movement["current"]
        - region_movement["previous"]
    )

    region_movement["change_percent"] = (
        region_movement["change"]
        / region_movement["previous"]
        * 100
    )

    region_movement.loc[
        region_movement["previous"] == 0,
        "change_percent"
    ] = None

    region_movement = (
        region_movement
        .reset_index()
        .sort_values("change", ascending=True)
    )

    # -----------------------------------------------------
    # ORDERS
    # -----------------------------------------------------

    orders = engine.orders.copy()

    orders["date"] = pd.to_datetime(
        orders["date"],
        format="mixed",
        errors="coerce"
    )

    orders = orders.dropna(subset=["date"])

    orders["month"] = (
        orders["date"]
        .dt.to_period("M")
        .astype(str)
    )

    current_orders = orders[
        orders["month"] == month
    ]

    previous_orders = orders[
        orders["month"] == previous_month
    ]

    current_order_count = len(current_orders)
    previous_order_count = len(previous_orders)

    if previous_order_count:

        order_change_percent = (
            (
                current_order_count
                - previous_order_count
            )
            / previous_order_count
        ) * 100

    else:

        order_change_percent = None

    # -----------------------------------------------------
    # INVENTORY CONTEXT
    # -----------------------------------------------------

    inventory = engine.inventory.copy()

    inventory["stock"] = pd.to_numeric(
        inventory["stock"],
        errors="coerce"
    ).fillna(0)

    inventory["reorder_level"] = pd.to_numeric(
        inventory["reorder_level"],
        errors="coerce"
    ).fillna(0)

    low_stock = inventory[
        inventory["stock"] <= inventory["reorder_level"]
    ].copy()

    # -----------------------------------------------------
    # MARKETING CONTEXT
    # -----------------------------------------------------

    marketing = engine.marketing.copy()

    marketing["date"] = pd.to_datetime(
        marketing["date"],
        format="mixed",
        errors="coerce"
    )

    marketing = marketing.dropna(subset=["date"])

    marketing["month"] = (
        marketing["date"]
        .dt.to_period("M")
        .astype(str)
    )

    current_marketing = marketing[
        marketing["month"] == month
    ]

    previous_marketing = marketing[
        marketing["month"] == previous_month
    ]

    def marketing_summary(data):

        if data.empty:
            return {
                "leads": 0,
                "conversions": 0,
                "spend": 0,
                "conversion_rate": 0
            }

        leads = pd.to_numeric(
            data.get(
                "leads",
                pd.Series(dtype=float)
            ),
            errors="coerce"
        ).fillna(0).sum()

        conversions = pd.to_numeric(
            data.get(
                "conversions",
                pd.Series(dtype=float)
            ),
            errors="coerce"
        ).fillna(0).sum()

        spend = pd.to_numeric(
            data.get(
                "spend",
                pd.Series(dtype=float)
            ),
            errors="coerce"
        ).fillna(0).sum()

        conversion_rate = (
            conversions / leads * 100
            if leads
            else 0
        )

        return {
            "leads": int(leads),
            "conversions": int(conversions),
            "spend": float(spend),
            "conversion_rate": round(
                conversion_rate,
                2
            )
        }

    current_marketing_summary = marketing_summary(
        current_marketing
    )

    previous_marketing_summary = marketing_summary(
        previous_marketing
    )

    return {
        "month": month,
        "previous_month": previous_month,
        "current_revenue": float(current["revenue"].sum()),
        "previous_revenue": float(previous["revenue"].sum()),
        "current_units": float(current["units"].sum()),
        "previous_units": float(previous["units"].sum()),
        "current_orders": current_order_count,
        "previous_orders": previous_order_count,
        "order_change_percent": order_change_percent,
        "product_movement": product_movement.to_dict("records"),
        "region_movement": region_movement.to_dict("records"),
        "low_stock": low_stock[
            ["product", "stock", "reorder_level"]
        ].to_dict("records"),
        "current_marketing": current_marketing_summary,
        "previous_marketing": previous_marketing_summary
    }


# =========================================================
# HISTORICAL DECLINE REPORT
# =========================================================

def historical_decline_report(engine, requested_month=None):

    if requested_month:

        details = historical_month_details(
            engine,
            requested_month
        )

        if details is None:
            return None

        month = requested_month

    else:

        decline = find_largest_sales_decline(engine)

        if decline is None:
            return None

        month = decline["month"]

        details = historical_month_details(
            engine,
            month
        )

    if details is None:
        return None

    current_revenue = details["current_revenue"]
    previous_revenue = details["previous_revenue"]

    if previous_revenue:

        revenue_change = (
            (
                current_revenue
                - previous_revenue
            )
            / previous_revenue
        ) * 100

    else:
        revenue_change = None

    current_units = details["current_units"]
    previous_units = details["previous_units"]

    if previous_units:

        units_change = (
            (
                current_units
                - previous_units
            )
            / previous_units
        ) * 100

    else:
        units_change = None

    product_declines = [
        item
        for item in details["product_movement"]
        if item["change"] < 0
    ]

    product_declines.sort(
        key=lambda x: x["change"]
    )

    region_declines = [
        item
        for item in details["region_movement"]
        if item["change"] < 0
    ]

    region_declines.sort(
        key=lambda x: x["change"]
    )

    evidence = []

    if revenue_change is not None:

        evidence.append(
            f"Revenue changed by {revenue_change:.2f}% "
            f"from {details['previous_month']} to {month}."
        )

    if units_change is not None:

        evidence.append(
            f"Units sold changed by {units_change:.2f}%."
        )

    if details["order_change_percent"] is not None:

        evidence.append(
            f"Orders changed by "
            f"{details['order_change_percent']:.2f}%."
        )

    drivers = []

    if units_change is not None and units_change < 0:

        drivers.append(
            "Lower sales volume was a measurable "
            "contributor to the revenue decline."
        )

    if product_declines:

        top_product = product_declines[0]

        drivers.append(
            f"{top_product['product']} had the largest "
            f"absolute product-level revenue decline, "
            f"changing by ₹{abs(top_product['change']):,.2f}."
        )

    if region_declines:

        top_region = region_declines[0]

        drivers.append(
            f"{top_region['region']} had the largest "
            f"absolute regional revenue decline, "
            f"changing by ₹{abs(top_region['change']):,.2f}."
        )

    if (
        details["order_change_percent"] is not None
        and details["order_change_percent"] < 0
    ):

        drivers.append(
            "The decline in order volume also supports "
            "lower demand as a contributor."
        )

    if not drivers:

        drivers.append(
            "The available sales data confirms the decline, "
            "but does not by itself establish a single "
            "causal factor."
        )

    inventory_risks = [
        item["product"]
        for item in details["low_stock"]
    ]

    recommendations = []

    if product_declines:

        recommendations.append(
            "Investigate the largest declining products "
            "individually and compare their demand, stock "
            "availability and order activity."
        )

    if region_declines:

        recommendations.append(
            "Review the weakest regions for changes in demand, "
            "customer activity and marketing performance."
        )

    if (
        details["order_change_percent"] is not None
        and details["order_change_percent"] < 0
    ):

        recommendations.append(
            "Investigate order cancellations, lost orders "
            "and customer purchasing activity."
        )

    if inventory_risks:

        recommendations.append(
            f"Check inventory pressure separately. "
            f"{len(inventory_risks)} products are currently "
            f"at or below their reorder levels."
        )

    marketing_change = None

    current_marketing = details["current_marketing"]
    previous_marketing = details["previous_marketing"]

    if previous_marketing["conversion_rate"]:

        marketing_change = (
            current_marketing["conversion_rate"]
            - previous_marketing["conversion_rate"]
        )

    if (
        marketing_change is not None
        and marketing_change < 0
    ):

        recommendations.append(
            "Review marketing conversion performance "
            "because the conversion rate also declined."
        )

    if not recommendations:

        recommendations.append(
            "Compare product, region, order, customer, "
            "inventory and marketing evidence before "
            "taking corrective action."
        )

    return {
        "month": month,
        "previous_month": details["previous_month"],
        "current_revenue": current_revenue,
        "previous_revenue": previous_revenue,
        "revenue_change_percent": revenue_change,
        "current_units": current_units,
        "previous_units": previous_units,
        "units_change_percent": units_change,
        "current_orders": details["current_orders"],
        "previous_orders": details["previous_orders"],
        "order_change_percent": details["order_change_percent"],
        "drivers": drivers,
        "evidence": evidence,
        "declining_products": product_declines[:5],
        "declining_regions": region_declines[:5],
        "inventory_risks": inventory_risks[:10],
        "current_marketing": current_marketing,
        "previous_marketing": previous_marketing,
        "recommendations": recommendations
    }


# =========================================================
# FORMAT HISTORICAL DECLINE REPORT
# =========================================================

def format_historical_decline_report(report):

    change = report["revenue_change_percent"]

    if change is None:

        change_text = (
            "Revenue could not be compared because "
            "the previous month had no recorded revenue."
        )

    else:

        change_text = (
            f"Revenue changed by **{change:.2f}%**."
        )

    product_lines = []

    for item in report["declining_products"][:5]:

        product_lines.append(
            f"- **{item['product']}**: "
            f"₹{abs(item['change']):,.2f} revenue decline"
        )

    region_lines = []

    for item in report["declining_regions"][:5]:

        region_lines.append(
            f"- **{item['region']}**: "
            f"₹{abs(item['change']):,.2f} revenue decline"
        )

    return (
        f"### Sales Decline Analysis\n\n"
        f"**Largest decline identified:** {report['month']}\n\n"
        f"Compared with **{report['previous_month']}**, "
        f"revenue changed from "
        f"**₹{report['previous_revenue']:,.2f}** "
        f"to **₹{report['current_revenue']:,.2f}**.\n\n"
        f"{change_text}\n\n"
        f"### What the data shows\n\n"
        + "\n".join(
            f"- {item}"
            for item in report["evidence"]
        )
        + "\n\n### Likely Business Drivers\n\n"
        + "\n".join(
            f"- {item}"
            for item in report["drivers"]
        )
        + "\n\n### Declining Products\n\n"
        + (
            "\n".join(product_lines)
            if product_lines
            else "No product-level revenue declines were identified."
        )
        + "\n\n### Declining Regions\n\n"
        + (
            "\n".join(region_lines)
            if region_lines
            else "No regional revenue declines were identified."
        )
        + "\n\n### Important Risk Context\n\n"
        + f"{len(report['inventory_risks'])} products "
        f"are currently at or below their reorder levels. "
        f"These are treated as **future operational risks**, "
        f"not automatically as the cause of the historical "
        f"sales decline.\n\n"
        + "### Recommended Actions\n\n"
        + "\n".join(
            f"{index}. {item}"
            for index, item in enumerate(
                report["recommendations"],
                start=1
            )
        )
    )


# =========================================================
# FORMAT HISTORICAL ACTION PLAN
# =========================================================

def format_historical_action_plan(report):

    change = report["revenue_change_percent"]

    if change is None:

        change_text = (
            "The available data does not provide "
            "a reliable percentage comparison."
        )

    else:

        change_text = (
            f"Revenue changed by **{change:.2f}%** "
            f"from {report['previous_month']} "
            f"to {report['month']}."
        )

    action_lines = []

    for index, recommendation in enumerate(
        report["recommendations"],
        start=1
    ):

        action_lines.append(
            f"{index}. **{recommendation}**"
        )

    priority_actions = []

    if report["declining_products"]:

        top_product = report["declining_products"][0]

        priority_actions.append(
            f"Investigate **{top_product['product']}** first, "
            f"as it had the largest product-level revenue "
            f"decline of ₹{abs(top_product['change']):,.2f}."
        )

    if report["declining_regions"]:

        top_region = report["declining_regions"][0]

        priority_actions.append(
            f"Investigate the **{top_region['region']}** region, "
            f"which had the largest regional revenue decline "
            f"of ₹{abs(top_region['change']):,.2f}."
        )

    if (
        report["order_change_percent"] is not None
        and report["order_change_percent"] < 0
    ):

        priority_actions.append(
            "Review order activity and cancellation patterns "
            "to determine whether weaker demand contributed "
            "to the decline."
        )

    if report["inventory_risks"]:

        priority_actions.append(
            f"Separately monitor the "
            f"**{len(report['inventory_risks'])}** products "
            f"currently at or below reorder levels. "
            f"This is a future operational risk, not proof "
            f"of the historical decline."
        )

    if not priority_actions:

        priority_actions.append(
            "Perform a deeper product, regional, order, "
            "customer and marketing investigation before "
            "taking corrective action."
        )

    return (
        f"### {report['month']} Business Action Plan\n\n"
        f"**Period investigated:** "
        f"{report['previous_month']} → {report['month']}\n\n"
        f"{change_text}\n\n"
        f"### What NEXORAAI Found\n\n"
        + "\n".join(
            f"- {driver}"
            for driver in report["drivers"]
        )
        + "\n\n### Priority Actions\n\n"
        + "\n".join(
            f"{index}. {action}"
            for index, action in enumerate(
                priority_actions,
                start=1
            )
        )
        + "\n\n### Recommended Investigation Plan\n\n"
        + "\n".join(action_lines)
        + "\n\n### Decision Note\n\n"
        "These actions are based on the available "
        "historical evidence. The data identifies measurable "
        "drivers and signals, but it does not prove that any "
        "single factor caused the entire decline."
    )


# =========================================================
# OPERATIONS INTELLIGENCE
# =========================================================

def get_operations():

    try:

        from agents.orchestrator import Orchestrator
        from analytics.engine import AnalyticsEngine

        orchestrator = Orchestrator(
            AnalyticsEngine()
        )

        return orchestrator.items()

    except Exception:

        return []


def format_pending_operations(operations):

    pending = [
        op
        for op in operations
        if op.get("status") == "pending_approval"
    ]

    if not pending:

        return (
            "### Approval Queue\n\n"
            "There are currently **no actions waiting "
            "for approval**."
        )

    lines = []

    for op in pending:

        payload = op.get("payload") or {}

        product = payload.get("product")

        quantity = payload.get("quantity")

        details = ""

        if product:
            details += f" | Product: **{product}**"

        if quantity is not None:
            details += f" | Quantity: **{quantity}**"

        lines.append(
            f"- **#{op['id']} — {op['title']}**"
            f" | Priority: **{payload.get('priority', 'N/A')}**"
            f" | Risk: **{op.get('risk', 'N/A')}**"
            f"{details}\n"
            f"  Reason: {op.get('reason', 'No reason provided.')}"
        )

    return (
        f"### Actions Waiting for Approval\n\n"
        f"NEXORAAI currently has **{len(pending)} "
        f"actions waiting for human approval**.\n\n"
        + "\n".join(lines)
        + "\n\n"
        "These actions remain pending until an authorized "
        "user approves or rejects them."
    )


def format_completed_operations(operations):

    completed = [
        op
        for op in operations
        if op.get("status") == "completed"
    ]

    if not completed:

        return (
            "### Execution History\n\n"
            "No completed operations are currently recorded."
        )

    lines = []

    for op in completed[:10]:

        payload = op.get("payload") or {}

        product = payload.get("product")
        quantity = payload.get("quantity")

        details = ""

        if product:
            details += f" | Product: **{product}**"

        if quantity is not None:
            details += f" | Quantity: **{quantity}**"

        lines.append(
            f"- **#{op['id']} — {op['title']}**"
            f"{details}"
            f" | Completed: {op.get('completed_at') or 'Recorded'}"
        )

    return (
        f"### Completed Operations\n\n"
        f"NEXORAAI has **{len(completed)} completed "
        f"operations** in the current operation history.\n\n"
        + "\n".join(lines)
    )


def format_rejected_operations(operations):

    rejected = [
        op
        for op in operations
        if op.get("status") == "rejected"
    ]

    if not rejected:

        return (
            "### Rejected Operations\n\n"
            "No rejected operations are currently recorded."
        )

    lines = []

    for op in rejected[:10]:

        lines.append(
            f"- **#{op['id']} — {op['title']}**"
            f" | Reason: {op.get('reason', 'No reason provided.')}"
        )

    return (
        f"### Rejected Operations\n\n"
        f"NEXORAAI has **{len(rejected)} rejected "
        f"operations** in the current operation history.\n\n"
        + "\n".join(lines)
    )


# =========================================================
# ANSWER
# =========================================================

def answer(question, context):

    try:

        from analytics.engine import AnalyticsEngine

        engine = AnalyticsEngine()

    except Exception:

        engine = None

    q = question.lower().strip()

    overview = context.get("overview", {})
    insights = context.get("insights", [])
    sales = context.get("sales", {})
    diagnosis = context.get("diagnosis", {})

    # =====================================================
    # OPERATIONS / APPROVAL QUESTIONS
    # =====================================================

    operation_question = any(
        phrase in q
        for phrase in [
            "waiting for approval",
            "pending approval",
            "pending approvals",
            "awaiting approval",
            "awaiting approvals",
            "actions pending",
            "pending actions",
            "operations pending",
            "which actions are waiting",
            "what actions are waiting",
            "show pending",
            "approval queue"
        ]
    )

    execution_question = any(
        phrase in q
        for phrase in [
            "what did nexoraa execute",
            "what did nexorai execute",
            "what has nexoraa executed",
            "what has nexorai executed",
            "what did nexoraa complete",
            "what did nexorai complete",
            "completed operations",
            "executed operations",
            "execution history",
            "what actions were executed"
        ]
    )

    rejected_question = any(
        phrase in q
        for phrase in [
            "rejected actions",
            "rejected operations",
            "what was rejected",
            "what actions were rejected",
            "show rejected"
        ]
    )

    if operation_question:

        operations = get_operations()

        return format_pending_operations(
            operations
        )

    if execution_question:

        operations = get_operations()

        return format_completed_operations(
            operations
        )

    if rejected_question:

        operations = get_operations()

        return format_rejected_operations(
            operations
        )

    # =====================================================
    # HISTORICAL SALES INTELLIGENCE
    # =====================================================

    if engine:

        historical_question = any(
            phrase in q
            for phrase in [
                "which month",
                "what month",
                "month had",
                "month where",
                "biggest decline",
                "largest decline",
                "highest decline",
                "sales went down",
                "sales fell",
                "sales drop",
                "sales declined",
                "revenue declined",
                "revenue fell",
                "revenue drop",
                "historical decline",
                "historically"
            ]
        )

        why_decline_question = (
            (
                "why" in q
                or "reason" in q
                or "cause" in q
                or "caused" in q
            )
            and
            any(
                word in q
                for word in [
                    "decline",
                    "declined",
                    "drop",
                    "dropped",
                    "fall",
                    "fell",
                    "decrease",
                    "decreased",
                    "down",
                    "sales",
                    "revenue"
                ]
            )
        )

        recommendation_question = (
            any(
                phrase in q
                for phrase in [
                    "what should we do",
                    "what should nexoraa do",
                    "what should nexorai do",
                    "what can we do",
                    "what do we do",
                    "what action should",
                    "what actions should",
                    "what action can",
                    "what actions can",
                    "how should we respond",
                    "how can we respond",
                    "how should nexoraa respond",
                    "how should nexorai respond",
                    "how to fix",
                    "how can we fix",
                    "what recommendations",
                    "recommendations for",
                    "recommend action",
                    "suggest actions",
                    "suggest action"
                ]
            )
            and
            any(
                word in q
                for word in [
                    "decline",
                    "declined",
                    "drop",
                    "dropped",
                    "fall",
                    "fell",
                    "decrease",
                    "decreased",
                    "down",
                    "sales",
                    "revenue"
                ]
            )
        )

        detected = detect_period(question)

        requested_month = None

        if (
            detected
            and re.fullmatch(
                r"20\d{2}-\d{2}",
                detected
            )
        ):

            requested_month = detected

        if (
            recommendation_question
            and requested_month
        ):

            report = historical_decline_report(
                engine,
                requested_month=requested_month
            )

            if report:

                return format_historical_action_plan(
                    report
                )

        if (
            historical_question
            or why_decline_question
        ):

            report = historical_decline_report(
                engine,
                requested_month=requested_month
            )

            if report:

                return format_historical_decline_report(
                    report
                )

    # =====================================================
    # TIME PERIOD DETECTION
    # =====================================================

    comparison = detect_comparison(question)
    period = detect_period(question)

    # =====================================================
    # COMPARISON QUESTION
    # =====================================================

    if comparison and engine:

        current_period, previous_period = comparison

        try:

            result = engine.compare_periods(
                current_period,
                previous_period
            )

            current = result["current"]
            previous = result["previous"]
            change = result["revenue_change_percent"]

            direction = (
                "increased"
                if change >= 0
                else "decreased"
            )

            return (
                f"### Business Period Comparison\n\n"
                f"**{current['period']}**\n"
                f"- Revenue: ₹{current['revenue']:,.2f}\n"
                f"- Units: {current['units']:,}\n"
                f"- Orders: {current['orders']:,}\n"
                f"- Customers: {current['customers']:,}\n"
                f"- Profit: ₹{current['profit']:,.2f}\n\n"
                f"**{previous['period']}**\n"
                f"- Revenue: ₹{previous['revenue']:,.2f}\n"
                f"- Units: {previous['units']:,}\n"
                f"- Orders: {previous['orders']:,}\n"
                f"- Customers: {previous['customers']:,}\n"
                f"- Profit: ₹{previous['profit']:,.2f}\n\n"
                f"### Revenue Change\n\n"
                f"Revenue **{direction} "
                f"{abs(change):.2f}%** "
                f"from {previous['period']} "
                f"to {current['period']}."
            )

        except ValueError as exc:

            return (
                f"I couldn't calculate that comparison "
                f"because one of the requested periods "
                f"is not supported: {exc}"
            )

    # =====================================================
    # SINGLE PERIOD BUSINESS QUESTION
    # =====================================================

    if period and engine:

        try:

            summary = engine.period_summary(period)

            is_period_question = any(
                word in q
                for word in [
                    "sales",
                    "revenue",
                    "profit",
                    "finance",
                    "financial",
                    "expense",
                    "order",
                    "orders",
                    "customer",
                    "customers",
                    "business",
                    "report",
                    "performance",
                    "units"
                ]
            )

            if is_period_question:

                requested_metrics = []

                if "sales" in q or "revenue" in q:

                    requested_metrics.append(
                        f"Revenue: ₹{summary['revenue']:,.2f}"
                    )

                if "profit" in q:

                    requested_metrics.append(
                        f"Profit: ₹{summary['profit']:,.2f}"
                    )

                if "expense" in q or "expenses" in q:

                    requested_metrics.append(
                        f"Expenses: ₹{summary['expenses']:,.2f}"
                    )

                if "order" in q or "orders" in q:

                    requested_metrics.append(
                        f"Orders: {summary['orders']:,}"
                    )

                if "customer" in q or "customers" in q:

                    requested_metrics.append(
                        f"Customers: {summary['customers']:,}"
                    )

                if "units" in q:

                    requested_metrics.append(
                        f"Units: {summary['units']:,}"
                    )

                if requested_metrics:

                    return (
                        f"### {summary['period']} Results\n\n"
                        f"**Period:** "
                        f"{summary['start']} → "
                        f"{summary['end']}\n\n"
                        +
                        "\n".join(
                            f"- {metric}"
                            for metric in requested_metrics
                        )
                    )

                return format_period_summary(summary)

        except ValueError:

            pass

    # =====================================================
    # GROQ AI REASONING
    # =====================================================

    key = os.getenv("GROQ_API_KEY")

    if key and Groq:

        client = Groq(api_key=key)

        prompt = f"""
You are NEXORAAI, an enterprise business intelligence
and autonomous operations assistant.

Answer the user's business question using ONLY the supplied
company context.

Rules:

1. Directly answer the question.
2. Use actual numbers from the context.
3. Explain the evidence behind your answer.
4. Identify likely causes only when the data supports them.
5. Clearly separate confirmed evidence, likely drivers,
   and future risks.
6. Recommend practical next actions.
7. Never invent missing information.
8. If the context does not contain enough information,
   clearly say what information is missing.
9. Keep the answer structured and easy for a business user
   to understand.
10. Respect the requested time period.
11. Do not turn inventory risk into a historical sales
    cause unless the data actually supports that relationship.

USER QUESTION:
{question}

COMPANY CONTEXT:
{json.dumps(context, default=str)[:30000]}
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )

        return response.choices[0].message.content

    # =====================================================
    # DETERMINISTIC BUSINESS REASONING
    # =====================================================

    revenue = overview.get("revenue", 0)
    growth = overview.get("revenue_growth", 0)
    orders = overview.get("orders", 0)
    customers = overview.get("customers", 0)
    profit = overview.get("profit", 0)
    low_stock = overview.get("low_stock_items", 0)

    # =====================================================
    # PRODUCT / REGION QUESTION
    # =====================================================

    if (
        "product" in q
        and "region" in q
        and (
            "revenue" in q
            or "growth" in q
        )
    ):

        top_products = sales.get("top_products", [])
        top_regions = sales.get("regions", [])

        product_text = ", ".join(
            f"{x.get('product')}: "
            f"₹{x.get('revenue', 0):,.0f}"
            for x in top_products[:5]
        )

        region_text = ", ".join(
            f"{x.get('region')}: "
            f"₹{x.get('revenue', 0):,.0f}"
            for x in top_regions[:5]
        )

        return (
            f"### Revenue Drivers\n\n"
            f"**Top products:** "
            f"{product_text or 'No product-level data available.'}\n\n"
            f"**Top regions:** "
            f"{region_text or 'No regional data available.'}\n\n"
            f"Overall revenue is **₹{revenue:,.0f}**, "
            f"with **{growth:.1f}% growth**.\n\n"
            f"**Recommended next step:** "
            f"Compare the strongest products and regions "
            f"against inventory availability and order demand "
            f"before increasing supply or marketing."
        )

    # =====================================================
    # INVENTORY INTELLIGENCE
    # =====================================================

    if any(
        word in q
        for word in [
            "inventory",
            "stock",
            "stockout"
        ]
    ):

        inventory_data = diagnosis.get(
            "inventory_evidence",
            {}
        )

        inventory_data = inventory_data.get(
            "intelligence",
            []
        )

        if inventory_data:

            priority_items = [
                item
                for item in inventory_data
                if item.get("priority")
                in ["CRITICAL", "HIGH"]
            ]

            details = []

            for item in priority_items[:8]:

                details.append(
                    f"- **{item['product']}** — "
                    f"{item['priority']} priority | "
                    f"Stock: {item['stock']} | "
                    f"Recent 30-day demand: "
                    f"{item['recent_demand']} | "
                    f"Days of stock: "
                    f"{item['days_of_stock']:.1f} | "
                    f"Recommended quantity: "
                    f"{item['recommended_quantity']}"
                )

            return (
                f"### Inventory Intelligence\n\n"
                f"NEXORAAI identified "
                f"**{len(priority_items)} "
                f"products requiring attention**.\n\n"
                f"{chr(10).join(details)}\n\n"
                f"### Recommended Approach\n\n"
                f"Prioritize CRITICAL items first, especially "
                f"products with very few days of remaining stock. "
                f"Then address HIGH-priority products according "
                f"to demand and replenishment requirements."
            )

        return (
            f"### Inventory Situation\n\n"
            f"NEXORAAI currently identifies "
            f"**{low_stock} low-stock items**, "
            f"but detailed inventory intelligence "
            f"is not currently available."
        )

    # =====================================================
    # ORDERS / CANCELLATION
    # =====================================================

    if any(
        word in q
        for word in [
            "order",
            "cancel",
            "cancellation"
        ]
    ):

        order_signals = [
            i
            for i in insights
            if i.get("domain") == "orders"
        ]

        if order_signals:

            return (
                f"### Order Situation\n\n"
                +
                "\n".join(
                    f"- **{i.get('title')}** — "
                    f"{i.get('summary', '')}"
                    for i in order_signals
                )
                +
                "\n\n**Recommended action:** "
                "Investigate cancellation reasons, "
                "delivery performance and inventory availability."
            )

        return (
            f"The current period contains "
            f"**{orders:,} orders**. "
            f"No major order-specific signal "
            f"is currently available."
        )

    # =====================================================
    # CUSTOMER QUESTION
    # =====================================================

    if any(
        word in q
        for word in [
            "customer",
            "customers",
            "churn"
        ]
    ):

        return (
            f"### Customer Situation\n\n"
            f"NEXORAAI currently has "
            f"**{customers:,} active customers** "
            f"in the available sales data.\n\n"
            f"**Recommended action:** "
            f"Segment customers by purchase activity, "
            f"value and recent behavior to identify "
            f"retention and growth opportunities."
        )

    # =====================================================
    # PROFIT / FINANCE
    # =====================================================

    if any(
        word in q
        for word in [
            "profit",
            "finance",
            "financial",
            "expense"
        ]
    ):

        return (
            f"### Financial Situation\n\n"
            f"Revenue: **₹{revenue:,.0f}**\n\n"
            f"Profit: **₹{profit:,.0f}**\n\n"
            f"Revenue growth: **{growth:.1f}%**\n\n"
            f"**Recommended action:** "
            f"Compare revenue growth with expenses, "
            f"product margins and operating costs before "
            f"making major financial decisions."
        )

    # =====================================================
    # BUSINESS RISK / SITUATION
    # =====================================================

    if any(
        word in q
        for word in [
            "risk",
            "problem",
            "issue",
            "situation",
            "action",
            "should",
            "why"
        ]
    ):

        signal_text = "\n".join(
            f"- **{i.get('title')}** — "
            f"{i.get('summary', '')}"
            for i in insights[:8]
        )

        return (
            f"### Current Business Situation\n\n"
            f"Revenue is **₹{revenue:,.0f}**, "
            f"with **{growth:.1f}% growth**.\n\n"
            f"Profit is **₹{profit:,.0f}** "
            f"and there are **{low_stock} "
            f"low-stock items**.\n\n"
            f"### Active Signals\n"
            f"{signal_text or 'No major active signals.'}\n\n"
            f"### Recommended Approach\n"
            f"Prioritize inventory risks, investigate "
            f"order issues, and evaluate the products "
            f"and regions contributing most to revenue "
            f"before taking operational action."
        )

    # =====================================================
    # GENERAL QUESTION
    # =====================================================

    return (
        f"### NEXORAAI Business Summary\n\n"
        f"Revenue: **₹{revenue:,.0f}**\n"
        f"Revenue growth: **{growth:.1f}%**\n"
        f"Orders: **{orders:,}**\n"
        f"Customers: **{customers:,}**\n"
        f"Profit: **₹{profit:,.0f}**\n"
        f"Low-stock items: **{low_stock}**\n\n"
        f"Ask me about **sales, products, regions, "
        f"inventory, orders, customers, finance, "
        f"profit, historical performance, business risks, "
        f"or autonomous operations**."
    )