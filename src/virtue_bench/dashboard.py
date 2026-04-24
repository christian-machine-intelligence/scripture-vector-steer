"""Lightweight live dashboard for watching VirtueBench experiment artifacts."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import tempfile
from collections import Counter, deque, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from .core.schema import RunResult


STAGES = ("smoke", "ratio", "full")
DEFAULT_REMOTE_PASSWORD_ENV = "VIRTUE_BENCH_REMOTE_PASSWORD"
RESULTS_DIR = Path(__file__).resolve().parents[3] / "results"


@dataclass(frozen=True)
class DashboardConfig:
    """Configuration for the live dashboard server."""

    output_prefix: str
    host: str = "127.0.0.1"
    port: int = 8765
    refresh_seconds: int = 5
    results_dir: Path = RESULTS_DIR
    remote_host: Optional[str] = None
    remote_user: Optional[str] = None
    remote_password_env: str = DEFAULT_REMOTE_PASSWORD_ENV
    remote_results_dir: Optional[str] = None


def _artifact_specs(prefix: str) -> list[dict[str, str]]:
    specs = [
        {"key": "launcher_status", "relative_path": f"{prefix}.status", "mode": "raw"},
        {"key": "launcher_pid", "relative_path": f"{prefix}.pid", "mode": "raw"},
        {"key": "console_log", "relative_path": f"{prefix}_console.log", "mode": "tail"},
        {"key": "preflight", "relative_path": f"{prefix}_preflight.json", "mode": "raw"},
        {"key": "vectors", "relative_path": f"{prefix}_vectors.pt", "mode": "none"},
    ]
    for stage in STAGES:
        specs.extend(
            [
                {
                    "key": f"{stage}_status",
                    "relative_path": f"{prefix}_{stage}.status.json",
                    "mode": "raw",
                },
                {
                    "key": f"{stage}_results",
                    "relative_path": f"{prefix}_{stage}.json",
                    "mode": "raw",
                },
                {
                    "key": f"{stage}_logs",
                    "relative_path": f"{prefix}_{stage}_logs.json",
                    "mode": "none",
                },
                {
                    "key": f"{stage}_checkpoint",
                    "relative_path": f"{prefix}_{stage}_checkpoint.json",
                    "mode": "raw",
                },
                {
                    "key": f"{stage}_discernment",
                    "relative_path": f"{prefix}_{stage}_discernment.json",
                    "mode": "none",
                },
            ]
        )
    return specs


def _tail_text(path: Path, *, max_lines: int = 120) -> str:
    lines: deque[str] = deque(maxlen=max_lines)
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            lines.append(line.rstrip("\n"))
    return "\n".join(lines)


def _collect_local_snapshot(config: DashboardConfig) -> dict[str, Any]:
    files: dict[str, dict[str, Any]] = {}
    for spec in _artifact_specs(config.output_prefix):
        path = config.results_dir / spec["relative_path"]
        if not path.exists():
            continue

        record: dict[str, Any] = {
            "exists": True,
            "relative_path": spec["relative_path"],
            "length": path.stat().st_size,
            "modified": datetime.fromtimestamp(
                path.stat().st_mtime,
                tz=timezone.utc,
            ).isoformat(),
        }
        if spec["mode"] == "raw":
            record["text"] = path.read_text(encoding="utf-8", errors="replace")
        elif spec["mode"] == "tail":
            record["text"] = _tail_text(path)
        files[spec["key"]] = record

    return {
        "source": {
            "kind": "local",
            "results_dir": str(config.results_dir),
        },
        "files": files,
    }


def _escape_powershell(value: str) -> str:
    return value.replace("'", "''")


def _run_ssh_with_password(
    host: str,
    user: str,
    password_env: str,
    remote_command: str,
    *,
    stdin_text: Optional[str] = None,
) -> str:
    password = os.environ.get(password_env)
    if not password:
        raise RuntimeError(
            f"Remote dashboard polling needs ${password_env} set in the environment."
        )

    with tempfile.TemporaryDirectory(prefix="virtue-bench-askpass-") as temp_dir:
        askpass = Path(temp_dir) / "askpass.sh"
        askpass.write_text(
            "#!/bin/sh\n"
            f"printf %s \"${password_env}\"\n",
            encoding="utf-8",
        )
        askpass.chmod(0o700)

        env = os.environ.copy()
        env["SSH_ASKPASS"] = str(askpass)
        env["SSH_ASKPASS_REQUIRE"] = "force"
        env.setdefault("DISPLAY", "virtue-bench-dashboard")

        proc = subprocess.run(
            [
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "ConnectTimeout=10",
                f"{user}@{host}",
                remote_command,
            ],
            input=stdin_text,
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
            check=False,
        )

    if proc.returncode != 0:
        stderr = proc.stderr.strip()
        raise RuntimeError(stderr or "remote ssh command failed")

    return proc.stdout


def _collect_remote_snapshot(config: DashboardConfig) -> dict[str, Any]:
    if not config.remote_host or not config.remote_user:
        raise RuntimeError("remote_host and remote_user are required for remote monitoring")

    remote_results_dir = config.remote_results_dir or (
        f"C:\\Users\\{config.remote_user}\\work\\virtue-bench-2\\results"
    )

    def fetch_record(relative_path: str, mode: str) -> Optional[dict[str, Any]]:
        windows_relative_path = relative_path.replace("/", "\\")
        escaped_path = _escape_powershell(
            f"{remote_results_dir}\\{windows_relative_path}"
        )
        escaped_rel = _escape_powershell(windows_relative_path)
        if mode == "raw":
            text_expr = "[System.IO.File]::ReadAllText($path)"
        elif mode == "tail":
            text_expr = "((Get-Content -Path $path -Tail 120) -join \"`n\")"
        else:
            text_expr = "$null"

        script = (
            f"$relativePath = '{escaped_rel}'\n"
            f"$path = '{escaped_path}'\n"
            "if (Test-Path $path) {\n"
            "    $item = Get-Item $path\n"
            "    $record = @{\n"
            "        exists = $true\n"
            "        relative_path = $relativePath\n"
            "        length = [int64]$item.Length\n"
            "        modified = $item.LastWriteTimeUtc.ToString('o')\n"
            "    }\n"
            f"    $text = {text_expr}\n"
            "    if ($null -ne $text) {\n"
            "        $record.text_b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes([string]$text))\n"
            "    }\n"
            "    Write-Output ($record | ConvertTo-Json -Compress)\n"
            "}\n"
        )
        output = _run_ssh_with_password(
            config.remote_host,
            config.remote_user,
            config.remote_password_env,
            "powershell -NoProfile -Command -",
            stdin_text=script,
        ).strip()
        if not output:
            return None
        record = json.loads(output)
        text_b64 = record.pop("text_b64", None)
        if text_b64 is not None:
            record["text"] = base64.b64decode(text_b64.encode("ascii")).decode("utf-8", errors="replace")
        return record

    files: dict[str, dict[str, Any]] = {}
    for spec in _artifact_specs(config.output_prefix):
        record = fetch_record(spec["relative_path"], spec["mode"])
        if record is not None:
            files[spec["key"]] = record

    return {
        "source": {
            "kind": "remote_windows",
            "host": config.remote_host,
            "user": config.remote_user,
            "results_dir": remote_results_dir,
        },
        "files": files,
    }


def _parse_json_file(files: dict[str, Any], key: str) -> Optional[Any]:
    text = files.get(key, {}).get("text")
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return None


def _format_status_counts(results: Iterable[RunResult]) -> str:
    counts = Counter(result.status for result in results)
    return ", ".join(f"{status}×{count}" for status, count in sorted(counts.items()))


def _summarize_stage_results(results: list[RunResult]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[RunResult]] = defaultdict(list)
    for result in results:
        grouped[(result.virtue, result.variant, result.condition)].append(result)

    rows = []
    for (virtue, variant, condition), bucket in sorted(grouped.items()):
        accuracies = [item.accuracy for item in bucket if item.accuracy is not None]
        mean_accuracy = (sum(accuracies) / len(accuracies)) if accuracies else None
        rows.append(
            {
                "virtue": virtue,
                "variant": variant,
                "condition": condition,
                "runs_seen": len(bucket),
                "mean_accuracy": mean_accuracy,
                "status_counts": _format_status_counts(bucket),
                "samples": max((item.samples for item in bucket), default=0),
            }
        )
    return rows


def _build_stage_state(stage: str, files: dict[str, Any]) -> Optional[dict[str, Any]]:
    stage_status = _parse_json_file(files, f"{stage}_status")
    results_payload = _parse_json_file(files, f"{stage}_results")
    checkpoint_payload = _parse_json_file(files, f"{stage}_checkpoint")

    parsed_results: list[RunResult] = []
    for payload in (results_payload, checkpoint_payload):
        if not payload:
            continue
        try:
            parsed_results = [RunResult(**row) for row in payload]
            break
        except Exception:
            continue

    has_anything = stage_status is not None or bool(parsed_results) or f"{stage}_logs" in files
    if not has_anything:
        return None

    progress = None
    current = None
    if stage_status:
        total_runs = int(stage_status.get("total_runs") or 0)
        completed_runs = int(stage_status.get("completed_runs") or 0)
        progress = {
            "completed_runs": completed_runs,
            "total_runs": total_runs,
            "percent": (completed_runs / total_runs * 100.0) if total_runs else 0.0,
        }
        current = {
            "virtue": stage_status.get("virtue"),
            "variant": stage_status.get("variant"),
            "condition": stage_status.get("condition"),
            "run_index": stage_status.get("run_index"),
            "note": stage_status.get("note"),
            "state": stage_status.get("state"),
            "updated_at": stage_status.get("updated_at"),
        }

    return {
        "name": stage,
        "status": stage_status,
        "progress": progress,
        "rows": _summarize_stage_results(parsed_results),
        "results_written": f"{stage}_results" in files,
        "logs_written": f"{stage}_logs" in files,
        "checkpoint_written": f"{stage}_checkpoint" in files,
        "current": current,
    }


def _build_overall_state(
    files: dict[str, Any],
    preflight: Optional[dict[str, Any]],
    stages: list[dict[str, Any]],
) -> tuple[str, str]:
    launcher_status = (files.get("launcher_status", {}).get("text") or "").strip().upper()
    if launcher_status == "FAILED":
        return "failed", "Launcher marked the run as FAILED."
    for stage in stages:
        current = stage.get("current") or {}
        if current.get("state") == "running":
            progress = stage.get("progress") or {}
            return (
                "running",
                f"{stage['name'].capitalize()} stage running "
                f"({progress.get('completed_runs', 0)}/{progress.get('total_runs', 0)} cells).",
            )
    if preflight and preflight.get("status") == "failed":
        return "failed", "Preflight divergence gate failed before stage execution."
    for stage in stages:
        current = stage.get("current") or {}
        if current.get("state") == "completed":
            return "completed", f"{stage['name'].capitalize()} stage completed."
    if launcher_status == "STARTED":
        return "running", "Launcher started; waiting for the first stage artifact."
    if preflight and preflight.get("status") == "passed":
        return "ready", "Preflight passed."
    return "idle", "Waiting for experiment artifacts."


def build_dashboard_state(snapshot: dict[str, Any], *, output_prefix: str) -> dict[str, Any]:
    files = snapshot.get("files", {})
    preflight = _parse_json_file(files, "preflight")

    preflight_summary = None
    if preflight:
        row_statuses = Counter(row.get("status", "unknown") for row in preflight.get("rows", []))
        preflight_summary = {
            "status": preflight.get("status"),
            "variant": preflight.get("variant"),
            "alpha_scale": preflight.get("alpha_scale"),
            "counts": dict(sorted(row_statuses.items())),
            "rows": preflight.get("rows", []),
        }

    stages = []
    for stage in STAGES:
        stage_state = _build_stage_state(stage, files)
        if stage_state is not None:
            stages.append(stage_state)

    overall_state, headline = _build_overall_state(files, preflight, stages)

    artifacts = []
    for spec in _artifact_specs(output_prefix):
        file_record = files.get(spec["key"])
        if not file_record:
            continue
        artifacts.append(
            {
                "key": spec["key"],
                "path": file_record.get("relative_path", spec["relative_path"]),
                "length": file_record.get("length"),
                "modified": file_record.get("modified"),
            }
        )

    return {
        "output_prefix": output_prefix,
        "source": snapshot.get("source", {}),
        "overall_state": overall_state,
        "headline": headline,
        "launcher_status": (files.get("launcher_status", {}).get("text") or "").strip() or None,
        "launcher_pid": (files.get("launcher_pid", {}).get("text") or "").strip() or None,
        "artifacts": artifacts,
        "preflight": preflight_summary,
        "stages": stages,
        "console_log_tail": files.get("console_log", {}).get("text") or "",
        "last_refreshed": datetime.now(timezone.utc).isoformat(),
    }


def _snapshot_for_dashboard(config: DashboardConfig) -> dict[str, Any]:
    if config.remote_host:
        return _collect_remote_snapshot(config)
    return _collect_local_snapshot(config)


def _dashboard_html(config: DashboardConfig) -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>VirtueBench Live Monitor</title>
    <style>
      :root {{
        --ink: #211a15;
        --muted: #6c6258;
        --paper: #f6f0e6;
        --card: rgba(255, 250, 242, 0.88);
        --line: rgba(96, 73, 49, 0.16);
        --accent: #9b5d2e;
        --accent-soft: rgba(155, 93, 46, 0.14);
        --good: #2f6f3b;
        --warn: #b07014;
        --bad: #9f2d27;
        --shadow: 0 18px 40px rgba(61, 40, 21, 0.10);
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(201, 156, 108, 0.26), transparent 34%),
          radial-gradient(circle at top right, rgba(109, 136, 117, 0.18), transparent 28%),
          linear-gradient(180deg, #fbf7f0 0%, #efe5d5 100%);
        min-height: 100vh;
      }}
      .shell {{
        max-width: 1320px;
        margin: 0 auto;
        padding: 28px;
      }}
      .hero {{
        display: grid;
        grid-template-columns: 1.6fr 1fr;
        gap: 18px;
        align-items: stretch;
        margin-bottom: 18px;
      }}
      .panel {{
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 22px;
        box-shadow: var(--shadow);
        backdrop-filter: blur(10px);
      }}
      .hero-main {{
        padding: 24px 26px 22px;
      }}
      .hero-meta {{
        padding: 22px;
        display: grid;
        gap: 12px;
      }}
      .eyebrow {{
        font-size: 12px;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--muted);
        margin-bottom: 10px;
      }}
      h1 {{
        margin: 0 0 10px;
        font-size: clamp(30px, 4vw, 48px);
        line-height: 0.98;
      }}
      .headline {{
        margin: 0;
        color: var(--muted);
        font-size: 18px;
        line-height: 1.35;
      }}
      .badge {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border-radius: 999px;
        padding: 8px 14px;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        width: fit-content;
      }}
      .badge.running {{ background: rgba(155, 93, 46, 0.14); color: var(--accent); }}
      .badge.completed {{ background: rgba(47, 111, 59, 0.14); color: var(--good); }}
      .badge.failed {{ background: rgba(159, 45, 39, 0.14); color: var(--bad); }}
      .badge.ready {{ background: rgba(47, 111, 59, 0.14); color: var(--good); }}
      .badge.idle {{ background: rgba(108, 98, 88, 0.14); color: var(--muted); }}
      .stat-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }}
      .stat {{
        padding: 14px 15px;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.48);
        border: 1px solid var(--line);
      }}
      .stat-label {{
        font-size: 11px;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--muted);
        margin-bottom: 6px;
      }}
      .stat-value {{
        font-size: 15px;
        line-height: 1.35;
        word-break: break-word;
      }}
      .section {{
        margin-top: 18px;
      }}
      .section-head {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 12px;
      }}
      .section-title {{
        margin: 0;
        font-size: 24px;
      }}
      .artifact-list {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }}
      .artifact {{
        border-radius: 999px;
        padding: 8px 12px;
        background: rgba(255, 255, 255, 0.56);
        border: 1px solid var(--line);
        font-size: 13px;
      }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(12, minmax(0, 1fr));
        gap: 18px;
      }}
      .span-7 {{ grid-column: span 7; }}
      .span-5 {{ grid-column: span 5; }}
      .span-12 {{ grid-column: span 12; }}
      .card-body {{
        padding: 20px 22px 22px;
      }}
      .progress-track {{
        margin-top: 14px;
        width: 100%;
        height: 12px;
        background: rgba(130, 104, 77, 0.14);
        border-radius: 999px;
        overflow: hidden;
      }}
      .progress-bar {{
        height: 100%;
        background: linear-gradient(90deg, #8b542b, #c68952);
        border-radius: 999px;
      }}
      table {{
        width: 100%;
        border-collapse: collapse;
      }}
      th, td {{
        text-align: left;
        padding: 10px 12px;
        border-bottom: 1px solid var(--line);
        vertical-align: top;
      }}
      th {{
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--muted);
      }}
      td {{
        font-size: 14px;
      }}
      .pill {{
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 3px 9px;
        font-size: 12px;
        background: var(--accent-soft);
        color: var(--accent);
      }}
      .pill.fail {{ background: rgba(159, 45, 39, 0.14); color: var(--bad); }}
      .pill.warn {{ background: rgba(176, 112, 20, 0.14); color: var(--warn); }}
      .log {{
        font-family: Menlo, Consolas, "SFMono-Regular", monospace;
        font-size: 12px;
        line-height: 1.45;
        white-space: pre-wrap;
        background: rgba(33, 26, 21, 0.92);
        color: #f7f2ea;
        padding: 18px;
        border-radius: 18px;
        min-height: 180px;
        overflow: auto;
      }}
      .empty {{
        color: var(--muted);
        font-style: italic;
      }}
      @media (max-width: 980px) {{
        .hero {{ grid-template-columns: 1fr; }}
        .span-7, .span-5, .span-12 {{ grid-column: span 12; }}
      }}
    </style>
  </head>
  <body>
    <div class="shell">
      <div class="hero">
        <section class="panel hero-main">
          <div class="eyebrow">VirtueBench Live Monitor</div>
          <div id="badge" class="badge idle">Waiting</div>
          <h1 id="title">Loading run status…</h1>
          <p id="headline" class="headline"></p>
        </section>
        <aside class="panel hero-meta">
          <div class="stat-grid">
            <div class="stat">
              <div class="stat-label">Output Prefix</div>
              <div id="prefix" class="stat-value"></div>
            </div>
            <div class="stat">
              <div class="stat-label">Source</div>
              <div id="source" class="stat-value"></div>
            </div>
            <div class="stat">
              <div class="stat-label">Launcher</div>
              <div id="launcher" class="stat-value"></div>
            </div>
            <div class="stat">
              <div class="stat-label">Last Refresh</div>
              <div id="refreshed" class="stat-value"></div>
            </div>
          </div>
        </aside>
      </div>

      <section class="section">
        <div class="section-head">
          <h2 class="section-title">Artifacts</h2>
          <div id="artifactCount" class="pill">0 files</div>
        </div>
        <div id="artifacts" class="artifact-list"></div>
      </section>

      <div class="grid section">
        <section class="panel span-7">
          <div class="card-body">
            <div class="section-head">
              <h2 class="section-title">Preflight</h2>
              <div id="preflightBadge" class="pill">No preflight yet</div>
            </div>
            <div id="preflightSummary" class="headline"></div>
            <div id="preflightRows" class="section"></div>
          </div>
        </section>

        <section class="panel span-5">
          <div class="card-body">
            <div class="section-head">
              <h2 class="section-title">Current Stage</h2>
            </div>
            <div id="stageCards"></div>
          </div>
        </section>
      </div>

      <section class="section">
        <div class="section-head">
          <h2 class="section-title">Stage Results</h2>
        </div>
        <div id="stageTables"></div>
      </section>

      <section class="section">
        <div class="section-head">
          <h2 class="section-title">Console Tail</h2>
        </div>
        <div id="console" class="log">Waiting for log output…</div>
      </section>
    </div>

    <script>
      const refreshMs = {config.refresh_seconds * 1000};

      function escapeHtml(value) {{
        return String(value ?? "")
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;")
          .replaceAll("'", "&#39;");
      }}

      function formatPercent(value) {{
        if (value === null || value === undefined) return "—";
        return `${{(value * 100).toFixed(2)}}%`;
      }}

      function formatTimestamp(value) {{
        if (!value) return "—";
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value;
        return date.toLocaleString();
      }}

      function renderArtifacts(artifacts) {{
        const target = document.getElementById("artifacts");
        document.getElementById("artifactCount").textContent = `${{artifacts.length}} files`;
        if (!artifacts.length) {{
          target.innerHTML = '<div class="empty">No artifacts written yet.</div>';
          return;
        }}
        target.innerHTML = artifacts.map((artifact) => `
          <div class="artifact">
            <strong>${{escapeHtml(artifact.key)}}</strong>
            <span> · ${{escapeHtml(artifact.path)}}</span>
          </div>
        `).join("");
      }}

      function renderPreflight(preflight) {{
        const badge = document.getElementById("preflightBadge");
        const summary = document.getElementById("preflightSummary");
        const rows = document.getElementById("preflightRows");
        if (!preflight) {{
          badge.className = "pill";
          badge.textContent = "No preflight yet";
          summary.textContent = "The run has not written a preflight artifact yet.";
          rows.innerHTML = "";
          return;
        }}
        const counts = Object.entries(preflight.counts || {{}})
          .map(([label, count]) => `${{label}}×${{count}}`)
          .join(", ");
        const badgeClass = preflight.status === "failed" ? "pill fail"
          : preflight.status === "warning" ? "pill warn"
          : "pill";
        badge.className = badgeClass;
        badge.textContent = preflight.status || "unknown";
        summary.textContent = `Variant ${{preflight.variant}} at alpha scale ${{preflight.alpha_scale}}. ${{counts || "No row counts."}}`;
        if (!(preflight.rows || []).length) {{
          rows.innerHTML = '<div class="empty">No preflight rows available.</div>';
          return;
        }}
        rows.innerHTML = `
          <table>
            <thead>
              <tr>
                <th>Virtue</th>
                <th>Status</th>
                <th>Control</th>
                <th>Steer</th>
                <th>Null</th>
                <th>Answer changes</th>
                <th>Null changes</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              ${{preflight.rows.map((row) => `
                <tr>
                  <td>${{escapeHtml(row.virtue)}}</td>
                  <td><span class="pill ${{row.status === "fail" ? "fail" : row.status === "warn" ? "warn" : ""}}">${{escapeHtml(row.status)}}</span></td>
                  <td>${{formatPercent(row.control_accuracy)}}</td>
                  <td>${{formatPercent(row.steer_accuracy)}}</td>
                  <td>${{formatPercent(row.null_accuracy)}}</td>
                  <td>${{escapeHtml(row.answer_changes)}}</td>
                  <td>${{escapeHtml(row.null_answer_changes)}}</td>
                  <td>${{escapeHtml((row.notes || []).join("; ") || "—")}}</td>
                </tr>
              `).join("")}}
            </tbody>
          </table>
        `;
      }}

      function renderStages(stages) {{
        const cards = document.getElementById("stageCards");
        const tables = document.getElementById("stageTables");
        if (!stages.length) {{
          cards.innerHTML = '<div class="empty">No stage status files yet.</div>';
          tables.innerHTML = '<div class="empty">No stage summaries yet.</div>';
          return;
        }}
        cards.innerHTML = stages.map((stage) => {{
          const current = stage.current || {{}};
          const progress = stage.progress;
          const note = current.note ? `<div class="headline">${{escapeHtml(current.note)}}</div>` : "";
          const currentLine = current.virtue
            ? `<div class="headline">${{escapeHtml(current.virtue)}} / ${{escapeHtml(current.variant)}} / ${{escapeHtml(current.condition)}} (run ${{(current.run_index ?? 0) + 1}})</div>`
            : '<div class="headline">No current cell recorded.</div>';
          const progressBlock = progress
            ? `
              <div class="headline">${{progress.completed_runs}} / ${{progress.total_runs}} cells</div>
              <div class="progress-track"><div class="progress-bar" style="width:${{progress.percent}}%"></div></div>
            `
            : '<div class="headline">No progress JSON yet.</div>';
          return `
            <div class="panel" style="margin-bottom: 14px;">
              <div class="card-body">
                <div class="section-head">
                  <h3 style="margin:0;">${{escapeHtml(stage.name)}}</h3>
                  <span class="pill">${{escapeHtml((current.state || stage.status?.state || "unknown"))}}</span>
                </div>
                ${{currentLine}}
                ${{note}}
                ${{progressBlock}}
              </div>
            </div>
          `;
        }}).join("");

        tables.innerHTML = stages.map((stage) => {{
          if (!(stage.rows || []).length) {{
            return `
              <div class="panel" style="margin-bottom:14px;">
                <div class="card-body">
                  <div class="section-head">
                    <h3 style="margin:0;">${{escapeHtml(stage.name)}}</h3>
                    <span class="pill">${{escapeHtml(stage.status?.state || "no rows")}}</span>
                  </div>
                  <div class="empty">No stage result rows yet.</div>
                </div>
              </div>
            `;
          }}
          return `
            <div class="panel" style="margin-bottom: 14px;">
              <div class="card-body">
                <div class="section-head">
                  <h3 style="margin:0;">${{escapeHtml(stage.name)}}</h3>
                  <span class="pill">${{stage.results_written ? "results saved" : "checkpoint only"}}</span>
                </div>
                <table>
                  <thead>
                    <tr>
                      <th>Virtue</th>
                      <th>Variant</th>
                      <th>Condition</th>
                      <th>Runs</th>
                      <th>Accuracy</th>
                      <th>Samples</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${{stage.rows.map((row) => `
                      <tr>
                        <td>${{escapeHtml(row.virtue)}}</td>
                        <td>${{escapeHtml(row.variant)}}</td>
                        <td>${{escapeHtml(row.condition)}}</td>
                        <td>${{escapeHtml(row.runs_seen)}}</td>
                        <td>${{formatPercent(row.mean_accuracy)}}</td>
                        <td>${{escapeHtml(row.samples)}}</td>
                        <td>${{escapeHtml(row.status_counts)}}</td>
                      </tr>
                    `).join("")}}
                  </tbody>
                </table>
              </div>
            </div>
          `;
        }}).join("");
      }}

      async function loadState() {{
        const response = await fetch("/api/state");
        const data = await response.json();
        if (data.error) {{
          document.getElementById("title").textContent = "Dashboard error";
          document.getElementById("headline").textContent = data.error;
          return;
        }}

        const badge = document.getElementById("badge");
        badge.className = `badge ${{data.overall_state || "idle"}}`;
        badge.textContent = data.overall_state || "idle";
        document.getElementById("title").textContent = "Watching " + (data.output_prefix || "run");
        document.getElementById("headline").textContent = data.headline || "";
        document.getElementById("prefix").textContent = data.output_prefix || "—";
        document.getElementById("source").textContent =
          data.source?.kind === "remote_windows"
            ? `${{data.source.user}} @ ${{data.source.host}}`
            : (data.source?.results_dir || "local");
        document.getElementById("launcher").textContent =
          [data.launcher_status, data.launcher_pid ? `pid ${{data.launcher_pid}}` : null]
            .filter(Boolean)
            .join(" · ") || "—";
        document.getElementById("refreshed").textContent = formatTimestamp(data.last_refreshed);
        renderArtifacts(data.artifacts || []);
        renderPreflight(data.preflight);
        renderStages(data.stages || []);
        document.getElementById("console").textContent =
          data.console_log_tail || "No console log yet.";
      }}

      loadState();
      setInterval(loadState, refreshMs);
    </script>
  </body>
</html>
"""


def serve_dashboard(config: DashboardConfig) -> None:
    """Serve a live dashboard for a specific output prefix."""

    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            if self.path in {"/", "/index.html"}:
                html = _dashboard_html(config).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html)))
                self.end_headers()
                self.wfile.write(html)
                return

            if self.path == "/api/state":
                try:
                    snapshot = _snapshot_for_dashboard(config)
                    payload = build_dashboard_state(snapshot, output_prefix=config.output_prefix)
                except Exception as exc:  # pragma: no cover - exercised manually
                    payload = {"error": str(exc)}

                body = json.dumps(payload, indent=2).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            self.send_response(404)
            self.end_headers()

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

    server = ThreadingHTTPServer((config.host, config.port), DashboardHandler)
    source_kind = "remote" if config.remote_host else "local"
    print(
        f"VirtueBench dashboard serving {source_kind} run '{config.output_prefix}' at "
        f"http://{config.host}:{config.port}"
    )
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    finally:
        server.server_close()
