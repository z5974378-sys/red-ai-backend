const API_BASE = "";

const fields = {
  positioning: document.querySelector("#positioning"),
  audience: document.querySelector("#audience"),
  savedTitles: document.querySelector("#savedTitles"),
  comments: document.querySelector("#comments"),
  competitors: document.querySelector("#competitors"),
  topicCount: document.querySelector("#topicCount"),
  riskLevel: document.querySelector("#riskLevel"),
  titleStyle: document.querySelector("#titleStyle"),
  noteContent: document.querySelector("#noteContent"),
};

const state = {
  topics: [],
  selectedIndex: -1,
  sessionId: null,
};

const storageKey = "red-ai-topic-bank-v2";

const sensitiveWords = ["医疗", "医美", "减肥", "理财", "投资", "保险", "法律", "药", "疗效", "治愈", "收益", "贷款", "最", "第一", "保证", "100%", "永久", "无效退款"];

// ── API helpers ───────────────────────────────────────────────────────────────

async function apiFetch(path, body) {
  const res = await fetch(API_BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "请求失败");
  }
  return res.json();
}

async function apiPatch(path, body) {
  const res = await fetch(API_BASE + path, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "请求失败");
  }
  return res.json();
}

// ── 核心功能 ──────────────────────────────────────────────────────────────────

async function generateTopics() {
  const inputs = readInputs();
  state.topics = [];
  state.selectedIndex = -1;
  renderTopics();
  hideEditor();
  setButtonLoading("generateBtn", true, "生成中…");

  try {
    const data = await apiFetch("/api/generate", {
      session_id: state.sessionId,
      positioning: inputs.positioning,
      audience: inputs.audience,
      saved_titles: inputs.savedTitles,
      comments: inputs.comments,
      competitors: inputs.competitors,
      topic_count: Number(inputs.topicCount) || 12,
      risk_level: inputs.riskLevel,
      title_style: inputs.titleStyle,
    });

    state.topics = data.topics || [];
    renderTopics();
    persistLocal();
    flashStatus("生成完成");
  } catch (err) {
    flashStatus("生成失败：" + err.message);
  } finally {
    setButtonLoading("generateBtn", false, "生成选题库");
  }
}

async function analyzeMaterials() {
  setButtonLoading("analyzeBtn", true, "分析中…");
  try {
    const res = await apiFetch("/api/analyze", {
      note_content: fields.noteContent.value.trim(),
      note_links: [],
      image_ids: [],
      title_style: fields.titleStyle.value,
      existing_fields: {
        positioning: fields.positioning.value,
        audience: fields.audience.value,
        saved_titles: fields.savedTitles.value,
        comments: fields.comments.value,
        competitors: fields.competitors.value,
      },
    });

    mergeField("positioning", res.positioning);
    mergeField("audience", res.audience);
    mergeField("savedTitles", res.saved_titles);
    mergeField("comments", res.comments);
    mergeField("competitors", res.competitors);
    flashStatus("已分析");
    persistLocal();
  } catch (err) {
    flashStatus("分析失败：" + err.message);
  } finally {
    setButtonLoading("analyzeBtn", false, "分析并填充左侧资料");
  }
}

async function rewriteSelected(tone) {
  if (state.selectedIndex < 0) return;
  const topic = state.topics[state.selectedIndex];
  const cover = document.querySelector("#coverEditor");
  const script = document.querySelector("#scriptEditor");

  try {
    const res = await apiFetch("/api/rewrite", {
      cover: cover.value,
      script: script.value,
      tone,
      topic_name: topic?.topic || "",
      positioning: fields.positioning.value,
    });
    cover.value = res.cover;
    script.value = res.script;
    flashStatus("已润色");
  } catch (err) {
    flashStatus("润色失败：" + err.message);
  }
}

async function localRiskCheck() {
  const text = document.querySelector("#checkText").value;
  const result = document.querySelector("#riskResult");

  if (!text.trim()) {
    result.textContent = "请先粘贴要检测的文案";
    result.className = "risk-result warning";
    return;
  }

  try {
    const res = await apiFetch("/api/compliance", { text });
    result.textContent = res.summary;
    result.className = `risk-result ${res.status === "ok" ? "ok" : "warning"}`;
  } catch (_) {
    // 降级到本地检测
    const hits = sensitiveWords.filter((word) => text.includes(word));
    if (!hits.length) {
      result.textContent = "本地词库未发现明显高风险词，发布前仍建议使用下方网站复查。";
      result.className = "risk-result ok";
    } else {
      result.textContent = `发现需复核词：${hits.join("、")}。建议弱化绝对化、功效化和收益承诺表达。`;
      result.className = "risk-result warning";
    }
  }
}

// ── session 持久化 ─────────────────────────────────────────────────────────────

async function persistToBackend() {
  if (!state.sessionId) return;
  try {
    await apiPatch(`/api/sessions/${state.sessionId}`, {
      positioning: fields.positioning.value,
      audience: fields.audience.value,
      saved_titles: fields.savedTitles.value,
      comments: fields.comments.value,
      competitors: fields.competitors.value,
      note_content: fields.noteContent.value,
      topic_count: Number(fields.topicCount.value) || 12,
      risk_level: fields.riskLevel.value,
      title_style: fields.titleStyle.value,
    });
  } catch (_) {}
}

function persistLocal() {
  const payload = {
    fields: Object.fromEntries(Object.entries(fields).map(([key, field]) => [key, field.value])),
    topics: state.topics,
    sessionId: state.sessionId,
    selectedIndex: state.selectedIndex,
  };
  localStorage.setItem(storageKey, JSON.stringify(payload));
  flashStatus("已保存");
}

function persist() {
  persistLocal();
  persistToBackend();
}

async function restore() {
  // 先尝试从 localStorage 读取 sessionId
  const raw = localStorage.getItem(storageKey);
  let savedSessionId = null;
  if (raw) {
    try {
      const local = JSON.parse(raw);
      savedSessionId = local.sessionId || null;
    } catch (_) {}
  }

  // 如果有 sessionId，尝试从后端恢复
  if (savedSessionId) {
    try {
      const res = await fetch(API_BASE + `/api/sessions/${savedSessionId}`);
      if (res.ok) {
        const session = await res.json();
        const f = session.fields;
        if (fields.positioning) fields.positioning.value = f.positioning || "";
        if (fields.audience) fields.audience.value = f.audience || "";
        if (fields.savedTitles) fields.savedTitles.value = f.saved_titles || "";
        if (fields.comments) fields.comments.value = f.comments || "";
        if (fields.competitors) fields.competitors.value = f.competitors || "";
        if (fields.noteLinks) fields.noteLinks.value = f.note_links || "";
        if (fields.noteContent) fields.noteContent.value = f.note_content || "";
        if (fields.topicCount) fields.topicCount.value = f.topic_count || 12;
        if (fields.riskLevel) fields.riskLevel.value = f.risk_level || "normal";
        if (fields.titleStyle) fields.titleStyle.value = f.title_style || "bold";

        state.topics = session.topics || [];
        state.sessionId = savedSessionId;

        renderTopics();
        return;
      }
    } catch (_) {}
  }

  // 降级：从 localStorage 恢复
  if (!raw) return;
  try {
    const payload = JSON.parse(raw);
    Object.entries(payload.fields || {}).forEach(([key, value]) => {
      if (fields[key]) fields[key].value = value;
    });
    state.topics = payload.topics || [];
    state.sessionId = payload.sessionId || null;
    state.selectedIndex = Number.isInteger(payload.selectedIndex) ? payload.selectedIndex : -1;

    renderTopics();
    if (state.selectedIndex >= 0 && state.topics[state.selectedIndex]) {
      selectTopic(state.selectedIndex);
    }
  } catch (_) {
    localStorage.removeItem(storageKey);
  }
}

// ── UI 工具函数 ────────────────────────────────────────────────────────────────

function setButtonLoading(id, loading, label) {
  const btn = document.querySelector(`#${id}`);
  if (!btn) return;
  btn.disabled = loading;
  btn.textContent = label;
}

function splitLines(value) {
  return value
    .split(/\n|；|;/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function mergeField(key, value) {
  if (!value || !value.trim()) return;
  const field = fields[key] || (key === "noteContent" ? document.querySelector("#noteContent") : null);
  if (!field) return;
  field.value = field.value.trim() ? `${field.value.trim()}\n${value.trim()}` : value.trim();
}

function readInputs() {
  return Object.fromEntries(Object.entries(fields).map(([key, field]) => [key, field.value.trim()]));
}

function priorityClass(priority) {
  return { 高: "high", 中: "medium", 低: "low" }[priority] || "low";
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => {
    const entities = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
    return entities[char];
  });
}

function dedupeTopics(topics) {
  const seen = new Set();
  return topics.filter((topic) => {
    const key = topic.topic;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

// ── 图片预览渲染 ───────────────────────────────────────────────────────────────

function renderTopics() {
  const filter = document.querySelector("#priorityFilter").value;
  const visible = state.topics
    .map((topic, index) => ({ topic, index }))
    .filter(({ topic }) => filter === "all" || topic.priority === filter);
  const body = document.querySelector("#topicBody");
  const template = document.querySelector("#topicRowTemplate");
  body.innerHTML = "";

  visible.forEach(({ topic, index }) => {
    const row = template.content.firstElementChild.cloneNode(true);
    row.dataset.index = String(index);
    if (index === state.selectedIndex) row.classList.add("selected-row");
    const cells = row.querySelectorAll("td");
    cells[0].innerHTML = `
      <div class="cell-stack">
        <span class="topic-title">${escapeHtml(topic.topic)}</span>
        <span class="tag-row">
          ${topic.series ? '<span class="tag series">可做系列</span>' : ""}
          ${topic.human ? '<span class="tag human">需人工判断</span>' : ""}
        </span>
        <button class="delete-topic-btn" data-index="${index}">删除</button>
      </div>
    `;
    cells[1].textContent = topic.pain;
    cells[2].textContent = topic.angle;
    cells[3].textContent = topic.cover;
    cells[4].textContent = topic.script;
    cells[5].innerHTML = `<span class="priority ${priorityClass(topic.priority)}">${topic.priority}</span>`;
    cells[6].textContent = topic.risk;
    row.addEventListener("click", (e) => {
      if (e.target.closest(".delete-topic-btn")) {
        const idx = Number(e.target.closest(".delete-topic-btn").dataset.index);
        state.topics.splice(idx, 1);
        if (state.selectedIndex === idx) {
          state.selectedIndex = -1;
          hideEditor();
        } else if (state.selectedIndex > idx) {
          state.selectedIndex -= 1;
        }
        renderTopics();
        persistLocal();
        return;
      }
      selectTopic(index);
    });
    body.appendChild(row);
  });

  document.querySelector("#emptyState").hidden = state.topics.length > 0;
  document.querySelector("#tableWrap").hidden = state.topics.length === 0;
  document.querySelector("#totalCount").textContent = state.topics.length;
  document.querySelector("#seriesCount").textContent = state.topics.filter((topic) => topic.series).length;
  document.querySelector("#humanCount").textContent = state.topics.filter((topic) => topic.human).length;
}

function selectTopic(index) {
  state.selectedIndex = index;
  const topic = state.topics[index];
  document.querySelector("#editorPanel").hidden = false;
  document.querySelector("#editorTitle").textContent = topic.topic;
  document.querySelector("#coverEditor").value = topic.cover;
  document.querySelector("#scriptEditor").value = topic.script;
  document.querySelector("#checkText").value = `${topic.topic}\n${topic.cover}\n${topic.script}`;
  renderTopics();
  persistLocal();
}

function hideEditor() {
  document.querySelector("#editorPanel").hidden = true;
  document.querySelector("#coverEditor").value = "";
  document.querySelector("#scriptEditor").value = "";
}

async function saveEdit() {
  if (state.selectedIndex < 0) return;
  const topic = state.topics[state.selectedIndex];
  topic.cover = document.querySelector("#coverEditor").value.trim();
  topic.script = document.querySelector("#scriptEditor").value.trim();
  document.querySelector("#checkText").value = `${topic.topic}\n${topic.cover}\n${topic.script}`;
  renderTopics();
  flashStatus("已更新");
  persistLocal();

  // 同步到后端
  if (state.sessionId && topic.id) {
    try {
      await apiPatch(`/api/sessions/${state.sessionId}/topics/${topic.id}`, {
        cover: topic.cover,
        script: topic.script,
      });
    } catch (_) {}
  }
}

function clearAll() {
  Object.values(fields).forEach((field) => {
    if (field.id === "topicCount") field.value = "12";
    else if (field.id === "riskLevel") field.value = "normal";
    else if (field.id === "titleStyle") field.value = "bold";
    else field.value = "";
  });
  document.querySelector("#riskResult").textContent = "等待检测";
  document.querySelector("#riskResult").className = "risk-result";
  state.topics = [];
  state.selectedIndex = -1;
  renderTopics();
  hideEditor();
  persistLocal();
}

function toTableText(topics) {
  const headers = ["选题", "用户痛点", "标题角度", "首图方案", "正文脚本", "优先级", "风险提醒"];
  const rows = topics.map((topic) => [topic.topic, topic.pain, topic.angle, topic.cover, topic.script, topic.priority, topic.risk]);
  return [headers, ...rows].map((row) => row.join("\t")).join("\n");
}

function downloadCsv() {
  const headers = ["选题", "用户痛点", "标题角度", "首图方案", "正文脚本", "优先级", "风险提醒"];
  const rows = state.topics.map((topic) => [topic.topic, topic.pain, topic.angle, topic.cover, topic.script, topic.priority, topic.risk]);
  const csv = [headers, ...rows]
    .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(","))
    .join("\n");
  const blob = new Blob([`﻿${csv}`], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `red-ai-topic-bank-${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

async function copyTopics() {
  if (!state.topics.length) return;
  await navigator.clipboard.writeText(toTableText(state.topics));
  flashStatus("已复制");
}

let statusTimer;
function flashStatus(text) {
  const status = document.querySelector("#saveStatus");
  status.textContent = text;
  clearTimeout(statusTimer);
  statusTimer = setTimeout(() => {
    status.textContent = "已保存";
  }, 1500);
}

// ── 事件绑定 ──────────────────────────────────────────────────────────────────

document.querySelector("#generateBtn").addEventListener("click", generateTopics);
document.querySelector("#clearBtn").addEventListener("click", clearAll);
document.querySelector("#copyBtn").addEventListener("click", copyTopics);
document.querySelector("#exportBtn").addEventListener("click", downloadCsv);
document.querySelector("#analyzeBtn").addEventListener("click", analyzeMaterials);
document.querySelector("#saveEditBtn").addEventListener("click", saveEdit);
document.querySelector("#localCheckBtn").addEventListener("click", localRiskCheck);
document.querySelector("#priorityFilter").addEventListener("change", renderTopics);
document.querySelectorAll(".rewrite-btn").forEach((button) => {
  button.addEventListener("click", () => rewriteSelected(button.dataset.tone));
});
Object.values(fields).forEach((field) => field.addEventListener("input", persist));

restore();
