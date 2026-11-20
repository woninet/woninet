// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
// `key` is matched against the keys inside "health" in the /api/health response.
// Matching ignores case and treats spaces, underscores and hyphens as equivalent.
const COMPONENTS = [
    { key: "monitor_core",  label: "Monitor Core",  icon: "fa-microchip" },
    { key: "database",      label: "Database",      icon: "fa-database" },
    { key: "configuration", label: "Configuration", icon: "fa-sliders" },
    { key: "utility", label: "Utility", icon: "fa-cog" },
];

const REFRESH_INTERVAL_MS = 10000;

// Status is derived on the client:
//   no error code and no message -> healthy
//   an error code or a message   -> failed
//   missing / unreadable data    -> unknown
const SEVERITY = { healthy: 0, unknown: 1, failed: 2 };

const OVERALL = {
    healthy: {
        icon: "fa-circle-check",
        title: "All systems operational",
        text: "Every component is reporting a healthy status.",
    },
    failed: {
        icon: "fa-circle-xmark",
        title: "Issues detected",
        text: "One or more components reported an error. Review the details below.",
    },
    unknown: {
        icon: "fa-circle-question",
        title: "Status unavailable",
        text: "The health status could not be determined.",
    },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, ch => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[ch]));
}

function normalizeKey(key) {
    return String(key).toLowerCase().replace(/[\s_-]+/g, " ").trim();
}

function hasValue(value) {
    return value !== null && value !== undefined && String(value).trim() !== "";
}

function setConnected(connected) {
    document.getElementById("status_dot").classList.toggle("disconnected", !connected);
    document.getElementById("status_text").textContent = connected ? "Connected" : "Disconnected";
}

function findEntry(health, key) {
    const target = normalizeKey(key);
    const match = Object.keys(health).find(k => normalizeKey(k) === target);
    return match === undefined ? undefined : health[match];
}

// Expects: { "error_code": <string|null>, "message": <string|null> }
function parseEntry(entry) {
    if (!entry || typeof entry !== "object") {
        return { status: "unknown", code: "", message: "" };
    }

    const code = entry.error_code;
    const message = entry.message;
    const docs_url = entry.docs_url;
    const status = hasValue(code) || hasValue(message) ? "failed" : "healthy";

    return { status, code: hasValue(code) ? code : "", message: hasValue(message) ? message : "" , docs_url: hasValue(docs_url) ? docs_url : ""};
}

function worstStatus(statuses) {
    return statuses.reduce(
        (worst, s) => (SEVERITY[s] > SEVERITY[worst] ? s : worst),
        "healthy"
    );
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------
function createCard(component, result) {
    const { status, code, message, docs_url } = result;

    let docs_helper = null;
    if (docs_url) {
        docs_helper = "For more information, see:";
    }
    let body;

    if (status === "failed") {
        body = `
        <dl class="error-details">
            <div class="error-row">
                <dt>Error Code</dt>
                <dd class="error-code">${escapeHtml(code || "Not provided")}</dd>
            </div>
            <div class="error-row">
                <dt>Message</dt>
                <dd>${escapeHtml(message || "No message provided.")}</dd>
                <p>${docs_helper || ""}</p>
                <a href='${docs_url}' target="_blank" rel="noopener noreferrer">${escapeHtml(docs_url || null)}</a>
            </div>
        </dl>`;
    } else if (status === "healthy") {
        body = `<p class="health-ok">No issues detected.</p>`;
    } else {
        body = `<p class="health-ok">Status was not reported by the API.</p>`;
    }

    return `
    <article class="health-card ${status}">
        <div class="health-card-header">
            <div class="health-card-icon"><i class="fa-solid ${component.icon}"></i></div>
            <div class="health-card-title">
                <h3>${escapeHtml(component.label)}</h3>
                <span class="health-badge ${status}">${status}</span>
            </div>
        </div>
        ${body}
    </article>`;
}

function renderOverall(status) {
    const info = OVERALL[status];
    const el = document.getElementById("overall");

    el.className = `overall ${status}`;
    el.querySelector(".overall-icon").innerHTML = `<i class="fa-solid ${info.icon}"></i>`;
    document.getElementById("overall_title").textContent = info.title;
    document.getElementById("overall_text").textContent = info.text;
}

function renderHealth(data) {
    const health = data && typeof data.health === "object" ? data.health : null;

    if (!health) {
        throw new Error("Response is missing the 'health' object.");
    }

    const results = COMPONENTS.map(component => ({
        component,
        result: parseEntry(findEntry(health, component.key)),
    }));

    document.getElementById("health_cards").innerHTML =
        results.map(({ component, result }) => createCard(component, result)).join("");

    renderOverall(worstStatus(results.map(r => r.result.status)));
}

function renderUnreachable() {
    document.getElementById("health_cards").innerHTML = COMPONENTS
        .map(component => createCard(component, { status: "unknown", code: "", message: "" , docs_url: ""}))
        .join("");

    renderOverall("unknown");
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------
async function loadHealth() {
    const refreshBtn = document.getElementById("refresh_btn");
    refreshBtn.disabled = true;
    refreshBtn.classList.add("loading");

    try {
        const response = await fetch("/api/health");
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        renderHealth(await response.json());
        setConnected(true);

    } catch (error) {
        // Any failure (network, HTTP error, bad payload) means the state is unknown.
        renderUnreachable();
        setConnected(false);
        console.error("Error loading health:", error);

    } finally {
        document.getElementById("last_checked").textContent =
            `Last checked: ${new Date().toLocaleTimeString()}`;
        refreshBtn.disabled = false;
        refreshBtn.classList.remove("loading");
    }
}

document.getElementById("refresh_btn").addEventListener("click", loadHealth);


async function restart_app() {
    const restartBtn = document.getElementById("restart_btn");
    restartBtn.disabled = true;
    restartBtn.classList.add("loading");

    try {
        const response = await fetch("/api/health/restart");
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        renderHealth(await response.json());
        setConnected(true);

    } catch (error) {
        // Any failure (network, HTTP error, bad payload) means the state is unknown.
        renderUnreachable();
        setConnected(false);
        console.error("Error loading health:", error);

    } finally {
        document.getElementById("last_checked").textContent =
            `Last checked: ${new Date().toLocaleTimeString()}`;
        restartBtn.disabled = false;
        restartBtn.classList.remove("loading");
        document.getElementById("refresh_btn").click();
    }
}

document.getElementById("restart_btn").addEventListener("click", restart_app);

loadHealth();
setInterval(loadHealth, REFRESH_INTERVAL_MS);
