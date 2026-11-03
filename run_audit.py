"""Rank Wise on-page SEO audit engine."""

from __future__ import annotations

import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

USER_AGENT = "RankWiseSEOBot/1.0 (+https://github.com/rank-wise)"
TIMEOUT = 12


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_url(raw: str) -> str:
    u = (raw or "").strip()
    if not u:
        raise ValueError("Enter a website URL.")
    if not re.match(r"^https?://", u, re.I):
        u = "https://" + u
    parsed = urlparse(u)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("That does not look like a valid public URL.")
    host = parsed.hostname or ""
    if host in ("localhost", "127.0.0.1", "0.0.0.0") or host.startswith("192.168.") or host.startswith("10."):
        raise ValueError("Private or local addresses are not allowed.")
    return u


def _fetch(url: str) -> tuple[str, int, float, str]:
    started = time.time()
    resp = requests.get(
        url,
        timeout=TIMEOUT,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        allow_redirects=True,
    )
    ms = int((time.time() - started) * 1000)
    final = resp.url
    text = resp.text or ""
    return text, resp.status_code, ms, final


def _head_ok(url: str) -> bool:
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": USER_AGENT}, allow_redirects=True)
        return r.status_code < 400 and len(r.text or "") > 0
    except requests.RequestException:
        return False


def _check_title(soup: BeautifulSoup) -> dict[str, Any]:
    tag = soup.find("title")
    title = (tag.get_text(strip=True) if tag else "") or ""
    length = len(title)
    items = [{"label": "Title", "value": title or "Missing"}, {"label": "Length", "value": f"{length} characters"}]
    if not title:
        return {
            "id": "title",
            "title": "Page title",
            "status": "error",
            "score": 0,
            "maxScore": 15,
            "summary": "No title tag was found.",
            "why": "Search results use the title tag as the main link text.",
            "recommendation": "Add a unique <title> of about 30–60 characters.",
            "items": items,
        }
    if length < 30 or length > 60:
        return {
            "id": "title",
            "title": "Page title",
            "status": "warning",
            "score": 10,
            "maxScore": 15,
            "summary": "Title is present but length is outside the usual 30–60 range.",
            "why": "Search results use the title tag as the main link text.",
            "recommendation": "Aim for roughly 30–60 characters that describe the page.",
            "items": items,
        }
    return {
        "id": "title",
        "title": "Page title",
        "status": "pass",
        "score": 15,
        "maxScore": 15,
        "summary": "Title is present and a good length.",
        "why": "Search results use the title tag as the main link text.",
        "recommendation": "",
        "items": items,
    }


def _check_meta(soup: BeautifulSoup) -> dict[str, Any]:
    meta = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    desc = (meta.get("content", "").strip() if meta else "") or ""
    length = len(desc)
    items = [{"label": "Description", "value": desc or "Missing"}, {"label": "Length", "value": f"{length} characters"}]
    if not desc:
        return {
            "id": "meta",
            "title": "Meta description",
            "status": "error",
            "score": 0,
            "maxScore": 15,
            "summary": "No meta description was found.",
            "why": "A clear summary helps searchers decide to open the page.",
            "recommendation": "Add a meta description of about 70–160 characters.",
            "items": items,
        }
    if length < 70 or length > 160:
        return {
            "id": "meta",
            "title": "Meta description",
            "status": "warning",
            "score": 10,
            "maxScore": 15,
            "summary": "Meta description is present but length is outside the usual range.",
            "why": "A clear summary helps searchers decide to open the page.",
            "recommendation": "Aim for roughly 70–160 characters.",
            "items": items,
        }
    return {
        "id": "meta",
        "title": "Meta description",
        "status": "pass",
        "score": 15,
        "maxScore": 15,
        "summary": "Meta description is present and a good length.",
        "why": "A clear summary helps searchers decide to open the page.",
        "recommendation": "",
        "items": items,
    }


def _check_headings(soup: BeautifulSoup) -> dict[str, Any]:
    h1 = soup.find_all("h1")
    h2 = soup.find_all("h2")
    h3 = soup.find_all("h3")
    items = [
        {"label": "H1", "value": str(len(h1))},
        {"label": "H2", "value": str(len(h2))},
        {"label": "H3", "value": str(len(h3))},
    ]
    if len(h1) == 0:
        return {
            "id": "headings",
            "title": "Headings",
            "status": "error",
            "score": 0,
            "maxScore": 15,
            "summary": "No H1 heading was found.",
            "why": "Headings outline the page for people and for crawlers.",
            "recommendation": "Add one clear H1 that names the main topic.",
            "items": items,
        }
    if len(h1) > 1:
        return {
            "id": "headings",
            "title": "Headings",
            "status": "warning",
            "score": 8,
            "maxScore": 15,
            "summary": "More than one H1 was found.",
            "why": "Headings outline the page for people and for crawlers.",
            "recommendation": "Keep a single main H1, then use H2 and H3 for sections.",
            "items": items,
        }
    if not h2 and not h3:
        return {
            "id": "headings",
            "title": "Headings",
            "status": "warning",
            "score": 10,
            "maxScore": 15,
            "summary": "One H1 is present, but H2 and H3 are missing.",
            "why": "Headings outline the page for people and for crawlers.",
            "recommendation": "Add section headings under the main H1.",
            "items": items,
        }
    return {
        "id": "headings",
        "title": "Headings",
        "status": "pass",
        "score": 15,
        "maxScore": 15,
        "summary": "Heading structure looks clear.",
        "why": "Headings outline the page for people and for crawlers.",
        "recommendation": "",
        "items": items,
    }


def _check_images(soup: BeautifulSoup) -> dict[str, Any]:
    imgs = soup.find_all("img")
    missing = 0
    for img in imgs:
        alt = img.get("alt")
        if alt is None or str(alt).strip() == "":
            missing += 1
    items = [
        {"label": "Images", "value": str(len(imgs))},
        {"label": "Missing alt", "value": str(missing)},
    ]
    if not imgs:
        return {
            "id": "images",
            "title": "Image alt text",
            "status": "pass",
            "score": 15,
            "maxScore": 15,
            "summary": "No images found on this page.",
            "why": "Alt text describes images when they cannot be seen.",
            "recommendation": "",
            "items": items,
        }
    if missing:
        status = "error" if missing == len(imgs) else "warning"
        score = 0 if status == "error" else 8
        return {
            "id": "images",
            "title": "Image alt text",
            "status": status,
            "score": score,
            "maxScore": 15,
            "summary": f"{missing} of {len(imgs)} images are missing alt text.",
            "why": "Alt text describes images when they cannot be seen.",
            "recommendation": "Add meaningful alt text to content images.",
            "items": items,
        }
    return {
        "id": "images",
        "title": "Image alt text",
        "status": "pass",
        "score": 15,
        "maxScore": 15,
        "summary": "All images include alt text.",
        "why": "Alt text describes images when they cannot be seen.",
        "recommendation": "",
        "items": items,
    }


def _check_links(soup: BeautifulSoup, base: str) -> dict[str, Any]:
    host = urlparse(base).netloc
    internal = 0
    external = 0
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
            continue
        abs_url = urljoin(base, href)
        p = urlparse(abs_url)
        if p.scheme not in ("http", "https"):
            continue
        if p.netloc == host:
            internal += 1
        else:
            external += 1
    items = [
        {"label": "Internal", "value": str(internal)},
        {"label": "External", "value": str(external)},
    ]
    if internal + external == 0:
        return {
            "id": "links",
            "title": "Links",
            "status": "warning",
            "score": 5,
            "maxScore": 10,
            "summary": "No crawlable links were found.",
            "why": "Internal and external links show how the page connects to the web.",
            "recommendation": "Add useful internal links where they help readers.",
            "items": items,
        }
    return {
        "id": "links",
        "title": "Links",
        "status": "pass",
        "score": 10,
        "maxScore": 10,
        "summary": "Internal and external links were counted.",
        "why": "Internal and external links show how the page connects to the web.",
        "recommendation": "",
        "items": items,
    }


def _check_url(url: str) -> dict[str, Any]:
    p = urlparse(url)
    items = [
        {"label": "Scheme", "value": p.scheme},
        {"label": "Host", "value": p.netloc},
        {"label": "Path", "value": p.path or "/"},
    ]
    score = 10
    status = "pass"
    notes = []
    if p.scheme != "https":
        score -= 5
        status = "warning"
        notes.append("Prefer HTTPS.")
    if not p.netloc or "." not in p.netloc:
        score = 0
        status = "error"
        notes.append("Domain looks incomplete.")
    path = p.path or "/"
    if len(path) > 120 or " " in path:
        score = min(score, 5)
        status = "warning" if status == "pass" else status
        notes.append("Path is long or contains spaces.")
    summary = "HTTPS with a clear domain." if status == "pass" else " ".join(notes) or "URL needs attention."
    return {
        "id": "url",
        "title": "URL structure",
        "status": status,
        "score": max(0, score),
        "maxScore": 10,
        "summary": summary,
        "why": "A clean, secure URL is easier to share and trust.",
        "recommendation": "" if status == "pass" else "Use HTTPS and a short, readable path.",
        "items": items,
    }


def _check_robots(origin: str) -> dict[str, Any]:
    url = urljoin(origin, "/robots.txt")
    found = _head_ok(url)
    items = [{"label": "URL", "value": url}, {"label": "Found", "value": "Yes" if found else "No"}]
    if found:
        return {
            "id": "robots",
            "title": "robots.txt",
            "status": "pass",
            "score": 10,
            "maxScore": 10,
            "summary": "robots.txt was found at the site root.",
            "why": "Crawlers look for robots.txt to learn crawl rules.",
            "recommendation": "",
            "items": items,
        }
    return {
        "id": "robots",
        "title": "robots.txt",
        "status": "error",
        "score": 0,
        "maxScore": 10,
        "summary": "robots.txt was not found at the site root.",
        "why": "Crawlers look for robots.txt to learn crawl rules.",
        "recommendation": f"Publish a robots.txt file at {url}",
        "items": items,
    }


def _check_sitemap(origin: str) -> dict[str, Any]:
    candidates = [
        urljoin(origin, "/sitemap.xml"),
        urljoin(origin, "/sitemap_index.xml"),
    ]
    found_url = ""
    for c in candidates:
        if _head_ok(c):
            found_url = c
            break
    items = [{"label": "URL", "value": found_url or candidates[0]}, {"label": "Found", "value": "Yes" if found_url else "No"}]
    if found_url:
        return {
            "id": "sitemap",
            "title": "sitemap.xml",
            "status": "pass",
            "score": 10,
            "maxScore": 10,
            "summary": "A sitemap was found.",
            "why": "A sitemap lists important pages for discovery.",
            "recommendation": "",
            "items": items,
        }
    return {
        "id": "sitemap",
        "title": "sitemap.xml",
        "status": "warning",
        "score": 4,
        "maxScore": 10,
        "summary": "No sitemap.xml was found at common paths.",
        "why": "A sitemap lists important pages for discovery.",
        "recommendation": f"Publish a sitemap at {candidates[0]} when the site has many pages.",
        "items": items,
    }


def _grade(score: int) -> str:
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 50:
        return "Needs work"
    return "Poor"


def _overall_status(checks: list[dict[str, Any]]) -> str:
    if any(c["status"] == "error" for c in checks):
        return "error"
    if any(c["status"] == "warning" for c in checks):
        return "warning"
    return "pass"


def run_audit(raw_url: str) -> dict[str, Any]:
    url = _normalize_url(raw_url)
    try:
        html, status_code, fetch_ms, final_url = _fetch(url)
    except requests.RequestException as e:
        raise ValueError(f"Could not fetch the page: {e}") from e

    if status_code >= 400:
        raise ValueError(f"The page returned HTTP {status_code}.")

    soup = BeautifulSoup(html, "lxml")
    parsed = urlparse(final_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    checks = [
        _check_title(soup),
        _check_meta(soup),
        _check_headings(soup),
        _check_images(soup),
        _check_links(soup, final_url),
        _check_url(final_url),
        _check_robots(origin),
        _check_sitemap(origin),
    ]

    score = sum(int(c["score"]) for c in checks)
    score = max(0, min(100, score))
    passed = sum(1 for c in checks if c["status"] == "pass")
    warnings = sum(1 for c in checks if c["status"] == "warning")
    errors = sum(1 for c in checks if c["status"] == "error")

    recommendations = []
    for c in checks:
        if c["status"] in ("error", "warning") and c.get("recommendation"):
            recommendations.append(
                {
                    "priority": c["status"],
                    "title": c["title"],
                    "body": c["recommendation"],
                }
            )

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    imgs = soup.find_all("img")
    missing_alt = sum(1 for img in imgs if img.get("alt") is None or str(img.get("alt")).strip() == "")

    return {
        "id": str(uuid.uuid4()),
        "sample": False,
        "url": url,
        "fetchedUrl": final_url,
        "statusCode": status_code,
        "fetchMs": fetch_ms,
        "analyzedAt": _now(),
        "score": score,
        "grade": _grade(score),
        "status": _overall_status(checks),
        "passed": passed,
        "warnings": warnings,
        "errors": errors,
        "page": {
            "title": title,
            "h1Count": len(soup.find_all("h1")),
            "h2Count": len(soup.find_all("h2")),
            "h3Count": len(soup.find_all("h3")),
            "imageCount": len(imgs),
            "missingAltCount": missing_alt,
            "internalLinks": next((i["value"] for c in checks if c["id"] == "links" for i in c["items"] if i["label"] == "Internal"), "0"),
            "externalLinks": next((i["value"] for c in checks if c["id"] == "links" for i in c["items"] if i["label"] == "External"), "0"),
            "robotsFound": any(c["id"] == "robots" and c["status"] == "pass" for c in checks),
            "sitemapFound": any(c["id"] == "sitemap" and c["status"] == "pass" for c in checks),
        },
        "recommendations": recommendations,
        "checks": checks,
    }
