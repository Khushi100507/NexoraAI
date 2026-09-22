let chart;


/* =========================================================
   BASIC HELPERS
========================================================= */

const money = n =>
    "₹" + Number(n || 0).toLocaleString("en-IN", {
        maximumFractionDigits: 0
    });


function percentChange(current, previous) {

    current = Number(current || 0);
    previous = Number(previous || 0);

    if (previous === 0) {
        return current === 0 ? 0 : 100;
    }

    return ((current - previous) / previous) * 100;

}


function changeText(current, previous) {

    const change =
        percentChange(current, previous);

    const direction =
        change > 0
            ? "↑"
            : change < 0
                ? "↓"
                : "→";

    return `
        ${direction}
        ${Math.abs(change).toFixed(2)}%
    `;

}


async function get(url) {

    const response = await fetch(url);

    if (!response.ok)
        throw Error(await response.text());

    return response.json();
}


/* =========================================================
   PAGE NAVIGATION
========================================================= */

function showSection(sectionId) {

    document
        .querySelectorAll(".page-section")
        .forEach(section => {

            section.classList.remove(
                "active-section"
            );

        });


    const selected =
        document.getElementById(sectionId);

    if (selected) {

        selected.classList.add(
            "active-section"
        );

    }


    document
        .querySelectorAll(".nav-btn")
        .forEach(button => {

            button.classList.remove("active");

        });


    const buttons =
        document.querySelectorAll(".nav-btn");

    buttons.forEach(button => {

        const onclick =
            button.getAttribute("onclick");

        if (
            onclick &&
            onclick.includes(
                `'${sectionId}'`
            )
        ) {

            button.classList.add("active");

        }

    });


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });

}


/* =========================================================
   PERFORMANCE PERIOD
========================================================= */

let selectedPeriod = "this_month";


async function loadPeriods() {

    const selector =
        document.querySelector("#performance-period");

    if (!selector)
        return;


    try {

        const data =
            await get("/api/periods");


        selector.innerHTML =
            data.periods.map(
                period => `

                    <option value="${period.value}">
                        ${period.label}
                    </option>

                `
            ).join("");


        selector.value =
            selectedPeriod;


    } catch (error) {

        console.error(
            "Period loading error:",
            error
        );

    }

}


async function changePerformancePeriod(period) {

    selectedPeriod = period;

    await loadPerformance(
        selectedPeriod
    );

}


async function loadPerformance(period = "this_month") {

    try {

        const sales =
            await get(
                `/api/sales?period=${encodeURIComponent(period)}`
            );


        const summary =
            await get(
                `/api/sales/summary?period=${encodeURIComponent(period)}`
            );


        performanceCards(
            summary
        );


        products(
            sales.top_products
        );


        graph(
            sales.daily
        );


        regions(
            sales.regions
        );


        updatePerformanceTitle(
            sales.period
        );


    } catch (error) {

        console.error(
            "Performance loading error:",
            error
        );

    }

}


/* =========================================================
   PERFORMANCE TITLE
========================================================= */

function updatePerformanceTitle(period) {

    const title =
        document.querySelector(
            "#performance-period-label"
        );

    if (title) {

        title.textContent =
            period || "Selected Period";

    }

}


/* =========================================================
   PERFORMANCE KPI CARDS
========================================================= */

function performanceCards(data) {

    const element =
        document.querySelector(
            "#performance-cards"
        );

    if (!element)
        return;


    element.innerHTML = [

        [
            "Revenue",
            money(data.revenue),
            data.period
        ],

        [
            "Orders",
            Number(
                data.orders || 0
            ).toLocaleString(),
            data.period
        ],

        [
            "Customers",
            Number(
                data.customers || 0
            ).toLocaleString(),
            data.period
        ],

        [
            "Profit",
            money(data.profit),
            data.period
        ],

        [
            "Units Sold",
            Number(
                data.units || 0
            ).toLocaleString(),
            data.period
        ]

    ].map(item => `

        <div class="card">

            <div class="label">
                ${item[0]}
            </div>

            <div class="value">
                ${item[1]}
            </div>

            <div class="muted">
                ${item[2]}
            </div>

        </div>

    `).join("");

}


/* =========================================================
   REFRESH EVERYTHING
========================================================= */

async function refreshAll() {

    try {

        const [
            overview,
            intelligence,
            diagnosisData,
            operationsData
        ] = await Promise.all([

            get("/api/overview"),

            get("/api/insights"),

            get("/api/diagnosis"),

            get("/api/operations")

        ]);


        cards(overview);


        insights(
            intelligence
        );


        diagnosis(
            diagnosisData
        );


        operations(
            operationsData
        );


        commandCenter(
            overview,
            intelligence,
            diagnosisData,
            operationsData
        );


        await loadPerformance(
            selectedPeriod
        );


    } catch (error) {

        console.error(
            "NEXORAAI refresh error:",
            error
        );

    }

}


/* =========================================================
   COMMAND CENTER KPI CARDS
========================================================= */

function cards(o) {

    const element =
        document.querySelector(
            "#cards"
        );

    if (!element)
        return;


    element.innerHTML = [

        [
            "Revenue",
            money(o.revenue),
            `${o.revenue_growth}% vs previous`
        ],

        [
            "Orders",
            Number(
                o.orders || 0
            ).toLocaleString(),
            o.period || "current period"
        ],

        [
            "Customers",
            Number(
                o.customers || 0
            ).toLocaleString(),
            o.period || "active in sales"
        ],

        [
            "Profit",
            money(o.profit),
            o.period || "current period"
        ],

        [
            "Low stock",
            o.low_stock_items,
            "items requiring attention"
        ]

    ].map(item => `

        <div class="card">

            <div class="label">
                ${item[0]}
            </div>

            <div class="value">
                ${item[1]}
            </div>

            <div class="muted">
                ${item[2]}
            </div>

        </div>

    `).join("");

}


/* =========================================================
   TOP PRODUCTS
========================================================= */

function products(data) {

    const element =
        document.querySelector(
            "#products"
        );

    if (!element)
        return;


    if (!data || !data.length) {

        element.innerHTML =
            "<p class='muted'>No product data available.</p>";

        return;

    }


    element.innerHTML =
        data.map(
            item => `

                <div class="product">

                    <span>
                        ${item.product}
                    </span>

                    <b>
                        ${money(item.revenue)}
                    </b>

                </div>

            `
        ).join("");

}


/* =========================================================
   REVENUE GRAPH
========================================================= */

function graph(data) {

    const canvas =
        document.querySelector(
            "#chart"
        );

    if (!canvas)
        return;


    if (chart)
        chart.destroy();


    chart = new Chart(
        canvas,
        {

            type: "line",

            data: {

                labels:
                    data.map(
                        item => item.date
                    ),

                datasets: [

                    {

                        label: "Revenue",

                        data:
                            data.map(
                                item =>
                                    item.revenue
                            ),

                        tension: 0.25,

                        fill: false

                    }

                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    },

                    tooltip: {

                        callbacks: {

                            label: function(context) {

                                return (
                                    "Revenue: " +
                                    money(
                                        context.raw
                                    )
                                );

                            }

                        }

                    }

                },

                scales: {

                    y: {

                        ticks: {

                            callback: function(value) {

                                return money(
                                    value
                                );

                            }

                        }

                    }

                }

            }

        }
    );

}


/* =========================================================
   REGIONAL PERFORMANCE
========================================================= */

function regions(data) {

    const element =
        document.querySelector(
            "#regions"
        );

    if (!element)
        return;


    if (!data || !data.length) {

        element.innerHTML =
            "<p class='muted'>No regional data available.</p>";

        return;

    }


    element.innerHTML =
        data.map(
            item => `

                <div class="product">

                    <span>
                        ${item.region}
                    </span>

                    <b>
                        ${money(item.revenue)}
                    </b>

                </div>

            `
        ).join("");

}


/* =========================================================
   ACTIVE INTELLIGENCE
========================================================= */

function insights(data) {

    const element =
        document.querySelector(
            "#insights"
        );

    if (!element)
        return;


    if (!data.length) {

        element.innerHTML =
            "<p class='muted'>No active signals.</p>";

        return;

    }


    element.innerHTML = data.map(
        item => `

            <div class="signal">

                <div class="tag">

                    ${item.severity}
                    ·
                    ${item.domain}

                </div>

                <b>
                    ${item.title}
                </b>

                <p>
                    ${item.summary}
                </p>

                <p>

                    <b>Next:</b>

                    ${item.recommendation}

                </p>

            </div>

        `
    ).join("");

}


/* =========================================================
   BUSINESS DIAGNOSIS
========================================================= */

function diagnosis(data) {

    const element =
        document.querySelector(
            "#diagnosis-content"
        );

    if (!element)
        return;


    const topRegion =
        Object.entries(
            data.top_regions || {}
        )[0];


    element.innerHTML = `

        <div class="diagnosis-grid">

            <div class="signal">

                <b>
                    Investigation
                </b>

                <p>
                    ${data.investigation}
                </p>

            </div>


            <div class="signal">

                <b>
                    Inventory Risks
                </b>

                <p>

                    ${
                        data.inventory_risks
                            ?.length || 0
                    }

                    products currently require
                    attention.

                </p>

            </div>


            <div class="signal">

                <b>
                    Leading Region
                </b>

                <p>

                    ${
                        topRegion
                            ? topRegion[0]
                            : "N/A"
                    }

                    ·

                    ${
                        topRegion
                            ? money(topRegion[1])
                            : "₹0"
                    }

                </p>

            </div>

        </div>


        <div class="signal">

            <b>
                Inventory Intelligence
            </b>

            <p>
                NEXORAAI is using recent demand,
                stock coverage and reorder levels
                to prioritize inventory risks.
            </p>

        </div>

    `;

}


/* =========================================================
   AUTONOMOUS OPERATIONS
========================================================= */

function operationStatusLabel(status) {

    const labels = {

        pending_approval: "PENDING APPROVAL",

        approved: "APPROVED",

        completed: "COMPLETED",

        rejected: "REJECTED",

        failed: "FAILED"

    };

    return labels[status] ||
        String(status || "").toUpperCase();

}


function operationRiskLabel(risk) {

    return String(
        risk || "UNKNOWN"
    ).toUpperCase();

}


function getVerificationData(item) {

    if (!item.verification)
        return null;

    try {

        return typeof item.verification === "string"
            ? JSON.parse(item.verification)
            : item.verification;

    } catch (error) {

        console.warn(
            "Could not parse operation verification:",
            error
        );

        return null;

    }

}


/* =========================================================
   OPERATION VERIFICATION RESULT
========================================================= */

function renderOperationResult(item) {

    const verification =
        getVerificationData(item);

    if (!verification)
        return "";


    const finalVerification =
        verification.verification ||
        verification;


    const execution =
        verification.execution || {};


    const executionResult =
        execution.request?.execution_result?.result ||
        execution.request?.execution_result ||
        {};


    const monitoring =
        verification.monitoring ||
        {};


    if (
        finalVerification.status === "VERIFIED" ||
        finalVerification.verified === true
    ) {

        const product =
            finalVerification.product ||
            executionResult.product ||
            item.payload?.product ||
            "";


        const oldStock =
            finalVerification.old_stock ??
            executionResult.old_stock;


        const actualStock =
            finalVerification.actual_stock ??
            finalVerification.new_stock ??
            executionResult.new_stock;


        const quantity =
            finalVerification.quantity ??
            finalVerification.quantity_added ??
            executionResult.quantity_added ??
            item.payload?.quantity;


        return `

            <div class="operation-result">

                <div class="operation-result-title">
                    ✓ Action verified
                </div>

                <div class="operation-result-details">

                    ${
                        product
                            ? `
                                <span>
                                    <b>Product:</b>
                                    ${product}
                                </span>
                            `
                            : ""
                    }

                    ${
                        quantity !== undefined
                            ? `
                                <span>
                                    <b>Quantity:</b>
                                    ${Number(
                                        quantity
                                    ).toLocaleString()}
                                    units
                                </span>
                            `
                            : ""
                    }

                    ${
                        oldStock !== undefined &&
                        actualStock !== undefined
                            ? `
                                <span>
                                    <b>Stock:</b>
                                    ${Number(
                                        oldStock
                                    ).toLocaleString()}
                                    →
                                    ${Number(
                                        actualStock
                                    ).toLocaleString()}
                                </span>
                            `
                            : ""
                    }

                    ${
                        monitoring.state
                            ? `
                                <span>
                                    <b>Monitoring:</b>
                                    ${monitoring.state}
                                </span>
                            `
                            : ""
                    }

                </div>

            </div>

        `;

    }


    if (item.status === "failed") {

        return `

            <div class="operation-result operation-failed">

                <div class="operation-result-title">
                    ✕ Execution failed
                </div>

                <p class="muted">
                    The operation could not be completed successfully.
                </p>

            </div>

        `;

    }


    return "";

}


/* =========================================================
   OPERATION CARD
========================================================= */

function renderOperationCard(
    item,
    options = {}
) {

    const status =
        item.status || "unknown";

    const risk =
        operationRiskLabel(
            item.risk
        );

    const payload =
        item.payload || {};

    const isPending =
        status === "pending_approval";

    const isApproved =
        status === "approved";

    const showProposal =
        options.showProposal !== false;

    const showResult =
        options.showResult !== false;

    const showActions =
        options.showActions !== false;

    const resultHTML =
        showResult
            ? renderOperationResult(item)
            : "";

    return `

        <div class="operation">

            <div class="operation-header">

                <div>

                    <b>
                        ${item.title || item.action}
                    </b>

                    <div class="operation-meta">

                        <span class="operation-status">
                            ${operationStatusLabel(status)}
                        </span>

                        <span class="operation-risk">
                            ${risk} RISK
                        </span>

                    </div>

                </div>

            </div>


            ${
                item.reason
                    ? `
                        <p>
                            ${item.reason}
                        </p>
                    `
                    : ""
            }


            ${
                showProposal &&
                payload.quantity
                    ? `
                        <div class="operation-proposal">

                            <span>
                                Proposed action
                            </span>

                            <strong>
                                Restock
                                ${Number(
                                    payload.quantity
                                ).toLocaleString()}
                                units
                            </strong>

                        </div>
                    `
                    : ""
            }


            ${
                showActions && isPending
                    ? `
                        <div class="actions">

                            <button
                                onclick="approve(${item.id})"
                            >
                                Approve
                            </button>

                            <button
                                onclick="reject(${item.id})"
                            >
                                Reject
                            </button>

                        </div>
                    `
                    : ""
            }


            ${
                showActions && isApproved
                    ? `
                        <div class="actions">

                            <button
                                onclick="executeOp(${item.id})"
                            >
                                Execute
                            </button>

                        </div>
                    `
                    : ""
            }


            ${resultHTML}

        </div>

    `;

}


/* =========================================================
   AUTONOMOUS OPERATIONS
   FINAL INFORMATION ARCHITECTURE
========================================================= */

function operations(data) {

    const element =
        document.querySelector(
            "#operations-content"
        );

    if (!element)
        return;


    if (!data || !data.length) {

        element.innerHTML = `

            <p class="muted">
                No autonomous operations have been generated yet.
            </p>

        `;

        return;

    }


    /*
       ACTIVE DECISIONS
       ----------------
       Only operations that can still be acted upon.
    */

    const active =
        data.filter(
            item =>
                item.status === "pending_approval" ||
                item.status === "approved"
        );


    /*
       COMPLETED OPERATIONS
       --------------------
       Successfully executed and verified actions.
    */

    const completed =
        data.filter(
            item =>
                item.status === "completed"
        );


    /*
       HISTORY
       -------
       Rejected and failed operations remain visible
       for traceability, but are not presented as
       current business decisions.
    */

    const history =
        data.filter(
            item =>
                item.status === "rejected" ||
                item.status === "failed"
        );


    let html = "";


    /* =====================================================
       ACTIVE DECISIONS
    ===================================================== */

    html += `

        <div class="operations-group">

            <div class="section-heading">

                <div>

                    <span class="eyebrow">
                        HUMAN DECISION REQUIRED
                    </span>

                    <h3>
                        Active Decisions
                    </h3>

                </div>

                <span class="decision-count">
                    ${active.length} active
                </span>

            </div>

    `;


    if (active.length > 0) {

        html += active
            .map(
                item =>
                    renderOperationCard(
                        item,
                        {
                            showProposal: true,
                            showResult: false,
                            showActions: true
                        }
                    )
            )
            .join("");

    } else {

        html += `

            <div class="success-state">

                <span>
                    ✓
                </span>

                <div>

                    <strong>
                        No active operational decisions.
                    </strong>

                    <p>
                        NEXORAAI is continuing to monitor
                        business conditions.
                    </p>

                </div>

            </div>

        `;

    }


    html += `

        </div>

    `;


    /* =====================================================
       COMPLETED OPERATIONS
    ===================================================== */

    html += `

        <div class="operations-group">

            <div class="section-heading">

                <div>

                    <span class="eyebrow">
                        AUTONOMOUS ACTIVITY
                    </span>

                    <h3>
                        Completed Operations
                    </h3>

                </div>

                <span class="decision-count">
                    ${completed.length} completed
                </span>

            </div>

    `;


    if (completed.length > 0) {

        html += completed
            .map(
                item =>
                    renderOperationCard(
                        item,
                        {
                            showProposal: false,
                            showResult: true,
                            showActions: false
                        }
                    )
            )
            .join("");

    } else {

        html += `

            <p class="muted">
                No completed autonomous operations yet.
            </p>

        `;

    }


    html += `

        </div>

    `;


    /* =====================================================
       OPERATION HISTORY
    ===================================================== */

    html += `

        <div class="operations-group">

            <div class="section-heading">

                <div>

                    <span class="eyebrow">
                        HISTORY
                    </span>

                    <h3>
                        Operation History
                    </h3>

                </div>

                <span class="decision-count">
                    ${history.length} records
                </span>

            </div>

    `;


    if (history.length > 0) {

        html += history
            .map(
                item =>
                    renderOperationCard(
                        item,
                        {
                            showProposal: false,
                            showResult: false,
                            showActions: false
                        }
                    )
            )
            .join("");

    } else {

        html += `

            <p class="muted">
                No historical operations.
            </p>

        `;

    }


    html += `

        </div>

    `;


    element.innerHTML =
        html;

}


/* =========================================================
   COMMAND CENTER
========================================================= */

function commandCenter(
    overview,
    intelligence,
    diagnosisData,
    operationsData
) {

    const summary =
        document.getElementById(
            "command-summary"
        );

    const actions =
        document.getElementById(
            "command-actions"
        );


    if (!summary || !actions)
        return;


    const growth =
        Number(
            overview.revenue_growth || 0
        );


    const revenue =
        overview.revenue || 0;


    const profit =
        overview.profit || 0;


    const inventoryRisks =
        diagnosisData.inventory_intelligence ||
        [];


    const criticalRisks =
        inventoryRisks
            .filter(
                item =>
                    item.priority === "CRITICAL"
            )
            .slice(0, 4);


    const totalRisks =
        inventoryRisks.length;


    const allOperations =
        operationsData || [];


    const pendingOperations =
        allOperations.filter(
            op =>
                op.status ===
                "pending_approval"
        );


    const completedOperations =
        allOperations.filter(
            op =>
                op.status ===
                "completed"
        );


    summary.innerHTML = `

        <div class="command-status">

            <div class="status-main">

                <span class="status-dot"></span>

                <div>

                    <h3>
                        Business is being actively monitored
                    </h3>

                    <p>

                        Revenue is currently

                        <strong>
                            ${
                                growth >= 0
                                    ? "growing"
                                    : "declining"
                            }

                            by

                            ${Math.abs(growth).toFixed(2)}%

                        </strong>

                        compared with the previous period.

                    </p>

                </div>

            </div>


            <div class="status-metrics">

                <div>

                    <span>
                        Revenue
                    </span>

                    <strong>
                        ₹${Number(
                            revenue
                        ).toLocaleString(
                            "en-IN"
                        )}
                    </strong>

                </div>


                <div>

                    <span>
                        Profit
                    </span>

                    <strong>
                        ₹${Number(
                            profit
                        ).toLocaleString(
                            "en-IN"
                        )}
                    </strong>

                </div>


                <div>

                    <span>
                        Inventory Risks
                    </span>

                    <strong>
                        ${totalRisks}
                    </strong>

                </div>

            </div>

        </div>

    `;


    let riskHTML = "";


    if (criticalRisks.length > 0) {

        riskHTML =
            criticalRisks.map(
                item => `

                    <div class="priority-card critical">

                        <div class="priority-top">

                            <span class="priority-label">
                                CRITICAL
                            </span>

                            <span class="priority-stock">

                                ${Number(
                                    item.days_of_stock
                                ).toFixed(1)}

                                days left

                            </span>

                        </div>


                        <h3>
                            ${item.product}
                        </h3>


                        <p>

                            <strong>
                                ${item.stock}
                            </strong>

                            units remaining
                            against reorder level

                            <strong>
                                ${item.reorder_level}
                            </strong>.

                        </p>


                        <div class="priority-action">

                            Recommended restock:

                            <strong>
                                ${item.recommended_quantity}
                                units
                            </strong>

                        </div>

                    </div>

                `
            ).join("");

    } else {

        riskHTML = `

            <div class="success-state">

                <span>
                    ✓
                </span>

                <div>

                    <strong>
                        No critical inventory risks detected.
                    </strong>

                    <p>
                        NEXORAAI is continuing to monitor inventory levels.
                    </p>

                </div>

            </div>

        `;

    }


    const moreRisks =
        Math.max(
            0,
            totalRisks -
            criticalRisks.length
        );


    actions.innerHTML = `

        <div class="attention-section">

            <div class="section-heading">

                <div>

                    <span class="eyebrow">
                        AI DETECTED
                    </span>

                    <h3>
                        Priority business risks
                    </h3>

                </div>


                <span class="risk-count">
                    ${totalRisks} total
                </span>

            </div>


            <div class="priority-grid">

                ${riskHTML}

            </div>


            ${
                moreRisks > 0

                    ?

                    `

                        <button
                            class="secondary-action"
                            onclick="showSection('intelligence')"
                        >

                            View
                            ${moreRisks}
                            more risks →

                        </button>

                    `

                    : ""

            }

        </div>


        <div class="decision-section">

            <div class="section-heading">

                <div>

                    <span class="eyebrow">
                        HUMAN DECISION REQUIRED
                    </span>

                    <h3>
                        Operational decisions
                    </h3>

                </div>


                <span class="decision-count">

                    ${pendingOperations.length}
                    pending

                </span>

            </div>


            ${
                pendingOperations.length > 0

                    ?

                    `

                        <div class="decision-box">

                            <div class="decision-icon">
                                !
                            </div>


                            <div class="decision-content">

                                <strong>

                                    ${pendingOperations.length}

                                    operational decisions
                                    are awaiting approval.

                                </strong>


                                <p>

                                    NEXORAAI has detected
                                    business conditions
                                    that require controlled action.
                                    Review the proposed actions
                                    before execution.

                                </p>

                            </div>


                            <button
                                onclick="showSection('operations')"
                            >

                                Review Operations →

                            </button>

                        </div>

                    `

                    :

                    `

                        <div class="success-state">

                            <span>
                                ✓
                            </span>

                            <div>

                                <strong>
                                    No operational approvals are waiting.
                                </strong>

                                <p>
                                    NEXORAAI is continuing to monitor the business.
                                </p>

                            </div>

                        </div>

                    `

            }

        </div>


        <div class="activity-section">

            <div class="section-heading">

                <div>

                    <span class="eyebrow">
                        AUTONOMOUS ACTIVITY
                    </span>

                    <h3>
                        Recent business activity
                    </h3>

                </div>

            </div>


            ${
                completedOperations.length > 0

                    ?

                    completedOperations
                        .slice(0, 3)
                        .map(
                            op => `

                                <div class="activity-item">

                                    <span class="activity-check">
                                        ✓
                                    </span>


                                    <div>

                                        <strong>
                                            ${op.title || op.action}
                                        </strong>


                                        <p>
                                            Operation completed
                                            and verification recorded.
                                        </p>

                                    </div>

                                </div>

                            `
                        )
                        .join("")

                    :

                    `

                        <p class="muted">
                            No completed autonomous operations yet.
                        </p>

                    `

            }

        </div>

    `;

}


/* =========================================================
   APPROVE / REJECT / EXECUTE
========================================================= */

async function approve(id) {

    try {

        const response =
            await fetch(
                `/api/operations/${id}/approve`,
                {
                    method: "POST"
                }
            );

        if (!response.ok)
            throw Error(await response.text());

        await refreshAll();

    } catch (error) {

        console.error(
            "Approval failed:",
            error
        );

    }

}


async function reject(id) {

    try {

        const response =
            await fetch(
                `/api/operations/${id}/reject`,
                {
                    method: "POST"
                }
            );

        if (!response.ok)
            throw Error(await response.text());

        await refreshAll();

    } catch (error) {

        console.error(
            "Rejection failed:",
            error
        );

    }

}


async function executeOp(id) {

    try {

        const response =
            await fetch(
                `/api/operations/${id}/execute`,
                {
                    method: "POST"
                }
            );

        if (!response.ok)
            throw Error(await response.text());

        await refreshAll();

    } catch (error) {

        console.error(
            "Execution failed:",
            error
        );

    }

}


/* =========================================================
   MARKDOWN RENDERER
========================================================= */

function renderMarkdown(text) {

    if (!text)
        return "";


    let html = text
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        );


    html = html.replace(
        /^### (.*)$/gm,
        "<h3>$1</h3>"
    );


    html = html.replace(
        /^## (.*)$/gm,
        "<h2>$1</h2>"
    );


    html = html.replace(
        /^# (.*)$/gm,
        "<h1>$1</h1>"
    );


    html = html.replace(
        /\*\*(.*?)\*\*/g,
        "<strong>$1</strong>"
    );


    html = html.replace(
        /^- (.*)$/gm,
        "<li>$1</li>"
    );


    html = html.replace(
        /(<li>.*?<\/li>\s*)+/gs,
        match =>
            `<ul>${match}</ul>`
    );


    html = html.replace(
        /\n{2,}/g,
        "</p><p>"
    );


    html = html.replace(
        /\n/g,
        "<br>"
    );


    return `

        <div class="ai-response">

            <p>
                ${html}
            </p>

        </div>

    `;

}


/* =========================================================
   ASK NEXORAAI
========================================================= */

async function ask() {

    const input =
        document.querySelector(
            "#question"
        );


    const answer =
        document.querySelector(
            "#answer"
        );


    const question =
        input.value.trim();


    if (!question)
        return;


    answer.innerHTML = `

        <div class="muted">

            NEXORAAI is investigating...

        </div>

    `;


    try {

        const response =
            await fetch(
                "/api/chat",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body: JSON.stringify({
                        question
                    })

                }
            );


        const data =
            await response.json();


        answer.innerHTML =
            renderMarkdown(
                data.answer
            );


    } catch (error) {

        console.error(error);


        answer.innerHTML = `

            <div class="signal">

                <b>
                    Investigation unavailable
                </b>

                <p>
                    NEXORAAI could not complete
                    the request. Please try again.
                </p>

            </div>

        `;

    }

}


/* =========================================================
   PERFORMANCE COMPARISON
========================================================= */

async function loadComparison() {

    const current =
        document.getElementById(
            "comparison-current"
        ).value;


    const previous =
        document.getElementById(
            "comparison-previous"
        ).value;


    const result =
        document.getElementById(
            "comparison-result"
        );


    result.innerHTML = `

        <p class="muted">
            Comparing business periods...
        </p>

    `;


    try {

        const comparison =
            await get(
                `/api/sales/compare?current=${encodeURIComponent(current)}&previous=${encodeURIComponent(previous)}`
            );


        renderComparison(
            comparison
        );


    } catch (error) {

        console.error(
            "Comparison error:",
            error
        );


        result.innerHTML = `

            <p class="muted">
                Comparison could not be completed.
            </p>

        `;

    }

}


/* =========================================================
   COMPARISON VALUE HELPERS
========================================================= */

function formatComparisonChange(value) {

    if (value === null || value === undefined) {

        return "N/A";

    }

    value = Number(value);

    if (value > 0) {

        return `
            ↑ ${Math.abs(value).toFixed(2)}%
        `;

    }

    if (value < 0) {

        return `
            ↓ ${Math.abs(value).toFixed(2)}%
        `;

    }

    return "→ 0.00%";

}


function comparisonDirection(value) {

    value = Number(value || 0);

    if (value > 0)
        return "increase";

    if (value < 0)
        return "decrease";

    return "neutral";

}


/* =========================================================
   COMPARISON METRIC CARD
========================================================= */

function comparisonMetricCard(
    label,
    currentValue,
    previousValue,
    change,
    formatter
) {

    const direction =
        comparisonDirection(change);


    return `

        <div class="comparison-card">

            <div class="label">
                ${label}
            </div>


            <div class="value">
                ${formatter(currentValue)}
            </div>


            <div class="comparison-change">

                Previous:
                ${formatter(previousValue)}

            </div>


            <div class="comparison-change">

                <strong>

                    ${formatComparisonChange(change)}

                </strong>

                ${
                    direction === "increase"
                        ? " increase"
                        : direction === "decrease"
                            ? " decrease"
                            : " no change"
                }

            </div>

        </div>

    `;

}


/* =========================================================
   PRODUCT MOVEMENT
========================================================= */

function renderProductMovement(data) {

    if (!data || !data.length) {

        return `
            <p class="muted">
                No product movement data available.
            </p>
        `;

    }

    return data
        .slice()
        .sort(
            (a, b) =>
                Math.abs(
                    Number(b.revenue_change || 0)
                ) -
                Math.abs(
                    Number(a.revenue_change || 0)
                )
        )
        .slice(0, 8)
        .map(item => {

            const change =
                Number(
                    item.revenue_change || 0
                );

            const changePercent =
                item.revenue_change_percent;

            const arrow =
                change > 0
                    ? "↑"
                    : change < 0
                        ? "↓"
                        : "→";

            return `

                <div class="comparison-driver">

                    <div>

                        <strong>
                            ${item.product}
                        </strong>

                        <span class="muted">

                            ${money(
                                item.current_revenue
                            )}

                            vs

                            ${money(
                                item.previous_revenue
                            )}

                        </span>

                    </div>


                    <div>

                        <strong>

                            ${arrow}

                            ${money(
                                Math.abs(change)
                            )}

                        </strong>

                        <span class="muted">

                            ${
                                changePercent === null ||
                                changePercent === undefined
                                    ? "N/A"
                                    : Math.abs(
                                        Number(
                                            changePercent
                                        )
                                    ).toFixed(2) + "%"
                            }

                        </span>

                    </div>

                </div>

            `;

        })
        .join("");

}


/* =========================================================
   REGIONAL MOVEMENT
========================================================= */

function renderRegionalMovement(data) {

    if (!data || !data.length) {

        return `
            <p class="muted">
                No regional movement data available.
            </p>
        `;

    }

    return data
        .slice()
        .sort(
            (a, b) =>
                Math.abs(
                    Number(b.revenue_change || 0)
                ) -
                Math.abs(
                    Number(a.revenue_change || 0)
                )
        )
        .map(item => {

            const change =
                Number(
                    item.revenue_change || 0
                );

            const changePercent =
                item.revenue_change_percent;

            const arrow =
                change > 0
                    ? "↑"
                    : change < 0
                        ? "↓"
                        : "→";

            return `

                <div class="comparison-driver">

                    <div>

                        <strong>
                            ${item.region}
                        </strong>

                        <span class="muted">

                            ${money(
                                item.current_revenue
                            )}

                            vs

                            ${money(
                                item.previous_revenue
                            )}

                        </span>

                    </div>


                    <div>

                        <strong>

                            ${arrow}

                            ${money(
                                Math.abs(change)
                            )}

                        </strong>

                        <span class="muted">

                            ${
                                changePercent === null ||
                                changePercent === undefined
                                    ? "N/A"
                                    : Math.abs(
                                        Number(
                                            changePercent
                                        )
                                    ).toFixed(2) + "%"
                            }

                        </span>

                    </div>

                </div>

            `;

        })
        .join("");

}


/* =========================================================
   BUSINESS DRIVER
========================================================= */

function renderBusinessDriver(data) {

    const driver =
        data.business_driver;


    if (!driver) {

        return `
            <p class="muted">
                No business interpretation is available.
            </p>
        `;

    }


    const summary =
        data.driver_summary || {};


    return `

        <div class="signal">

            <p>
                ${driver}
            </p>


            <div class="comparison-driver-list">

                ${
                    summary.largest_product
                        ?

                        `

                            <div class="comparison-driver">

                                <div>

                                    <strong>
                                        Largest product driver
                                    </strong>

                                    <span class="muted">
                                        ${summary.largest_product}
                                    </span>

                                </div>

                                <strong>
                                    ${money(
                                        summary.largest_product_change
                                    )}
                                </strong>

                            </div>

                        `

                        : ""

                }


                ${
                    summary.largest_region
                        ?

                        `

                            <div class="comparison-driver">

                                <div>

                                    <strong>
                                        Largest regional driver
                                    </strong>

                                    <span class="muted">
                                        ${summary.largest_region}
                                    </span>

                                </div>

                                <strong>
                                    ${money(
                                        summary.largest_region_change
                                    )}
                                </strong>

                            </div>

                        `

                        : ""

                }

            </div>

        </div>

    `;

}


/* =========================================================
   RENDER COMPARISON
========================================================= */

function renderComparison(data) {

    const current =
        data.current;


    const previous =
        data.previous;


    const result =
        document.getElementById(
            "comparison-result"
        );


    if (!result)
        return;


    const changes =
        data.metric_changes || {};


    const revenueChange =
        Number(
            changes.revenue ??
            data.revenue_change_percent ??
            0
        );


    const revenueDirection =
        revenueChange >= 0
            ? "increased"
            : "decreased";


    const cardsHTML = [

        comparisonMetricCard(
            "Revenue",
            current.revenue,
            previous.revenue,
            changes.revenue,
            money
        ),

        comparisonMetricCard(
            "Orders",
            current.orders,
            previous.orders,
            changes.orders,
            value =>
                Number(
                    value || 0
                ).toLocaleString()
        ),

        comparisonMetricCard(
            "Customers",
            current.customers,
            previous.customers,
            changes.customers,
            value =>
                Number(
                    value || 0
                ).toLocaleString()
        ),

        comparisonMetricCard(
            "Units",
            current.units,
            previous.units,
            changes.units,
            value =>
                Number(
                    value || 0
                ).toLocaleString()
        ),

        comparisonMetricCard(
            "Profit",
            current.profit,
            previous.profit,
            changes.profit,
            money
        ),

        comparisonMetricCard(
            "Expenses",
            current.expenses,
            previous.expenses,
            changes.expenses,
            money
        )

    ].join("");


    result.innerHTML = `

        <div class="comparison-section">

            <h3>
                ${current.period}
                vs
                ${previous.period}
            </h3>


            <p class="comparison-summary">

                Revenue

                <strong>

                    ${revenueDirection}
                    by
                    ${Math.abs(
                        revenueChange
                    ).toFixed(2)}%

                </strong>

                compared with
                ${previous.period}.

            </p>


            <div class="comparison-grid">

                ${cardsHTML}

            </div>


            <div class="comparison-section">

                <h3>
                    Business Drivers
                </h3>

                ${renderBusinessDriver(data)}

            </div>


            <div class="comparison-section">

                <h3>
                    Product Movement
                </h3>


                <div class="comparison-driver-list">

                    ${renderProductMovement(
                        data.product_movement
                    )}

                </div>

            </div>


            <div class="comparison-section">

                <h3>
                    Regional Movement
                </h3>


                <div class="comparison-driver-list">

                    ${renderRegionalMovement(
                        data.regional_movement
                    )}

                </div>

            </div>

        </div>

    `;

}


/* =========================================================
   COMPARISON PERIODS
========================================================= */

async function loadComparisonPeriods() {

    const currentSelector =
        document.getElementById(
            "comparison-current"
        );


    const previousSelector =
        document.getElementById(
            "comparison-previous"
        );


    if (
        !currentSelector ||
        !previousSelector
    ) {

        return;

    }


    try {

        const data =
            await get(
                "/api/periods"
            );


        const options =
            data.periods.map(
                period => `

                    <option
                        value="${period.value}"
                    >
                        ${period.label}
                    </option>

                `
            ).join("");


        currentSelector.innerHTML =
            options;


        previousSelector.innerHTML =
            options;


        currentSelector.value =
            "this_month";


        previousSelector.value =
            "last_month";


    } catch (error) {

        console.error(
            "Comparison periods error:",
            error
        );

    }

}


/* =========================================================
   INITIAL LOAD
========================================================= */

async function initialize() {

    await loadPeriods();

    await loadComparisonPeriods();

    await refreshAll();

}


initialize();


/* =========================================================
   AUTOMATIC MONITORING
========================================================= */

setInterval(
    refreshAll,
    60000
);