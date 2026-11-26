/* Sanjaya Research: Figuring Out, decoded.
   Renders data.json (written by analysis/export_site.py) into the page.
   Plain SVG/HTML, no libraries. Every chart has a legend or direct labels,
   a hover/focus tooltip, and a data table. */
(function () {
  "use strict";

  var SHORT = {
    "Psychology & Self-Growth": "Psychology",
    "Business & Startups": "Business",
    "Health & Fitness": "Health",
    "Money & Investing": "Money",
    "Geopolitics & Defence": "Geopolitics",
    "Entertainment & Celebrities": "Entertainment",
    "Politics & Governance": "Politics",
    "Crime & Dark Side": "Crime",
    "Education & Career": "Education",
    "Spirituality & Mysteries": "Spirituality",
    "History & Culture": "History",
    "Tech & AI": "Tech & AI",
    Sports: "Sports",
    Other: "Other",
  };
  var NS = "http://www.w3.org/2000/svg";
  var root = document.body;
  var css = getComputedStyle(root);
  var token = function (name) {
    return css.getPropertyValue(name).trim();
  };
  var D; // data
  var COLOR = {};

  // ---------- helpers ----------
  function $(id) {
    return document.getElementById(id);
  }
  function el(tag, attrs, parent) {
    var n = document.createElement(tag);
    for (var k in attrs || {}) {
      if (k === "text") n.textContent = attrs[k];
      else if (k === "html") n.innerHTML = attrs[k];
      else n.setAttribute(k, attrs[k]);
    }
    if (parent) parent.appendChild(n);
    return n;
  }
  function svg(tag, attrs, parent) {
    var n = document.createElementNS(NS, tag);
    for (var k in attrs || {}) {
      if (k === "text") n.textContent = attrs[k];
      else n.setAttribute(k, attrs[k]);
    }
    if (parent) parent.appendChild(n);
    return n;
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  var pct = function (x, d) {
    return (100 * x).toFixed(d || 0) + "%";
  };
  var mil = function (v) {
    if (v == null) return "n/a";
    return v >= 1e6 ? (v / 1e6).toFixed(v >= 1e7 ? 0 : 1) + "M" : Math.round(v / 1e3) + "K";
  };
  var short = function (t) {
    return SHORT[t] || t;
  };
  function color(t) {
    return COLOR[t] || token("--other");
  }

  // ---------- tooltip ----------
  var tip = $("tip");
  function showTip(html, x, y) {
    tip.innerHTML = html;
    tip.hidden = false;
    var w = tip.offsetWidth,
      h = tip.offsetHeight;
    var left = x + 16,
      top = y + 16;
    if (left + w > window.innerWidth - 8) left = x - w - 16;
    if (top + h > window.innerHeight - 8) top = y - h - 16;
    tip.style.left = Math.max(8, left) + "px";
    tip.style.top = Math.max(8, top) + "px";
  }
  function hideTip() {
    tip.hidden = true;
  }
  function tipFor(node, htmlFn) {
    node.addEventListener("mousemove", function (e) {
      showTip(htmlFn(), e.clientX, e.clientY);
    });
    node.addEventListener("mouseleave", hideTip);
    node.addEventListener("focus", function () {
      var r = node.getBoundingClientRect();
      showTip(htmlFn(), r.left + r.width / 2, r.bottom);
    });
    node.addEventListener("blur", hideTip);
  }
  function row(sw, label, value) {
    return (
      '<div class="tip-row"><span class="swatch" style="background:' + sw + '"></span><span>' +
      esc(label) + "</span><span>" + value + "</span></div>"
    );
  }

  function table(container, headers, rows) {
    var t = el("table", {}, container);
    var tr = el("tr", {}, el("thead", {}, t));
    headers.forEach(function (h) {
      el("th", { text: h, scope: "col" }, tr);
    });
    var tb = el("tbody", {}, t);
    rows.forEach(function (r) {
      var x = el("tr", {}, tb);
      r.forEach(function (c) {
        el("td", { text: c }, x);
      });
    });
  }

  function hbars(container, items, opts) {
    container.innerHTML = "";
    var max = opts.max || Math.max.apply(null, items.map(function (i) { return i.value; }));
    items.forEach(function (it) {
      var r = el("div", { class: "hbar" + (it.lead ? " is-lead" : "") + (it.muted ? " is-muted" : ""), tabindex: "0" }, container);
      el("span", { class: "hbar-label", text: it.label }, r);
      var fill = el("span", { class: "hbar-fill" }, el("span", { class: "hbar-track" }, r));
      el("span", { class: "hbar-value", text: it.display }, r);
      requestAnimationFrame(function () {
        fill.style.width = Math.max(0.6, (100 * it.value) / max) + "%";
      });
      if (it.tip) tipFor(r, it.tip);
    });
  }

  // ---------- hero ----------
  function renderHero() {
    var c = D.counts;
    var stats = [
      ["Episodes", c.episodes],
      ["Transcripts", c.transcripts],
      ["Guests", c.guests],
      ["Mention links", c.mention_links.toLocaleString("en-IN")],
    ];
    var dl = $("r-stats");
    stats.forEach(function (s) {
      var d = el("div", {}, dl);
      el("dt", { text: s[0] }, d);
      el("dd", { text: s[1] }, d);
    });

    var f = D.forecast;
    var probs = Object.entries(f.topic_probabilities);
    var lead = probs[0];
    $("call-ep").textContent = "FO" + f.next_episode;
    $("dial-pct").textContent = pct(lead[1]);
    $("call-topic").textContent = lead[0];
    var lang = f.p_english >= 0.5 ? "English" : "Hindi";
    var pl = Math.max(f.p_english, 1 - f.p_english);
    $("call-sub").textContent = "Next: " + short(probs[1][0]) + " " + pct(probs[1][1]) + ", " +
      short(probs[2][0]) + " " + pct(probs[2][1]) + " · " + lang + " " + pct(pl);
    var C = 2 * Math.PI * 86;
    requestAnimationFrame(function () {
      $("dial-arc").style.strokeDasharray = C * lead[1] + " " + C;
    });
    $("call-card").setAttribute("aria-label",
      "Forecast for episode " + f.next_episode + ": " + lead[0] + ", " + pct(lead[1]) + " chance.");

    var m = f.backtest["Combined model (signals + trend)"];
    var foot = $("call-foot");
    [[pct(m.top1), "first guess right"], [pct(m.top3), "right in top 3"], [pct(f.language_backtest.model), "language right"]]
      .forEach(function (x) {
        var d = el("div", {}, foot);
        el("b", { text: x[0] }, d);
        el("span", { text: x[1] }, d);
      });
  }

  // ---------- forecast ----------
  function renderForecast() {
    var f = D.forecast;
    var probs = Object.entries(f.topic_probabilities).filter(function (p) { return p[1] >= 0.005; });
    hbars($("chart-forecast"), probs.map(function (p, i) {
      return {
        label: p[0], value: p[1], display: pct(p[1]), lead: i === 0,
        tip: function () { return '<div class="tip-title">' + esc(p[0]) + "</div>" + pct(p[1], 1) + " chance the next episode is on this topic"; },
      };
    }), {});
    table($("t-forecast"), ["Topic", "Probability"], probs.map(function (p) { return [p[0], pct(p[1], 1)]; }));

    var box = $("profiles");
    f.profiles.forEach(function (p, i) {
      var d = el("article", { class: "profile" }, box);
      el("span", { class: "profile-idx", text: "0" + (i + 1) }, d);
      el("h4", { text: p.topic }, d);
      el("span", { class: "profile-p", text: pct(p.p) }, d);
      var guest = p.guest.indexOf("outside") === 0 ? "A guest outside the usual categories" : p.guest.charAt(0).toUpperCase() + p.guest.slice(1);
      el("p", { text: guest + ", in " + p.language + "." }, d);
      var ul = el("ul", { class: "chips", "aria-label": "Likely subjects" }, d);
      p.entities.forEach(function (e) { el("li", { text: e }, ul); });
    });
    el("p", { class: "profiles-note", text: "Likely profiles: the guest type and subjects that go with each topic in recent episodes. Hypotheses from patterns, not inside information." }, box);

    var bt = f.backtest;
    var names = [
      ["Combined model (signals + trend)", "This forecast"],
      ["Always the most common topic", "Most common topic"],
      ["Signals model alone", "Signals alone"],
    ];
    var items = [];
    names.forEach(function (n, i) {
      var r = bt[n[0]];
      items.push({ label: n[1] + " · first guess", value: r.top1, display: pct(r.top1), lead: i === 0 });
    });
    items.push({ label: "Random guess · first guess", value: 1 / 13, display: pct(1 / 13), muted: true });
    names.forEach(function (n, i) {
      var r = bt[n[0]];
      items.push({ label: n[1] + " · top 3", value: r.top3, display: pct(r.top3), lead: i === 0 });
    });
    hbars($("chart-backtest"), items, { max: 0.5 });
    var m = bt["Combined model (signals + trend)"], base = bt["Always the most common topic"];
    $("backtest-note").textContent =
      "Each of the last 120 episodes was predicted using only the episodes before it. The forecast's first guess beats the obvious baseline (" +
      pct(m.top1) + " vs " + pct(base.top1) + "), but its top three is no better than always naming the three most common topics (" +
      pct(m.top3) + " vs " + pct(base.top3) + "). Read it as a ranking, not a call.";

    var ol = $("track");
    D.track.slice().reverse().forEach(function (t) {
      var li = el("li", {}, ol);
      el("span", { class: "track-ep", text: "FO" + t.episode }, li);
      var body = el("div", { class: "track-body" }, li);
      body.innerHTML = "Predicted <b>" + t.predicted.map(short).map(esc).join(", ") + "</b>" +
        (t.actual ? "<br>Actual <b>" + esc(t.actual) + "</b>" : "<br>Waiting for the episode");
      var v = t.actual == null ? ["pending", "Pending"] : t.in_top3 ? ["hit", "In top 3"] : ["miss", "Missed"];
      el("span", { class: "verdict " + v[0], text: v[1] }, li);
    });
  }

  // ---------- findings ----------
  function renderFindings() {
    var r0 = D.river[0], r1 = D.river[D.river.length - 1];
    var lang = D.language;
    var minL = lang.reduce(function (a, b) { return b.english < a.english ? b : a; });
    var lastL = lang[lang.length - 1], firstL = lang[0];
    var mv = {};
    D.made_vs_watched.forEach(function (m) { mv[m.topic] = m; });
    var geo = mv["Geopolitics & Defence"], health = mv["Health & Fitness"];
    var L = D.by_length;
    var m = D.forecast.backtest["Combined model (signals + trend)"];
    var items = [
      ["From business to the mind.",
        "Business was " + pct(r0["Business & Startups"]) + " of the first 40 episodes and is " + pct(r1["Business & Startups"]) +
        " of the last 40. Psychology and self-growth went from " + pct(r0["Psychology & Self-Growth"]) + " to " + pct(r1["Psychology & Self-Growth"]) + "."],
      ["Geopolitics is the under-made hit.",
        geo ? "It is " + pct(geo.episode_share) + " of recent episodes but " + pct(geo.view_share) + " of all views, with a " + mil(geo.median) +
          " median. Three of the eight most-watched episodes ever are geopolitics or defence." : ""],
      ["Health is made most, watched least.",
        health ? "The most frequent recent topic at " + pct(health.episode_share) + " of episodes, it draws " + pct(health.view_share) +
          " of views and a " + mil(health.median) + " median, the lowest of the big topics." : ""],
      ["The language went to Hindi and back.",
        "English-language episodes were " + pct(firstL.english) + " early on, fell to " + pct(minL.english) + " around FO" + minL.episode +
          ", and are " + pct(lastL.english) + " now, as international guests took over. Both languages draw about the same views."],
      ["Longer conversations get watched more.",
        "Episodes over two hours have a " + mil(L[L.length - 1].median) + " median, against " + mil(L[1].median) +
          " for 60 to 90 minutes. Bigger guests tend to get longer conversations, so length is partly a marker of the guest."],
      ["The next topic is only weakly predictable.",
        "The forecast's first guess is right " + pct(m.top1) + " of the time. Most of the choice is the guest's availability, which no public data shows."],
    ];
    var ol = $("findings-list");
    items.forEach(function (it) {
      var li = el("li", {}, ol);
      el("h3", { text: it[0] }, li);
      el("p", { text: it[1] }, li);
    });
    $("findings-lede").textContent =
      "Read across FO" + D.counts.first + " to FO" + D.counts.last + ", the show has quietly reinvented itself: new subjects, a new language, and a gap between what it makes and what its audience watches.";
  }

  // ---------- axes ----------
  function frame(container, h, m) {
    container.innerHTML = "";
    var W = container.clientWidth || 600;
    var H = h || container.clientHeight || 260;
    var s = svg("svg", { viewBox: "0 0 " + W + " " + H, role: "img" }, container);
    return { s: s, W: W, H: H, m: m, iw: W - m.l - m.r, ih: H - m.t - m.b };
  }
  function xTicks(f, x0, x1, xs) {
    var g = svg("g", { class: "axis" }, f.s);
    var step = x1 - x0 > 300 ? 100 : 50;
    for (var v = Math.ceil(x0 / step) * step; v <= x1; v += step) {
      svg("text", { x: xs(v), y: f.H - 6, "text-anchor": "middle", text: "FO" + v }, g);
    }
  }
  function yGrid(f, ys, vals, fmt) {
    var g = svg("g", {}, f.s);
    vals.forEach(function (v) {
      svg("line", { class: v === 0 ? "baseline" : "gridline", x1: f.m.l, x2: f.m.l + f.iw, y1: ys(v), y2: ys(v) }, g);
      svg("text", { class: "ann", x: f.m.l - 8, y: ys(v) + 4, "text-anchor": "end", text: fmt(v) }, g);
    });
  }

  // ---------- topic river (stacked area) ----------
  function renderRiver() {
    var data = D.river, keys = D.focus.concat(["Other"]);
    var box = $("chart-river");
    var f = frame(box, null, { t: 8, r: 12, b: 26, l: 40 });
    var x0 = data[0].episode, x1 = data[data.length - 1].episode;
    var xs = function (v) { return f.m.l + ((v - x0) / (x1 - x0)) * f.iw; };
    var ys = function (v) { return f.m.t + f.ih - v * f.ih; };
    yGrid(f, ys, [0, 0.25, 0.5, 0.75, 1], function (v) { return pct(v); });
    var acc = data.map(function () { return 0; });
    var layers = [];
    keys.forEach(function (k) {
      var lower = acc.slice();
      var upper = data.map(function (d, i) { return (acc[i] += d[k]); });
      layers.push({ key: k, lower: lower, upper: upper });
      var top = data.map(function (d, i) { return xs(d.episode) + "," + ys(upper[i]); });
      var bot = data.map(function (d, i) { return xs(d.episode) + "," + ys(lower[i]); }).reverse();
      svg("path", { d: "M" + top.join("L") + "L" + bot.join("L") + "Z", fill: color(k), opacity: k === "Other" ? 0.9 : 1 }, f.s);
    });
    // 2px surface gaps between layers
    layers.slice(0, -1).forEach(function (l) {
      svg("path", { d: "M" + data.map(function (d, i) { return xs(d.episode) + "," + ys(l.upper[i]); }).join("L"), fill: "none", stroke: token("--surface"), "stroke-width": 2 }, f.s);
    });
    // direct labels where a band is thick enough, at ~88% of the width
    var li = Math.floor(data.length * 0.9), labelled = 0;
    layers.forEach(function (l) {
      var th = l.upper[li] - l.lower[li];
      if (f.iw > 520 && th > 0.085 && labelled < 4 && l.key !== "Other") {
        labelled++;
        svg("text", { class: "direct-label", x: xs(data[li].episode), y: ys((l.upper[li] + l.lower[li]) / 2) + 4, "text-anchor": "middle", text: short(l.key) }, f.s);
      }
    });
    xTicks(f, x0, x1, xs);
    var cross = svg("line", { class: "crosshair", y1: f.m.t, y2: f.m.t + f.ih, opacity: 0 }, f.s);
    var hit = svg("rect", { class: "hit-area", x: f.m.l, y: f.m.t, width: f.iw, height: f.ih, tabindex: 0, "aria-label": "Topic mix over time; use the data table for values" }, f.s);
    function at(clientX) {
      var r = box.getBoundingClientRect();
      var px = ((clientX - r.left) / r.width) * f.W;
      var v = x0 + ((px - f.m.l) / f.iw) * (x1 - x0);
      var i = 0, best = Infinity;
      data.forEach(function (d, k) { var dd = Math.abs(d.episode - v); if (dd < best) { best = dd; i = k; } });
      return i;
    }
    function show(i, cx, cy) {
      var d = data[i];
      cross.setAttribute("x1", xs(d.episode)); cross.setAttribute("x2", xs(d.episode)); cross.setAttribute("opacity", 1);
      var html = '<div class="tip-title">FO' + (d.episode - 39) + "–FO" + d.episode + "</div>";
      keys.slice().reverse().forEach(function (k) { html += row(color(k), short(k), pct(d[k])); });
      showTip(html, cx, cy);
    }
    hit.addEventListener("mousemove", function (e) { show(at(e.clientX), e.clientX, e.clientY); });
    hit.addEventListener("mouseleave", function () { cross.setAttribute("opacity", 0); hideTip(); });
    hit.addEventListener("focus", function () { var r = box.getBoundingClientRect(); show(data.length - 1, r.right - 40, r.top + 20); });
    hit.addEventListener("blur", function () { cross.setAttribute("opacity", 0); hideTip(); });
  }

  function legend(container, keys) {
    container.innerHTML = "";
    keys.forEach(function (k) {
      var s = el("span", { class: "key" }, container);
      el("i", { class: "swatch", style: "background:" + color(k) }, s);
      s.appendChild(document.createTextNode(short(k)));
    });
  }

  // ---------- made vs watched (dumbbell) ----------
  function dumbbell(box, rows, opts) {
    var rh = 34;
    var f = frame(box, rows.length * rh + 30, { t: 6, r: 58, b: 24, l: Math.min(130, (box.clientWidth || 400) * 0.34) });
    var max = opts.max;
    var xs = function (v) { return f.m.l + (v / max) * f.iw; };
    var g = svg("g", {}, f.s);
    opts.ticks.forEach(function (v) {
      svg("line", { class: v === 0 ? "baseline" : "gridline", x1: xs(v), x2: xs(v), y1: f.m.t, y2: f.H - f.m.b }, g);
      svg("text", { class: "ann", x: xs(v), y: f.H - 6, "text-anchor": "middle", text: pct(v) }, g);
    });
    rows.forEach(function (r, i) {
      var y = f.m.t + i * rh + rh / 2;
      var a = xs(r.a), b = xs(r.b);
      svg("text", { class: "ann ann-strong", x: f.m.l - 10, y: y + 4, "text-anchor": "end", text: short(r.label) }, f.s);
      svg("line", { x1: a, x2: b, y1: y, y2: y, stroke: token("--hair-strong").replace(/[\d.]+\)$/, "0.45)"), "stroke-width": 2 }, f.s);
      svg("circle", { cx: a, cy: y, r: 5, fill: token("--surface"), stroke: token("--ivory-soft"), "stroke-width": 2 }, f.s);
      svg("circle", { cx: b, cy: y, r: 5.5, fill: opts.bColor, stroke: token("--surface"), "stroke-width": 2 }, f.s);
      svg("text", { class: "ann ann-strong", x: f.W - 4, y: y + 4, "text-anchor": "end", text: r.note }, f.s);
      var hit = svg("rect", { class: "hit-area", x: 0, y: y - rh / 2, width: f.W, height: rh, tabindex: 0, "aria-label": r.aria }, f.s);
      tipFor(hit, function () { return r.tip; });
    });
  }

  function renderMade() {
    var rows = D.made_vs_watched.slice().sort(function (a, b) {
      return (b.view_share / b.episode_share) - (a.view_share / a.episode_share);
    }).map(function (m) {
      var ratio = m.view_share / m.episode_share;
      return {
        label: m.topic, a: m.episode_share, b: m.view_share, note: ratio.toFixed(1) + "×",
        aria: m.topic + ": " + pct(m.episode_share) + " of episodes, " + pct(m.view_share) + " of views",
        tip: '<div class="tip-title">' + esc(m.topic) + "</div>" +
          row("transparent;box-shadow:inset 0 0 0 2px " + token("--ivory-soft"), "Share of episodes", pct(m.episode_share, 1)) +
          row(token("--accent"), "Share of views", pct(m.view_share, 1)) +
          "<div style='margin-top:.35rem'>" + m.episodes + " episodes · median <b>" + mil(m.median) + "</b> views</div>",
      };
    });
    var max = Math.max.apply(null, rows.map(function (r) { return Math.max(r.a, r.b); }));
    max = Math.ceil(max * 20) / 20;
    var ticks = [0];
    for (var v = 0.05; v <= max + 1e-9; v += 0.05) ticks.push(+v.toFixed(2));
    dumbbell($("chart-made"), rows, { max: max, ticks: ticks, bColor: token("--accent") });
    table($("t-made"), ["Topic", "Episodes", "Share of episodes", "Share of views", "Median views"],
      D.made_vs_watched.map(function (m) { return [m.topic, m.episodes, pct(m.episode_share, 1), pct(m.view_share, 1), mil(m.median)]; }));
  }

  // ---------- language swing (line) ----------
  function renderLang() {
    var data = D.language;
    var box = $("chart-lang");
    var f = frame(box, null, { t: 14, r: 16, b: 26, l: 40 });
    var x0 = data[0].episode, x1 = data[data.length - 1].episode;
    var xs = function (v) { return f.m.l + ((v - x0) / (x1 - x0)) * f.iw; };
    var ys = function (v) { return f.m.t + f.ih - v * f.ih; };
    // shade the Hindi-first stretch (English share under 25%)
    var lo = data.filter(function (d) { return d.english < 0.25; });
    if (lo.length) {
      var a = xs(lo[0].episode), b = xs(lo[lo.length - 1].episode);
      svg("rect", { x: a, y: f.m.t, width: Math.max(2, b - a), height: f.ih, fill: "rgba(243,239,230,0.045)" }, f.s);
      svg("text", { class: "ann", x: (a + b) / 2, y: f.m.t + 12, "text-anchor": "middle", text: "Mostly Hindi" }, f.s);
    }
    yGrid(f, ys, [0, 0.5, 1], function (v) { return pct(v); });
    var pts = data.map(function (d) { return xs(d.episode) + "," + ys(d.english); });
    svg("path", { d: "M" + xs(x0) + "," + ys(0) + "L" + pts.join("L") + "L" + xs(x1) + "," + ys(0) + "Z", fill: "rgba(243,239,230,0.06)" }, f.s);
    svg("path", { d: "M" + pts.join("L"), fill: "none", stroke: token("--ivory"), "stroke-width": 2, "stroke-linejoin": "round" }, f.s);
    var last = data[data.length - 1];
    svg("circle", { cx: xs(last.episode), cy: ys(last.english), r: 4, fill: token("--ivory"), stroke: token("--surface"), "stroke-width": 2 }, f.s);
    svg("text", { class: "ann ann-strong", x: xs(last.episode) - 8, y: ys(last.english) - 10, "text-anchor": "end", text: pct(last.english) + " English now" }, f.s);
    xTicks(f, x0, x1, xs);
    var cross = svg("line", { class: "crosshair", y1: f.m.t, y2: f.m.t + f.ih, opacity: 0 }, f.s);
    var dot = svg("circle", { r: 4, fill: token("--ivory"), opacity: 0 }, f.s);
    var hit = svg("rect", { class: "hit-area", x: f.m.l, y: f.m.t, width: f.iw, height: f.ih }, f.s);
    hit.addEventListener("mousemove", function (e) {
      var r = box.getBoundingClientRect();
      var v = x0 + ((((e.clientX - r.left) / r.width) * f.W - f.m.l) / f.iw) * (x1 - x0);
      var d = data.reduce(function (p, c) { return Math.abs(c.episode - v) < Math.abs(p.episode - v) ? c : p; });
      cross.setAttribute("x1", xs(d.episode)); cross.setAttribute("x2", xs(d.episode)); cross.setAttribute("opacity", 1);
      dot.setAttribute("cx", xs(d.episode)); dot.setAttribute("cy", ys(d.english)); dot.setAttribute("opacity", 1);
      showTip('<div class="tip-title">FO' + (d.episode - 39) + "–FO" + d.episode + "</div><b>" + pct(d.english) + "</b> of these episodes in English", e.clientX, e.clientY);
    });
    hit.addEventListener("mouseleave", function () { cross.setAttribute("opacity", 0); dot.setAttribute("opacity", 0); hideTip(); });
    table($("t-lang"), ["Episodes", "English share"], data.filter(function (_, i) { return i % 5 === 0; }).map(function (d) {
      return ["FO" + (d.episode - 39) + "–" + d.episode, pct(d.english)];
    }));
  }

  function renderLength() {
    var L = D.by_length;
    var max = Math.max.apply(null, L.map(function (l) { return l.median; }));
    hbars($("chart-length"), L.map(function (l) {
      return {
        label: l.length, value: l.median, display: mil(l.median), lead: l.median === max,
        tip: function () { return '<div class="tip-title">' + esc(l.length) + "</div>" + l.episodes + " episodes · median <b>" + mil(l.median) + "</b> views"; },
      };
    }), {});
  }

  // ---------- signals ----------
  function renderStrip() {
    var rec = D.recent;
    var box = $("chart-strip");
    var keys = D.focus.concat(["Other"]);
    legend($("legend-strip"), keys);
    box.innerHTML = "";
    rec.forEach(function (r, i) {
      var b = el("button", {
        class: "strip-cell" + (i === rec.length - 1 ? " is-last" : ""), type: "button", role: "listitem",
        style: "background:" + color(D.focus.indexOf(r.topic) >= 0 ? r.topic : "Other"),
        "aria-label": "FO" + r.episode + ", " + r.topic + ": " + r.title,
      }, box);
      tipFor(b, function () {
        return '<div class="tip-title">FO' + r.episode + " · " + esc(r.title) + "</div>" +
          row(color(D.focus.indexOf(r.topic) >= 0 ? r.topic : "Other"), r.topic, "") +
          "<div style='margin-top:.3rem'>" + (r.language || "Language not known yet") + " · " + (r.views == null ? "views n/a" : "<b>" + mil(r.views) + "</b> views") + "</div>";
      });
    });
    var ax = el("div", { class: "strip-axis" });
    el("span", { text: "FO" + rec[0].episode }, ax);
    el("span", { text: "FO" + rec[rec.length - 1].episode + " · latest" }, ax);
    box.after(ax);

    var log = $("recent-log");
    rec.slice(-6).reverse().forEach(function (r) {
      var li = el("li", {}, log);
      el("i", { class: "swatch", style: "background:" + color(D.focus.indexOf(r.topic) >= 0 ? r.topic : "Other") }, li);
      el("span", { class: "ep", text: "FO" + r.episode }, li);
      var t = el("span", { class: "t", text: r.title, title: r.title }, li);
      el("span", { class: "topic-name", text: r.topic + (r.views == null ? "" : " · " + mil(r.views)) }, t);
    });
  }

  function renderMomentum() {
    var rows = D.signals.momentum.filter(function (m) { return m.last100 >= 0.03 || m.last20 >= 0.05; }).slice(0, 8)
      .map(function (m) {
        var d = Math.round(100 * (m.last20 - m.last100));
        return {
          label: m.topic, a: m.last100, b: m.last20, note: (d > 0 ? "+" : "") + d + " pts",
          aria: m.topic + ": " + pct(m.last100) + " of the last 100, " + pct(m.last20) + " of the last 20",
          tip: '<div class="tip-title">' + esc(m.topic) + "</div>Last 100 episodes <b>" + pct(m.last100) + "</b><br>Last 20 episodes <b>" + pct(m.last20) + "</b>",
        };
      });
    var max = Math.max.apply(null, rows.map(function (r) { return Math.max(r.a, r.b); }));
    max = Math.ceil(max * 10) / 10;
    var ticks = [];
    for (var v = 0; v <= max + 1e-9; v += 0.1) ticks.push(+v.toFixed(1));
    dumbbell($("chart-momentum"), rows, { max: max, ticks: ticks, bColor: token("--ivory") });
  }

  function renderEntities() {
    var ents = D.signals.entities;
    var ul = $("entities");
    var up = ents.filter(function (e) { return e.ratio >= 1.15; }).slice(0, 4);
    var down = ents.filter(function (e) { return e.ratio <= 0.85; }).slice(-4).reverse();
    function group(label, list) {
      el("li", { class: "group", text: label }, ul);
      if (!list.length) el("li", { text: "Nothing notable" }, ul);
      list.forEach(function (e) {
        var li = el("li", { tabindex: 0 }, ul);
        el("span", { text: e.entity }, li);
        el("span", { class: "chg", text: (e.ratio >= 1 ? "▲ " : "▼ ") + e.ratio.toFixed(1) + "×" }, li);
        tipFor(li, function () { return '<div class="tip-title">' + esc(e.entity) + "</div>Mentions per 1,000 words<br>120 episodes before: <b>" + e.prior.toFixed(2) + "</b><br>Last 30 episodes: <b>" + e.recent.toFixed(2) + "</b>"; });
      });
    }
    group("Rising", up);
    group("Fading", down);
  }

  function renderOverdue() {
    var ul = $("overdue");
    D.signals.overdue.forEach(function (o) {
      var li = el("li", {}, ul);
      var a = el("span", { text: o.topic }, li);
      el("small", { text: o.since + " episodes since last · usually every " + Math.round(o.usual_gap) }, a);
      el("span", { class: "factor", text: o.factor.toFixed(1) + "×" }, li);
    });
  }

  function renderTop() {
    var ol = $("top-list");
    var max = D.top[0].views;
    D.top.forEach(function (t) {
      var li = el("li", {}, ol);
      var title = el("span", { class: "title", text: t.title }, li);
      el("small", { text: "FO" + t.episode + " · " + t.topic }, title);
      el("span", { class: "views", text: mil(t.views) }, li);
      var bar = el("span", { class: "bar" }, li);
      el("i", { style: "width:" + (100 * t.views) / max + "%" }, bar);
    });
  }

  function renderMethod() {
    var c = D.counts;
    var steps = [
      ["01", "Collect", c.episodes, "episodes", "The channel's full video list, and transcripts of every episode in English and Hindi, downloaded and kept with their source.", "fetch_videos.py · fetch_transcripts.py"],
      ["02", "Resolve", c.guests, "guests", "One record: episodes linked to guests, 13 topics, and " + c.mention_links.toLocaleString("en-IN") + " mentions of people, countries, companies and ideas. Each link says where it came from.", "ontology.py → sanjaya.db"],
      ["03", "See", 13, "topics", "Topic tagging across English, Hindi and Hinglish, trends over time, what gets watched, and what is rising in the conversations.", "analyze.py · research.py"],
      ["04", "Act", D.track.length, "forecasts logged", "A tested forecast of the next episode, logged before release and scored when the episode comes out. Refreshed every two days.", "predict.py · export_site.py"],
    ];
    var ol = $("pipeline");
    steps.forEach(function (s) {
      var li = el("li", {}, ol);
      el("span", { class: "step", text: s[0] }, li);
      el("h3", { text: s[1] }, li);
      el("div", { class: "big", html: s[2] + "<small>" + esc(s[3]) + "</small>" }, li);
      el("p", { text: s[4] }, li);
      el("code", { text: s[5] }, li);
    });
    $("updated").textContent = "Data updated " + new Date(D.updated + "T00:00:00").toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" }) +
      ". Source: public YouTube videos and auto-generated captions.";
  }

  // ---------- boot ----------
  function drawSvgCharts() {
    renderRiver();
    renderMade();
    renderLang();
    renderMomentum();
  }

  fetch("data.json")
    .then(function (r) { return r.json(); })
    .then(function (data) {
      D = data;
      D.focus.forEach(function (t, i) { COLOR[t] = token("--t" + (i + 1)); });
      COLOR.Other = token("--other");
      renderHero();
      renderForecast();
      renderFindings();
      legend($("legend-river"), D.focus.concat(["Other"]));
      table($("t-river"), ["Episodes"].concat(D.focus.concat(["Other"]).map(short)),
        D.river.filter(function (_, i) { return i % 5 === 0; }).map(function (d) {
          return ["FO" + (d.episode - 39) + "–" + d.episode].concat(D.focus.concat(["Other"]).map(function (k) { return pct(d[k]); }));
        }));
      renderLength();
      renderStrip();
      renderEntities();
      renderOverdue();
      renderTop();
      renderMethod();
      drawSvgCharts();
      var lastW = window.innerWidth, t;
      window.addEventListener("resize", function () {
        if (window.innerWidth === lastW) return;
        lastW = window.innerWidth;
        clearTimeout(t);
        t = setTimeout(drawSvgCharts, 150);
      });
    })
    .catch(function (err) {
      var m = el("p", { class: "fineprint", text: "The research data could not be loaded. " + err }, null);
      document.querySelector(".r-hero .wrap").appendChild(m);
    });
})();
