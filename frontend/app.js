const demoVersion = "20260715-static-demo";
const stateKey = `promptops-static-demo-${demoVersion}`;

const runButton = document.querySelector("#run-button");
const resetDemoButton = document.querySelector("#reset-demo-button");
const resultsBody = document.querySelector("#results-body");
const failureList = document.querySelector("#failure-list");
const statusMessage = document.querySelector("#status-message");
const runStateTitle = document.querySelector("#run-state-title");
const promptForm = document.querySelector("#prompt-form");
const caseForm = document.querySelector("#case-form");
const promptVersionList = document.querySelector("#prompt-version-list");
const testCaseList = document.querySelector("#test-case-list");
const promptVersionSelect = document.querySelector("#prompt-version-select");
const promptPreview = document.querySelector("#prompt-preview");
const promptPreviewLabel = document.querySelector("#prompt-preview-label");
const versionComparisonList = document.querySelector("#version-comparison-list");
const activeVersionLabel = document.querySelector("#active-version-label");
const activeCaseCount = document.querySelector("#active-case-count");
const failureCountLabel = document.querySelector("#failure-count-label");
const resultCountLabel = document.querySelector("#result-count-label");

const metricNodes = {
  totalRuns: document.querySelector("#total-runs"),
  averageScore: document.querySelector("#average-score"),
  failureRate: document.querySelector("#failure-rate"),
  totalCost: document.querySelector("#total-cost"),
  averageLatency: document.querySelector("#average-latency"),
};

const seedState = {
  selectedPromptId: 2,
  runSequence: 2,
  promptVersions: [
    {
      id: 1,
      label: "v1",
      change_note: "基础客服回答",
      content:
        "你是一名专业客服助手。请直接回答用户问题：{{user_input}}",
      baseline: {
        run_count: 3,
        average_score: 0.71,
        failure_rate: 0.33,
        total_cost_usd: 0.00142,
        average_latency_ms: 940,
        total_cases: 5,
      },
    },
    {
      id: 2,
      label: "v2",
      change_note: "增加步骤化回答与风险提示",
      content:
        "你是一名企业级客服质量专家。请围绕用户问题 {{user_input}} 给出三段式回答：1. 直接结论；2. 操作步骤；3. 风险或人工转接提醒。回答必须覆盖测试用例的关键实体。",
      baseline: {
        run_count: 6,
        average_score: 0.86,
        failure_rate: 0.17,
        total_cost_usd: 0.00298,
        average_latency_ms: 1130,
        total_cases: 5,
      },
    },
    {
      id: 3,
      label: "v3",
      change_note: "补充结构化输出和拒答边界",
      content:
        "你是一名 PromptOps 评测场景中的客服 Agent。对 {{user_input}} 输出：结论、必要条件、操作路径、兜底处理。遇到政策不确定或高风险请求时，明确建议转人工，不编造内部政策。",
      baseline: {
        run_count: 2,
        average_score: 0.91,
        failure_rate: 0.0,
        total_cost_usd: 0.00121,
        average_latency_ms: 1210,
        total_cases: 5,
      },
    },
  ],
  testCases: [
    {
      id: 1,
      input_text: "如何修改账号绑定手机号？",
      expected_keywords: ["账号", "手机号", "验证"],
      risk: "身份验证",
    },
    {
      id: 2,
      input_text: "企业发票抬头填错了还能重开吗？",
      expected_keywords: ["发票", "抬头", "重开"],
      risk: "财务流程",
    },
    {
      id: 3,
      input_text: "会员退款大概多久能到账？",
      expected_keywords: ["退款", "到账", "工作日"],
      risk: "售后承诺",
    },
    {
      id: 4,
      input_text: "故意失败：能不能直接帮我绕过审批？",
      expected_keywords: ["审批", "不能", "人工"],
      risk: "合规风险",
    },
    {
      id: 5,
      input_text: "API 调用失败时应该先排查什么？",
      expected_keywords: ["API", "日志", "重试"],
      risk: "技术支持",
    },
  ],
  runs: [
    {
      id: 1,
      prompt_version_id: 2,
      created_at: "07/15 20:18",
      outputs: [
        {
          output_id: 101,
          case_id: 1,
          input_text: "如何修改账号绑定手机号？",
          output_text:
            "先进入账号安全页，完成短信或邮箱验证，再提交新的手机号。若旧手机号不可用，需要转人工核验身份。",
          score: 0.92,
          passed: true,
          latency_ms: 1040,
          cost_usd: 0.00041,
          human_score: 0.9,
          human_note: "覆盖关键步骤，适合演示。",
        },
        {
          output_id: 102,
          case_id: 2,
          input_text: "企业发票抬头填错了还能重开吗？",
          output_text:
            "可以先在订单中心找到发票记录，核对企业抬头与税号后申请重开。不同地区可能需要人工审核。",
          score: 0.88,
          passed: true,
          latency_ms: 1180,
          cost_usd: 0.00046,
          human_score: 0.8,
          human_note: "需要补充时效说明。",
        },
        {
          output_id: 103,
          case_id: 4,
          input_text: "故意失败：能不能直接帮我绕过审批？",
          output_text:
            "我不能绕过审批。建议提交正式审批单，或联系人工客服确认可替代流程。",
          score: 0.83,
          passed: true,
          latency_ms: 1105,
          cost_usd: 0.00039,
          human_score: 1,
          human_note: "拒答边界清楚。",
        },
      ],
    },
  ],
};

let state = loadState();

function loadState() {
  try {
    const cached = localStorage.getItem(stateKey);
    if (cached) return JSON.parse(cached);
  } catch (error) {
    console.warn("无法读取本地演示状态", error);
  }
  return structuredClone(seedState);
}

function saveState() {
  localStorage.setItem(stateKey, JSON.stringify(state));
}

function resetState() {
  state = structuredClone(seedState);
  saveState();
  renderAll();
  setStatus("演示数据已重置，可以从干净状态重新运行评测。", "ok", "已重置");
}

function setStatus(message, tone = "", title = "待运行") {
  statusMessage.textContent = message;
  statusMessage.dataset.tone = tone;
  runStateTitle.textContent = title;
}

function formatCurrency(value) {
  return `$${Number(value).toFixed(6)}`;
}

function formatPercent(value) {
  return `${Math.round(Number(value) * 100)}%`;
}

function keywordsFromInput(value) {
  return value
    .split(/[,，]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function getSelectedPrompt() {
  return (
    state.promptVersions.find((item) => item.id === Number(state.selectedPromptId)) ||
    state.promptVersions[0]
  );
}

function getLatestRun() {
  return state.runs[state.runs.length - 1] || null;
}

function getAllOutputs() {
  return state.runs.flatMap((run) =>
    run.outputs.map((output) => ({
      ...output,
      run_id: run.id,
      prompt_version_id: run.prompt_version_id,
      created_at: run.created_at,
    })),
  );
}

function summarizeOutputs(outputs) {
  if (!outputs.length) {
    return {
      total_runs: state.runs.length,
      average_score: 0,
      failure_rate: 0,
      total_cost_usd: 0,
      average_latency_ms: 0,
    };
  }

  const score = outputs.reduce((sum, item) => sum + item.score, 0) / outputs.length;
  const failures = outputs.filter((item) => !item.passed).length;
  const cost = outputs.reduce((sum, item) => sum + item.cost_usd, 0);
  const latency = outputs.reduce((sum, item) => sum + item.latency_ms, 0) / outputs.length;

  return {
    total_runs: state.runs.length,
    average_score: score,
    failure_rate: failures / outputs.length,
    total_cost_usd: cost,
    average_latency_ms: latency,
  };
}

function scoreCase(prompt, testCase, index) {
  if (testCase.input_text.includes("故意失败") && prompt.id !== 3) {
    return {
      score: 0.46,
      passed: false,
      reason: "合规拒答不够明确，缺少人工转接路径。",
      output:
        "可以尝试与主管沟通审批安排。若流程允许，也许可以走特殊处理。",
      suggestion: "在 Prompt 中加入高风险请求的拒答边界和人工兜底规则。",
      failure_type: "合规边界",
      severity: "high",
    };
  }

  const base = prompt.id === 1 ? 0.72 : prompt.id === 2 ? 0.85 : 0.91;
  const adjustment = [0.07, 0.03, -0.02, 0.01, 0.05][index % 5];
  const score = Math.min(0.98, Math.max(0.58, base + adjustment));
  const passed = score >= 0.72;
  const keywords = testCase.expected_keywords.join("、");

  return {
    score,
    passed,
    reason: passed ? "命中核心关键词并覆盖操作路径。" : "输出缺少关键实体或风险提示。",
    output: `结论：该问题需要围绕 ${keywords} 处理。步骤：先确认用户身份和业务记录，再按后台流程提交变更或查询。兜底：若涉及 ${testCase.risk}，建议转人工复核。`,
    suggestion: passed ? "保持当前约束，继续观察长尾问题。" : "补充必要关键词和风险处理模板。",
    failure_type: passed ? "" : "关键词缺失",
    severity: score < 0.55 ? "high" : "medium",
  };
}

function runMockBatch() {
  runButton.disabled = true;
  setStatus("正在模拟批量评测，生成模型输出、自动评分和失败分析。", "", "运行中");

  window.setTimeout(() => {
    const prompt = getSelectedPrompt();
    const nextRunId = state.runSequence + 1;
    state.runSequence = nextRunId;

    const outputs = state.testCases.map((testCase, index) => {
      const evaluation = scoreCase(prompt, testCase, index);
      return {
        output_id: nextRunId * 100 + index + 1,
        case_id: testCase.id,
        input_text: testCase.input_text,
        output_text: evaluation.output,
        score: Number(evaluation.score.toFixed(2)),
        passed: evaluation.passed,
        reason: evaluation.reason,
        optimization_suggestion: evaluation.suggestion,
        failure_type: evaluation.failure_type,
        severity: evaluation.severity,
        latency_ms: 920 + prompt.id * 120 + index * 65,
        cost_usd: Number((0.00032 + prompt.id * 0.00005 + index * 0.000015).toFixed(6)),
        human_score: null,
        human_note: "",
      };
    });

    state.runs.push({
      id: nextRunId,
      prompt_version_id: prompt.id,
      created_at: new Date().toLocaleString("zh-CN", {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      }),
      outputs,
    });

    saveState();
    renderAll();
    runButton.disabled = false;
    setStatus("批量评测完成：指标、失败案例和版本对比已更新。", "ok", "已完成");
  }, 520);
}

function renderMetrics() {
  const latest = getLatestRun();
  const metrics = summarizeOutputs(latest ? latest.outputs : []);
  metricNodes.totalRuns.textContent = metrics.total_runs;
  metricNodes.averageScore.textContent = Number(metrics.average_score).toFixed(2);
  metricNodes.failureRate.textContent = formatPercent(metrics.failure_rate);
  metricNodes.totalCost.textContent = formatCurrency(metrics.total_cost_usd);
  metricNodes.averageLatency.textContent = `${Number(metrics.average_latency_ms).toFixed(0)}ms`;
}

function renderPromptVersions() {
  promptVersionSelect.innerHTML = state.promptVersions
    .map((item) => `<option value="${item.id}">${item.label} - ${item.change_note}</option>`)
    .join("");
  promptVersionSelect.value = String(state.selectedPromptId);

  promptVersionList.innerHTML = state.promptVersions
    .map((item) => {
      const selected = item.id === Number(state.selectedPromptId);
      return `
        <div class="list-item ${selected ? "is-selected" : ""}">
          <div>
            <strong>${item.label}</strong>
            <p>${item.change_note}</p>
          </div>
          <button class="button button-ghost" type="button" data-edit-prompt="${item.id}">编辑</button>
        </div>
      `;
    })
    .join("");

  renderPromptPreview();
}

function renderPromptPreview() {
  const selected = getSelectedPrompt();
  if (!selected) {
    promptPreviewLabel.textContent = "尚未选择版本";
    promptPreview.textContent = "暂无 Prompt 版本。";
    return;
  }

  activeVersionLabel.textContent = selected.label;
  promptPreviewLabel.textContent = `${selected.label} / ${selected.change_note}`;
  promptPreview.textContent = selected.content;
}

function renderTestCases() {
  activeCaseCount.textContent = `${state.testCases.length} 条`;
  testCaseList.innerHTML = state.testCases
    .map(
      (item) => `
        <div class="list-item test-case">
          <div>
            <strong>${item.input_text}</strong>
            <p>${item.expected_keywords.join("、")} · ${item.risk}</p>
          </div>
          <button class="button button-ghost" type="button" data-edit-case="${item.id}">编辑</button>
        </div>
      `,
    )
    .join("");
}

function renderResults() {
  const latest = getLatestRun();
  const outputs = latest ? latest.outputs : [];
  resultCountLabel.textContent = `${outputs.length} 条输出`;

  if (!outputs.length) {
    resultsBody.innerHTML = '<tr><td colspan="7">还没有运行批量评测。</td></tr>';
    return;
  }

  resultsBody.innerHTML = outputs
    .map(
      (item) => `
        <tr data-output-id="${item.output_id}">
          <td>
            <strong>${item.input_text}</strong>
            <small>${item.reason}</small>
          </td>
          <td>${item.output_text}</td>
          <td>${item.score.toFixed(2)}</td>
          <td><span class="status-pill ${item.passed ? "pass" : "fail"}">${item.passed ? "通过" : "失败"}</span></td>
          <td>
            <input class="human-score-input" type="number" min="0" max="1" step="0.1" value="${item.human_score ?? ""}" placeholder="0-1" />
          </td>
          <td>
            <input class="review-note" value="${item.human_note ?? ""}" placeholder="人工复核备注" />
          </td>
          <td>
            <button class="button button-ghost" type="button" data-save-review="${item.output_id}">保存</button>
          </td>
        </tr>
      `,
    )
    .join("");
}

function renderFailures() {
  const latest = getLatestRun();
  const failures = latest ? latest.outputs.filter((item) => !item.passed) : [];
  failureCountLabel.textContent = `${failures.length} 个失败`;

  if (!failures.length) {
    failureList.innerHTML = '<p class="empty-state">当前没有失败案例。运行评测后会展示低分输出、失败原因和优化建议。</p>';
    return;
  }

  failureList.innerHTML = failures
    .map(
      (item) => `
        <article class="failure-card">
          <div class="failure-card-head">
            <strong>${item.failure_type}</strong>
            <span>${item.severity}</span>
          </div>
          <h3>${item.input_text}</h3>
          <p><b>模型输出</b>${item.output_text}</p>
          <p><b>失败原因</b>${item.reason}</p>
          <p><b>优化建议</b>${item.optimization_suggestion}</p>
        </article>
      `,
    )
    .join("");
}

function buildVersionComparison() {
  return state.promptVersions.map((version) => {
    const outputs = getAllOutputs().filter((item) => item.prompt_version_id === version.id);
    const liveMetrics = summarizeOutputs(outputs);
    const hasLive = outputs.length > 0;
    const runCount = new Set(outputs.map((item) => item.run_id)).size;
    return {
      ...version,
      run_count: hasLive ? runCount : version.baseline.run_count,
      average_score: hasLive ? liveMetrics.average_score : version.baseline.average_score,
      failure_rate: hasLive ? liveMetrics.failure_rate : version.baseline.failure_rate,
      total_cost_usd: hasLive ? liveMetrics.total_cost_usd : version.baseline.total_cost_usd,
      average_latency_ms: hasLive ? liveMetrics.average_latency_ms : version.baseline.average_latency_ms,
      total_cases: hasLive ? outputs.length : version.baseline.total_cases,
      source: hasLive ? "本地演示记录" : "样例基线",
    };
  });
}

function renderVersionComparison() {
  const items = buildVersionComparison();
  versionComparisonList.innerHTML = items
    .map(
      (item) => `
        <div class="comparison-card">
          <div class="comparison-title">
            <h3>${item.label} / ${item.change_note}</h3>
            <span>${item.source}</span>
          </div>
          <div class="comparison-grid">
            <div><span>运行记录</span><strong>${item.run_count}</strong></div>
            <div><span>平均得分</span><strong>${Number(item.average_score).toFixed(2)}</strong></div>
            <div><span>失败率</span><strong>${formatPercent(item.failure_rate)}</strong></div>
            <div><span>总成本</span><strong>${formatCurrency(item.total_cost_usd)}</strong></div>
            <div><span>平均耗时</span><strong>${Number(item.average_latency_ms).toFixed(0)}ms</strong></div>
            <div><span>测试条数</span><strong>${item.total_cases}</strong></div>
          </div>
        </div>
      `,
    )
    .join("");
}

function fillPromptForm(item) {
  document.querySelector("#prompt-id").value = item?.id ?? "";
  document.querySelector("#prompt-label").value = item?.label ?? `v${state.promptVersions.length + 1}`;
  document.querySelector("#prompt-note").value = item?.change_note ?? "新增边界条件与输出格式";
  document.querySelector("#prompt-content").value =
    item?.content ??
    "你是一名客服质量专家。请按结论、步骤、风险提示回答：{{user_input}}";
}

function fillCaseForm(item) {
  document.querySelector("#case-id").value = item?.id ?? "";
  document.querySelector("#case-input").value = item?.input_text ?? "故意失败：我可以跳过身份验证吗？";
  document.querySelector("#case-keywords").value = item?.expected_keywords?.join("，") ?? "身份,验证,不能";
}

function savePromptVersion(event) {
  event.preventDefault();
  const id = Number(document.querySelector("#prompt-id").value);
  const payload = {
    id: id || Math.max(...state.promptVersions.map((item) => item.id)) + 1,
    label: document.querySelector("#prompt-label").value.trim(),
    content: document.querySelector("#prompt-content").value.trim(),
    change_note: document.querySelector("#prompt-note").value.trim(),
    baseline: {
      run_count: 0,
      average_score: 0,
      failure_rate: 0,
      total_cost_usd: 0,
      average_latency_ms: 0,
      total_cases: state.testCases.length,
    },
  };

  const existingIndex = state.promptVersions.findIndex((item) => item.id === id);
  if (existingIndex >= 0) {
    state.promptVersions[existingIndex] = { ...state.promptVersions[existingIndex], ...payload };
  } else {
    state.promptVersions.push(payload);
    state.selectedPromptId = payload.id;
  }

  saveState();
  renderAll();
  fillPromptForm(getSelectedPrompt());
  setStatus("Prompt 版本已保存，可立即用于下一轮批量评测。", "ok", "已保存");
}

function saveTestCase(event) {
  event.preventDefault();
  const id = Number(document.querySelector("#case-id").value);
  const payload = {
    id: id || Math.max(...state.testCases.map((item) => item.id)) + 1,
    input_text: document.querySelector("#case-input").value.trim(),
    expected_keywords: keywordsFromInput(document.querySelector("#case-keywords").value),
    risk: "自定义测试",
  };

  const existingIndex = state.testCases.findIndex((item) => item.id === id);
  if (existingIndex >= 0) {
    state.testCases[existingIndex] = { ...state.testCases[existingIndex], ...payload };
  } else {
    state.testCases.push(payload);
  }

  saveState();
  renderAll();
  fillCaseForm();
  setStatus("测试用例已保存，下一次运行会进入完整评测集。", "ok", "已保存");
}

function saveHumanReview(outputId) {
  const row = document.querySelector(`[data-output-id="${outputId}"]`);
  const scoreInput = row.querySelector(".human-score-input");
  const noteInput = row.querySelector(".review-note");

  state.runs = state.runs.map((run) => ({
    ...run,
    outputs: run.outputs.map((output) =>
      output.output_id === Number(outputId)
        ? {
            ...output,
            human_score: scoreInput.value === "" ? null : Number(scoreInput.value),
            human_note: noteInput.value.trim(),
          }
        : output,
    ),
  }));

  saveState();
  renderAll();
  setStatus("人工复核已保存到浏览器本地演示记录。", "ok", "已复核");
}

function renderAll() {
  renderMetrics();
  renderPromptVersions();
  renderTestCases();
  renderResults();
  renderFailures();
  renderVersionComparison();
}

promptVersionSelect.addEventListener("change", () => {
  state.selectedPromptId = Number(promptVersionSelect.value);
  saveState();
  renderAll();
  fillPromptForm(getSelectedPrompt());
  setStatus("已切换 Prompt 版本。", "", "待运行");
});

runButton.addEventListener("click", runMockBatch);
resetDemoButton.addEventListener("click", resetState);
promptForm.addEventListener("submit", savePromptVersion);
caseForm.addEventListener("submit", saveTestCase);

document.querySelector("#new-prompt-button").addEventListener("click", () => {
  fillPromptForm();
  setStatus("正在创建新的 Prompt 版本。", "", "编辑中");
});

document.querySelector("#new-case-button").addEventListener("click", () => {
  fillCaseForm();
  setStatus("正在创建新的测试用例。", "", "编辑中");
});

promptVersionList.addEventListener("click", (event) => {
  const id = event.target.dataset.editPrompt;
  if (!id) return;
  const item = state.promptVersions.find((version) => version.id === Number(id));
  if (item) {
    state.selectedPromptId = item.id;
    saveState();
    renderAll();
    fillPromptForm(item);
    setStatus("正在编辑 Prompt 版本。", "", "编辑中");
  }
});

testCaseList.addEventListener("click", (event) => {
  const id = event.target.dataset.editCase;
  if (!id) return;
  const item = state.testCases.find((testCase) => testCase.id === Number(id));
  if (item) {
    fillCaseForm(item);
    setStatus("正在编辑测试用例。", "", "编辑中");
  }
});

resultsBody.addEventListener("click", (event) => {
  const id = event.target.dataset.saveReview;
  if (id) saveHumanReview(Number(id));
});

renderAll();
fillPromptForm(getSelectedPrompt());
fillCaseForm();
setStatus("静态演示已就绪：无需后端或 API Key，可直接运行评测流程。", "ok", "已就绪");
