/**
 * Dashboard Interactive Controller
 * Module 3 - Johns Hopkins University Software Concepts (EN.605.601)
 */

document.addEventListener("DOMContentLoaded", () => {
    const btnPullData = document.getElementById("btn-pull-data");
    const btnUpdateAnalysis = document.getElementById("btn-update-analysis");
    const statusAlertBox = document.getElementById("status-alert-box");
    const statusMessage = document.getElementById("status-message");
    const liveIndicator = document.getElementById("live-indicator");
    const liveStatusText = document.getElementById("live-status-text");
    const totalDbCount = document.getElementById("total-db-count");

    let pollInterval = null;

    // Pull Data Button Handler
    if (btnPullData) {
        btnPullData.addEventListener("click", async () => {
            btnPullData.disabled = true;
            setLiveStatus(true, "Scraping Grad Café...");
            setStatusBox("active", "Initiating data pull from Grad Café. Please wait...");

            try {
                const res = await fetch("/api/pull-data", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" }
                });
                const data = await res.json();

                if (res.ok) {
                    setStatusBox("active", data.message);
                    startStatusPolling();
                } else {
                    setStatusBox("error", data.message || "Failed to start data pull.");
                    btnPullData.disabled = false;
                    setLiveStatus(false, "Ready");
                }
            } catch (err) {
                setStatusBox("error", `Network Error: ${err.message}`);
                btnPullData.disabled = false;
                setLiveStatus(false, "Ready");
            }
        });
    }

    // Update Analysis Button Handler
    if (btnUpdateAnalysis) {
        btnUpdateAnalysis.addEventListener("click", async () => {
            btnUpdateAnalysis.disabled = true;
            btnUpdateAnalysis.style.opacity = "0.7";

            try {
                const res = await fetch("/api/update-analysis");
                const result = await res.json();

                if (result.success) {
                    updateDashboardMetrics(result.data);

                    if (result.is_scraping) {
                        setStatusBox("active", `New data is currently being retrieved from Grad Café (${result.status_message}). Analysis updated with current database state.`);
                        setLiveStatus(true, "Scrape in progress...");
                    } else {
                        setStatusBox("neutral", "Analysis refreshed successfully with latest PostgreSQL data.");
                        setLiveStatus(false, "Database Ready");
                    }
                } else {
                    setStatusBox("error", "Error updating analysis metrics.");
                }
            } catch (err) {
                setStatusBox("error", `Failed to refresh analysis: ${err.message}`);
            } finally {
                btnUpdateAnalysis.disabled = false;
                btnUpdateAnalysis.style.opacity = "1";
            }
        });
    }

    // Polling function for active scrape
    function startStatusPolling() {
        if (pollInterval) clearInterval(pollInterval);

        pollInterval = setInterval(async () => {
            try {
                const res = await fetch("/api/status");
                const status = await res.json();

                if (status.is_running) {
                    setStatusBox("active", status.status);
                    setLiveStatus(true, "Scraping in progress...");
                } else {
                    clearInterval(pollInterval);
                    pollInterval = null;
                    btnPullData.disabled = false;
                    setLiveStatus(false, "Database Ready");

                    if (status.error) {
                        setStatusBox("error", `Data pull failed: ${status.error}`);
                    } else {
                        setStatusBox("neutral", status.status || "Data pull completed successfully.");
                        // Trigger analysis update automatically
                        btnUpdateAnalysis.click();
                    }
                }
            } catch (err) {
                console.error("Polling error:", err);
            }
        }, 2000);
    }

    function setLiveStatus(isRunning, text) {
        if (!liveIndicator || !liveStatusText) return;
        liveIndicator.className = `live-status-badge ${isRunning ? "running" : "idle"}`;
        liveStatusText.textContent = text;
    }

    function setStatusBox(type, msg) {
        if (!statusAlertBox || !statusMessage) return;
        statusAlertBox.className = `status-alert ${type}`;
        statusMessage.textContent = msg;
    }

    function updateDashboardMetrics(d) {
        if (!d) return;

        // Total count
        if (totalDbCount && d.total_records) {
            totalDbCount.innerHTML = `PostgreSQL Total Rows: <strong>${Number(d.total_records).toLocaleString()}</strong>`;
        }

        // Q1
        const elQ1 = document.getElementById("val-q1");
        if (elQ1 && d.q1 !== undefined) elQ1.textContent = Number(d.q1).toLocaleString();

        // Q2
        const elQ2 = document.getElementById("val-q2");
        if (elQ2 && d.q2 !== undefined) elQ2.textContent = `${Number(d.q2).toFixed(2)}%`;

        // Q3
        if (d.q3) {
            const elGpa = document.getElementById("val-gpa");
            if (elGpa) elGpa.textContent = Number(d.q3.gpa).toFixed(2);
            const elGre = document.getElementById("val-gre");
            if (elGre) elGre.textContent = Number(d.q3.gre).toFixed(2);
            const elGreV = document.getElementById("val-gre-v");
            if (elGreV) elGreV.textContent = Number(d.q3.gre_v).toFixed(2);
            const elGreAw = document.getElementById("val-gre-aw");
            if (elGreAw) elGreAw.textContent = Number(d.q3.gre_aw).toFixed(2);
        }

        // Q4
        const elQ4 = document.getElementById("val-q4");
        if (elQ4 && d.q4 !== undefined) elQ4.textContent = Number(d.q4).toFixed(2);

        // Q5
        const elQ5 = document.getElementById("val-q5");
        if (elQ5 && d.q5 !== undefined) elQ5.textContent = `${Number(d.q5).toFixed(2)}%`;

        // Q6
        const elQ6 = document.getElementById("val-q6");
        if (elQ6 && d.q6 !== undefined) elQ6.textContent = Number(d.q6).toFixed(2);

        // Q7
        const elQ7 = document.getElementById("val-q7");
        if (elQ7 && d.q7 !== undefined) elQ7.textContent = Number(d.q7).toLocaleString();

        // Q8 & Q9
        if (d.q9) {
            const elQ8 = document.getElementById("val-q8");
            if (elQ8) elQ8.textContent = d.q9.original;
            const elQ9 = document.getElementById("val-q9");
            if (elQ9) elQ9.textContent = d.q9.llm;
            const elDiff = document.getElementById("val-diff");
            if (elDiff) {
                elDiff.textContent = d.q9.diff > 0 ? `+${d.q9.diff}` : `${d.q9.diff}`;
            }
        }
    }
});
