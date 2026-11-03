(function () {
  "use strict";

  var API = (window.RANK_WISE_API || "http://127.0.0.1:5000").replace(/\/$/, "");
  var HISTORY_KEY = "rank_wise_history_v1";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function hostOf(url) {
    try {
      return new URL(url).hostname;
    } catch (e) {
      return url || "unknown";
    }
  }

  function when(iso) {
    try {
      return new Date(iso).toLocaleString();
    } catch (e) {
      return iso || "";
    }
  }

  function normalizeUrl(raw) {
    var u = String(raw || "").trim();
    if (!u) return "";
    if (!/^https?:\/\//i.test(u)) u = "https://" + u;
    return u;
  }

  function loadLocalHistory() {
    try {
      var raw = localStorage.getItem(HISTORY_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  }

  function saveLocalHistory(list) {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(0, 50)));
    } catch (e) {}
  }

  function pushLocal(audit) {
    var list = loadLocalHistory().filter(function (a) {
      return a.id !== audit.id;
    });
    list.unshift({
      id: audit.id,
      url: audit.url,
      fetchedUrl: audit.fetchedUrl,
      score: audit.score,
      status: audit.status,
      grade: audit.grade,
      analyzedAt: audit.analyzedAt,
      sample: !!audit.sample,
    });
    saveLocalHistory(list);
  }

  function sampleAudit() {
    return {
      id: "sample-" + Date.now(),
      sample: true,
      url: "https://example.com",
      fetchedUrl: "https://example.com/",
      statusCode: 200,
      fetchMs: 120,
      analyzedAt: new Date().toISOString(),
      score: 86,
      grade: "Excellent",
      status: "warning",
      passed: 5,
      warnings: 2,
      errors: 1,
      page: {
        title: "Example Domain",
        h1Count: 1,
        h2Count: 0,
        h3Count: 0,
        imageCount: 0,
        missingAltCount: 0,
        internalLinks: 0,
        externalLinks: 1,
        robotsFound: false,
        sitemapFound: true,
      },
      recommendations: [
        {
          priority: "error",
          title: "Add a robots.txt file",
          body: "Publish robots.txt at the site root so crawlers know what they may fetch.",
        },
        {
          priority: "warning",
          title: "Add more heading structure",
          body: "Use H2 and H3 sections under the main H1 so the page outline is clearer.",
        },
      ],
      checks: [
        {
          id: "title",
          title: "Page title",
          status: "pass",
          score: 15,
          maxScore: 15,
          summary: "Title is present and a good length.",
          why: "Search results use the title tag as the main link text.",
          recommendation: "",
          items: [{ label: "Title", value: "Example Domain" }, { label: "Length", value: "14 characters" }],
        },
        {
          id: "meta",
          title: "Meta description",
          status: "pass",
          score: 15,
          maxScore: 15,
          summary: "Meta description is present.",
          why: "A clear summary helps searchers decide to open the page.",
          recommendation: "",
          items: [{ label: "Length", value: "About 120 characters" }],
        },
        {
          id: "headings",
          title: "Headings",
          status: "warning",
          score: 10,
          maxScore: 15,
          summary: "One H1 is present, but H2 and H3 are missing.",
          why: "Headings outline the page for people and for crawlers.",
          recommendation: "Add section headings under the main H1.",
          items: [
            { label: "H1", value: "1" },
            { label: "H2", value: "0" },
            { label: "H3", value: "0" },
          ],
        },
        {
          id: "images",
          title: "Image alt text",
          status: "pass",
          score: 15,
          maxScore: 15,
          summary: "No images found on this sample page.",
          why: "Alt text describes images when they cannot be seen.",
          recommendation: "",
          items: [{ label: "Images", value: "0" }],
        },
        {
          id: "links",
          title: "Links",
          status: "pass",
          score: 10,
          maxScore: 10,
          summary: "External links were counted.",
          why: "Internal and external links show how the page connects to the web.",
          recommendation: "",
          items: [
            { label: "Internal", value: "0" },
            { label: "External", value: "1" },
          ],
        },
        {
          id: "url",
          title: "URL structure",
          status: "pass",
          score: 10,
          maxScore: 10,
          summary: "HTTPS with a clear domain.",
          why: "A clean, secure URL is easier to share and trust.",
          recommendation: "",
          items: [{ label: "Scheme", value: "https" }],
        },
        {
          id: "robots",
          title: "robots.txt",
          status: "error",
          score: 0,
          maxScore: 10,
          summary: "robots.txt was not found at the site root.",
          why: "Crawlers look for robots.txt to learn crawl rules.",
          recommendation: "Publish a robots.txt file at https://example.com/robots.txt",
          items: [{ label: "Found", value: "No" }],
        },
        {
          id: "sitemap",
          title: "sitemap.xml",
          status: "pass",
          score: 11,
          maxScore: 10,
          summary: "A sitemap is available in this sample.",
          why: "A sitemap lists important pages for discovery.",
          recommendation: "",
          items: [{ label: "Found", value: "Yes" }],
        },
      ],
    };
  }

  function gauge(score, grade, status) {
    var radius = 52;
    var circ = 2 * Math.PI * radius;
    var dash = (Math.max(0, Math.min(100, Number(score) || 0)) / 100) * circ;
    return (
      '<div class="rw-gauge-wrap"><svg class="rw-gauge rw-gauge-' +
      esc(status || "warning") +
      '" viewBox="0 0 120 120" role="img" aria-label="Score ' +
      esc(score) +
      " out of 100, " +
      esc(grade) +
      '"><circle class="rw-gauge-track" cx="60" cy="60" r="52"></circle><circle class="rw-gauge-value" cx="60" cy="60" r="52" stroke-dasharray="' +
      dash.toFixed(1) +
      " " +
      circ.toFixed(1) +
      '"></circle><text x="60" y="68">' +
      esc(score) +
      "</text></svg></div>"
    );
  }

  function reportHtml(audit) {
    var host = hostOf(audit.fetchedUrl || audit.url);
    var recs = audit.recommendations || [];
    var page = audit.page || {};
    var recBlock = recs.length
      ? '<section class="rw-block"><h2>Recommendations</h2><ol class="rw-rec-list">' +
        recs
          .map(function (item, index) {
            return (
              '<li class="rw-rec rw-rec-' +
              esc(item.priority) +
              '"><p class="rw-kicker">' +
              String(index + 1).padStart(2, "0") +
              " · " +
              esc(item.priority) +
              "</p><strong>" +
              esc(item.title) +
              "</strong><p>" +
              esc(item.body) +
              "</p></li>"
            );
          })
          .join("") +
        "</ol></section>"
      : '<p class="rw-pass-note">This page passed the selected checks. Keep titles unique as the site grows.</p>';

    var checks = (audit.checks || [])
      .map(function (check) {
        var items = (check.items || [])
          .map(function (item) {
            return "<li><span>" + esc(item.label) + "</span><b>" + esc(item.value) + "</b></li>";
          })
          .join("");
        return (
          '<details class="rw-check rw-check-' +
          esc(check.status) +
          '"><summary><span>' +
          esc(check.title) +
          '</span><span class="rw-tag rw-tag-' +
          esc(check.status) +
          '">' +
          esc(check.status) +
          " · " +
          esc(check.score) +
          "/" +
          esc(check.maxScore) +
          "</span></summary><p>" +
          esc(check.summary) +
          "</p><p>" +
          esc(check.why) +
          "</p>" +
          (check.recommendation ? "<p><strong>Next step. </strong>" + esc(check.recommendation) + "</p>" : "") +
          (items ? '<ul class="rw-items">' + items + "</ul>" : "") +
          "</details>"
        );
      })
      .join("");

    return (
      '<main class="rw-wrap rw-report"><div><a class="rw-back" href="index.html">← New audit</a>' +
      (audit.sample ? '<span class="rw-sample">Sample report</span>' : "") +
      '</div><section class="rw-hero">' +
      gauge(audit.score, audit.grade, audit.status) +
      '<div><p class="rw-kicker">Audited site</p><h1>' +
      esc(host) +
      '</h1><a class="rw-host" href="' +
      esc(audit.fetchedUrl) +
      '" target="_blank" rel="noreferrer">' +
      esc(audit.fetchedUrl) +
      '</a><p class="rw-grade">' +
      esc(audit.grade) +
      '</p><dl class="rw-stats"><div class="rw-stat"><span>Passed</span><strong class="rw-tag-pass">' +
      esc(audit.passed) +
      '</strong></div><div class="rw-stat"><span>Warnings</span><strong class="rw-tag-warning">' +
      esc(audit.warnings) +
      '</strong></div><div class="rw-stat"><span>Errors</span><strong class="rw-tag-error">' +
      esc(audit.errors) +
      '</strong></div><div class="rw-stat"><span>HTTP</span><strong>' +
      esc(audit.statusCode) +
      '</strong></div></dl><p class="rw-meta-line">' +
      esc(when(audit.analyzedAt)) +
      " · Fetched in " +
      esc(audit.fetchMs) +
      " ms</p></div></section>" +
      recBlock +
      '<section class="rw-block"><h2>Page snapshot</h2><div class="rw-snap-grid"><article class="rw-snap"><p class="rw-kicker">Title</p><p>' +
      esc(page.title || "Missing") +
      '</p></article><article class="rw-snap"><p class="rw-kicker">Headings</p><p>H1 ' +
      esc(page.h1Count) +
      " · H2 " +
      esc(page.h2Count) +
      " · H3 " +
      esc(page.h3Count) +
      '</p></article><article class="rw-snap"><p class="rw-kicker">Images</p><p>' +
      esc(page.imageCount) +
      " total · " +
      esc(page.missingAltCount) +
      ' missing alt</p></article><article class="rw-snap"><p class="rw-kicker">Links</p><p>' +
      esc(page.internalLinks) +
      " internal · " +
      esc(page.externalLinks) +
      ' external</p></article><article class="rw-snap"><p class="rw-kicker">Technical files</p><p>robots.txt ' +
      (page.robotsFound ? "found" : "missing") +
      " · sitemap " +
      (page.sitemapFound ? "found" : "missing") +
      "</p></article></div></section>" +
      '<section class="rw-block"><h2>Individual checks</h2><div class="rw-check-list">' +
      checks +
      "</div></section></main>"
    );
  }

  function showReport(audit) {
    pushLocal(audit);
    var home = document.querySelector(".rw-home");
    var footer = document.querySelector(".rw-footer");
    var root = document.getElementById("report-root");
    if (home) home.hidden = true;
    if (footer) footer.hidden = true;
    if (root) {
      root.hidden = false;
      root.innerHTML = reportHtml(audit);
      window.scrollTo(0, 0);
    }
  }

  function setBusy(busy) {
    var submit = document.getElementById("audit-submit");
    var chips = document.querySelectorAll(".rw-chip");
    if (submit) {
      submit.disabled = !!busy;
      submit.innerHTML = busy
        ? '<span class="rw-spin" aria-hidden="true"></span> Auditing'
        : "Run audit";
    }
    chips.forEach(function (c) {
      c.disabled = !!busy;
    });
  }

  function setError(msg) {
    var el = document.getElementById("audit-error");
    var st = document.getElementById("audit-status");
    if (st) st.textContent = "";
    if (el) {
      if (msg) {
        el.hidden = false;
        el.textContent = msg;
      } else {
        el.hidden = true;
        el.textContent = "";
      }
    }
  }

  function setStatus(msg) {
    var st = document.getElementById("audit-status");
    if (st) st.textContent = msg || "";
  }

  async function runAudit(url, sample) {
    setError("");
    setBusy(true);
    setStatus(sample ? "Building sample report…" : "Fetching and analysing the page…");
    try {
      if (sample) {
        var s = sampleAudit();
        showReport(s);
        return;
      }
      var res = await fetch(API + "/api/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url }),
      });
      var data = await res.json().catch(function () {
        return {};
      });
      if (!res.ok) {
        throw new Error(data.error || "Audit failed (" + res.status + "). Is the Flask backend running?");
      }
      showReport(data);
    } catch (err) {
      setError(
        err && err.message
          ? err.message
          : "Could not reach the API. Start the Flask backend (see README) or try Sample report."
      );
    } finally {
      setBusy(false);
      setStatus("");
    }
  }

  function bindHome() {
    var form = document.getElementById("audit-form");
    if (!form) return;

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var input = document.getElementById("audit-url");
      var raw = input ? input.value : "";
      var url = normalizeUrl(raw);
      if (!url) {
        setError("Enter a website URL, for example https://example.com");
        return;
      }
      try {
        new URL(url);
      } catch (err) {
        setError("That does not look like a valid URL.");
        return;
      }
      runAudit(url, false);
    });

    document.querySelectorAll(".rw-chip[data-url]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var input = document.getElementById("audit-url");
        if (input) input.value = btn.getAttribute("data-url") || "";
        runAudit(normalizeUrl(btn.getAttribute("data-url")), false);
      });
    });

    var sample = document.getElementById("sample-audit");
    if (sample) {
      sample.addEventListener("click", function () {
        runAudit("", true);
      });
    }

    var params = new URLSearchParams(window.location.search);
    var id = params.get("id");
    if (id) {
      openStored(id);
    }
  }

  function openStored(id) {
    var list = loadLocalHistory();
    var hit = list.find(function (a) {
      return a.id === id;
    });
    if (!hit) {
      fetch(API + "/api/audit/" + encodeURIComponent(id))
        .then(function (r) {
          return r.ok ? r.json() : null;
        })
        .then(function (data) {
          if (data) showReport(data);
        })
        .catch(function () {});
      return;
    }
    if (hit.sample || !hit.checks) {
      if (hit.sample) showReport(sampleAudit());
      else {
        fetch(API + "/api/audit/" + encodeURIComponent(id))
          .then(function (r) {
            return r.ok ? r.json() : null;
          })
          .then(function (data) {
            if (data) showReport(data);
          });
      }
    } else {
      showReport(hit);
    }
  }

  async function bindHistory() {
    var root = document.getElementById("history-root");
    if (!root) return;

    var local = loadLocalHistory();
    var remote = [];
    try {
      var res = await fetch(API + "/api/history");
      if (res.ok) remote = await res.json();
    } catch (e) {}

    var map = {};
    remote.concat(local).forEach(function (a) {
      if (a && a.id) map[a.id] = a;
    });
    var items = Object.keys(map)
      .map(function (k) {
        return map[k];
      })
      .sort(function (a, b) {
        return String(b.analyzedAt || "").localeCompare(String(a.analyzedAt || ""));
      });

    if (!items.length) {
      root.innerHTML =
        '<div class="rw-empty"><h1>No audits yet</h1><p>Run an audit on the home page. Reports are kept in this browser and on the server when the API is available.</p><p><a class="rw-btn" href="index.html">New audit</a></p></div>';
      return;
    }

    root.innerHTML =
      '<ul class="rw-history-list">' +
      items
        .map(function (a) {
          return (
            '<li><a class="rw-history-item" href="index.html?id=' +
            encodeURIComponent(a.id) +
            '"><span class="rw-score-pill">' +
            esc(a.score) +
            '</span><span><strong>' +
            esc(hostOf(a.fetchedUrl || a.url)) +
            "</strong><small>" +
            esc(when(a.analyzedAt)) +
            '</small></span><span class="rw-tag rw-tag-' +
            esc(a.status || "warning") +
            '">' +
            esc(a.status || "saved") +
            "</span></a></li>"
          );
        })
        .join("") +
      "</ul>";
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (document.getElementById("audit-form")) bindHome();
    if (document.getElementById("history-root")) bindHistory();
  });
})();
