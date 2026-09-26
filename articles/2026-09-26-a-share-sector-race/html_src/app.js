(() => {
  "use strict";

  const DATA = JSON.parse(document.getElementById("race-data").textContent);
  const axisFollow = DATA.axisFollow === true;
  const $ = (id) => document.getElementById(id);
  const COLORS = DATA.colors;
  const DAY_MS = 230;
  const state = { modeIndex: 0, position: 0, playing: false, speed: .75, lastTime: 0, frame: 0, frameMs: 16, axis: null, lineAxis: null };
  const lineCanvas = $("line-chart");
  const raceCanvas = $("race-chart");
  const sizes = new Map();
  const seriesCount = DATA.boards.length;

  for (const mode of DATA.modes) {
    mode.rankings = mode.dates.map((_, day) => {
      const sorted = Array.from({ length: seriesCount }, (_, i) => i);
      sorted.sort((a, b) => {
        const va = mode.series[a][day], vb = mode.series[b][day];
        if (va === null) return vb === null ? a - b : 1;
        if (vb === null) return -1;
        return vb - va || a - b;
      });
      const rank = new Array(seriesCount);
      sorted.forEach((index, place) => { rank[index] = place; });
      return rank;
    });
    const finite = mode.series.flat().filter((value) => value !== null);
    const min = Math.min(0, ...finite), max = Math.max(0, ...finite);
    const pad = Math.max((max - min) * .07, 4);
    mode.lineDomain = [min - pad, max + pad];
    mode.prefixMin = [];
    mode.prefixMax = [];
    let seenMin = 0, seenMax = 0;
    for (let day = 0; day < mode.dates.length; day++) {
      for (const series of mode.series) {
        const value = series[day];
        if (value !== null) { seenMin = Math.min(seenMin, value); seenMax = Math.max(seenMax, value); }
      }
      mode.prefixMin.push(seenMin);
      mode.prefixMax.push(seenMax);
    }
  }

  const tabs = $("mode-tabs");
  DATA.modes.forEach((mode, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "mode-tab";
    button.id = `mode-tab-${index}`;
    button.role = "tab";
    button.textContent = mode.label;
    button.setAttribute("aria-selected", String(index === 0));
    button.addEventListener("click", () => chooseMode(index));
    tabs.appendChild(button);
  });
  $("as-of").textContent = DATA.asOf;

  function currentMode() { return DATA.modes[state.modeIndex]; }
  function clamp(value, lo, hi) { return Math.max(lo, Math.min(hi, value)); }
  function ease(value) { return value * value * (3 - 2 * value); }
  function percent(value) { return `${value >= 0 ? "+" : ""}${value.toFixed(1)}%`; }

  function monotoneSlope(previous, current, next) {
    const incoming = current - previous;
    const outgoing = next - current;
    if (incoming * outgoing <= 0) return 0;
    return 2 * incoming * outgoing / (incoming + outgoing);
  }

  function smoothValue(previous, start, end, next, t) {
    const delta = end - start;
    const startSlope = previous === null ? delta : monotoneSlope(previous, start, end);
    const endSlope = next === null ? delta : monotoneSlope(start, end, next);
    const t2 = t * t, t3 = t2 * t;
    return (2 * t3 - 3 * t2 + 1) * start + (t3 - 2 * t2 + t) * startSlope
      + (-2 * t3 + 3 * t2) * end + (t3 - t2) * endSlope;
  }

  function interpolated() {
    const mode = currentMode();
    const before = Math.floor(state.position);
    const after = Math.min(mode.dates.length - 1, before + 1);
    const t = state.position - before;
    const entries = new Array(seriesCount);
    for (let i = 0; i < seriesCount; i++) {
      const a = mode.series[i][before], b = mode.series[i][after];
      let value = 0, alpha = 0;
      if (a !== null && b !== null) {
        const previous = before > 0 ? mode.series[i][before - 1] : null;
        const next = after < mode.dates.length - 1 ? mode.series[i][after + 1] : null;
        value = smoothValue(previous, a, b, next, t);
        alpha = 1;
      }
      else if (a !== null) { value = a; alpha = 1 - t; }
      else if (b !== null) { value = b; alpha = ease(t); }
      const rankA = mode.rankings[before][i], rankB = mode.rankings[after][i];
      const rankPrevious = before > 0 ? mode.rankings[before - 1][i] : null;
      const rankNext = after < mode.dates.length - 1 ? mode.rankings[after + 1][i] : null;
      entries[i] = {
        i, value, alpha,
        rank: smoothValue(rankPrevious, rankA, rankB, rankNext, t),
      };
    }
    return { before, after, t, entries };
  }

  function setPlaying(playing) {
    state.playing = playing;
    state.lastTime = 0;
    const button = $("play-button");
    button.innerHTML = playing ? "Ⅱ <span>暂停</span>" : "▶ <span>播放</span>";
    button.setAttribute("aria-label", playing ? "暂停动画" : "播放动画");
    if (playing) state.frame = requestAnimationFrame(tick);
    else cancelAnimationFrame(state.frame);
  }

  function tick(now) {
    if (!state.playing) return;
    if (state.lastTime) {
      const elapsed = Math.min(now - state.lastTime, 64);
      state.frameMs = elapsed;
      state.position = Math.min(currentMode().dates.length - 1, state.position + elapsed / DAY_MS * state.speed);
      render();
    }
    state.lastTime = now;
    if (state.position >= currentMode().dates.length - 1) {
      setPlaying(false);
      state.axis = null;
      state.lineAxis = null;
      render();
    }
    else state.frame = requestAnimationFrame(tick);
  }

  function chooseMode(index) {
    setPlaying(false);
    state.modeIndex = index;
    state.axis = null;
    state.lineAxis = null;
    const mode = currentMode();
    state.position = mode.dates.length - 1;
    for (const tab of tabs.children) tab.setAttribute("aria-selected", String(tab.id === `mode-tab-${index}`));
    $("timeline").max = String(mode.dates.length - 1);
    $("timeline-start").textContent = mode.dates[0];
    $("timeline-end").textContent = mode.dates.at(-1);
    $("day-count").textContent = `${mode.dates.length} 个`;
    $("mode-kicker").textContent = mode.id === "20d" ? "滑动窗口 · 最近 20 个交易日" : "固定起点 · 累计涨跌幅";
    $("line-title").textContent = mode.id === "20d" ? "滚动 20 日收益的历史曲线" : "板块累计涨跌幅曲线";
    $("race-title").textContent = mode.id === "20d" ? "当前 20 日涨跌幅排名" : "当前累计涨跌幅排名";
    render();
  }

  $("play-button").addEventListener("click", () => {
    if (state.playing) {
      setPlaying(false);
      state.position = Math.round(state.position);
      state.axis = null;
      state.lineAxis = null;
      render();
      return;
    }
    if (state.position >= currentMode().dates.length - 1) { state.position = 0; state.axis = null; state.lineAxis = null; }
    setPlaying(true);
    render();
  });
  $("reset-button").addEventListener("click", () => {
    setPlaying(false);
    state.position = 0;
    state.axis = null;
    state.lineAxis = null;
    render();
  });
  $("timeline").addEventListener("input", (event) => {
    setPlaying(false);
    state.position = Number(event.target.value);
    state.axis = null;
    state.lineAxis = null;
    render();
  });
  $("speed").addEventListener("change", (event) => { state.speed = Number(event.target.value); });

  function fitCanvas(canvas) {
    const rect = canvas.getBoundingClientRect();
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.max(1, Math.round(rect.width * ratio));
    canvas.height = Math.max(1, Math.round(rect.height * ratio));
    sizes.set(canvas, { width: rect.width, height: rect.height, ratio });
  }

  function context(canvas) {
    const size = sizes.get(canvas);
    if (!size) return null;
    const ctx = canvas.getContext("2d");
    ctx.setTransform(size.ratio, 0, 0, size.ratio, 0, 0);
    ctx.clearRect(0, 0, size.width, size.height);
    return { ctx, ...size };
  }

  function drawLine(snapshot) {
    const target = context(lineCanvas);
    if (!target) return;
    const { ctx, width: w, height: h } = target;
    const mode = currentMode();
    const compact = w < 520;
    const left = compact ? 39 : 53, right = 13, top = 15, bottom = 36;
    const plotW = w - left - right, plotH = h - top - bottom;
    let [lo, hi] = mode.lineDomain;
    const progress = snapshot.before + snapshot.t;
    let xMax = mode.dates.length - 1;
    if (axisFollow) {
      const visible = snapshot.entries.filter((entry) => entry.alpha > .001);
      const seenLo = Math.min(mode.prefixMin[snapshot.before], 0, ...visible.map((entry) => entry.value));
      const seenHi = Math.max(mode.prefixMax[snapshot.before], 0, ...visible.map((entry) => entry.value));
      const pad = Math.max((seenHi - seenLo) * .07, 4);
      const target = { lo: seenLo - pad, hi: seenHi + pad };
      if (state.playing && state.lineAxis) {
        const blend = 1 - Math.exp(-state.frameMs / 270);
        state.lineAxis.lo = Math.min(state.lineAxis.lo + (target.lo - state.lineAxis.lo) * blend, seenLo - pad * .2);
        state.lineAxis.hi = Math.max(state.lineAxis.hi + (target.hi - state.lineAxis.hi) * blend, seenHi + pad * .2);
      } else state.lineAxis = target;
      ({ lo, hi } = state.lineAxis);
      xMax = Math.min(mode.dates.length - 1, Math.max(10, progress));
    }
    const x = (index) => left + plotW * index / Math.max(1, xMax);
    const y = (value) => top + plotH * (hi - value) / (hi - lo);
    ctx.font = `${compact ? 10 : 11}px Microsoft YaHei, Arial`;
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (let tick = 0; tick <= 5; tick++) {
      const value = lo + (hi - lo) * tick / 5;
      const yy = y(value);
      ctx.strokeStyle = "#e7ebe9";
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(left, yy); ctx.lineTo(w - right, yy); ctx.stroke();
      ctx.fillStyle = "#879195";
      ctx.fillText(`${value.toFixed(0)}%`, left - 7, yy);
    }
    if (lo < 0 && hi > 0) {
      ctx.strokeStyle = "#89969a"; ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.moveTo(left, y(0)); ctx.lineTo(w - right, y(0)); ctx.stroke();
    }
    ctx.fillStyle = "#819093";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    const tickMax = axisFollow ? Math.min(mode.dates.length - 1, Math.max(10, Math.floor(progress))) : mode.dates.length - 1;
    for (let tick = 0; tick <= 5; tick++) {
      const index = Math.round(tickMax * tick / 5);
      const label = axisFollow && xMax < 120 ? mode.dates[index].slice(5) : mode.dates[index].slice(2, 7);
      const halfLabel = ctx.measureText(label).width / 2;
      ctx.fillText(label, clamp(x(index), left + halfLabel, w - right - halfLabel), h - bottom + 11);
    }
    const cursorX = x(snapshot.before + snapshot.t);
    ctx.strokeStyle = "#9da9aa"; ctx.globalAlpha = .47; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(cursorX, top); ctx.lineTo(cursorX, top + plotH); ctx.stroke();
    ctx.globalAlpha = 1;
    const strength = (index) => clamp((7 - snapshot.entries[index].rank) / 4, 0, 1);
    const order = Array.from({ length: seriesCount }, (_, i) => i).sort((a, b) => strength(a) - strength(b));
    for (const i of order) {
      const series = mode.series[i];
      ctx.beginPath();
      let started = false;
      for (let day = 0; day <= snapshot.before; day++) {
        const value = series[day];
        if (value === null) { started = false; continue; }
        if (!started) { ctx.moveTo(x(day), y(value)); started = true; }
        else ctx.lineTo(x(day), y(value));
      }
      if (snapshot.after > snapshot.before && series[snapshot.after] !== null) {
        const entry = snapshot.entries[i];
        if (!started) ctx.moveTo(x(snapshot.before + snapshot.t), y(entry.value));
        else ctx.lineTo(x(snapshot.before + snapshot.t), y(entry.value));
      }
      ctx.strokeStyle = COLORS[i];
      const emphasis = strength(i);
      ctx.globalAlpha = (.17 + .75 * emphasis) * snapshot.entries[i].alpha;
      ctx.lineWidth = (compact ? .9 : 1) + (compact ? 1 : 1.35) * emphasis;
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
    for (const entry of snapshot.entries) {
      if (entry.rank >= 3 || entry.alpha < .95) continue;
      const value = entry.value;
      const xx = x(snapshot.before + snapshot.t), yy = y(value);
      ctx.beginPath(); ctx.arc(xx, yy, compact ? 3 : 4, 0, Math.PI * 2);
      ctx.fillStyle = COLORS[entry.i]; ctx.fill();
      ctx.strokeStyle = "#ffffff"; ctx.lineWidth = 1.5; ctx.stroke();
    }
    ctx.strokeStyle = "#e0e7e5";
    ctx.strokeRect(left, top, plotW, plotH);
  }

  function drawRace(snapshot) {
    const target = context(raceCanvas);
    if (!target) return;
    const { ctx, width: w, height: h } = target;
    const compact = w < 520;
    const left = compact ? 81 : Math.max(135, Math.min(172, w * .155));
    const right = compact ? 48 : 66;
    const top = 47, bottom = 13;
    const plotW = w - left - right;
    const rowH = (h - top - bottom) / seriesCount;
    const visible = snapshot.entries.filter((entry) => entry.alpha > .001);
    const min = Math.min(0, ...visible.map((entry) => entry.value));
    const max = Math.max(0, ...visible.map((entry) => entry.value));
    const pad = Math.max((max - min) * .15, .7);
    const currentLo = min - pad, currentHi = max + pad;
    if (state.playing) {
      let futureMin = min, futureMax = max;
      const last = Math.min(currentMode().dates.length - 1, Math.ceil(state.position) + 2);
      for (let day = Math.ceil(state.position); day <= last; day++) {
        for (const series of currentMode().series) {
          const value = series[day];
          if (value !== null) { futureMin = Math.min(futureMin, value); futureMax = Math.max(futureMax, value); }
        }
      }
      const futurePad = Math.max((futureMax - futureMin) * .15, .7);
      const targetLo = futureMin - futurePad, targetHi = futureMax + futurePad;
      if (!state.axis) state.axis = { lo: targetLo, hi: targetHi };
      const smoothing = 1 - Math.exp(-state.frameMs / 270);
      state.axis.lo += (targetLo - state.axis.lo) * smoothing;
      state.axis.hi += (targetHi - state.axis.hi) * smoothing;
      state.axis.lo = Math.min(state.axis.lo, currentLo);
      state.axis.hi = Math.max(state.axis.hi, currentHi);
    } else state.axis = { lo: currentLo, hi: currentHi };
    const { lo, hi } = state.axis;
    const x = (value) => left + plotW * (value - lo) / (hi - lo);
    const zero = x(0);
    for (let rank = 0; rank < seriesCount; rank++) {
      if (rank % 2 === 1) {
        ctx.fillStyle = "#f7f9f8";
        ctx.fillRect(left, top + rank * rowH, plotW, rowH);
      }
    }
    ctx.font = `${compact ? 10 : 11}px Microsoft YaHei, Arial`;
    ctx.textAlign = "center";
    ctx.textBaseline = "bottom";
    for (let tick = 0; tick <= 5; tick++) {
      const value = lo + (hi - lo) * tick / 5;
      const xx = x(value);
      ctx.strokeStyle = "#e5eae8"; ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);
      ctx.beginPath(); ctx.moveTo(xx, top); ctx.lineTo(xx, h - bottom); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = "#819093";
      ctx.fillText(`${value.toFixed(Math.abs(hi - lo) < 20 ? 1 : 0)}%`, xx, 31);
    }
    ctx.strokeStyle = "#778587"; ctx.lineWidth = 1.25;
    ctx.beginPath(); ctx.moveTo(zero, top); ctx.lineTo(zero, h - bottom); ctx.stroke();
    const entries = [...visible].sort((a, b) => b.rank - a.rank);
    for (const entry of entries) {
      const yy = top + (entry.rank + .5) * rowH;
      const end = x(entry.value);
      const barLeft = Math.min(zero, end), barW = Math.abs(zero - end);
      const barH = Math.min(rowH * .68, 24);
      const prominence = clamp((5 - entry.rank) / 5, 0, 1);
      ctx.globalAlpha = entry.alpha * (.77 + .23 * prominence) * (entry.value < 0 ? .72 : 1);
      ctx.fillStyle = COLORS[entry.i];
      ctx.fillRect(barLeft, yy - barH / 2, barW, barH);
      ctx.globalAlpha = entry.alpha;
      ctx.fillStyle = "#293b42";
      ctx.font = `${compact ? 11 : 13}px Microsoft YaHei, Arial`;
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      ctx.fillText(DATA.boards[entry.i].name, left - (compact ? 6 : 13), yy);
      ctx.font = `${compact ? 10 : 12}px Microsoft YaHei, Arial`;
      if (compact) {
        ctx.textAlign = "right";
        ctx.fillStyle = "#42525a";
        ctx.fillText(percent(entry.value), w - 3, yy);
      } else if (entry.value >= 0) {
        const inside = end > w - right - (compact ? 33 : 45) && barW > (compact ? 38 : 50);
        ctx.textAlign = inside ? "right" : "left";
        ctx.fillStyle = inside ? "#26343b" : "#42525a";
        ctx.fillText(percent(entry.value), end + (inside ? -5 : 5), yy);
      } else {
        const inside = compact ? barW > 34 : (end < left + 55 && barW > 65);
        ctx.textAlign = inside ? "left" : "right";
        ctx.fillStyle = inside ? "#26343b" : "#42525a";
        ctx.fillText(percent(entry.value), end + (inside ? 5 : -5), yy);
      }
    }
    ctx.globalAlpha = 1;
  }

  function render() {
    const mode = currentMode();
    const snapshot = interpolated();
    const transitioning = snapshot.after > snapshot.before && snapshot.t > .01 && snapshot.t < .99;
    const day = transitioning ? snapshot.before : Math.round(state.position);
    const ranked = snapshot.entries.filter((entry) => entry.alpha > .5).sort((a, b) => b.value - a.value);
    const leader = ranked[0];
    $("current-date").textContent = mode.dates[day];
    $("current-window").textContent = transitioning
      ? `过渡至 ${mode.dates[snapshot.after]} · 数值平滑演示`
      : (mode.windowStarts ? `当前窗口 ${mode.windowStarts[day]} 至 ${mode.dates[day]}` : "");
    $("leader-name").textContent = leader ? DATA.boards[leader.i].name : "—";
    $("leader-value").textContent = leader ? percent(leader.value) : "—";
    $("timeline").value = String(day);
    $("timeline").style.setProperty("--progress", `${100 * day / Math.max(1, mode.dates.length - 1)}%`);
    drawLine(snapshot);
    drawRace(snapshot);
  }

  const observer = new ResizeObserver(() => {
    fitCanvas(lineCanvas);
    fitCanvas(raceCanvas);
    render();
  });
  observer.observe(lineCanvas);
  observer.observe(raceCanvas);
  fitCanvas(lineCanvas);
  fitCanvas(raceCanvas);
  chooseMode(0);
})();
