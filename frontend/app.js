const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? `http://${window.location.hostname}:8002/api` 
    : "http://127.0.0.1:8002/api";

let pollInterval = null;
let complaintChart = null;
let complaintThemesChart = null;
let costBreakdownChart = null;
let savingsPotentialChart = null;
let predImage1B64 = null;
let predImage2B64 = null;

// ══════════════ MODE TAB SWITCHING ══════════════

document.getElementById('modeAnalytics').addEventListener('click', () => switchMode('analytics'));
document.getElementById('modePrediction').addEventListener('click', () => switchMode('prediction'));

function switchMode(mode) {
    document.getElementById('modeAnalytics').classList.toggle('active', mode === 'analytics');
    document.getElementById('modePrediction').classList.toggle('active', mode === 'prediction');
    document.getElementById('sectionAnalytics').classList.toggle('active', mode === 'analytics');
    document.getElementById('sectionPrediction').classList.toggle('active', mode === 'prediction');
}

// ══════════════ ANALYTICS WORKFLOW ══════════════

document.getElementById('analyticsBtn').addEventListener('click', startAnalytics);

async function startAnalytics() {
    const url = document.getElementById('analyticsUrl').value.trim();
    if (!url || !url.startsWith('http')) {
        document.getElementById('analyticsUrlError').classList.remove('hidden');
        return;
    }
    document.getElementById('analyticsUrlError').classList.add('hidden');

    const loading = document.getElementById('analyticsLoading');
    const results = document.getElementById('analyticsResults');
    loading.classList.remove('hidden');
    results.classList.add('hidden');
    loading.scrollIntoView({ behavior: 'smooth' });
    resetAnalyticsProgress();

    try {
        const res = await fetch(`${API_BASE}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        if (!res.ok) throw new Error('API request failed');
        const data = await res.json();
        pollAnalytics(data.job_id);
    } catch (err) {
        document.getElementById('analyticsStatus').innerText = "Error: API Offline or Blocked";
        document.getElementById('analyticsStatus').classList.add('text-rose-500');
    }
}

function pollAnalytics(jobId) {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/status/${jobId}`);
            const data = await res.json();
            updateAnalyticsProgress(data.progress, data.message);
            if (data.status === 'completed') {
                clearInterval(pollInterval);
                setTimeout(() => showAnalyticsResults(data.result), 800);
            } else if (data.status === 'failed') {
                clearInterval(pollInterval);
                document.getElementById('analyticsStatus').innerText = "Error: " + data.message;
                document.getElementById('analyticsStatus').classList.add('text-rose-500');
            }
        } catch (e) { console.error(e); }
    }, 2000);
}

function updateAnalyticsProgress(progress, message) {
    document.getElementById('analyticsPercent').innerText = `${progress}%`;
    document.getElementById('analyticsBar').style.width = `${progress}%`;
    document.getElementById('analyticsStatus').innerText = message;
    const thresholds = [0, 14, 28, 42, 56, 70, 85];
    for (let i = 1; i <= 7; i++) {
        const step = document.getElementById(`a-step-${i}`);
        const t = thresholds[i-1];
        if (progress > t + 14) {
            step.classList.remove('opacity-30', 'scale-95', 'active');
            step.classList.add('completed', 'opacity-100', 'scale-100');
        } else if (progress > t) {
            step.classList.remove('opacity-30', 'scale-95', 'completed');
            step.classList.add('active', 'opacity-100', 'scale-110');
        } else {
            step.classList.add('opacity-30', 'scale-95');
            step.classList.remove('active', 'completed', 'opacity-100', 'scale-110', 'scale-100');
        }
    }
}

function resetAnalyticsProgress() {
    document.getElementById('analyticsBar').style.width = '0%';
    document.getElementById('analyticsPercent').innerText = '0%';
    document.getElementById('analyticsStatus').classList.remove('text-rose-500');
    for (let i = 1; i <= 7; i++) {
        document.getElementById(`a-step-${i}`).className = 'a-step group flex flex-col items-center gap-3 transition-all opacity-30 scale-95';
    }
}

// Strip markdown code blocks / bolding from text
function cleanText(text) {
    if (!text) return "";
    return text.toString()
        .replace(/```[\s\S]*?```/g, '') // remove large blocks
        .replace(/`/g, '')              // remove inline
        .replace(/\*\*/g, '')           // remove bold
        .trim();
}

function showAnalyticsResults(report) {
    document.getElementById('analyticsLoading').classList.add('hidden');
    const results = document.getElementById('analyticsResults');
    results.classList.remove('hidden');
    results.scrollIntoView({ behavior: 'smooth' });

    document.getElementById('resProductName').innerText = report.product_name;
    document.getElementById('resPlatform').innerText = report.platform.toUpperCase();
    document.getElementById('resRating').innerText = report.rating;
    document.getElementById('resTotalReviews').innerText = report.total_reviews;

    // Gauge
    animateGauge('resRiskScore', 'riskGaugeSVG', report.return_risk_score, 44);
    const rl = document.getElementById('resRiskLevel');
    rl.innerText = `${report.risk_level} RISK`;
    rl.className = `w-full text-center py-3 rounded-2xl text-xs font-black uppercase tracking-[0.2em] shadow-sm border ${
        report.risk_level === 'High' ? 'bg-rose-50 text-rose-600 border-rose-100' :
        report.risk_level === 'Medium' ? 'bg-amber-50 text-amber-600 border-amber-100' :
        'bg-emerald-50 text-emerald-600 border-emerald-100'
    }`;

    // Chart
    initBarChart('complaintChart', report.complaint_clusters);

    // Mismatches
    document.getElementById('mismatchContainer').innerHTML = report.listing_mismatches.map(m => `
        <div class="p-6 bg-amber-50/50 rounded-3xl border border-amber-100 hover:shadow-md transition-all overflow-safe">
            <div class="flex items-center gap-2 mb-2">
                <span class="text-[10px] font-black uppercase text-amber-600 tracking-widest bg-amber-100 px-2 py-0.5 rounded">Mismatch</span>
            </div>
            <h4 class="font-bold text-slate-800 text-sm mb-2 overflow-safe">${cleanText(m.listing_claim)}</h4>
            <p class="text-[11px] text-slate-600 font-medium leading-relaxed italic overflow-safe">${cleanText(m.review_evidence)}</p>
        </div>
    `).join('');

    // Recommendations
    document.getElementById('recommendationContainer').innerHTML = report.recommendations.map(r => `
        <div class="flex items-start gap-4 p-5 bg-white rounded-2xl border border-slate-100 shadow-sm hover:border-indigo-200 transition-colors overflow-safe">
            <div class="mt-1 w-6 h-6 bg-indigo-50 text-indigo-600 rounded-lg flex items-center justify-center shrink-0">
                <i data-lucide="check-circle" class="w-4 h-4"></i>
            </div>
            <div class="min-w-0 overflow-safe">
                <p class="text-sm font-bold text-slate-800 overflow-safe">${cleanText(r)}</p>
                <p class="text-[10px] text-slate-400 uppercase font-black tracking-widest mt-1">Strategic Action</p>
            </div>
        </div>
    `).join('');

    // Clusters
    document.getElementById('clusterContainer').innerHTML = report.complaint_clusters.map(c => `
        <div class="border border-slate-100 rounded-3xl p-8 bg-white/50 hover:bg-white transition-all premium-shadow overflow-hidden">
            <div class="flex justify-between items-start mb-6">
                <div class="min-w-0 flex-1 mr-3">
                    <span class="text-[10px] text-slate-400 font-black uppercase tracking-widest mb-1 block">Common Issue</span>
                    <h4 class="font-extrabold text-slate-800 text-lg tracking-tight overflow-safe">${cleanText(c.theme)}</h4>
                </div>
                <div class="text-right shrink-0">
                    <span class="text-indigo-600 text-xl font-black tracking-tighter">${c.percentage}%</span>
                    <p class="text-[9px] text-slate-400 font-black uppercase tracking-widest">Impact</p>
                </div>
            </div>
            <div class="mb-2 text-xs font-bold text-slate-700">Example Customer Quotes:</div>
            <div class="cluster-content space-y-3">
                ${c.example_reviews.map(rev => `
                    <div class="text-xs text-slate-500 pl-4 border-l-2 border-indigo-100 py-1 hover:border-indigo-400 hover:text-slate-700 leading-relaxed font-medium overflow-safe italic">
                        "${cleanText(rev)}"
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');

    // Suggestions
    if (report.suggestions) {
        document.getElementById('sugListing').innerHTML = report.suggestions.listing_improvements.map(i => `<li class="flex items-start gap-2"><div class="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0"></div><span class="flex-1">${cleanText(i)}</span></li>`).join('');
        document.getElementById('sugCustomer').innerHTML = report.suggestions.customer_expectation_fixes.map(i => `<li class="flex items-start gap-2"><div class="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0"></div><span class="flex-1">${cleanText(i)}</span></li>`).join('');
        document.getElementById('sugSeller').innerHTML = report.suggestions.seller_optimization.map(i => `<li class="flex items-start gap-2"><div class="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0"></div><span class="flex-1">${cleanText(i)}</span></li>`).join('');
    }

    // Cost Estimation Charts
    if (report.cost_estimation) {
        initCostBreakdownChart('costBreakdownChart', report.cost_estimation.return_cost_breakdown);
        initSavingsPotentialChart('savingsPotentialChart', report.cost_estimation.potential_savings);
    }

    lucide.createIcons();
}

// ══════════════ PREDICTION WORKFLOW ══════════════

document.getElementById('predImage1').addEventListener('change', (e) => handlePredImage(e, 1));
document.getElementById('predImage2').addEventListener('change', (e) => handlePredImage(e, 2));
document.getElementById('predictionBtn').addEventListener('click', startPrediction);

function handlePredImage(event, index) {
    const file = event.target.files[0];
    if (!file) return;
    const zone = document.getElementById(`predUpload${index}Zone`);
    const label = document.getElementById(`predUpload${index}Label`);
    const reader = new FileReader();
    reader.onload = (e) => {
        const b64Data = e.target.result.split(',');
        const b64 = b64Data.length > 1 ? b64Data[1] : b64Data[0];
        if (index === 1) predImage1B64 = b64; else predImage2B64 = b64;
        zone.classList.add('has-file');
        label.textContent = file.name.length > 25 ? file.name.slice(0, 22) + '...' : file.name;
    };
    reader.readAsDataURL(file);
}

async function startPrediction() {
    const title = document.getElementById('predTitle').value.trim();
    const desc = document.getElementById('predDescription').value.trim();
    
    // UI Validation
    if (title.length < 20 || desc.length < 50) {
        const errEl = document.getElementById('predInputError');
        errEl.innerHTML = '<i data-lucide="alert-circle" class="w-4 h-4"></i> Title must be at least 20 chars and Description at least 50 chars';
        errEl.classList.remove('hidden');
        if (typeof lucide !== 'undefined') lucide.createIcons();
        return;
    }

    if (!title || (!predImage1B64 && !predImage2B64)) {
        const errEl = document.getElementById('predInputError');
        errEl.innerHTML = '<i data-lucide="alert-circle" class="w-4 h-4"></i> Please provide listing title and at least one image';
        errEl.classList.remove('hidden');
        if (typeof lucide !== 'undefined') lucide.createIcons();
        return;
    }
    document.getElementById('predInputError').classList.add('hidden');

    const loading = document.getElementById('predictionLoading');
    const results = document.getElementById('predictionResults');
    loading.classList.remove('hidden');
    results.classList.add('hidden');
    loading.scrollIntoView({ behavior: 'smooth' });
    resetPredProgress();

    // Simulate prediction pipeline locally (since prediction doesn't use URL scraping)
    simulatePredPipeline(title, desc);
}

async function simulatePredPipeline(title, desc) {
    const steps = [
        { p: 15, msg: 'Agent 1: Analyzing product images...' },
        { p: 35, msg: 'Agent 2: Analyzing listing text...' },
        { p: 55, msg: 'Agent 3: Extracting prediction features...' },
        { p: 75, msg: 'Agent 4: Computing return prediction...' },
        { p: 90, msg: 'Agent 5: Generating prediction report...' },
    ];

    for (let i = 0; i < steps.length; i++) {
        await sleep(800);
        updatePredProgress(steps[i].p, steps[i].msg);
    }

    // Call backend prediction API endpoint
    try {
        const res = await fetch(`${API_BASE}/prediction/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_title: title,
                product_description: desc,
                product_images: [predImage1B64, predImage2B64].filter(Boolean)
            })
        });

        if (!res.ok) throw new Error('Prediction API failed');
        const data = await res.json();

        updatePredProgress(100, 'Prediction complete!');
        await sleep(600);
        showPredictionResults(data);
    } catch (err) {
        console.error(err);
        document.getElementById('predStatus').innerText = 'Error: ' + err.message;
        document.getElementById('predStatus').classList.add('text-rose-500');
    }
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function updatePredProgress(progress, message) {
    document.getElementById('predPercent').innerText = `${progress}%`;
    document.getElementById('predBar').style.width = `${progress}%`;
    document.getElementById('predStatus').innerText = message;
    const thresholds = [0, 20, 40, 60, 80];
    for (let i = 1; i <= 5; i++) {
        const step = document.getElementById(`p-step-${i}`);
        const t = thresholds[i-1];
        if (progress > t + 20) {
            step.classList.remove('opacity-30', 'scale-95', 'active');
            step.classList.add('completed', 'opacity-100', 'scale-100');
        } else if (progress > t) {
            step.classList.remove('opacity-30', 'scale-95', 'completed');
            step.classList.add('active', 'opacity-100', 'scale-110');
        } else {
            step.classList.add('opacity-30', 'scale-95');
            step.classList.remove('active', 'completed', 'opacity-100', 'scale-110', 'scale-100');
        }
    }
}

function resetPredProgress() {
    document.getElementById('predBar').style.width = '0%';
    document.getElementById('predPercent').innerText = '0%';
    document.getElementById('predStatus').classList.remove('text-rose-500');
    for (let i = 1; i <= 5; i++) {
        document.getElementById(`p-step-${i}`).className = 'p-step group flex flex-col items-center gap-3 transition-all opacity-30 scale-95';
    }
}

function showPredictionResults(pred) {
    document.getElementById('predictionLoading').classList.add('hidden');
    const results = document.getElementById('predictionResults');
    results.classList.remove('hidden');
    results.scrollIntoView({ behavior: 'smooth' });

    // Gauge
    const score = pred.return_risk_score;
    const level = pred.risk_level;
    animatePredGauge(score, level.toUpperCase());

    // Probability
    animateFloat('predProbability', score / 100);
    document.getElementById('predProbBar').style.width = `${score}%`;

    // Risk badge
    const badge = document.getElementById('predRiskLevel');
    badge.innerText = `${level.toUpperCase()} RETURN RISK`;
    badge.className = 'w-full text-center py-3.5 rounded-2xl text-sm font-black uppercase tracking-[0.15em] shadow-sm border ' + (
        level.toUpperCase() === 'LOW' ? 'bg-emerald-50 text-emerald-600 border-emerald-100' :
        level.toUpperCase() === 'MEDIUM' ? 'bg-amber-50 text-amber-600 border-amber-100' :
        'bg-rose-50 text-rose-600 border-rose-100'
    );

    // Summary
    const summaryParts = [];
    if (pred.possible_return_reasons && pred.possible_return_reasons.length > 0) {
        summaryParts.push(`Key risk factors: ${pred.possible_return_reasons.join(', ')}.`);
    }
    summaryParts.push(`Return risk score is ${pred.return_risk_score}/100 with ${pred.prediction_confidence}% confidence (${level} risk).`);
    document.getElementById('predSummaryText').innerText = summaryParts.join(' ');

    // Drivers
    const dc = document.getElementById('predDriversContainer');
    if (pred.possible_return_reasons && pred.possible_return_reasons.length > 0) {
        dc.innerHTML = pred.possible_return_reasons.map((reason, idx) => {
            const isHigh = idx < 2; // Arbitrary logic for visual
            const cls = isHigh ? 'impact-high' : 'impact-medium';
            const check = isHigh ? '⚠' : '✔';
            const impText = isHigh ? 'high' : 'medium';
            return `
                <div class="flex items-start gap-4 p-5 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-all overflow-safe">
                    <div class="mt-0.5 w-10 h-10 ${cls} rounded-xl flex items-center justify-center shrink-0 border">
                        <i data-lucide="${isHigh ? 'alert-triangle' : 'info'}" class="w-5 h-5"></i>
                    </div>
                    <div class="flex-1 min-w-0 overflow-safe">
                        <div class="flex items-center gap-2 mb-1 flex-wrap">
                            <span class="text-[11px]">${check}</span>
                            <p class="text-sm font-bold text-slate-800 overflow-safe">${cleanText(reason)}</p>
                            <span class="px-2 py-0.5 rounded-md text-[9px] font-black uppercase tracking-wider ${cls} border">${impText}</span>
                        </div>
                        <p class="text-xs text-slate-500 font-medium leading-relaxed overflow-safe">Predicted possible return reason from the model.</p>
                    </div>
                </div>
            `;
        }).join('');
    } else {
        dc.innerHTML = '<div class="text-center py-8 text-slate-400 font-medium whitespace-nowrap"><p>No specific risks extracted</p></div>';
    }

    // Image analysis (Using image_quality_score and listing_clarity_score)
    const ic = document.getElementById('imageAnalysisContainer');
    const noData = document.getElementById('imageNoData');
    
    noData.classList.add('hidden');
    ic.innerHTML = `
        <div class="p-6 bg-white rounded-3xl border border-slate-100 shadow-sm hover:shadow-md transition-all overflow-safe">
            <div class="flex items-center gap-3 mb-5">
                <div class="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center border border-blue-100">
                    <i data-lucide="image" class="w-5 h-5 text-blue-600"></i>
                </div>
                <div>
                    <h4 class="font-bold text-slate-800 text-sm">Overall Image Quality</h4>
                    <p class="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Quality: ${pred.image_quality_score}%</p>
                </div>
            </div>
            <div class="w-full h-2 bg-slate-100 rounded-full overflow-hidden mb-4">
                <div class="h-full rounded-full transition-all duration-700 ${pred.image_quality_score > 70 ? 'bg-emerald-400' : pred.image_quality_score > 50 ? 'bg-amber-400' : 'bg-rose-400'}" style="width: ${pred.image_quality_score}%"></div>
            </div>
            <div class="space-y-2 overflow-safe">
                <div class="flex items-center gap-2 p-2 rounded-lg border ${pred.image_quality_score > 70 ? 'bg-emerald-50 border-emerald-100' : 'bg-amber-50 border-amber-100'}">
                    <i data-lucide="${pred.image_quality_score > 70 ? 'check-circle' : 'alert-triangle'}" class="w-4 h-4 ${pred.image_quality_score > 70 ? 'text-emerald-600' : 'text-amber-600'}"></i>
                    <span class="text-xs font-bold ${pred.image_quality_score > 70 ? 'text-emerald-700' : 'text-amber-700'} overflow-safe">${pred.image_quality_score > 70 ? 'Good Image Quality' : 'Potential Image Issues'}</span>
                </div>
            </div>
        </div>
        <div class="p-6 bg-white rounded-3xl border border-slate-100 shadow-sm hover:shadow-md transition-all overflow-safe">
            <div class="flex items-center gap-3 mb-5">
                <div class="w-10 h-10 bg-purple-50 rounded-xl flex items-center justify-center border border-purple-100">
                    <i data-lucide="file-text" class="w-5 h-5 text-purple-600"></i>
                </div>
                <div>
                    <h4 class="font-bold text-slate-800 text-sm">Listing Text Clarity</h4>
                    <p class="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Clarity: ${pred.listing_clarity_score}%</p>
                </div>
            </div>
            <div class="w-full h-2 bg-slate-100 rounded-full overflow-hidden mb-4">
                <div class="h-full rounded-full transition-all duration-700 ${pred.listing_clarity_score > 70 ? 'bg-emerald-400' : pred.listing_clarity_score > 50 ? 'bg-amber-400' : 'bg-rose-400'}" style="width: ${pred.listing_clarity_score}%"></div>
            </div>
            <div class="space-y-2 overflow-safe">
                <div class="flex items-center gap-2 p-2 rounded-lg border ${pred.listing_clarity_score > 70 ? 'bg-emerald-50 border-emerald-100' : 'bg-amber-50 border-amber-100'}">
                    <i data-lucide="${pred.listing_clarity_score > 70 ? 'check-circle' : 'alert-triangle'}" class="w-4 h-4 ${pred.listing_clarity_score > 70 ? 'text-emerald-600' : 'text-amber-600'}"></i>
                    <span class="text-xs font-bold ${pred.listing_clarity_score > 70 ? 'text-emerald-700' : 'text-amber-700'} overflow-safe">${pred.listing_clarity_score > 70 ? 'Clear description' : 'Lacks technical specs'}</span>
                </div>
            </div>
        </div>
    `;

    // Complaint themes chart
    if (complaintThemesChart) {
        complaintThemesChart.data.labels = ['N/A (Use Analytics Tab)'];
        complaintThemesChart.data.datasets[0].data = [0];
        complaintThemesChart.update();
    }

    // External complaints
    const ec = document.getElementById('externalComplaintsContainer');
    ec.innerHTML = '<div class="text-center py-8 text-slate-400 font-medium"><p>External complaints are only available in the full Analytics scan</p></div>';

    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// ══════════════ SHARED HELPERS ══════════════

function animateGauge(scoreId, circleId, score, radius) {
    const el = document.getElementById(scoreId);
    const circle = document.getElementById(circleId);
    const circ = 2 * Math.PI * radius;
    let cur = 0;
    const iv = setInterval(() => {
        if (cur >= score) { el.innerText = score; clearInterval(iv); }
        else { cur++; el.innerText = cur; }
    }, 15);
    const off = circ - (score / 100) * circ;
    circle.style.strokeDasharray = `${circ} ${circ}`;
    circle.style.strokeDashoffset = circ;
    circle.getBoundingClientRect();
    circle.style.strokeDashoffset = off;
}

function animatePredGauge(score, level) {
    const el = document.getElementById('predRiskScore');
    const circle = document.getElementById('predGaugeSVG');
    const circ = 2 * Math.PI * 52;
    let gradId = level === 'LOW' ? 'pred-gauge-grad-low' : level === 'MEDIUM' ? 'pred-gauge-grad-med' : 'pred-gauge-grad-high';
    circle.setAttribute('stroke', `url(#${gradId})`);
    let cur = 0;
    const iv = setInterval(() => {
        if (cur >= score) { el.innerText = score; clearInterval(iv); }
        else { cur++; el.innerText = cur; }
    }, 15);
    const off = circ - (score / 100) * circ;
    circle.style.strokeDasharray = `${circ}`;
    circle.style.strokeDashoffset = `${circ}`;
    requestAnimationFrame(() => { circle.style.strokeDashoffset = `${off}`; });
}

function animateFloat(elId, target) {
    const el = document.getElementById(elId);
    const start = performance.now();
    const dur = 1500;
    function tick(now) {
        const p = Math.min((now - start) / dur, 1);
        const eased = 1 - Math.pow(1 - p, 3);
        el.innerText = (target * eased).toFixed(2);
        if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
}

function initBarChart(canvasId, clusters) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    if (complaintChart) complaintChart.destroy();
    const grad = ctx.createLinearGradient(0, 0, 0, 400);
    grad.addColorStop(0, 'rgba(79, 70, 229, 1)'); // Indigo solid
    grad.addColorStop(1, 'rgba(147, 51, 234, 1)'); // Purple solid
    complaintChart = new Chart(ctx, {
        type: 'bar',
        data: { 
            labels: clusters.map(c => c.theme.length > 20 ? c.theme.substring(0, 17) + '...' : c.theme), 
            datasets: [{ 
                label: 'Cluster Impact', 
                data: clusters.map(c => c.percentage), 
                backgroundColor: grad, 
                borderRadius: { topLeft: 8, topRight: 8, bottomLeft: 0, bottomRight: 0 }, 
                borderSkipped: 'bottom',
                barThickness: 32 
            }] 
        },
        options: { 
            responsive: true, 
            maintainAspectRatio: false, 
            plugins: { 
                legend: { display: false }, 
                tooltip: { backgroundColor: '#1e293b', padding: 12, cornerRadius: 12, titleFont: { size: 14 }, bodyFont: { size: 14 } } 
            }, 
            scales: { 
                y: { 
                    beginAtZero: true, 
                    suggestedMax: 100, 
                    grid: { display: false }, 
                    ticks: { color: '#94a3b8', font: { weight: 'bold', size: 13 }, callback: v => v + '%' } 
                }, 
                x: { 
                    grid: { display: false }, 
                    ticks: { color: '#64748b', font: { weight: 'bold', size: 14 }, maxRotation: 45, minRotation: 45, autoSkip: false } 
                } 
            } 
        }
    });
}

function initHorizontalChart(canvasId, clusters) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    if (complaintThemesChart) complaintThemesChart.destroy();
    const colors = ['rgba(239,68,68,0.85)', 'rgba(245,158,11,0.85)', 'rgba(99,102,241,0.85)', 'rgba(16,185,129,0.85)', 'rgba(168,85,247,0.85)'];
    complaintThemesChart = new Chart(ctx, {
        type: 'bar',
        data: { labels: clusters.map(c => c.theme.length > 25 ? c.theme.substring(0, 22) + '...' : c.theme), datasets: [{ label: 'Complaint %', data: clusters.map(c => c.percentage), backgroundColor: clusters.map((_, i) => colors[i % colors.length]), borderRadius: 10, barThickness: 28 }] },
        options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { backgroundColor: '#1e293b', padding: 12, cornerRadius: 12, titleFont: { size: 14 }, bodyFont: { size: 14 }, callbacks: { label: ctx => `${ctx.parsed.x.toFixed(1)}%` } } }, scales: { x: { beginAtZero: true, max: 100, grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { color: '#94a3b8', font: { weight: 'bold', size: 13 }, callback: v => v + '%' } }, y: { grid: { display: false }, ticks: { color: '#334155', font: { weight: 'bold', size: 14 } } } } }
    });
}

function initCostBreakdownChart(canvasId, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    if (costBreakdownChart) costBreakdownChart.destroy();
    costBreakdownChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Logistics', 'Refunds', 'Warehouse', 'Restocking'],
            datasets: [{
                label: 'Estimated Loss (₹)',
                data: [data.logistics, data.refunds, data.warehouse, data.restocking],
                backgroundColor: 'rgba(239, 68, 68, 0.85)',
                borderRadius: 8,
                barThickness: 40
            }]
        },
        options: { 
            responsive: true, maintainAspectRatio: false, 
            plugins: { legend: { display: false }, tooltip: { backgroundColor: '#1e293b', padding: 12, cornerRadius: 12, titleFont: { size: 14 }, bodyFont: { size: 14 }, callbacks: { label: ctx => `₹${ctx.parsed.y.toLocaleString()}` } } },
            scales: { 
                y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { color: '#94a3b8', font: { weight: 'bold', size: 13 }, callback: v => '₹' + v.toLocaleString() } },
                x: { grid: { display: false }, ticks: { color: '#64748b', font: { weight: 'bold', size: 14 } } }
            } 
        }
    });
}

function initSavingsPotentialChart(canvasId, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    if (savingsPotentialChart) savingsPotentialChart.destroy();
    
    const grad = ctx.createLinearGradient(0, 0, 0, 250);
    grad.addColorStop(0, 'rgba(16, 185, 129, 0.4)');
    grad.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

    savingsPotentialChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Better Images', 'Clear Desc', 'Size Chart', 'Better Pkg'],
            datasets: [{
                label: 'Potential Savings (₹)',
                data: [data.better_images, data.clear_description, data.size_chart, data.better_packaging],
                borderColor: '#10b981',
                backgroundColor: grad,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#fff',
                pointBorderColor: '#10b981',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: { 
            responsive: true, maintainAspectRatio: false, 
            plugins: { legend: { display: false }, tooltip: { backgroundColor: '#1e293b', padding: 12, cornerRadius: 12, titleFont: { size: 14 }, bodyFont: { size: 14 }, callbacks: { label: ctx => `₹${ctx.parsed.y.toLocaleString()}` } } },
            scales: { 
                y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { color: '#94a3b8', font: { weight: 'bold', size: 13 }, callback: v => '₹' + v.toLocaleString() } },
                x: { grid: { display: false }, ticks: { color: '#64748b', font: { weight: 'bold', size: 14 } } }
            }
        }
    });
}
