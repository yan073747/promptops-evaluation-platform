const runButton = document.querySelector("#run-button");
const resetDemoButton = document.querySelector("#reset-demo-button");
const resultsBody = document.querySelector("#results-body");
const failureList = document.querySelector("#failure-list");
const statusMessage = document.querySelector("#status-message");
const promptForm = document.querySelector("#prompt-form");
const caseForm = document.querySelector("#case-form");
const promptVersionList = document.querySelector("#prompt-version-list");
const testCaseList = document.querySelector("#test-case-list");
const promptVersionSelect = document.querySelector("#prompt-version-select");
const promptPreview = document.querySelector("#prompt-preview");
const promptPreviewLabel = document.querySelector("#prompt-preview-label");
const versionComparisonList = document.querySelector("#version-comparison-list");

const metricNodes = {
  totalRuns: document.querySelector("#total-runs"),
  averageScore: document.querySelector("#average-score"),
  failureRate: document.querySelector("#failure-rate"),
  totalCost: document.querySelector("#total-cost"),
  averageLatency: document.querySelector("#average-latency"),
};

let promptVersions = [];
let testCases = [];

function setStatus(message, state = "") {
  statusMessage.textContent = message;
  statusMessage.className = `status-message ${state}`.trim();
}

function formatCurrency(value) {
  return `$${Number(value).toFixed(6)}`;
}

function keywordsFromInput(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function renderDashboard(metrics) {
  metricNodes.totalRuns.textContent = metrics.total_runs;
  metricNodes.averageScore.textContent = Number(metrics.average_score).toFixed(2);
  metricNodes.failureRate.textContent = `${Math.round(Number(metrics.failure_rate) * 100)}%`;
  metricNodes.totalCost.textContent = formatCurrency(metrics.total_cost_usd);
  metricNodes.averageLatency.textContent = `${Number(metrics.average_latency_ms).toFixed(0)}ms`;
}

function renderPromptVersions(items) {
  promptVersions = items;
  promptVersionSelect.innerHTML = items
    .map((item) => `<option value="${item.id}">${item.label} - ${item.change_note}</option>`)
    .join("");

  promptVersionList.innerHTML = items
    .map(
      (item) => `
        <div class="list-item">
          <div>
            <strong>${item.label}</strong>
            <p>${item.change_note}</p>
          </div>
          <button class="secondary-button" type="button" data-edit-prompt="${item.id}">编辑</button>
        </div>
      `,
    )
    .join("");

  renderPromptPreview();
}

function renderPromptPreview() {
  const selectedId = Number(promptVersionSelect.value);
  const selected = promptVersions.find((item) => item.id === selectedId) || promptVersions[0];
  if (!selected) {
    promptPreviewLabel.textContent = "尚未选择版本";
    promptPreview.textContent = "暂无 Prompt 版本。";
    return;
  }
  promptPreviewLabel.textContent = `${selected.label} / ${selected.change_note}`;
  promptPreview.textContent = selected.content;
}

function renderTestCases(items) {
  testCases = items;
  testCaseList.innerHTML = items
    .map(
      (item) => `
        <div class="list-item">
          <div>
            <strong>${item.input_text}</strong>
            <p>期望关键词：${item.expected_keywords.join("、")}</p>
          </div>
          <button class="secondary-button" type="button" data-edit-case="${item.id}">编辑</button>
        </div>
      `,
    )
    .join("");
}

function renderResults(items) {
  if (!items.length) {
    resultsBody.innerHTML = '<tr><td colspan="6">还没有运行批量测试。</td></tr>';
    return;
  }

  resultsBody.innerHTML = items
    .map(
      (item) => `
      <tr data-output-id="${item.output_id}">
        <td>${item.input_text}</td>
        <td>${item.score.toFixed(2)}</td>
        <td class="${item.passed ? "status-pass" : "status-fail"}">${item.passed ? "通过" : "失败"}</td>
        <td>
          <input class="human-score-input" type="number" min="0" max="1" step="0.1" value="${item.human_score ?? ""}" placeholder="0-1" />
        </td>
        <td>
          <input class="review-note" value="${item.human_note ?? ""}" placeholder="人工复核备注" />
        </td>
        <td>
          <button class="secondary-button" type="button" data-save-review="${item.output_id}">保存</button>
        </td>
      </tr>
    `,
    )
    .join("");
}

function renderFailures(failures) {
  if (!failures.length) {
    failureList.innerHTML = '<p class="label">当前没有失败案例。</p>';
    return;
  }

  failureList.innerHTML = failures
    .map(
      (item) => `
        <article class="failure-card">
          <h3>${item.test_input}</h3>
          <div class="failure-meta">
            <span>${item.failure_type}</span>
            <span>严重程度：${item.severity}</span>
            <span>得分：${Number(item.score).toFixed(2)}</span>
          </div>
          <p><strong>模型输出：</strong>${item.output_text || "暂无输出"}</p>
          <p><strong>失败原因：</strong>${item.analysis_note}</p>
          <p><strong>优化建议：</strong>${item.optimization_suggestion}</p>
        </article>
      `,
    )
    .join("");
}

function renderVersionComparison(items) {
  if (!items.length) {
    versionComparisonList.innerHTML = '<p class="label">暂无 Prompt 版本。</p>';
    return;
  }

  versionComparisonList.innerHTML = items
    .map(
      (item) => `
        <div class="comparison-card">
          <h3>${item.label} / ${item.change_note}</h3>
          <div class="comparison-grid">
            <div>
              <span>运行次数</span>
              <strong>${item.run_count}</strong>
            </div>
            <div>
              <span>平均得分</span>
              <strong>${Number(item.average_score).toFixed(2)}</strong>
            </div>
            <div>
              <span>失败率</span>
              <strong>${Math.round(Number(item.failure_rate) * 100)}%</strong>
            </div>
            <div>
              <span>总成本</span>
              <strong>${formatCurrency(item.total_cost_usd)}</strong>
            </div>
            <div>
              <span>平均耗时</span>
              <strong>${Number(item.average_latency_ms).toFixed(0)}ms</strong>
            </div>
            <div>
              <span>测试条数</span>
              <strong>${item.total_cases}</strong>
            </div>
          </div>
        </div>
      `,
    )
    .join("");
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`请求失败：${response.status}`);
  }
  return response.json();
}

async function refreshDashboard() {
  const metrics = await fetchJson("/api/dashboard");
  renderDashboard(metrics);
}

async function refreshPromptVersions() {
  const items = await fetchJson("/api/prompt-versions");
  renderPromptVersions(items);
}

async function refreshTestCases() {
  const items = await fetchJson("/api/test-cases");
  renderTestCases(items);
}

async function refreshFailures() {
  const failures = await fetchJson("/api/failure-cases");
  renderFailures(failures);
}

async function refreshVersionComparison() {
  const items = await fetchJson("/api/prompt-version-comparison");
  renderVersionComparison(items);
}

async function runMockBatch() {
  runButton.disabled = true;
  setStatus("正在运行 Mock 批量评测...");
  try {
    const result = await fetchJson("/api/runs/mock", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt_version_id: Number(promptVersionSelect.value) }),
    });
    renderResults(result.items);
    await refreshDashboard();
    await refreshFailures();
    await refreshVersionComparison();
    setStatus("Mock 批量评测完成，指标已更新。", "is-ok");
  } catch (error) {
    setStatus(error.message, "is-error");
  } finally {
    runButton.disabled = false;
  }
}

async function resetDemoData() {
  resetDemoButton.disabled = true;
  runButton.disabled = true;
  setStatus("正在重置演示数据...");
  try {
    await fetchJson("/api/demo/reset", { method: "POST" });
    resultsBody.innerHTML = '<tr><td colspan="6">还没有运行批量测试。</td></tr>';
    promptForm.reset();
    caseForm.reset();
    document.querySelector("#prompt-id").value = "";
    document.querySelector("#case-id").value = "";
    await Promise.all([
      refreshDashboard(),
      refreshPromptVersions(),
      refreshTestCases(),
      refreshFailures(),
      refreshVersionComparison(),
    ]);
    setStatus("演示数据已重置，可以开始录制或展示。", "is-ok");
  } catch (error) {
    setStatus(error.message, "is-error");
  } finally {
    resetDemoButton.disabled = false;
    runButton.disabled = false;
  }
}

async function savePromptVersion(event) {
  event.preventDefault();
  const id = document.querySelector("#prompt-id").value;
  const payload = {
    template_id: 1,
    label: document.querySelector("#prompt-label").value.trim(),
    content: document.querySelector("#prompt-content").value.trim(),
    change_note: document.querySelector("#prompt-note").value.trim(),
  };
  const url = id ? `/api/prompt-versions/${id}` : "/api/prompt-versions";
  const method = id ? "PUT" : "POST";

  await fetchJson(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  document.querySelector("#prompt-id").value = "";
  await refreshPromptVersions();
  setStatus("Prompt 版本已保存。", "is-ok");
}

async function saveTestCase(event) {
  event.preventDefault();
  const id = document.querySelector("#case-id").value;
  const payload = {
    input_text: document.querySelector("#case-input").value.trim(),
    expected_keywords: keywordsFromInput(document.querySelector("#case-keywords").value),
  };
  const url = id ? `/api/test-cases/${id}` : "/api/test-cases";
  const method = id ? "PUT" : "POST";

  await fetchJson(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  document.querySelector("#case-id").value = "";
  await refreshTestCases();
  await refreshDashboard();
  setStatus("测试用例已保存。", "is-ok");
}

async function saveHumanReview(outputId) {
  const row = document.querySelector(`[data-output-id="${outputId}"]`);
  const scoreInput = row.querySelector(".human-score-input");
  const noteInput = row.querySelector(".review-note");
  await fetchJson(`/api/model-outputs/${outputId}/human-review`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      human_score: Number(scoreInput.value),
      human_note: noteInput.value.trim(),
    }),
  });
  setStatus("人工评分已保存。", "is-ok");
}

function editPromptVersion(id) {
  const item = promptVersions.find((version) => version.id === id);
  if (!item) return;
  document.querySelector("#prompt-id").value = item.id;
  document.querySelector("#prompt-label").value = item.label;
  document.querySelector("#prompt-note").value = item.change_note;
  document.querySelector("#prompt-content").value = item.content;
  setStatus("正在编辑 Prompt 版本。");
}

function editTestCase(id) {
  const item = testCases.find((testCase) => testCase.id === id);
  if (!item) return;
  document.querySelector("#case-id").value = item.id;
  document.querySelector("#case-input").value = item.input_text;
  document.querySelector("#case-keywords").value = item.expected_keywords.join(",");
  setStatus("正在编辑测试用例。");
}

async function boot() {
  try {
    await Promise.all([
      refreshDashboard(),
      refreshPromptVersions(),
      refreshTestCases(),
      refreshFailures(),
      refreshVersionComparison(),
    ]);
    setStatus("已连接 FastAPI 后端。", "is-ok");
  } catch (error) {
    setStatus(error.message, "is-error");
  }
}

runButton.addEventListener("click", runMockBatch);
resetDemoButton.addEventListener("click", resetDemoData);
promptVersionSelect.addEventListener("change", renderPromptPreview);
promptForm.addEventListener("submit", savePromptVersion);
caseForm.addEventListener("submit", saveTestCase);
document.querySelector("#new-prompt-button").addEventListener("click", () => {
  promptForm.reset();
  document.querySelector("#prompt-id").value = "";
});
document.querySelector("#new-case-button").addEventListener("click", () => {
  caseForm.reset();
  document.querySelector("#case-id").value = "";
});
promptVersionList.addEventListener("click", (event) => {
  const id = event.target.dataset.editPrompt;
  if (id) editPromptVersion(Number(id));
});
testCaseList.addEventListener("click", (event) => {
  const id = event.target.dataset.editCase;
  if (id) editTestCase(Number(id));
});
resultsBody.addEventListener("click", async (event) => {
  const id = event.target.dataset.saveReview;
  if (id) {
    await saveHumanReview(Number(id));
  }
});

boot();
