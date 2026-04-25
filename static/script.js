/* ============================================================================
   ELECTRICITY BILL PREDICTOR — JavaScript
   ============================================================================ */

document.addEventListener("DOMContentLoaded", () => {
    // ── Tab Switching ────────────────────────────────────────────────────────
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabPanels = document.querySelectorAll(".tab-content");

    tabBtns.forEach((btn) => {
        btn.addEventListener("click", () => {
            const target = btn.dataset.tab;

            tabBtns.forEach((b) => b.classList.remove("active"));
            tabPanels.forEach((p) => p.classList.remove("active"));

            btn.classList.add("active");
            document.getElementById(`panel-${target}`).classList.add("active");
        });
    });

    // ── Single Prediction ────────────────────────────────────────────────────
    const form = document.getElementById("predict-form");
    const resultPanel = document.getElementById("single-result");
    const resultValue = document.getElementById("result-value");
    const resultDetails = document.getElementById("result-details");
    const loading = document.getElementById("loading-overlay");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        loading.classList.remove("hidden");

        const formData = new FormData(form);
        const payload = {};
        for (const [key, value] of formData.entries()) {
            payload[key] = parseFloat(value);
        }

        try {
            const res = await fetch("/predict", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            const data = await res.json();

            if (data.error) {
                alert("Error: " + data.error);
                return;
            }

            // Display result
            resultValue.textContent = `₹ ${data.prediction.toLocaleString("en-IN", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            })}`;

            // Build detail tags
            resultDetails.innerHTML = "";
            data.features_used.forEach((feat, i) => {
                const tag = document.createElement("span");
                tag.className = "detail-tag";
                tag.textContent = `${feat.replace(/_/g, " ")}: ${data.input_values[i]}`;
                resultDetails.appendChild(tag);
            });

            resultPanel.classList.remove("hidden");

            // Scroll to result
            resultPanel.scrollIntoView({ behavior: "smooth", block: "center" });
        } catch (err) {
            alert("Request failed: " + err.message);
        } finally {
            loading.classList.add("hidden");
        }
    });

    // ── Fill Sample Values ───────────────────────────────────────────────────
    document.getElementById("btn-sample").addEventListener("click", () => {
        const features = window.FEATURES || [];
        const stats = window.FEATURE_STATS || {};

        features.forEach((feat) => {
            const input = document.getElementById(`input-${feat}`);
            if (input && stats[feat]) {
                // Use median as a sensible sample value
                input.value = stats[feat].median;
            }
        });

        // Add a subtle animation
        document.querySelectorAll(".input-group input").forEach((inp) => {
            inp.style.transition = "background 0.3s";
            inp.style.background = "rgba(108, 92, 231, 0.12)";
            setTimeout(() => {
                inp.style.background = "";
            }, 600);
        });
    });

    // ── Reset hides result ───────────────────────────────────────────────────
    document.getElementById("btn-reset").addEventListener("click", () => {
        resultPanel.classList.add("hidden");
    });

    // ── File Upload (Batch) ──────────────────────────────────────────────────
    const uploadZone = document.getElementById("upload-zone");
    const fileInput = document.getElementById("file-input");
    const fileInfo = document.getElementById("file-info");
    const fileName = document.getElementById("file-name");
    const btnRemoveFile = document.getElementById("btn-remove-file");
    const btnUpload = document.getElementById("btn-upload-predict");
    const batchResults = document.getElementById("batch-results");

    let selectedFile = null;

    // Click to browse
    uploadZone.addEventListener("click", () => fileInput.click());

    // Drag & Drop
    uploadZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadZone.classList.add("drag-over");
    });
    uploadZone.addEventListener("dragleave", () => {
        uploadZone.classList.remove("drag-over");
    });
    uploadZone.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadZone.classList.remove("drag-over");
        if (e.dataTransfer.files.length) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length) {
            handleFile(fileInput.files[0]);
        }
    });

    function handleFile(file) {
        if (!file.name.match(/\.xlsx?$/i)) {
            alert("Please upload an Excel file (.xlsx)");
            return;
        }
        selectedFile = file;
        fileName.textContent = `📎 ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        fileInfo.classList.remove("hidden");
        uploadZone.classList.add("hidden");
        btnUpload.classList.remove("hidden");
        batchResults.classList.add("hidden");
    }

    btnRemoveFile.addEventListener("click", () => {
        selectedFile = null;
        fileInput.value = "";
        fileInfo.classList.add("hidden");
        uploadZone.classList.remove("hidden");
        btnUpload.classList.add("hidden");
        batchResults.classList.add("hidden");
    });

    // Upload & Predict
    btnUpload.addEventListener("click", async () => {
        if (!selectedFile) return;
        loading.classList.remove("hidden");

        const formData = new FormData();
        formData.append("file", selectedFile);

        try {
            const res = await fetch("/predict-batch", {
                method: "POST",
                body: formData,
            });

            const data = await res.json();

            if (data.error) {
                alert("Error: " + data.error);
                return;
            }

            renderBatchResults(data);
        } catch (err) {
            alert("Upload failed: " + err.message);
        } finally {
            loading.classList.add("hidden");
        }
    });

    function renderBatchResults(data) {
        const thead = document.getElementById("results-thead");
        const tbody = document.getElementById("results-tbody");
        const batchCount = document.getElementById("batch-count");

        batchCount.textContent = `${data.count} rows predicted`;

        // Build header
        const features = window.FEATURES || [];
        let headerHTML = "<tr>";
        headerHTML += '<th>#</th>';
        features.forEach((f) => {
            headerHTML += `<th>${f.replace(/_/g, " ")}</th>`;
        });
        headerHTML += '<th>Predicted Bill (₹)</th>';
        headerHTML += "</tr>";
        thead.innerHTML = headerHTML;

        // Build body
        let bodyHTML = "";
        data.predictions.forEach((row, i) => {
            bodyHTML += "<tr>";
            bodyHTML += `<td>${i + 1}</td>`;
            features.forEach((f) => {
                bodyHTML += `<td>${row[f] ?? "—"}</td>`;
            });
            bodyHTML += `<td class="predicted">₹ ${row.predicted_bill.toLocaleString("en-IN", {
                minimumFractionDigits: 2,
            })}</td>`;
            bodyHTML += "</tr>";
        });
        tbody.innerHTML = bodyHTML;

        batchResults.classList.remove("hidden");
        batchResults.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    // ── Download Template ────────────────────────────────────────────────────
    document.getElementById("btn-download-template").addEventListener("click", () => {
        const features = window.FEATURES || [];
        const stats = window.FEATURE_STATS || {};

        // Create CSV content (Excel can open CSV)
        let csv = features.join(",") + "\n";
        // Add 3 sample rows using median values
        for (let r = 0; r < 3; r++) {
            const row = features.map((f) => {
                const s = stats[f];
                if (!s) return 0;
                // Vary the sample a bit for each row
                const variation = 1 + (r - 1) * 0.15;
                return (s.median * variation).toFixed(2);
            });
            csv += row.join(",") + "\n";
        }

        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "electricity_template.csv";
        a.click();
        URL.revokeObjectURL(url);
    });

    // ── Entrance Animations ──────────────────────────────────────────────────
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = "1";
                    entry.target.style.transform = "translateY(0)";
                }
            });
        },
        { threshold: 0.1 }
    );

    document.querySelectorAll(".stat-card, .card").forEach((el) => {
        el.style.opacity = "0";
        el.style.transform = "translateY(20px)";
        el.style.transition = "opacity 0.6s ease, transform 0.6s ease";
        observer.observe(el);
    });

    // ══════════════════════════════════════════════════════════════════════════
    // CHARTS & ANALYTICS
    // ══════════════════════════════════════════════════════════════════════════
    let chartsLoaded = false;
    let chartInstances = {};

    // Chart.js global defaults for dark theme
    if (typeof Chart !== "undefined") {
        Chart.defaults.color = "#a0a0c0";
        Chart.defaults.borderColor = "rgba(108, 92, 231, 0.12)";
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.plugins.legend.labels.usePointStyle = true;
        Chart.defaults.plugins.legend.labels.padding = 16;
        Chart.defaults.plugins.tooltip.backgroundColor = "rgba(18, 18, 42, 0.95)";
        Chart.defaults.plugins.tooltip.borderColor = "rgba(108, 92, 231, 0.3)";
        Chart.defaults.plugins.tooltip.borderWidth = 1;
        Chart.defaults.plugins.tooltip.cornerRadius = 10;
        Chart.defaults.plugins.tooltip.padding = 12;
        Chart.defaults.plugins.tooltip.titleFont = { weight: "600", size: 13 };
        Chart.defaults.plugins.tooltip.bodyFont = { size: 12 };
    }

    // Color palette
    const COLORS = {
        primary: "#6c5ce7",
        primaryLight: "#a29bfe",
        primaryAlpha: "rgba(108, 92, 231, 0.6)",
        accent: "#00cec9",
        accentAlpha: "rgba(0, 206, 201, 0.6)",
        success: "#00b894",
        successAlpha: "rgba(0, 184, 148, 0.5)",
        warning: "#fdcb6e",
        warningAlpha: "rgba(253, 203, 110, 0.5)",
        danger: "#ff7675",
        dangerAlpha: "rgba(255, 118, 117, 0.5)",
        pink: "#fd79a8",
        pinkAlpha: "rgba(253, 121, 168, 0.5)",
        gridLine: "rgba(108, 92, 231, 0.08)",
        white: "#f0f0ff",
    };

    // Gradient colors for bar charts
    const BAR_COLORS = [
        "#6c5ce7", "#00cec9", "#00b894", "#fdcb6e",
        "#fd79a8", "#a29bfe", "#55efc4", "#ffeaa7", "#fab1a0",
    ];
    const BAR_COLORS_ALPHA = BAR_COLORS.map((c) => c + "cc");

    // Load chart data when charts tab is clicked
    tabBtns.forEach((btn) => {
        btn.addEventListener("click", () => {
            if (btn.dataset.tab === "charts" && !chartsLoaded) {
                loadCharts();
            }
        });
    });

    async function loadCharts() {
        const chartsLoading = document.getElementById("charts-loading");
        const chartsGrid = document.getElementById("charts-grid");

        try {
            const res = await fetch("/api/charts");
            const data = await res.json();

            if (data.error) {
                chartsLoading.innerHTML = `<p style="color: var(--danger);">⚠️ ${data.error}</p>`;
                return;
            }

            chartsLoaded = true;
            chartsLoading.classList.add("hidden");
            chartsGrid.classList.remove("hidden");

            // Render all charts with staggered animation
            setTimeout(() => renderActualVsPredicted(data.actual_vs_predicted), 100);
            setTimeout(() => renderErrorDistribution(data.errors), 200);
            setTimeout(() => renderFeatureImportance(data.coefficients), 300);
            setTimeout(() => renderResiduals(data.residuals_vs_predicted), 400);
            setTimeout(() => renderCorrelation(data.correlation), 500);
            setTimeout(() => renderTargetDistribution(data.target_distribution), 600);

            // Observe chart cards for entrance animation
            document.querySelectorAll(".chart-card").forEach((el, i) => {
                el.style.opacity = "0";
                el.style.transform = "translateY(20px)";
                el.style.transition = `opacity 0.6s ease ${i * 0.1}s, transform 0.6s ease ${i * 0.1}s`;
                requestAnimationFrame(() => {
                    el.style.opacity = "1";
                    el.style.transform = "translateY(0)";
                });
            });
        } catch (err) {
            chartsLoading.innerHTML = `<p style="color: var(--danger);">⚠️ Failed to load charts: ${err.message}</p>`;
        }
    }

    // ── 1. Actual vs Predicted Scatter Plot ──────────────────────────────────
    function renderActualVsPredicted(data) {
        const ctx = document.getElementById("chart-actual-vs-predicted");
        if (!ctx || !data) return;

        const points = data.actual.map((a, i) => ({ x: a, y: data.predicted[i] }));
        const allVals = [...data.actual, ...data.predicted];
        const minVal = Math.floor(Math.min(...allVals));
        const maxVal = Math.ceil(Math.max(...allVals));

        chartInstances.avp = new Chart(ctx, {
            type: "scatter",
            data: {
                datasets: [
                    {
                        label: "Predictions",
                        data: points,
                        backgroundColor: COLORS.primaryAlpha,
                        borderColor: COLORS.primary,
                        borderWidth: 1.5,
                        pointRadius: 5,
                        pointHoverRadius: 8,
                        pointHoverBackgroundColor: COLORS.accent,
                    },
                    {
                        label: "Perfect Prediction Line",
                        data: [
                            { x: minVal, y: minVal },
                            { x: maxVal, y: maxVal },
                        ],
                        type: "line",
                        borderColor: COLORS.danger,
                        borderWidth: 2,
                        borderDash: [8, 4],
                        pointRadius: 0,
                        fill: false,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "top" },
                    tooltip: {
                        callbacks: {
                            label: (ctx) =>
                                `Actual: ₹${ctx.raw.x} | Predicted: ₹${ctx.raw.y}`,
                        },
                    },
                },
                scales: {
                    x: {
                        title: { display: true, text: "Actual Bill (₹)", font: { weight: "600" } },
                        grid: { color: COLORS.gridLine },
                    },
                    y: {
                        title: { display: true, text: "Predicted Bill (₹)", font: { weight: "600" } },
                        grid: { color: COLORS.gridLine },
                    },
                },
            },
        });
    }

    // ── 2. Error Distribution Histogram ──────────────────────────────────────
    function renderErrorDistribution(errors) {
        const ctx = document.getElementById("chart-error-dist");
        if (!ctx || !errors) return;

        // Build histogram bins
        const min = Math.floor(Math.min(...errors));
        const max = Math.ceil(Math.max(...errors));
        const binCount = 20;
        const binWidth = (max - min) / binCount;
        const bins = Array(binCount).fill(0);
        const labels = [];

        for (let i = 0; i < binCount; i++) {
            const lo = min + i * binWidth;
            const hi = lo + binWidth;
            labels.push(`${lo.toFixed(0)}`);
            errors.forEach((e) => {
                if (e >= lo && (i === binCount - 1 ? e <= hi : e < hi)) bins[i]++;
            });
        }

        // Color bars: negative errors red, near-zero green, positive blue
        const barColors = labels.map((l) => {
            const v = parseFloat(l);
            if (Math.abs(v) < binWidth) return COLORS.successAlpha;
            return v < 0 ? COLORS.dangerAlpha : COLORS.primaryAlpha;
        });
        const borderColors = labels.map((l) => {
            const v = parseFloat(l);
            if (Math.abs(v) < binWidth) return COLORS.success;
            return v < 0 ? COLORS.danger : COLORS.primary;
        });

        chartInstances.errorDist = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Frequency",
                        data: bins,
                        backgroundColor: barColors,
                        borderColor: borderColors,
                        borderWidth: 1.5,
                        borderRadius: 4,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: (items) => `Error range: ${items[0].label} to ${(parseFloat(items[0].label) + binWidth).toFixed(0)}`,
                            label: (ctx) => `Count: ${ctx.raw}`,
                        },
                    },
                },
                scales: {
                    x: {
                        title: { display: true, text: "Prediction Error (Actual - Predicted)", font: { weight: "600" } },
                        grid: { color: COLORS.gridLine },
                    },
                    y: {
                        title: { display: true, text: "Frequency", font: { weight: "600" } },
                        grid: { color: COLORS.gridLine },
                        beginAtZero: true,
                    },
                },
            },
        });
    }

    // ── 3. Feature Importance Bar Chart ──────────────────────────────────────
    function renderFeatureImportance(coeffData) {
        const ctx = document.getElementById("chart-feature-importance");
        if (!ctx || !coeffData) return;

        // Sort by absolute value
        const indices = coeffData.features
            .map((_, i) => i)
            .sort((a, b) => coeffData.abs_values[b] - coeffData.abs_values[a]);

        const sortedFeatures = indices.map((i) =>
            coeffData.features[i].replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
        );
        const sortedValues = indices.map((i) => coeffData.values[i]);
        const colors = sortedValues.map((v) =>
            v >= 0 ? COLORS.accentAlpha : COLORS.dangerAlpha
        );
        const borders = sortedValues.map((v) =>
            v >= 0 ? COLORS.accent : COLORS.danger
        );

        chartInstances.importance = new Chart(ctx, {
            type: "bar",
            data: {
                labels: sortedFeatures,
                datasets: [
                    {
                        label: "Coefficient",
                        data: sortedValues,
                        backgroundColor: colors,
                        borderColor: borders,
                        borderWidth: 1.5,
                        borderRadius: 6,
                    },
                ],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => {
                                const dir = ctx.raw >= 0 ? "↑ Increases" : "↓ Decreases";
                                return `${dir} bill by ${Math.abs(ctx.raw).toFixed(4)} per unit`;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        title: { display: true, text: "Coefficient Value", font: { weight: "600" } },
                        grid: { color: COLORS.gridLine },
                    },
                    y: {
                        grid: { display: false },
                        ticks: { font: { weight: "500" } },
                    },
                },
            },
        });
    }

    // ── 4. Residuals vs Predicted ────────────────────────────────────────────
    function renderResiduals(data) {
        const ctx = document.getElementById("chart-residuals");
        if (!ctx || !data) return;

        const points = data.predicted.map((p, i) => ({
            x: p,
            y: data.residuals[i],
        }));

        const pointColors = points.map((p) =>
            Math.abs(p.y) > 100 ? COLORS.dangerAlpha : COLORS.accentAlpha
        );

        chartInstances.residuals = new Chart(ctx, {
            type: "scatter",
            data: {
                datasets: [
                    {
                        label: "Residuals",
                        data: points,
                        backgroundColor: pointColors,
                        borderColor: pointColors.map((c) => c.replace("0.5", "1").replace("0.6", "1")),
                        borderWidth: 1,
                        pointRadius: 5,
                        pointHoverRadius: 8,
                    },
                    {
                        label: "Zero Line",
                        data: [
                            { x: Math.min(...data.predicted), y: 0 },
                            { x: Math.max(...data.predicted), y: 0 },
                        ],
                        type: "line",
                        borderColor: COLORS.warning,
                        borderWidth: 2,
                        borderDash: [6, 4],
                        pointRadius: 0,
                        fill: false,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "top" },
                    tooltip: {
                        callbacks: {
                            label: (ctx) =>
                                `Predicted: ₹${ctx.raw.x} | Error: ₹${ctx.raw.y}`,
                        },
                    },
                },
                scales: {
                    x: {
                        title: { display: true, text: "Predicted Value (₹)", font: { weight: "600" } },
                        grid: { color: COLORS.gridLine },
                    },
                    y: {
                        title: { display: true, text: "Residual (Actual - Predicted)", font: { weight: "600" } },
                        grid: { color: COLORS.gridLine },
                    },
                },
            },
        });
    }

    // ── 5. Correlation Chart ─────────────────────────────────────────────────
    function renderCorrelation(data) {
        const ctx = document.getElementById("chart-correlation");
        if (!ctx || !data) return;

        // Show correlation of each feature with the target (last column)
        const targetIdx = data.labels.length - 1;
        const targetLabel = data.labels[targetIdx];
        const featureLabels = data.labels.slice(0, -1).map((l) =>
            l.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
        );
        const correlations = data.matrix.slice(0, -1).map((row) =>
            parseFloat(row[targetIdx].toFixed(3))
        );

        // Sort by absolute correlation
        const indices = correlations
            .map((_, i) => i)
            .sort((a, b) => Math.abs(correlations[b]) - Math.abs(correlations[a]));

        const sortedLabels = indices.map((i) => featureLabels[i]);
        const sortedValues = indices.map((i) => correlations[i]);
        const colors = sortedValues.map((v) => {
            const intensity = Math.abs(v);
            if (v >= 0) {
                return `rgba(0, 206, 201, ${0.3 + intensity * 0.7})`;
            } else {
                return `rgba(255, 118, 117, ${0.3 + intensity * 0.7})`;
            }
        });
        const borderClr = sortedValues.map((v) =>
            v >= 0 ? COLORS.accent : COLORS.danger
        );

        chartInstances.correlation = new Chart(ctx, {
            type: "bar",
            data: {
                labels: sortedLabels,
                datasets: [
                    {
                        label: `Correlation with ${targetLabel.replace(/_/g, " ")}`,
                        data: sortedValues,
                        backgroundColor: colors,
                        borderColor: borderClr,
                        borderWidth: 1.5,
                        borderRadius: 6,
                    },
                ],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: "top" },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => {
                                const v = ctx.raw;
                                let strength = "Weak";
                                if (Math.abs(v) > 0.7) strength = "Strong";
                                else if (Math.abs(v) > 0.4) strength = "Moderate";
                                return `Correlation: ${v} (${strength})`;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        min: -1,
                        max: 1,
                        title: { display: true, text: "Correlation Coefficient", font: { weight: "600" } },
                        grid: { color: COLORS.gridLine },
                    },
                    y: {
                        grid: { display: false },
                        ticks: { font: { weight: "500" } },
                    },
                },
            },
        });
    }

    // ── 6. Target Distribution ───────────────────────────────────────────────
    function renderTargetDistribution(data) {
        const ctx = document.getElementById("chart-target-dist");
        if (!ctx || !data) return;

        const values = data.values;
        const binCount = 25;
        const min = data.min;
        const max = data.max;
        const binWidth = (max - min) / binCount;
        const bins = Array(binCount).fill(0);
        const labels = [];

        for (let i = 0; i < binCount; i++) {
            const lo = min + i * binWidth;
            labels.push(`${lo.toFixed(0)}`);
            values.forEach((v) => {
                const hi = lo + binWidth;
                if (v >= lo && (i === binCount - 1 ? v <= hi : v < hi)) bins[i]++;
            });
        }

        // Gradient effect via per-bar colors
        const barColors = bins.map((_, i) => {
            const ratio = i / binCount;
            const r = Math.round(108 + (0 - 108) * ratio);
            const g = Math.round(92 + (206 - 92) * ratio);
            const b = Math.round(231 + (201 - 231) * ratio);
            return `rgba(${r}, ${g}, ${b}, 0.65)`;
        });
        const barBorders = bins.map((_, i) => {
            const ratio = i / binCount;
            const r = Math.round(108 + (0 - 108) * ratio);
            const g = Math.round(92 + (206 - 92) * ratio);
            const b = Math.round(231 + (201 - 231) * ratio);
            return `rgb(${r}, ${g}, ${b})`;
        });

        chartInstances.targetDist = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Bill Amount (₹)",
                        data: bins,
                        backgroundColor: barColors,
                        borderColor: barBorders,
                        borderWidth: 1.5,
                        borderRadius: 3,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: (items) =>
                                `₹${items[0].label} – ₹${(parseFloat(items[0].label) + binWidth).toFixed(0)}`,
                            label: (ctx) => `${ctx.raw} households`,
                        },
                    },
                },
                scales: {
                    x: {
                        title: { display: true, text: "Bill Amount (₹)", font: { weight: "600" } },
                        grid: { color: COLORS.gridLine },
                    },
                    y: {
                        title: { display: true, text: "Number of Households", font: { weight: "600" } },
                        grid: { color: COLORS.gridLine },
                        beginAtZero: true,
                    },
                },
            },
        });
    }
});

