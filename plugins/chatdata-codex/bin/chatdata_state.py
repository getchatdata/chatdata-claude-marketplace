#!/usr/bin/env python3
"""Local state helper for the ChatData agent workbench.

This helper intentionally keeps v1 licensing local and simple. It enforces the
7-day trial and a manual license-key path without pretending to be a hardened
payments system.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


TRIAL_DAYS = 7
CLOCK_SKEW_TOLERANCE = timedelta(minutes=10)
STATE_SCHEMA_VERSION = "1.0"
DEFAULT_SETTINGS = {
    "telemetry": False,
    "status_line": True,
    "proof_receipts": True,
    "default_confidence_floor": "medium",
    "local_first": True,
    "company_repo_required_for_team_work": True,
    "portal_sync": True,
}


@dataclass
class Paths:
    home: Path
    project: Path

    @property
    def license_path(self) -> Path:
        return self.home / "license.json"

    @property
    def profile_path(self) -> Path:
        return self.home / "profile.json"

    @property
    def settings_path(self) -> Path:
        return self.home / "settings.json"

    @property
    def proof_log_path(self) -> Path:
        return self.project / "impact-log.jsonl"

    @property
    def metrics_dir(self) -> Path:
        return self.project / "metrics"

    @property
    def corrections_dir(self) -> Path:
        return self.project / "corrections"

    @property
    def data_sources_path(self) -> Path:
        return self.project / "data-sources.json"

    @property
    def company_repo_manifest_path(self) -> Path:
        return self.project / "company-repo.json"

    @property
    def onboarding_path(self) -> Path:
        return self.project / "onboarding.json"

    @property
    def company_domain_map_path(self) -> Path:
        return self.home / "company-domain-map.json"


def now_utc() -> datetime:
    override = os.environ.get("CHATDATA_NOW")
    if override:
        parsed = datetime.fromisoformat(override.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc)
    return datetime.now(timezone.utc)


def paths_from_args(args: argparse.Namespace) -> Paths:
    home = Path(args.home or os.environ.get("CHATDATA_HOME", "~/.chatdata")).expanduser().resolve()
    project = Path(args.project or os.environ.get("CHATDATA_PROJECT", ".chatdata")).expanduser()
    if not project.is_absolute():
        project = (Path.cwd() / project).resolve()
    return Paths(home=home, project=project)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_corrupt": True, "path": str(path)}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_project_dirs(paths: Paths) -> None:
    paths.home.mkdir(parents=True, exist_ok=True)
    paths.project.mkdir(parents=True, exist_ok=True)
    paths.metrics_dir.mkdir(parents=True, exist_ok=True)
    paths.corrections_dir.mkdir(parents=True, exist_ok=True)


def license_checksum(email_hash: str, expires_at: str) -> str:
    digest = hashlib.sha256(f"chatdata-license:v1:{email_hash}:{expires_at}".encode("utf-8")).hexdigest()
    return digest[:12].upper()


def issue_license(email: str, expires_at: str) -> str:
    normalized = email.strip().lower()
    email_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:10].upper()
    checksum = license_checksum(email_hash, expires_at)
    return f"CHATDATA-{expires_at.replace('-', '')}-{email_hash}-{checksum}"


def parse_license_key(key: str) -> dict[str, Any]:
    parts = key.strip().split("-")
    if len(parts) != 4 or parts[0] != "CHATDATA":
        return {"ok": False, "reason": "license key should look like CHATDATA-YYYYMMDD-EMAILHASH-CHECKSUM"}

    raw_date, email_hash, checksum = parts[1], parts[2], parts[3]
    if len(raw_date) != 8 or not raw_date.isdigit():
        return {"ok": False, "reason": "license key date is invalid"}

    expires_at = f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
    expected = license_checksum(email_hash, expires_at)
    if checksum.upper() != expected:
        return {"ok": False, "reason": "license key checksum is invalid"}

    try:
        datetime.fromisoformat(expires_at)
    except ValueError:
        return {"ok": False, "reason": "license key expiry date is invalid"}

    return {
        "ok": True,
        "license_key": key.strip(),
        "email_hash": email_hash,
        "license_expires_at": expires_at,
    }


def ensure_license(paths: Paths) -> dict[str, Any]:
    license_state = read_json(paths.license_path, {})
    current = now_utc()
    if license_state.get("_corrupt"):
        return license_state

    if not license_state:
        trial_started = current
        trial_ends = trial_started + timedelta(days=TRIAL_DAYS)
        license_state = {
            "schema_version": STATE_SCHEMA_VERSION,
            "trial_started_at": trial_started.isoformat(),
            "trial_ends_at": trial_ends.isoformat(),
            "last_seen_at": trial_started.isoformat(),
            "license_key": None,
            "license_expires_at": None,
            "activated_at": None,
        }
        write_json(paths.license_path, license_state)
    return license_state


def trial_status(paths: Paths) -> dict[str, Any]:
    state = ensure_license(paths)
    current = now_utc()

    if state.get("_corrupt"):
        return {
            "state": "blocked",
            "active": False,
            "reason": "license state is corrupt; run /chatdata:license after moving the corrupt file aside",
            "path": state.get("path"),
        }

    last_seen_at = parse_datetime(state.get("last_seen_at"))
    if last_seen_at and current + CLOCK_SKEW_TOLERANCE < last_seen_at:
        return {
            "state": "blocked",
            "active": False,
            "reason": "system clock moved backwards; restore the clock or activate a license",
            "last_seen_at": last_seen_at.isoformat(),
        }
    if not last_seen_at or current > last_seen_at:
        state["last_seen_at"] = current.isoformat()
        write_json(paths.license_path, state)

    license_expires = state.get("license_expires_at")
    if license_expires:
        expiry_date = datetime.fromisoformat(license_expires).replace(tzinfo=timezone.utc)
        if current.date() <= expiry_date.date():
            return {
                "state": "licensed",
                "active": True,
                "license_expires_at": license_expires,
                "trial_days_remaining": 0,
            }

    trial_ends = datetime.fromisoformat(state["trial_ends_at"].replace("Z", "+00:00"))
    if trial_ends.tzinfo is None:
        trial_ends = trial_ends.replace(tzinfo=timezone.utc)
    remaining_seconds = (trial_ends - current).total_seconds()
    days_remaining = max(0, int((remaining_seconds + 86399) // 86400))

    if remaining_seconds >= 0:
        return {
            "state": "trial",
            "active": True,
            "trial_ends_at": state["trial_ends_at"],
            "trial_days_remaining": days_remaining,
        }

    return {
        "state": "expired",
        "active": False,
        "trial_ends_at": state["trial_ends_at"],
        "trial_days_remaining": 0,
        "reason": "7-day trial expired; activate a license to continue using ChatData value commands",
    }


def load_settings(paths: Paths) -> dict[str, Any]:
    existing = read_json(paths.settings_path, {})
    if existing.get("_corrupt"):
        return existing
    settings = {**DEFAULT_SETTINGS, **existing}
    write_json(paths.settings_path, settings)
    return settings


def load_profile(paths: Paths) -> dict[str, Any]:
    profile = read_json(paths.profile_path, {})
    if profile.get("_corrupt"):
        return profile
    return profile


def proof_entries(paths: Paths) -> list[dict[str, Any]]:
    if not paths.proof_log_path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in paths.proof_log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            entries.append({"corrupt_line": line})
    return entries


def impact_totals(entries: list[dict[str, Any]]) -> dict[str, float]:
    clean_entries = [entry for entry in entries if "corrupt_line" not in entry]
    return {
        "receipts": float(len(clean_entries)),
        "minutes": sum(float(entry.get("estimated_time_saved_minutes") or 0) for entry in clean_entries),
        "value": sum(float(entry.get("estimated_value_usd") or 0) for entry in clean_entries),
    }


def impact_line(paths: Paths) -> str:
    entries = proof_entries(paths)
    totals = impact_totals(entries)
    metrics_dir = metric_packet_dir(paths)
    metrics = list(metrics_dir.glob("*.yaml")) if metrics_dir.exists() else []
    company_repo = read_json(paths.company_repo_manifest_path, {})
    repo_state = "repo:on" if company_repo and not company_repo.get("_corrupt") else "repo:missing"
    return (
        "CHATDATA impact | "
        f"receipts:{int(totals['receipts'])} | "
        f"time:{totals['minutes']:.0f}m | "
        f"value:${totals['value']:,.0f} | "
        f"metrics:{len(metrics)} | "
        f"{repo_state}"
    )


def sample_dataset_path() -> Path | None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "data" / "plugin-test-datasets" / "retail_clean" / "orders.csv"
        if candidate.exists():
            return candidate
    return None


def data_source_count(paths: Paths) -> int:
    data_sources = read_json(paths.data_sources_path, {"sources": []})
    if data_sources.get("_corrupt"):
        return 0
    return len(data_sources.get("sources") or [])


def profile_has_context(profile: dict[str, Any]) -> bool:
    if not profile or profile.get("_corrupt"):
        return False
    has_role = bool(profile.get("role")) and profile.get("role") != "data professional"
    has_metrics = bool(profile.get("focus_metrics"))
    has_forums = bool(profile.get("recurring_forums"))
    has_context = bool(profile.get("business_context"))
    return has_role and (has_metrics or has_forums or has_context)


def guided_onboarding(paths: Paths) -> dict[str, Any]:
    profile = load_profile(paths)
    company_repo = read_json(paths.company_repo_manifest_path, {})
    entries = proof_entries(paths)
    metrics_dir = metric_packet_dir(paths)
    metric_count = len(list(metrics_dir.glob("*.yaml"))) if metrics_dir.exists() else 0
    sample_path = sample_dataset_path()
    source_count = data_source_count(paths)
    company_repo_ready = bool(company_repo and not company_repo.get("_corrupt") and company_repo.get("path"))

    components = [
        {
            "id": "profile",
            "label": "Capture role, owned metrics, and recurring forum",
            "done": profile_has_context(profile),
            "why": "ChatData needs the job-to-be-done before it can choose the right trust workflow.",
            "action": '/chatdata:start --role "<role>" --metrics "<3-5 metrics>" --forums "<WBR, exec review, board update>"',
        },
        {
            "id": "company_context",
            "label": "Attach the multiplayer company context repo",
            "done": company_repo_ready,
            "why": "Reusable metric packets, answer paths, corrections, proof, and evals should not stay in one chat.",
            "action": '/chatdata:login with the portal email and token, or /chatdata:company-repo --email "<work email>"',
        },
        {
            "id": "data_source",
            "label": "Connect a first data source",
            "done": source_count > 0,
            "why": "The first proof run needs one concrete source, even if it is the synthetic onboarding dataset.",
            "action": (
                f'/chatdata:connect-data --name "Retail clean sample" --kind csv --path "{sample_path}" '
                '--notes "Synthetic onboarding dataset"'
                if sample_path
                else '/chatdata:connect-data --name "<source name>" --kind "<csv|duckdb|warehouse|mcp|repo>" --path "<path-or-identifier>"'
            ),
        },
        {
            "id": "metric_packet",
            "label": "Create or attach one metric trust packet",
            "done": metric_count > 0,
            "why": "ChatData should prove the metric definition before it tries to explain movement.",
            "action": '/chatdata:metrics "Gross Margin Rate"' if sample_path else '/chatdata:metrics "<metric name>"',
        },
        {
            "id": "proof_receipt",
            "label": "Record the first proof receipt",
            "done": len(entries) > 0,
            "why": "The trial should show visible value before day 7.",
            "action": (
                '/chatdata:proof --record --workflow "onboarding" '
                '--question "Can ChatData produce one trusted first-session workflow?" '
                '--confidence "medium" --time-saved-minutes "15"'
            ),
        },
    ]

    next_index = None
    for index, component in enumerate(components):
        if not component["done"]:
            next_index = index
            break
    for index, component in enumerate(components):
        if component["done"]:
            component["status"] = "done"
        elif index == next_index:
            component["status"] = "next"
        else:
            component["status"] = "pending"

    completed = sum(1 for component in components if component["done"])
    onboarding = {
        "schema_version": STATE_SCHEMA_VERSION,
        "updated_at": now_utc().isoformat(),
        "completed": completed,
        "total": len(components),
        "complete": completed == len(components),
        "sample_dataset_path": str(sample_path) if sample_path else None,
        "components": components,
    }
    write_json(paths.onboarding_path, onboarding)
    return onboarding


def render_guided_onboarding(paths: Paths, *, full: bool = True) -> None:
    onboarding = guided_onboarding(paths)
    print("")
    print("Guided onboarding")
    print(f"- Progress: {onboarding['completed']}/{onboarding['total']} components complete")
    if onboarding["complete"]:
        print("- Status: complete. Run /chatdata:proof to export receipts or /chatdata:audit-context before stakeholder-facing work.")
        return
    for component in onboarding["components"]:
        marker = {"done": "done", "next": "next", "pending": "pending"}[component["status"]]
        print(f"- [{marker}] {component['label']}")
        if full and component["status"] == "next":
            print(f"  Why: {component['why']}")
            print(f"  Run: {component['action']}")
    if onboarding.get("sample_dataset_path"):
        print("  First-session demo prompt:")
        print(
            f"  /chatdata:investigate why gross margin fell in Q4 2025 versus Q3 2025. "
            f"Use {onboarding['sample_dataset_path']}."
        )


def command_start(args: argparse.Namespace) -> int:
    paths = paths_from_args(args)
    ensure_project_dirs(paths)
    state = ensure_license(paths)
    settings = load_settings(paths)
    profile = load_profile(paths)
    if not profile:
        profile = {
            "schema_version": STATE_SCHEMA_VERSION,
            "created_at": now_utc().isoformat(),
            "role": args.role or "data professional",
            "business_context": args.business_context or "",
            "focus_metrics": split_csv(args.metrics),
            "recurring_forums": split_csv(args.forums),
            "preferred_output": args.output or "decision brief",
        }
        write_json(paths.profile_path, profile)

    if args.role:
        profile["role"] = args.role
    if args.business_context:
        profile["business_context"] = args.business_context
    if args.metrics:
        profile["focus_metrics"] = split_csv(args.metrics)
    if args.forums:
        profile["recurring_forums"] = split_csv(args.forums)
    if args.output:
        profile["preferred_output"] = args.output
    if args.email:
        profile["email"] = args.email.strip().lower()
    if args.token:
        profile["chatdata_token"] = args.token.strip()
    if args.api_url:
        profile["chatdata_api_url"] = args.api_url.rstrip("/")
    if args.role or args.business_context or args.metrics or args.forums or args.output or args.email or args.token or args.api_url:
        write_json(paths.profile_path, profile)

    print("ChatData trial is ready.")
    print(f"Trial started: {state['trial_started_at']}")
    print(f"Trial ends: {state['trial_ends_at']}")
    print(f"Local profile: {paths.profile_path}")
    print(f"Project state: {paths.project}")
    print(f"Telemetry: {'on' if settings.get('telemetry') else 'off'}")
    if profile.get("email") and profile.get("chatdata_token"):
        sync_result = sync_portal(paths, profile["email"], profile["chatdata_token"], profile.get("chatdata_api_url") or "https://getchatdata.com")
        if sync_result["ok"]:
            print(f"Portal sync: attached {sync_result['repo']} for {sync_result['domain']}")
        else:
            print(f"Portal sync: {sync_result['reason']}")
    print("Run /chatdata:status any time to see trial days, proof receipts, and setup health.")
    render_guided_onboarding(paths)
    return 0


def command_status(args: argparse.Namespace) -> int:
    paths = paths_from_args(args)
    ensure_project_dirs(paths)
    status = trial_status(paths)
    settings = load_settings(paths)
    profile = load_profile(paths)
    company_repo = read_json(paths.company_repo_manifest_path, {})
    entries = proof_entries(paths)
    metrics_dir = metric_packet_dir(paths)
    metrics = list(metrics_dir.glob("*.yaml")) if metrics_dir.exists() else []
    total_minutes = sum(float(entry.get("estimated_time_saved_minutes") or 0) for entry in entries if "corrupt_line" not in entry)
    total_value = sum(float(entry.get("estimated_value_usd") or 0) for entry in entries if "corrupt_line" not in entry)

    print("ChatData status")
    print(impact_line(paths))
    print(f"- State: {status['state']}")
    print(f"- Active: {'yes' if status['active'] else 'no'}")
    if "trial_days_remaining" in status:
        print(f"- Trial days remaining: {status['trial_days_remaining']}")
    if status.get("license_expires_at"):
        print(f"- License expires: {status['license_expires_at']}")
    if status.get("reason"):
        print(f"- Reason: {status['reason']}")
    print(f"- Profile: {'configured' if profile and not profile.get('_corrupt') else 'missing'}")
    if company_repo and not company_repo.get("_corrupt"):
        print(f"- Company repo: configured ({company_repo.get('repo', 'unknown')})")
        print(f"- Company repo path: {company_repo.get('path', 'unknown')}")
        print(f"- Company repo sync mode: {company_repo.get('sync_mode', 'local-git')}")
    else:
        print("- Company repo: missing")
    print(f"- Trusted metrics: {len(metrics)}")
    print(f"- Proof receipts: {len(entries)}")
    print(f"- Estimated time saved: {total_minutes:.0f} minutes")
    print(f"- Estimated value created: ${total_value:,.0f}")
    print(f"- Local-first mode: {'on' if settings.get('local_first') else 'off'}")
    print(f"- Telemetry: {'on' if settings.get('telemetry') else 'off'}")
    onboarding = guided_onboarding(paths)
    if onboarding["complete"]:
        print("- Guided onboarding: complete")
    else:
        render_guided_onboarding(paths, full=False)
    return 0


def command_onboarding(args: argparse.Namespace) -> int:
    paths = paths_from_args(args)
    ensure_project_dirs(paths)
    ensure_license(paths)
    load_settings(paths)
    render_guided_onboarding(paths)
    return 0


def command_impact(args: argparse.Namespace) -> int:
    paths = paths_from_args(args)
    ensure_project_dirs(paths)
    print(impact_line(paths))
    return 0


def require_active(paths: Paths) -> bool:
    status = trial_status(paths)
    if status["active"]:
        return True
    print(status.get("reason", "ChatData is not active."), file=sys.stderr)
    print("Allowed commands while inactive: /chatdata:status, /chatdata:license, /chatdata:proof export.", file=sys.stderr)
    return False


def require_company_repo(paths: Paths) -> bool:
    company_repo = read_json(paths.company_repo_manifest_path, {})
    if company_repo.get("_corrupt"):
        print(f"Company repo manifest is corrupt: {company_repo['path']}", file=sys.stderr)
        return False
    if not company_repo:
        print("Company context repo is missing.", file=sys.stderr)
        print("Run /chatdata:company-repo once to create or attach the shared private repo.", file=sys.stderr)
        return False
    repo_path = Path(str(company_repo.get("path", ""))).expanduser()
    if not repo_path.exists():
        print(f"Company context repo path does not exist: {repo_path}", file=sys.stderr)
        print("Clone the private repo or rerun /chatdata:company-repo with the correct --path.", file=sys.stderr)
        return False
    return True


def command_guard(args: argparse.Namespace) -> int:
    paths = paths_from_args(args)
    ensure_project_dirs(paths)
    if not require_active(paths):
        return 2
    if args.company_repo and not require_company_repo(paths):
        return 2
    return 0


def command_license(args: argparse.Namespace) -> int:
    paths = paths_from_args(args)
    ensure_project_dirs(paths)

    if args.issue:
        if not args.email or not args.expires:
            print("--issue requires --email and --expires YYYY-MM-DD", file=sys.stderr)
            return 2
        print(issue_license(args.email, args.expires))
        return 0

    if not args.key:
        print("Pass --key CHATDATA-YYYYMMDD-EMAILHASH-CHECKSUM to activate a license.", file=sys.stderr)
        return 2

    parsed = parse_license_key(args.key)
    if not parsed["ok"]:
        print(parsed["reason"], file=sys.stderr)
        return 2

    state = ensure_license(paths)
    state.update(
        {
            "license_key": parsed["license_key"],
            "license_email_hash": parsed["email_hash"],
            "license_expires_at": parsed["license_expires_at"],
            "activated_at": now_utc().isoformat(),
        }
    )
    write_json(paths.license_path, state)
    print(f"ChatData license activated through {parsed['license_expires_at']}.")
    return 0


def command_settings(args: argparse.Namespace) -> int:
    paths = paths_from_args(args)
    ensure_project_dirs(paths)
    settings = load_settings(paths)
    if settings.get("_corrupt"):
        print(f"Settings file is corrupt: {settings['path']}", file=sys.stderr)
        return 2

    if args.set:
        for pair in args.set:
            if "=" not in pair:
                print(f"Invalid setting {pair!r}; expected key=value", file=sys.stderr)
                return 2
            key, raw_value = pair.split("=", 1)
            settings[key.strip()] = parse_setting_value(raw_value.strip())
        write_json(paths.settings_path, settings)

    print(json.dumps(settings, indent=2, sort_keys=True))
    return 0


def command_activate_session(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace or Path.cwd()).expanduser().resolve()
    claude_dir = workspace / ".claude"
    settings_path = claude_dir / "settings.local.json"
    plugin_root = Path(args.plugin_root or Path(__file__).resolve().parents[1]).expanduser().resolve()
    status_script = plugin_root / "scripts" / "chatdata-status-line.js"

    if not status_script.exists():
        print(f"ChatData statusline script is missing: {status_script}", file=sys.stderr)
        return 2

    settings = read_json(settings_path, {})
    if settings.get("_corrupt"):
        print(f"Claude project settings are corrupt: {settings['path']}", file=sys.stderr)
        return 2

    claude_dir.mkdir(parents=True, exist_ok=True)
    settings["agent"] = "chatdata:code"
    settings["statusLine"] = {
        "type": "command",
        "command": f"node {shlex.quote(str(status_script))}",
    }
    settings["attribution"] = {
        "commit": "Co-Authored-By: ChatData <support@getchatdata.com>",
        "pr": "Built with ChatData",
    }
    settings["spinnerVerbs"] = {
        "mode": "replace",
        "verbs": [
            "Reading company context",
            "Checking metric trust",
            "Validating evidence",
            "Writing proof",
            "Syncing context",
        ],
    }
    write_json(settings_path, settings)

    print("ChatData session activation written.")
    print(f"- Workspace: {workspace}")
    print(f"- Claude settings: {settings_path}")
    print("- Agent: chatdata:code")
    print(f"- Status line: {status_script}")
    print("Restart Claude Code from this workspace for the footer metadata to switch from Woz to ChatData.")
    return 0


def command_connect_data(args: argparse.Namespace) -> int:
    paths = paths_from_args(args)
    ensure_project_dirs(paths)
    if not require_active(paths):
        return 2
    data_sources = read_json(paths.data_sources_path, {"sources": []})
    if data_sources.get("_corrupt"):
        print(f"Data source file is corrupt: {data_sources['path']}", file=sys.stderr)
        return 2

    source = {
        "name": args.name,
        "kind": args.kind,
        "path": args.path,
        "notes": args.notes or "",
        "connected_at": now_utc().isoformat(),
    }
    data_sources.setdefault("sources", []).append(source)
    write_json(paths.data_sources_path, data_sources)
    company_root = company_repo_root(paths)
    if company_root:
        shared_sources_path = company_root / "sources" / "data-sources.json"
        shared_sources = read_json(shared_sources_path, {"sources": []})
        if not shared_sources.get("_corrupt"):
            shared_sources.setdefault("sources", []).append(source)
            write_json(shared_sources_path, shared_sources)
    print(f"Recorded data source {args.name} ({args.kind}).")
    print(f"Manifest: {paths.data_sources_path}")
    if company_root:
        print(f"Shared manifest: {company_root / 'sources' / 'data-sources.json'}")
    return 0


def command_company_repo(args: argparse.Namespace) -> int:
    paths = paths_from_args(args)
    ensure_project_dirs(paths)
    if not require_active(paths):
        return 2

    if args.require:
        if not require_company_repo(paths):
            return 2
        company_repo = read_json(paths.company_repo_manifest_path, {})
        print(f"Company context repo ready: {company_repo.get('repo')} at {company_repo.get('path')}")
        return 0

    if args.email and not args.company:
        attached = attach_company_repo_from_domain(paths, args.email)
        if attached:
            print("ChatData company context repo attached from email domain.")
            print(f"Email domain: {attached['domain']}")
            print(f"Repo: {attached['repo']}")
            print(f"Local path: {attached['path']}")
            print(f"Sync mode: {attached.get('sync_mode', 'chatdata-managed')}")
            return 0
        profile = load_profile(paths)
        token = profile.get("chatdata_token") or os.environ.get("CHATDATA_TOKEN")
        api_url = profile.get("chatdata_api_url") or os.environ.get("CHATDATA_API_URL") or "https://getchatdata.com"
        if token:
            synced = sync_portal(paths, args.email, token, api_url)
            if synced["ok"]:
                print("ChatData company context repo synced from portal.")
                print(f"Email domain: {synced['domain']}")
                print(f"Repo: {synced['repo']}")
                print(f"Local path: {synced['path']}")
                print(f"Sync mode: {synced['sync_mode']}")
                return 0
        print(f"No company repo mapping found for email domain: {email_domain(args.email)}", file=sys.stderr)
        print("Run /chatdata:login once with the ChatData token, or have ChatData provision the private repo in the portal.", file=sys.stderr)
        return 2

    company = (args.company or "").strip()
    if not company:
        print("--company cannot be blank", file=sys.stderr)
        return 2

    repo = args.repo or default_company_repo_name(company)
    owner = args.owner or ""
    sync_mode = args.sync_mode or "local-git"
    repo_path = Path(args.path or (paths.project / "company-repo")).expanduser()
    if not repo_path.is_absolute():
        repo_path = (Path.cwd() / repo_path).resolve()
    remote = args.remote or (f"git@github.com:{owner}/{repo}.git" if owner else "")

    scaffold_company_repo(repo_path, company=company, repo=repo, owner=owner, remote=remote, sync_mode=sync_mode)

    manifest = {
        "schema_version": STATE_SCHEMA_VERSION,
        "configured_at": now_utc().isoformat(),
        "company": company,
        "domain": email_domain(args.email) if args.email else args.domain or "",
        "repo": repo,
        "owner": owner,
        "path": str(repo_path),
        "remote": remote,
        "sync_mode": sync_mode,
        "chatdata_api_url": args.chatdata_api_url or "",
        "required_for_team_work": True,
        "source_of_truth": [
            "metrics",
            "answer-paths",
            "corrections",
            "proof",
            "decisions",
            "sources",
            "playbooks",
            "evals",
        ],
    }
    write_json(paths.company_repo_manifest_path, manifest)
    if args.domain or args.email:
        domain = args.domain or email_domain(args.email)
        upsert_domain_mapping(paths, domain, manifest)

    print("ChatData company context repo configured.")
    print(f"Company: {company}")
    if manifest["domain"]:
        print(f"Domain: {manifest['domain']}")
    print(f"Repo: {repo}")
    print(f"Local path: {repo_path}")
    if remote:
        print(f"Remote: {remote}")
    else:
        print("Remote: not set. Create a private GitHub repo, then add the remote.")
    print(f"Sync mode: {sync_mode}")
    print(f"Manifest: {paths.company_repo_manifest_path}")
    return 0


def command_login(args: argparse.Namespace) -> int:
    paths = paths_from_args(args)
    ensure_project_dirs(paths)
    if not require_active(paths):
        return 2
    profile = load_profile(paths)
    email = (args.email or profile.get("email") or "").strip().lower()
    token = read_login_token(args, profile)
    api_url = (args.api_url or profile.get("chatdata_api_url") or os.environ.get("CHATDATA_API_URL") or "https://getchatdata.com").rstrip("/")

    if not email:
        print("--email is required the first time you sync ChatData portal config", file=sys.stderr)
        return 2
    if not token:
        print("--token is required the first time you sync ChatData portal config", file=sys.stderr)
        return 2

    profile["email"] = email
    profile["chatdata_token"] = token
    profile["chatdata_api_url"] = api_url
    write_json(paths.profile_path, profile)

    result = sync_portal(paths, email, token, api_url)
    if not result["ok"]:
        print(result["reason"], file=sys.stderr)
        return 2

    print("ChatData portal sync complete.")
    print(f"Email: {email}")
    print(f"Company key: {result['domain']}")
    print(f"Repo: {result['repo']}")
    print(f"Local path: {result['path']}")
    print(f"Sync mode: {result['sync_mode']}")
    if result.get("remote"):
        print(f"Remote: {result['remote']}")
    else:
        print("Remote: managed by ChatData portal; local repo scaffold is ready.")
    return 0


def read_login_token(args: argparse.Namespace, profile: dict[str, Any]) -> str:
    if args.token_stdin:
        return sys.stdin.read().strip()
    if args.token_env:
        return os.environ.get(args.token_env, "").strip()
    return (args.token or profile.get("chatdata_token") or os.environ.get("CHATDATA_TOKEN") or "").strip()


def sync_company_context(paths: Paths) -> dict[str, Any]:
    company_repo = read_json(paths.company_repo_manifest_path, {})
    if not company_repo or company_repo.get("_corrupt"):
        return {"ok": False, "status": "blocked", "reason": "company repo is not configured"}

    repo_root = company_repo_root(paths)
    if not repo_root:
        return {"ok": False, "status": "blocked", "reason": "company repo local path is missing"}

    if company_repo.get("sync_mode") == "chatdata-managed":
        backend_sync = sync_company_context_via_backend(paths, repo_root, company_repo)
        if backend_sync["ok"]:
            return backend_sync
        if backend_sync.get("hard_block"):
            return backend_sync

    remote = str(company_repo.get("remote") or company_repo.get("repo_url") or "").strip()
    if not remote:
        return {"ok": False, "status": "blocked", "reason": "company repo remote is missing"}
    remote = preferred_git_remote(remote)

    if not (repo_root / ".git").exists():
        init = run_command(["git", "init", "-b", "main"], cwd=repo_root)
        if init["returncode"] != 0:
            init = run_command(["git", "init"], cwd=repo_root)
        if init["returncode"] != 0:
            return {"ok": False, "status": "blocked", "reason": f"git init failed: {init['stderr'].strip()}"}

    existing_remote = run_command(["git", "remote", "get-url", "origin"], cwd=repo_root)
    if existing_remote["returncode"] != 0:
        added = run_command(["git", "remote", "add", "origin", remote], cwd=repo_root)
        if added["returncode"] != 0:
            return {"ok": False, "status": "blocked", "reason": f"git remote add failed: {added['stderr'].strip()}"}
    elif existing_remote["stdout"].strip() != remote:
        updated = run_command(["git", "remote", "set-url", "origin", remote], cwd=repo_root)
        if updated["returncode"] != 0:
            return {"ok": False, "status": "blocked", "reason": f"git remote update failed: {updated['stderr'].strip()}"}

    status = run_command(["git", "status", "--porcelain"], cwd=repo_root)
    if status["returncode"] != 0:
        return {"ok": False, "status": "blocked", "reason": f"git status failed: {status['stderr'].strip()}"}

    changed_lines = [line for line in status["stdout"].splitlines() if line.strip()]
    if changed_lines:
        added = run_command(["git", "add", "."], cwd=repo_root)
        if added["returncode"] != 0:
            return {"ok": False, "status": "blocked", "reason": f"git add failed: {added['stderr'].strip()}"}
        committed = run_command(
            [
                "git",
                "-c",
                "user.name=ChatData",
                "-c",
                "user.email=sync@getchatdata.com",
                "commit",
                "-m",
                "Sync ChatData company context",
            ],
            cwd=repo_root,
        )
        if committed["returncode"] != 0 and "nothing to commit" not in committed["stdout"].lower():
            return {"ok": False, "status": "blocked", "reason": f"git commit failed: {committed['stderr'].strip()}"}

    pushed = push_company_context(repo_root, remote)
    if pushed["returncode"] != 0:
        return {"ok": False, "status": "blocked", "reason": f"git push failed: {pushed['stderr'].strip()}"}

    company_repo["last_synced_at"] = now_utc().isoformat()
    company_repo["last_sync_status"] = "synced"
    company_repo["remote"] = remote
    write_json(paths.company_repo_manifest_path, company_repo)
    upsert_domain_mapping(paths, str(company_repo.get("domain") or ""), company_repo)
    return {
        "ok": True,
        "status": "synced",
        "repo": company_repo.get("repo"),
        "path": str(repo_root),
        "remote": remote,
        "changed_files": len(changed_lines),
    }


def sync_company_context_via_backend(paths: Paths, repo_root: Path, company_repo: dict[str, Any]) -> dict[str, Any]:
    profile = load_profile(paths)
    token = str(profile.get("chatdata_token") or "").strip()
    api_url = str(company_repo.get("chatdata_api_url") or profile.get("chatdata_api_url") or "https://getchatdata.com").rstrip("/")
    if not token:
        return {
            "ok": False,
            "status": "blocked",
            "hard_block": True,
            "reason": "chatdata-managed sync requires a portal token; run /chatdata:login",
        }

    files = collect_context_files(repo_root)
    if not files:
        return {
            "ok": True,
            "status": "synced",
            "repo": company_repo.get("repo"),
            "path": str(repo_root),
            "remote": company_repo.get("remote") or company_repo.get("repo_url") or "",
            "changed_files": 0,
            "backend_managed": True,
        }

    payload = {
        "message": "Sync ChatData company context",
        "files": files,
    }
    request = urllib.request.Request(
        f"{api_url}/api/portal/sync-context",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ChatDataPlugin/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        try:
            error_payload = json.loads(error.read().decode("utf-8"))
            reason = error_payload.get("error") or str(error_payload.get("failed") or "") or f"backend sync returned HTTP {error.code}"
        except Exception:
            reason = f"backend sync returned HTTP {error.code}"
        return {"ok": False, "status": "blocked", "hard_block": True, "reason": reason}
    except urllib.error.URLError as error:
        return {"ok": False, "status": "blocked", "hard_block": True, "reason": f"could not reach ChatData backend: {error.reason}"}
    except TimeoutError:
        return {"ok": False, "status": "blocked", "hard_block": True, "reason": "backend sync timed out"}

    try:
        result = json.loads(body)
    except json.JSONDecodeError:
        return {"ok": False, "status": "blocked", "hard_block": True, "reason": "backend sync returned invalid JSON"}

    if not result.get("ok"):
        return {"ok": False, "status": "blocked", "hard_block": True, "reason": result.get("error") or str(result.get("failed") or "backend sync failed")}

    company_repo["last_synced_at"] = now_utc().isoformat()
    company_repo["last_sync_status"] = "synced"
    if result.get("repoUrl"):
        company_repo["repo_url"] = result["repoUrl"]
        company_repo["remote"] = git_remote_from_repo_url(str(result["repoUrl"]))
    write_json(paths.company_repo_manifest_path, company_repo)
    upsert_domain_mapping(paths, str(company_repo.get("domain") or ""), company_repo)
    return {
        "ok": True,
        "status": "synced",
        "repo": result.get("repo") or company_repo.get("repo"),
        "path": str(repo_root),
        "remote": company_repo.get("remote") or company_repo.get("repo_url") or "",
        "changed_files": int(result.get("files") or len(files)),
        "backend_managed": True,
    }


def collect_context_files(repo_root: Path) -> list[dict[str, str]]:
    files: list[dict[str, str]] = []
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(repo_root)
        parts = relative.parts
        if not parts or parts[0] == ".git" or any(part in {".DS_Store", "__pycache__"} for part in parts):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if len(content) > 1_000_000:
            continue
        files.append({"path": relative.as_posix(), "content": content})
    return files


def push_company_context(repo_root: Path, remote: str) -> dict[str, Any]:
    pushed = run_command(["git", "push", "-u", "origin", "HEAD:main"], cwd=repo_root)
    if pushed["returncode"] == 0:
        return pushed
    if remote_ahead_error(pushed):
        reconciled = reconcile_remote_main(repo_root)
        if reconciled["returncode"] == 0:
            return run_command(["git", "push", "-u", "origin", "HEAD:main"], cwd=repo_root)
        return reconciled
    if not remote.startswith("https://github.com/"):
        return pushed

    token = run_command(["gh", "auth", "token"], cwd=repo_root)
    if token["returncode"] != 0 or not token["stdout"].strip():
        return pushed

    return run_command(
        [
            "git",
            "-c",
            f"http.https://github.com/.extraheader=AUTHORIZATION: bearer {token['stdout'].strip()}",
            "push",
            "-u",
            "origin",
            "HEAD:main",
        ],
        cwd=repo_root,
    )


def remote_ahead_error(result: dict[str, Any]) -> bool:
    output = f"{result.get('stdout', '')}\n{result.get('stderr', '')}".lower()
    return "fetch first" in output or "non-fast-forward" in output or "failed to push some refs" in output


def reconcile_remote_main(repo_root: Path) -> dict[str, Any]:
    fetched = run_command(["git", "fetch", "origin", "main"], cwd=repo_root)
    if fetched["returncode"] != 0:
        return fetched

    merge_base = run_command(["git", "merge-base", "HEAD", "origin/main"], cwd=repo_root)
    if merge_base["returncode"] != 0:
        return run_command(
            [
                "git",
                "-c",
                "user.name=ChatData",
                "-c",
                "user.email=sync@getchatdata.com",
                "merge",
                "--allow-unrelated-histories",
                "-X",
                "ours",
                "--no-edit",
                "origin/main",
            ],
            cwd=repo_root,
        )

    rebased = run_command(["git", "pull", "--rebase", "--autostash", "origin", "main"], cwd=repo_root)
    if rebased["returncode"] != 0:
        run_command(["git", "rebase", "--abort"], cwd=repo_root)
    return rebased


def preferred_git_remote(remote: str) -> str:
    if not remote.startswith("https://github.com/"):
        return remote
    protocol = gh_git_protocol()
    if protocol == "ssh":
        parsed = urllib.parse.urlparse(remote)
        repo_path = parsed.path.strip("/")
        if repo_path:
            suffix = repo_path if repo_path.endswith(".git") else f"{repo_path}.git"
            return f"git@github.com:{suffix}"
    return remote


def gh_git_protocol() -> str:
    status = run_command(["gh", "auth", "status"], cwd=Path.cwd())
    output = f"{status.get('stdout', '')}\n{status.get('stderr', '')}".lower()
    if "git operations protocol: ssh" in output:
        return "ssh"
    if "git operations protocol: https" in output:
        return "https"
    return ""


def command_github(args: argparse.Namespace) -> int:
    paths = paths_from_args(args)
    ensure_project_dirs(paths)
    company_repo = read_json(paths.company_repo_manifest_path, {})

    print("ChatData GitHub status")
    if company_repo and not company_repo.get("_corrupt"):
        print(f"- Company repo: {company_repo.get('repo', 'unknown')}")
        print(f"- Sync mode: {company_repo.get('sync_mode', 'local-git')}")
        print(f"- Local path: {company_repo.get('path', 'unknown')}")
        print(f"- Remote: {company_repo.get('remote') or 'not set'}")
    else:
        print("- Company repo: missing")

    gh_status = run_command(["gh", "auth", "status"], cwd=Path.cwd())
    if gh_status["available"]:
        print(f"- gh auth: {'ok' if gh_status['returncode'] == 0 else 'not authenticated'}")
    else:
        print("- gh auth: gh CLI not found")

    repo_root = company_repo_root(paths)
    if repo_root:
        git_status = run_command(["git", "status", "--short"], cwd=repo_root)
        if company_repo.get("sync_mode") == "chatdata-managed":
            print(f"- Backend sync remote: {company_repo.get('remote') or company_repo.get('repo_url') or 'not configured'}")
        else:
            git_remote = run_command(["git", "remote", "get-url", "origin"], cwd=repo_root)
            print(f"- Git remote: {git_remote['stdout'].strip() if git_remote['returncode'] == 0 else 'not configured'}")
        if git_status["returncode"] == 0:
            changed_lines = [line for line in git_status["stdout"].splitlines() if line.strip()]
            print(f"- Local repo changes: {len(changed_lines)}")
        else:
            print("- Local repo changes: unavailable")

    print("")
    sync = sync_company_context(paths)
    if sync["ok"]:
        print("Context sync: synced")
        print(f"- Remote: {sync['remote']}")
        print(f"- Changed files committed: {sync['changed_files']}")
    else:
        print("Context sync: blocked")
        print(f"- Reason: {sync['reason']}")

    if args.create_plan:
        company = args.company or company_repo.get("company") or "<Company>"
        owner = args.owner or company_repo.get("owner") or "<github-owner>"
        repo = args.repo or company_repo.get("repo") or default_company_repo_name(company)
        print("")
        print("Private repo creation plan")
        print(f"1. gh repo create {owner}/{repo} --private --description \"ChatData shared context repo for {company}\"")
        print(f"2. git -C {company_repo.get('path', '<local-path>')} remote add origin git@github.com:{owner}/{repo}.git")
        print("3. git add . && git commit -m \"Initialize ChatData company context\"")
        print("4. git push -u origin main")
        print("5. Grant the customer's GitHub users or team access.")
    return 0


def attach_company_repo_from_domain(paths: Paths, email: str) -> dict[str, Any] | None:
    domain = email_domain(email)
    if not domain:
        return None
    mapping = read_json(paths.company_domain_map_path, {"domains": {}})
    if mapping.get("_corrupt"):
        return None
    entry = mapping.get("domains", {}).get(domain)
    if not entry:
        return None
    repo_path = Path(str(entry.get("path") or paths.project / "company-repo")).expanduser()
    if not repo_path.is_absolute():
        repo_path = (Path.cwd() / repo_path).resolve()
    if not repo_path.exists():
        repo_path.mkdir(parents=True, exist_ok=True)
    entry = {**entry, "domain": domain, "path": str(repo_path), "attached_at": now_utc().isoformat()}
    write_json(paths.company_repo_manifest_path, entry)
    return entry


def sync_portal(paths: Paths, email: str, token: str, api_url: str) -> dict[str, Any]:
    config = fetch_portal_config(api_url, token)
    if not config.get("ok"):
        return {"ok": False, "reason": config.get("error", "Portal sync failed")}

    domain = str(config.get("domain") or email_domain(email) or "").lower()
    company_repo = config.get("companyRepo") or {}
    repo = str(company_repo.get("repoName") or repo_name_from_domain(domain))
    owner = str(company_repo.get("githubOwner") or "")
    repo_url = str(company_repo.get("repoUrl") or "")
    sync_mode = str(company_repo.get("syncMode") or "chatdata-managed")
    repo_path = paths.home / "company-repos" / repo
    remote = git_remote_from_repo_url(repo_url) if repo_url else (f"git@github.com:{owner}/{repo}.git" if owner else "")

    scaffold_company_repo(repo_path, company=domain, repo=repo, owner=owner, remote=remote, sync_mode=sync_mode)
    manifest = {
        "schema_version": STATE_SCHEMA_VERSION,
        "configured_at": now_utc().isoformat(),
        "company": domain,
        "domain": domain,
        "repo": repo,
        "owner": owner,
        "path": str(repo_path),
        "remote": remote,
        "repo_url": repo_url,
        "sync_mode": sync_mode,
        "chatdata_api_url": api_url.rstrip("/"),
        "portal_synced_at": now_utc().isoformat(),
        "required_for_team_work": True,
        "source_of_truth": [
            "metrics",
            "answer-paths",
            "corrections",
            "proof",
            "decisions",
            "sources",
            "playbooks",
            "evals",
        ],
    }
    write_json(paths.company_repo_manifest_path, manifest)
    upsert_domain_mapping(paths, domain, manifest)
    return {
        "ok": True,
        "domain": domain,
        "repo": repo,
        "path": str(repo_path),
        "remote": remote,
        "sync_mode": sync_mode,
    }


def fetch_portal_config(api_url: str, token: str) -> dict[str, Any]:
    base = api_url.rstrip("/")
    url = f"{base}/api/portal/config"
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "ChatDataPlugin/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        try:
            payload = json.loads(error.read().decode("utf-8"))
            return {"ok": False, "error": payload.get("error") or f"Portal returned HTTP {error.code}"}
        except Exception:
            return {"ok": False, "error": f"Portal returned HTTP {error.code}"}
    except urllib.error.URLError as error:
        return {"ok": False, "error": f"Could not reach ChatData portal: {error.reason}"}
    except TimeoutError:
        return {"ok": False, "error": "Timed out while contacting ChatData portal"}

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return {"ok": False, "error": "ChatData portal returned invalid JSON"}
    if not isinstance(payload, dict):
        return {"ok": False, "error": "ChatData portal returned invalid config"}
    return payload


def repo_name_from_domain(domain: str) -> str:
    slug = []
    last_was_sep = False
    for char in domain.lower():
        if char.isalnum():
            slug.append(char)
            last_was_sep = False
        elif not last_was_sep:
            slug.append("-")
            last_was_sep = True
    cleaned = "".join(slug).strip("-") or "company-com"
    return f"ChatData-{cleaned}"


def git_remote_from_repo_url(repo_url: str) -> str:
    if repo_url.startswith("git@") or repo_url.endswith(".git"):
        return repo_url
    parsed = urllib.parse.urlparse(repo_url)
    if parsed.netloc == "github.com" and parsed.path.strip("/"):
        return f"https://github.com/{parsed.path.strip('/')}.git"
    return repo_url


def upsert_domain_mapping(paths: Paths, domain: str, manifest: dict[str, Any]) -> None:
    if not domain:
        return
    mapping = read_json(paths.company_domain_map_path, {"schema_version": STATE_SCHEMA_VERSION, "domains": {}})
    if mapping.get("_corrupt"):
        mapping = {"schema_version": STATE_SCHEMA_VERSION, "domains": {}}
    mapping.setdefault("domains", {})[domain] = {
        "company": manifest.get("company", ""),
        "repo": manifest.get("repo", ""),
        "owner": manifest.get("owner", ""),
        "path": manifest.get("path", ""),
        "remote": manifest.get("remote", ""),
        "sync_mode": manifest.get("sync_mode", "chatdata-managed"),
        "chatdata_api_url": manifest.get("chatdata_api_url", ""),
        "updated_at": now_utc().isoformat(),
    }
    write_json(paths.company_domain_map_path, mapping)


def email_domain(email: str | None) -> str:
    if not email or "@" not in email:
        return ""
    return email.rsplit("@", 1)[1].strip().lower()


def command_metrics(args: argparse.Namespace) -> int:
    paths = paths_from_args(args)
    ensure_project_dirs(paths)
    if not require_active(paths):
        return 2
    metric_id = slugify(args.metric_id)
    metric_dir = metric_packet_dir(paths)
    metric_dir.mkdir(parents=True, exist_ok=True)
    metric_path = metric_dir / f"{metric_id}.yaml"
    if metric_path.exists() and not args.force:
        print(f"Metric already exists: {metric_path}", file=sys.stderr)
        return 1

    metric = metric_template(metric_id, args.label or metric_id.replace("_", " ").title())
    metric_path.write_text(metric, encoding="utf-8")
    print(f"Created metric trust packet: {metric_path}")
    return 0


def command_proof(args: argparse.Namespace) -> int:
    paths = paths_from_args(args)
    ensure_project_dirs(paths)

    if args.record:
        if not require_active(paths):
            return 2
        entry = {
            "schema_version": STATE_SCHEMA_VERSION,
            "created_at": now_utc().isoformat(),
            "workflow": args.workflow or "analysis",
            "question": args.question or "",
            "artifact": args.artifact or "",
            "sources_used": split_csv(args.sources),
            "validation_checks": split_csv(args.validation),
            "confidence": args.confidence or "medium",
            "estimated_time_saved_minutes": float(args.time_saved_minutes or 0),
            "estimated_value_usd": float(args.value_usd or 0),
            "next_action": args.next_action or "",
        }
        with paths.proof_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
        company_root = company_repo_root(paths)
        if company_root:
            shared_proof_path = company_root / "proof" / "impact-log.jsonl"
            shared_proof_path.parent.mkdir(parents=True, exist_ok=True)
            with shared_proof_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")
        print(f"Recorded ChatData proof receipt: {paths.proof_log_path}")
        if company_root:
            print(f"Recorded shared proof receipt: {company_root / 'proof' / 'impact-log.jsonl'}")
        return 0

    entries = proof_entries(paths)
    if args.json:
        print(json.dumps(entries, indent=2, sort_keys=True))
        return 0

    print("ChatData proof pack")
    print(impact_line(paths))
    print(f"- Receipts: {len(entries)}")
    print(
        f"- Estimated time saved: {sum(float(entry.get('estimated_time_saved_minutes') or 0) for entry in entries if 'corrupt_line' not in entry):.0f} minutes"
    )
    print(
        f"- Estimated value created: ${sum(float(entry.get('estimated_value_usd') or 0) for entry in entries if 'corrupt_line' not in entry):,.0f}"
    )
    for entry in entries[-5:]:
        if "corrupt_line" in entry:
            print("- Corrupt proof line skipped")
            continue
        print(f"- {entry.get('created_at')}: {entry.get('workflow')} | {entry.get('question')} | {entry.get('confidence')}")
    return 0


def command_benchmark(args: argparse.Namespace) -> int:
    paths = paths_from_args(args)
    ensure_project_dirs(paths)
    if not require_active(paths):
        return 2
    print("ChatData vs unguided AI analytics")
    print("Benchmark type: local workflow smoke test")
    print("Dataset: synthetic funnel, retail margin, and recurring KPI questions")
    print("Baseline: normal agent prompt without ChatData guardrails")
    print("ChatData workflow: frame -> trust packet -> data quality -> investigate -> validate -> shared proof")
    print("")
    rows = [
        ("Cleanup loops avoided", "manual", "tracked"),
        ("Ambiguity caught before SQL", "partial", "required"),
        ("Metric definition cited", "inconsistent", "required"),
        ("Trusted source path used", "manual", "required"),
        ("Data quality checks run", "optional", "required"),
        ("Confidence/caveats visible", "inconsistent", "required"),
        ("Decision owner and follow-up captured", "rare", "required"),
        ("Reusable context saved to company repo", "rare", "default"),
        ("Proof receipt created", "no", "default"),
    ]
    for label, baseline, chatdata in rows:
        print(f"- {label}: baseline={baseline}; chatdata={chatdata}")
    print("")
    print("Dashboard line:")
    print(impact_line(paths))
    print("")
    print("Use this as a local/private benchmark until a reproducible public benchmark suite exists.")
    return 0


def command_audit_context(args: argparse.Namespace) -> int:
    paths = paths_from_args(args)
    ensure_project_dirs(paths)
    if not require_active(paths):
        return 2
    if not require_company_repo(paths):
        return 2
    repo_root = company_repo_root(paths)
    if not repo_root:
        print("Company repo path is missing or unavailable.", file=sys.stderr)
        return 2

    audit = audit_company_repo(repo_root)
    print("ChatData context audit")
    print(f"- Repo: {repo_root}")
    print(f"- Grade: {audit['grade']}")
    print(f"- Metrics: {audit['metric_count']}")
    print(f"- Answer paths: {audit['answer_path_count']}")
    print(f"- Trusted queries: {audit['trusted_query_count']}")
    print(f"- Eval files: {audit['eval_file_count']}")
    print(f"- Eval questions: {audit['eval_question_count']}")
    print("")
    if audit["critical"]:
        print("Critical gaps")
        for issue in audit["critical"]:
            print(f"- {issue}")
        print("")
    if audit["warnings"]:
        print("Warnings")
        for issue in audit["warnings"][:20]:
            print(f"- {issue}")
        if len(audit["warnings"]) > 20:
            print(f"- ... {len(audit['warnings']) - 20} more warnings")
        print("")
    if audit["recommended"]:
        print("Recommended fixes")
        for fix in audit["recommended"]:
            print(f"- {fix}")
        print("")
    print("Closed-loop rule")
    print("- Read metrics, answer paths, sources, corrections, decisions, playbooks, and evals before raw discovery.")
    print("- Write useful corrections, trusted SQL, metric packets, evals, and proof receipts back to the repo.")
    print("- Treat grade C or D as not ready for final stakeholder-facing answers.")
    return 2 if args.strict and audit["grade"] in {"C", "D"} else 0


def default_company_repo_name(company: str) -> str:
    parts = []
    current = []
    for char in company:
        if char.isalnum():
            current.append(char)
        elif current:
            parts.append("".join(current))
            current = []
    if current:
        parts.append("".join(current))
    suffix = "".join(part[:1].upper() + part[1:] for part in parts) or "Company"
    return f"ChatData-{suffix}"


def company_repo_root(paths: Paths) -> Path | None:
    company_repo = read_json(paths.company_repo_manifest_path, {})
    if not company_repo or company_repo.get("_corrupt"):
        return None
    raw_path = company_repo.get("path")
    if not raw_path:
        return None
    repo_path = Path(str(raw_path)).expanduser()
    return repo_path if repo_path.exists() else None


def metric_packet_dir(paths: Paths) -> Path:
    company_root = company_repo_root(paths)
    if company_root:
        return company_root / "metrics"
    return paths.metrics_dir


def audit_company_repo(repo_root: Path) -> dict[str, Any]:
    required_dirs = ["metrics", "answer-paths", "corrections", "proof", "decisions", "sources", "playbooks", "evals"]
    critical: list[str] = []
    warnings: list[str] = []
    recommended: list[str] = []

    for folder in required_dirs:
        if not (repo_root / folder).is_dir():
            critical.append(f"Missing required folder: {folder}/")

    metric_files = sorted((repo_root / "metrics").glob("*.yaml")) if (repo_root / "metrics").exists() else []
    answer_path_files = sorted((repo_root / "answer-paths").glob("*.yaml")) if (repo_root / "answer-paths").exists() else []
    eval_files = sorted((repo_root / "evals").glob("*.yaml")) if (repo_root / "evals").exists() else []
    trusted_query_files = sorted((repo_root / "queries" / "trusted").glob("*.sql")) if (repo_root / "queries" / "trusted").exists() else []

    metric_ids: set[str] = set()
    required_metric_fields = [
        "metric_id",
        "definition",
        "business_owner",
        "data_owner",
        "grain",
        "timezone",
        "trusted_query_path",
        "freshness_rule",
        "review_status",
        "trust_state",
        "last_reviewed_at",
    ]
    for metric_file in metric_files:
        payload = metric_file.read_text(encoding="utf-8")
        metric_id = yaml_scalar(payload, "metric_id") or metric_file.stem
        metric_ids.add(metric_id)
        for field in required_metric_fields:
            value = yaml_scalar(payload, field)
            if not value or value.upper() == "TBD":
                warnings.append(f"{metric_file.relative_to(repo_root)} missing {field}")
        trust_state = (yaml_scalar(payload, "trust_state") or "").lower()
        review_status = (yaml_scalar(payload, "review_status") or "").lower()
        if trust_state not in {"verified", "trusted"} and review_status not in {"reviewed", "approved"}:
            warnings.append(f"{metric_file.relative_to(repo_root)} is not reviewed or trusted")
        trusted_query_path = yaml_scalar(payload, "trusted_query_path")
        if trusted_query_path:
            query_path = repo_root / trusted_query_path
            if not query_path.exists():
                critical.append(f"{metric_file.relative_to(repo_root)} references missing trusted query: {trusted_query_path}")

    for answer_path in answer_path_files:
        payload = answer_path.read_text(encoding="utf-8")
        metric = yaml_scalar(payload, "metric")
        query_path = yaml_scalar(payload, "query_or_retrieval_path")
        review_status = (yaml_scalar(payload, "review_status") or "").lower()
        if metric and metric not in metric_ids:
            critical.append(f"{answer_path.relative_to(repo_root)} references unknown metric: {metric}")
        if query_path and not (repo_root / query_path).exists():
            warnings.append(f"{answer_path.relative_to(repo_root)} references missing query path: {query_path}")
        if review_status not in {"reviewed", "approved"}:
            warnings.append(f"{answer_path.relative_to(repo_root)} is not reviewed")

    eval_question_count = 0
    for eval_file in eval_files:
        payload = eval_file.read_text(encoding="utf-8")
        eval_question_count += len(re.findall(r"(?m)^[ \t]*-[ \t]+.+", payload))

    if not metric_files:
        critical.append("No metric packets found. ChatData has no governed metric definitions to trust.")
        recommended.append("Create metric packets for the first 3-10 recurring decision metrics.")
    if not answer_path_files:
        warnings.append("No answer paths found. Recurring questions will not compound yet.")
        recommended.append("Add answer paths for the highest-frequency WBR or KPI questions.")
    if not trusted_query_files:
        warnings.append("No trusted SQL files found under queries/trusted/.")
        recommended.append("Add blessed SQL paths for reviewed dashboard totals or WBR metrics.")
    if eval_question_count < max(3, len(metric_files)):
        warnings.append("Eval coverage is thin for the number of metrics.")
        recommended.append("Create evals for ambiguity, time range, trusted source tie-out, bad definitions, and partial periods.")
    if not (repo_root / "proof" / "impact-log.jsonl").exists():
        warnings.append("No proof impact log yet.")
        recommended.append("Record proof receipts after useful analyses so value and corrections compound.")

    score = 100 - 25 * len(critical) - 6 * len(warnings)
    if score >= 85:
        grade = "A"
    elif score >= 70:
        grade = "B"
    elif score >= 50:
        grade = "C"
    else:
        grade = "D"

    return {
        "grade": grade,
        "critical": critical,
        "warnings": warnings,
        "recommended": dedupe(recommended),
        "metric_count": len(metric_files),
        "answer_path_count": len(answer_path_files),
        "trusted_query_count": len(trusted_query_files),
        "eval_file_count": len(eval_files),
        "eval_question_count": eval_question_count,
    }


def yaml_scalar(payload: str, key: str) -> str:
    match = re.search(rf"(?m)^[ \t]*{re.escape(key)}:[ \t]*(.*?)[ \t]*$", payload)
    if not match:
        return ""
    value = match.group(1).strip()
    if value in {"", "[]", "null", "None"}:
        return ""
    return value.strip("'\"")


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def write_text_if_missing(path: Path, content: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def scaffold_company_repo(
    repo_path: Path, *, company: str, repo: str, owner: str, remote: str, sync_mode: str
) -> None:
    repo_path.mkdir(parents=True, exist_ok=True)
    folders = [
        "metrics",
        "answer-paths",
        "corrections",
        "proof",
        "decisions",
        "sources",
        "playbooks",
        "evals",
    ]
    for folder in folders:
        (repo_path / folder).mkdir(parents=True, exist_ok=True)

    today = now_utc().date().isoformat()
    write_text_if_missing(
        repo_path / "README.md",
        f"""# {repo}

Private ChatData context repo for {company}.

This repo is the multiplayer source of truth for ChatData analysis. Keep reusable context here instead of leaving it in private chats, notebooks, or one-off prompts.

## What Belongs Here

- `metrics/`: trusted metric packets with owners, grain, filters, exclusions, freshness, caveats, and validation rules.
- `answer-paths/`: reviewed paths for recurring questions, including SQL, source links, checks, and approved wording.
- `corrections/`: mistakes, gotchas, rejected definitions, and caveats ChatData must remember.
- `proof/`: receipts from useful analyses and decision-ready work.
- `decisions/`: WBR notes, business decisions, owner, date, and follow-up.
- `sources/`: blessed dashboards, semantic layer references, dbt/model links, warehouse notes, and docs.
- `playbooks/`: repeatable workflows for KPI movement, WBR prep, anomaly triage, and metric cleanup.
- `evals/`: questions and expected behavior that test whether ChatData is using the right context.

## Rule

Before meaningful analysis, ChatData reads this repo. After useful analysis, ChatData proposes a change back to this repo.
""",
    )
    write_text_if_missing(
        repo_path / "chatdata.yml",
        f"""schema_version: {STATE_SCHEMA_VERSION}
company: {company}
repo: {repo}
owner: {owner}
remote: {remote}
created_at: {today}
mode: multiplayer
sync_mode: {sync_mode}
required_for_team_work: true
gates:
  - read_company_context_before_analysis
  - use_metric_packets_before_raw_discovery
  - write_reusable_context_back_to_repo
  - record_proof_for_material_findings
  - prefer_pull_request_for_shared_context_changes
""",
    )
    section_readmes = {
        "metrics": "Trusted metric packets. One YAML file per governed metric.",
        "answer-paths": "Reviewed answer paths for recurring business questions.",
        "corrections": "Corrections, caveats, and known traps ChatData must remember.",
        "proof": "Impact receipts and evidence packs from useful work.",
        "decisions": "Decision memos, WBR notes, owners, and follow-up dates.",
        "sources": "Blessed dashboards, SQL paths, semantic objects, dbt/model links, and data-source notes.",
        "playbooks": "Repeatable workflows for common analysis patterns.",
        "evals": "Questions and expected behavior used to test ChatData reliability.",
    }
    for folder, description in section_readmes.items():
        write_text_if_missing(repo_path / folder / "README.md", f"# {folder}\n\n{description}\n")


def run_command(command: list[str], cwd: Path, timeout: int = 30) -> dict[str, Any]:
    try:
        result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False)
    except FileNotFoundError:
        return {"available": False, "returncode": 127, "stdout": "", "stderr": "command not found"}
    except subprocess.TimeoutExpired:
        return {"available": True, "returncode": 124, "stdout": "", "stderr": "command timed out"}
    return {
        "available": True,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_setting_value(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "yes", "on"}:
        return True
    if lowered in {"false", "no", "off"}:
        return False
    try:
        return int(value)
    except ValueError:
        return value


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def slugify(value: str) -> str:
    result = []
    last_was_sep = False
    for char in value.strip().lower():
        if char.isalnum():
            result.append(char)
            last_was_sep = False
        elif not last_was_sep:
            result.append("_")
            last_was_sep = True
    return "".join(result).strip("_") or "metric"


def metric_template(metric_id: str, label: str) -> str:
    today = now_utc().date().isoformat()
    return f"""metric_id: {metric_id}
label: {label}
definition: Replace with the official plain-English definition.
business_owner: TBD
data_owner: TBD
grain: TBD
timezone: America/Los_Angeles
filters: []
exclusions: []
trusted_dashboard_url:
trusted_query_path:
trusted_query_backend:
freshness_rule: Define when this source is fresh enough to answer.
validation_tolerance:
  pct_delta_max: 0.5
known_caveats: []
clarification_rules:
  - if date range omitted, ask for or infer the decision period before querying
escalation_rules:
  - if benchmark delta exceeds tolerance, mark needs_review
review_status: draft
trust_state: draft
last_reviewed_at: {today}
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ChatData local state helper")
    parser.add_argument("--home", help="Override ~/.chatdata for tests or isolated runs")
    parser.add_argument("--project", help="Override project .chatdata directory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="Initialize local trial, profile, and project state")
    start.add_argument("--role")
    start.add_argument("--business-context")
    start.add_argument("--metrics")
    start.add_argument("--forums")
    start.add_argument("--output")
    start.add_argument("--email", help="Work email used for ChatData portal sync")
    start.add_argument("--token", help="ChatData portal token")
    start.add_argument("--api-url", help="ChatData portal API URL")
    start.set_defaults(func=command_start)

    status = subparsers.add_parser("status", help="Show trial, proof, and setup status")
    status.set_defaults(func=command_status)

    onboarding = subparsers.add_parser("onboarding", help="Show the guided first-session onboarding checklist")
    onboarding.set_defaults(func=command_onboarding)

    impact = subparsers.add_parser("impact", help="Print one branded ChatData impact line")
    impact.set_defaults(func=command_impact)

    guard = subparsers.add_parser("guard", help="Return success only when trial/license is active")
    guard.add_argument("--company-repo", action="store_true", help="Also require a configured company context repo")
    guard.set_defaults(func=command_guard)

    license_parser = subparsers.add_parser("license", help="Activate or issue a manual license")
    license_parser.add_argument("--key")
    license_parser.add_argument("--issue", action="store_true")
    license_parser.add_argument("--email")
    license_parser.add_argument("--expires")
    license_parser.set_defaults(func=command_license)

    settings = subparsers.add_parser("settings", help="Show or update local settings")
    settings.add_argument("--set", action="append")
    settings.set_defaults(func=command_settings)

    activate_session = subparsers.add_parser(
        "activate-session",
        help="Make ChatData own this Claude Code workspace footer, agent metadata, and attribution",
    )
    activate_session.add_argument("--workspace", help="Workspace directory to update; defaults to the current directory")
    activate_session.add_argument("--plugin-root", help="Plugin root for tests or custom installs")
    activate_session.set_defaults(func=command_activate_session)

    login = subparsers.add_parser("login", help="Sync ChatData portal config and attach company repo")
    login.add_argument("--email")
    login.add_argument("--token")
    login.add_argument("--token-env", help="Read the ChatData portal token from this environment variable")
    login.add_argument("--token-stdin", action="store_true", help="Read the ChatData portal token from stdin")
    login.add_argument("--api-url")
    login.set_defaults(func=command_login)

    connect = subparsers.add_parser("connect-data", help="Record a data source manifest entry")
    connect.add_argument("--name", required=True)
    connect.add_argument("--kind", required=True, choices=["csv", "duckdb", "warehouse", "mcp", "repo"])
    connect.add_argument("--path", required=True)
    connect.add_argument("--notes")
    connect.set_defaults(func=command_connect_data)

    company_repo = subparsers.add_parser("company-repo", help="Create, attach, or require the shared company context repo")
    company_repo.add_argument("--company")
    company_repo.add_argument("--domain")
    company_repo.add_argument("--email")
    company_repo.add_argument("--owner")
    company_repo.add_argument("--repo")
    company_repo.add_argument("--path")
    company_repo.add_argument("--remote")
    company_repo.add_argument(
        "--sync-mode",
        choices=["local-git", "chatdata-managed", "customer-github-app"],
        help="How shared context sync should be handled",
    )
    company_repo.add_argument("--chatdata-api-url")
    company_repo.add_argument("--require", action="store_true")
    company_repo.set_defaults(func=command_company_repo)

    github = subparsers.add_parser("github", help="Show GitHub and company repo sync readiness")
    github.add_argument("--create-plan", action="store_true")
    github.add_argument("--company")
    github.add_argument("--owner")
    github.add_argument("--repo")
    github.set_defaults(func=command_github)

    audit_context = subparsers.add_parser("audit-context", help="Audit company repo context health")
    audit_context.add_argument("--strict", action="store_true", help="Exit non-zero on grade C or D")
    audit_context.set_defaults(func=command_audit_context)

    metrics = subparsers.add_parser("metrics", help="Create a metric trust packet")
    metrics.add_argument("metric_id")
    metrics.add_argument("--label")
    metrics.add_argument("--force", action="store_true")
    metrics.set_defaults(func=command_metrics)

    proof = subparsers.add_parser("proof", help="Record or export proof receipts")
    proof.add_argument("--record", action="store_true")
    proof.add_argument("--workflow")
    proof.add_argument("--question")
    proof.add_argument("--artifact")
    proof.add_argument("--sources")
    proof.add_argument("--validation")
    proof.add_argument("--confidence")
    proof.add_argument("--time-saved-minutes")
    proof.add_argument("--value-usd")
    proof.add_argument("--next-action")
    proof.add_argument("--json", action="store_true")
    proof.set_defaults(func=command_proof)

    benchmark = subparsers.add_parser("benchmark", help="Print a synthetic ChatData workflow benchmark")
    benchmark.set_defaults(func=command_benchmark)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
