/* PAHIBALO: theme, menu, search and the GWA calculator. No libraries.
   Every page works without this file; it only adds live search and the calculator. */
(function () {
  "use strict";
  var ROOT = window.PAHI_ROOT || "";
  var doc = document.documentElement;
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  function $(s, el) { return (el || document).querySelector(s); }
  function $$(s, el) { return Array.prototype.slice.call((el || document).querySelectorAll(s)); }
  function esc(s) { return String(s || "").replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function icon(name) { return '<svg class="ic" aria-hidden="true"><use href="#i-' + name + '"/></svg>'; }

  /* ---------- light / dark */
  var themeBtn = $("#themeBtn");
  if (themeBtn) themeBtn.addEventListener("click", function () {
    var dark = doc.dataset.theme ? doc.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    doc.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("pahi-theme", doc.dataset.theme); } catch (e) {}
  });

  /* ---------- "More" sheet: the phone bar button and the "More" tab in the top menu open the same list */
  var moreBtns = Array.prototype.slice.call(document.querySelectorAll("[data-more]")), sheet = $("#moreSheet"), opener = null;
  var moreBtn = moreBtns[0];
  function setSheet(open, from) {
    sheet.hidden = !open;
    if (from) opener = from;
    moreBtns.forEach(function (b) { b.setAttribute("aria-expanded", String(open)); });
    if (open) $("a", sheet).focus(); else if (opener) opener.focus();
  }
  if (moreBtn && sheet) {
    moreBtns.forEach(function (b) { b.addEventListener("click", function () { setSheet(sheet.hidden, b); }); });
    $("#moreClose").addEventListener("click", function () { setSheet(false); });
    sheet.addEventListener("click", function (e) { if (e.target === sheet) setSheet(false); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !sheet.hidden) setSheet(false); });
  }

  /* ---------- hub pages: show pages for one stage (Freshies, Juniors, Seniors) plus pages for every year */
  var gf = $(".gfilter"), hubList = $("#hubList");
  if (gf && hubList) {
    $$("button", gf).forEach(function (b) {
      b.addEventListener("click", function () {
        var g = b.dataset.g;
        $$("button", gf).forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
        $$(".row", hubList).forEach(function (r) {
          var gs = (r.dataset.groups || "all").split(" ");
          r.hidden = !!g && gs.indexOf("all") < 0 && gs.indexOf(g) < 0;
        });
      });
    });
  }

  /* ---------- press "/" anywhere to search */
  document.addEventListener("keydown", function (e) {
    if (e.key !== "/" || e.ctrlKey || e.metaKey || /input|textarea|select/i.test(document.activeElement.tagName)) return;
    var box = $("#q") || $("#sq");
    e.preventDefault();
    if (box) box.focus(); else location.href = ROOT + "search.html";
  });

  /* ---------- search engine (index built by build.py: title, aliases, tasks, summary, body) */
  var STOP = { a: 1, an: 1, the: 1, to: 1, i: 1, my: 1, need: 1, for: 1, how: 1, of: 1, in: 1, get: 1, want: 1, where: 1, is: 1, can: 1, me: 1, and: 1, on: 1, at: 1 };
  var TYPEWORD = { form: "form", forms: "form", slip: "form", org: "org", orgs: "org", club: "org", clubs: "org", office: "office", offices: "office", competition: "competition", competitions: "competition", guide: "guide", rules: "guide" };
  function norm(s) { return String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9.\s-]/g, " ").replace(/\s+/g, " ").trim(); }
  function words(s) { return norm(s).split(/[\s.-]+/).filter(Boolean); }
  function oneEditApart(a, b) {
    if (a === b) return true;
    if (Math.abs(a.length - b.length) > 1) return false;
    var i = 0, j = 0, edits = 0;
    while (i < a.length && j < b.length) {
      if (a[i] === b[j]) { i++; j++; continue; }
      if (++edits > 1) return false;
      if (a.length > b.length) i++; else if (b.length > a.length) j++; else { i++; j++; }
    }
    return edits + (a.length - i) + (b.length - j) <= 1;
  }
  var index = null;
  function getIndex() {
    if (!index) index = (window.PAHI_INDEX || []).map(function (it) {
      return { it: it, t: norm(it.t), tw: words(it.t), a: it.a.map(norm), aw: it.a.map(words), s: norm(it.s), c: norm(it.c), b: norm(it.b) };
    });
    return index;
  }
  function wordHit(list, w, short) { return list.some(function (x) { return short ? x === w : x.indexOf(w) === 0; }); }

  function search(q, area, grade) {
    var nq = norm(q), toks = words(q).filter(function (w) { return !STOP[w]; }), hint = null;
    if (toks.length > 1) toks = toks.filter(function (w) { if (TYPEWORD[w]) { hint = TYPEWORD[w]; return false; } return true; });
    var out = [];
    getIndex().forEach(function (p) {
      var it = p.it;
      if (area && area !== "all" && it.h !== area) return;
      if (grade && it.gg.length && it.gg.indexOf(grade) < 0) return;  /* pages for every year stay */
      if (!nq) { out.push({ it: it, score: 0, hits: 0 }); return; }
      var score = 0, hits = 0, why = "";
      if (p.t === nq) score += 120;
      p.a.forEach(function (a, i) { if (a === nq) { score += 100; why = it.a[i]; } });
      toks.forEach(function (w) {
        var s = 0, short = w.length < 3;
        if (p.t.indexOf(w) === 0) s = 30;
        else if (wordHit(p.tw, w, false)) s = 22;
        else if (!short && p.t.indexOf(w) >= 0) s = 12;
        if (s < 18) p.aw.forEach(function (aw, i) { if (s < 18 && wordHit(aw, w, short)) { s = 18; if (!why) why = it.a[i]; } });
        if (!s && !short) s = p.s.indexOf(w) >= 0 ? 7 : p.c.indexOf(w) >= 0 ? 6 : p.b.indexOf(w) >= 0 ? 3 : 0;
        if (!s && w.length >= 4 && (p.tw.some(function (x) { return oneEditApart(x, w); }) || p.aw.some(function (aw) { return aw.some(function (x) { return oneEditApart(x, w); }); }))) s = 9;
        if (s) { hits++; score += s; }
      });
      if (hint && it.y === hint) score += 10;
      if (score > 0) out.push({ it: it, score: score, hits: hits, why: why });
    });
    if (nq) {
      out.sort(function (x, y) { return (y.hits - x.hits) || (y.score - x.score) || x.it.t.localeCompare(y.it.t); });
      var best = out.length ? out[0].hits : 0;
      if (toks.length > 1) out = out.filter(function (r) { return r.hits >= Math.max(1, best - 1); });
    } else {
      var order = $$("#areaChips button").map(function (b) { return b.dataset.area; });  /* Site Areas order */
      out.sort(function (x, y) { return (order.indexOf(x.it.h) - order.indexOf(y.it.h)) || x.it.t.localeCompare(y.it.t); });
    }
    return { results: out, toks: toks };
  }
  function mark(text, toks) {
    var s = esc(text);
    toks.forEach(function (w) {
      if (w.length < 2) return;
      s = s.replace(new RegExp("(^|[\\s(])(" + w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig"), "$1<mark>$2</mark>");
    });
    return s;
  }
  function rowHTML(r, toks) {
    var it = r.it;
    var why = r.why && norm(r.why) !== norm(it.t) ? '<small class="why">matches “' + esc(r.why) + '”</small>' : "";
    var gg = (it.gg || []).map(function (g) { return '<span class="gchip gg-' + g + '">' + g.charAt(0).toUpperCase() + g.slice(1) + "</span>"; }).join("");
    var thumb = it.p && it.y !== "office" ? '<img class="row-thumb' + (it.pl ? " is-logo" : "") + '" src="' + ROOT + "img/photos/" + it.p + (it.pl ? "-300" : "-600") + '.webp" alt="" width="64" height="64" loading="lazy" onerror="this.onerror=null;this.src=this.src.replace(/-600\\.webp$/,\'.webp\')">'
      : '<span class="tag t-' + it.tg + '">' + esc(it.tg) + "</span>";
    return '<a class="row k-' + it.tg + '" href="' + ROOT + it.u + '"><span class="row-ic t-' + it.tg + '">' + icon(it.i) + "</span>" +
      '<span class="row-main"><b>' + mark(it.t, toks) + "</b>" + (it.c ? '<small class="con">' + esc(it.c) + "</small>" : "") +
      (it.s ? '<small class="sum">' + esc(it.s) + "</small>" : "") + why + (gg ? '<span class="gchips">' + gg + "</span>" : "") + "</span>" + thumb + "</a>";
  }

  /* ---------- home: results drop down under the search box */
  var homeForm = $("#homeSearch"), q = $("#q"), peek = $("#peek");
  if (homeForm && q && peek) {
    var showPeek = function () {
      var v = q.value.trim();
      if (!v) { peek.hidden = true; return; }
      var r = search(v), top = r.results.slice(0, 5);
      peek.innerHTML = top.length
        ? '<div class="dir">' + top.map(function (x) { return rowHTML(x, r.toks); }).join("") + '</div><a class="peek-all" href="' + ROOT + "search.html?q=" + encodeURIComponent(v) + '">See all ' + r.results.length + " results</a>"
        : '<p class="empty">Nothing for “' + esc(v) + '” yet. Try a nickname, or what you need to do, like “go home”.</p>';
      peek.hidden = false;
    };
    q.addEventListener("input", showPeek);
    q.addEventListener("focus", showPeek);
    q.addEventListener("keydown", function (e) { if (e.key === "Escape") { peek.hidden = true; } });
    document.addEventListener("click", function (e) { if (!homeForm.contains(e.target)) peek.hidden = true; });
  }

  /* ---------- search page */
  var sq = $("#sq"), results = $("#results");
  if (sq && results) {
    var box = $("#filterBox");
    if (box && matchMedia("(min-width: 700px)").matches) box.open = true;
    var params = new URLSearchParams(location.search);
    var state = { q: params.get("q") || "", area: params.get("area") || "all", grade: params.get("grade") || "" };
    sq.value = state.q;
    var run = function () {
      var r = search(state.q, state.area, state.grade), n = r.results.length;
      results.classList.remove("fresh"); void results.offsetWidth; if (!reduce) results.classList.add("fresh");
      results.innerHTML = n ? r.results.map(function (x) { return rowHTML(x, r.toks); }).join("")
        : '<p class="empty">Nothing found. Try fewer words, a nickname, or the “All” filter.</p>';
      $("#count").textContent = state.q ? n + (n === 1 ? " result" : " results") + " for “" + state.q + "”" : n + " pages";
      $$("#areaChips button").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.area === state.area)); });
      $$("#gradeChips button").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.grade === state.grade)); });
      var on = [], chip = $('#areaChips [data-area="' + state.area + '"]');
      if (state.area !== "all" && chip) on.push(chip.textContent);
      if (state.grade) on.push(state.grade.charAt(0).toUpperCase() + state.grade.slice(1));
      $("#filterNote").textContent = on.length ? "(" + on.join(", ") + ")" : "";
      var u = new URLSearchParams();
      if (state.q) u.set("q", state.q);
      if (state.area !== "all") u.set("area", state.area);
      if (state.grade) u.set("grade", state.grade);
      history.replaceState(null, "", location.pathname + (String(u) ? "?" + u : ""));
    };
    var timer;
    sq.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(function () { state.q = sq.value.trim(); run(); }, 100); });
    $$("#areaChips button").forEach(function (b) { b.addEventListener("click", function () { state.area = b.dataset.area; run(); }); });
    $$("#gradeChips button").forEach(function (b) { b.addEventListener("click", function () { state.grade = state.grade === b.dataset.grade ? "" : b.dataset.grade; run(); }); });
    run();
  }

  /* ---------- GWA calculator (units come from the Curriculum and Units guide) */
  var sets = window.GWA_SETS, form = $("#gwaForm");
  if (sets && form) {
    var GRADES = ["1.00", "1.25", "1.50", "1.75", "2.00", "2.25", "2.50", "2.75", "3.00", "4.00", "5.00"];
    var current = $("#gwaSets input:checked").value;
    var draw = function () {
      form.innerHTML = sets[current].map(function (s, i) {
        if (s.ng) return '<div class="gwa-line gwa-ng"><div class="gwa-name"><b>' + esc(s.n) + "</b><small>" + s.u + " units</small></div><em>Complete or Incomplete, not in the GWA</em></div>";
        var opts = '<option value="">' + (s.opt ? "none" : "–") + "</option>" + GRADES.map(function (g) { return "<option>" + g + "</option>"; }).join("");
        return '<div class="gwa-line"><div class="gwa-name"><label for="g' + i + '">' + esc(s.n) + "</label><small>" + s.u + (s.u === 1 ? " unit" : " units") + '</small></div><div class="gwa-pick">' +
          '<button type="button" class="gwa-step" data-step="-1" data-for="g' + i + '" aria-label="One step better for ' + esc(s.n) + '">−</button>' +
          '<select id="g' + i + '" data-i="' + i + '">' + opts + "</select>" +
          '<button type="button" class="gwa-step" data-step="1" data-for="g' + i + '" aria-label="One step lower for ' + esc(s.n) + '">+</button></div></div>';
      }).join("");
      calc(false);
    };
    /* − and + move a subject's grade one step through the list (1.00, 1.25 … 5.00). An empty one starts at 1.00. */
    form.addEventListener("click", function (e) {
      var b = e.target.closest(".gwa-step");
      if (!b) return;
      var sel = document.getElementById(b.dataset.for), n = sel.options.length;
      if (!sel.value) sel.selectedIndex = 1;
      else sel.selectedIndex = Math.min(n - 1, Math.max(1, sel.selectedIndex + (+b.dataset.step)));
      calc(true);
    });
    var calc = function (bump) {
      var list = sets[current], total = 0, units = 0, lines = [], filled = 0, needed = 0;
      $$("select", form).forEach(function (sel) {
        var s = list[+sel.dataset.i];
        if (!s.opt) needed++;
        if (!sel.value) return;
        if (!s.opt) filled++;
        var g = parseFloat(sel.value);
        total += g * s.u; units += s.u;
        lines.push(s.n + ": " + sel.value + " × " + s.u + " = " + (g * s.u).toFixed(3));
      });
      var out = $("#gwaVal");
      if (!units) { out.textContent = "…"; $("#gwaMood").textContent = "Choose a grade for each subject."; $("#gwaWork").textContent = "Nothing yet."; return; }
      var gwa = total / units;
      /* The report card cuts the GWA to two decimals; it does not round (1.5298 shows as 1.52). */
      var cut = (Math.floor(gwa * 100 + 1e-9) / 100).toFixed(2);
      out.textContent = cut;
      if (bump && !reduce) { out.classList.remove("bump"); void out.offsetWidth; out.classList.add("bump"); }
      $("#gwaMood").textContent = filled < needed ? filled + " of " + needed + " subjects so far" : "all " + needed + " subjects in";
      $("#gwaWork").textContent = lines.join("\n") + "\n\nTotal: " + total.toFixed(3) + " ÷ " + units.toFixed(1) + " units = " + gwa.toFixed(4) + "\nOn the report card: " + cut + " (cut to two decimals, not rounded)";
    };
    $$("#gwaSets input").forEach(function (r) { r.addEventListener("change", function () { current = r.value; draw(); }); });
    form.addEventListener("change", function () { calc(true); });
    draw();
  }
})();
