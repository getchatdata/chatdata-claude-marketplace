#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised by local smoke tests when PyYAML is absent
    yaml = None


def sha256_for_paths(paths: list[Path], root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def list_files(root: Path, pattern: str) -> list[Path]:
    return [path for path in root.glob(pattern) if path.is_file()]


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        if yaml is not None:
            return to_jsonable(yaml.safe_load(handle))
        return to_jsonable(simple_yaml_load(handle.read()))


def simple_yaml_load(text: str):
    """Parse the small YAML subset used by the ChatData template repo.

    This keeps local packaging working on fresh machines before PyYAML is
    installed. It is not a general YAML parser.
    """

    lines = [
        line.rstrip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not lines:
        return None
    value, _ = parse_yaml_block(lines, 0, indentation(lines[0]))
    return value


def parse_yaml_block(lines: list[str], index: int, indent: int):
    if index >= len(lines):
        return None, index
    stripped = lines[index][indent:]
    if stripped.startswith("- "):
        return parse_yaml_list(lines, index, indent)
    return parse_yaml_dict(lines, index, indent)


def parse_yaml_dict(lines: list[str], index: int, indent: int):
    result = {}
    while index < len(lines):
        current_indent = indentation(lines[index])
        if current_indent < indent:
            break
        if current_indent > indent:
            break
        stripped = lines[index][indent:]
        if stripped.startswith("- "):
            break
        key, raw_value = split_yaml_pair(stripped)
        index += 1
        if raw_value == "":
            if index < len(lines) and indentation(lines[index]) > indent:
                nested, index = parse_yaml_block(lines, index, indentation(lines[index]))
                result[key] = nested
            else:
                result[key] = None
        else:
            result[key] = parse_yaml_scalar(raw_value)
    return result, index


def parse_yaml_list(lines: list[str], index: int, indent: int):
    result = []
    while index < len(lines):
        current_indent = indentation(lines[index])
        if current_indent < indent:
            break
        if current_indent != indent:
            break
        stripped = lines[index][indent:]
        if not stripped.startswith("- "):
            break
        item_text = stripped[2:].strip()
        index += 1
        if item_text == "":
            item, index = parse_yaml_block(lines, index, indentation(lines[index]))
            result.append(item)
            continue
        if looks_like_yaml_pair(item_text):
            key, raw_value = split_yaml_pair(item_text)
            item = {key: parse_yaml_scalar(raw_value) if raw_value else None}
            if index < len(lines) and indentation(lines[index]) > indent:
                nested, index = parse_yaml_block(lines, index, indentation(lines[index]))
                if isinstance(nested, dict):
                    item.update(nested)
                else:
                    item[key] = nested
            result.append(item)
            continue
        result.append(parse_yaml_scalar(item_text))
    return result, index


def indentation(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def split_yaml_pair(text: str) -> tuple[str, str]:
    key, value = text.split(":", 1)
    return key.strip(), value.strip()


def looks_like_yaml_pair(text: str) -> bool:
    if ":" not in text:
        return False
    key, _ = text.split(":", 1)
    return bool(key.strip()) and " " not in key.strip()


def parse_yaml_scalar(value: str):
    if value == "":
        return None
    if value in {"[]", "{}"}:
        return [] if value == "[]" else {}
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_yaml_scalar(item.strip()) for item in inner.split(",")]
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none", "~"}:
        return None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def to_jsonable(value):
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def copy_if_exists(source: Path, destination: Path) -> None:
    if not source.exists():
        return

    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def build_metric(metric_path: Path) -> dict:
    payload = load_yaml(metric_path)
    return {
        "metricId": payload["metric_id"],
        "label": payload["label"],
        "definition": payload["definition"],
        "businessOwner": payload["business_owner"],
        "dataOwner": payload["data_owner"],
        "grain": payload["grain"],
        "timezone": payload["timezone"],
        "filters": payload.get("filters", []),
        "exclusions": payload.get("exclusions", []),
        "trustedDashboardUrl": payload.get("trusted_dashboard_url"),
        "trustedQueryPath": payload.get("trusted_query_path"),
        "trustedQueryBackend": payload.get("trusted_query_backend"),
        "freshnessRule": payload["freshness_rule"],
        "validationTolerance": {
            "pctDeltaMax": float(payload["validation_tolerance"]["pct_delta_max"])
        },
        "knownCaveats": payload.get("known_caveats", []),
        "clarificationRules": payload.get("clarification_rules", []),
        "escalationRules": payload.get("escalation_rules", []),
        "reviewStatus": payload["review_status"],
        "trustState": payload["trust_state"],
        "lastReviewedAt": payload["last_reviewed_at"],
    }


def build_answer_path(answer_path: Path) -> dict:
    payload = load_yaml(answer_path)
    slack_response = payload.get("slack_response", {})
    return {
        "answerPathId": payload["answer_path_id"],
        "canonicalQuestion": payload["canonical_question"],
        "aliases": payload.get("aliases", []),
        "metricId": payload["metric"],
        "routeId": payload["route_id"],
        "preferredDimensions": payload.get("preferred_dimensions", []),
        "retrievalPath": payload["query_or_retrieval_path"],
        "validationRoutine": payload["validation_routine"],
        "benchmarkSourcePreference": payload.get("benchmark_source_preference", []),
        "caveats": payload.get("caveats", []),
        "expectedAnswerState": payload["expected_answer_state"],
        "reviewStatus": payload["review_status"],
        "maturity": payload["maturity"],
        "recurrenceTier": payload["recurrence_tier"],
        "businessValueTier": payload["business_value_tier"],
        "slackResponse": {
            "draft": slack_response["draft"],
            "benchmarked": slack_response.get("benchmarked"),
            "verified": slack_response["verified"],
            "trusted": slack_response.get("trusted"),
            "needsReview": slack_response.get("needs_review"),
            "nextActionDraft": slack_response["next_action_draft"],
            "nextActionVerified": slack_response["next_action_verified"],
            "nextActionTrusted": slack_response.get("next_action_trusted"),
            "evidenceDraft": slack_response.get("evidence_draft", []),
            "evidenceVerified": slack_response.get("evidence_verified", []),
            "benchmarkLinkKeywords": slack_response.get("benchmark_link_keywords", []),
            "screenshotKeywords": slack_response.get("screenshot_keywords", []),
        },
    }


def build_trusted_artifacts(artifacts_path: Path) -> list[dict]:
    if not artifacts_path.exists():
        return []

    payload = load_yaml(artifacts_path) or {}
    artifacts = payload.get("trusted_artifacts", [])
    return [
        {
            "artifactId": artifact["artifact_id"],
            "metricId": artifact["metric_id"],
            "label": artifact["label"],
            "sourceType": artifact["source_type"],
            "url": artifact.get("url"),
            "queryPath": artifact.get("query_path"),
            "freshness": artifact["freshness"],
            "currentValue": float(artifact["current_value"]),
            "previousValue": float(artifact["previous_value"]),
            "tolerancePct": float(artifact["tolerance_pct"]),
            "dimensions": artifact.get("dimensions", []),
            "lastValidatedAt": artifact["last_validated_at"],
        }
        for artifact in artifacts
    ]


def guess_route_id(question: str) -> str:
    normalized = question.lower()
    if "real" in normalized or "data issue" in normalized or "dashboard issue" in normalized:
        return "movement-real-or-data-issue"
    if "mobile paid search" in normalized or "paid search" in normalized:
        return "mobile-paid-search-follow-up"
    if "segment" in normalized or "channel" in normalized or "device" in normalized or "market" in normalized:
        return "segment-driver"
    return "self-serve-conversion-drop"


def build_eval_questions(evals_path: Path) -> list[dict]:
    if not evals_path.exists():
        return []

    payload = load_yaml(evals_path) or {}
    questions = payload.get("questions", [])
    results = []
    for index, question in enumerate(questions, start=1):
        route_id = guess_route_id(question)
        accepted = ["verified"]
        if route_id == "mobile-paid-search-follow-up":
            accepted = ["draft", "benchmarked", "needs_review"]
        elif route_id == "segment-driver":
            accepted = ["verified", "trusted"]

        results.append(
            {
                "evalId": f"generated-eval-{index:02d}",
                "canonicalQuestion": question,
                "expectedRouteId": route_id,
                "expectedMetricId": "self_serve_conversion",
                "requiredFilters": ["weekly business review period", "exclude test accounts"],
                "expectedCaveats": ["campaign tagging changed during the same period"],
                "validationReference": "weekly-dashboard-self-serve-conversion",
                "acceptedAnswerStates": accepted,
            }
        )
    return results


def maybe_post_bundle(runtime_url: Optional[str], admin_token: Optional[str], bundle: dict) -> None:
    if not runtime_url or not admin_token:
        return

    request = urllib.request.Request(
        runtime_url.rstrip("/") + "/admin/publish-bundle",
        data=json.dumps(bundle).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {admin_token}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8")
        print(f"Runtime publish response: {body}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render an immutable ChatData Slack bundle from canonical repo files."
    )
    parser.add_argument("repo_path", help="Path to the trust-layer repo")
    parser.add_argument("--customer-id", default="demo-open-door-like")
    parser.add_argument("--workspace-id", default="demo-slack-workspace")
    parser.add_argument(
        "--pilot-domain",
        default="seller-funnel-weekly-business-review",
    )
    parser.add_argument(
        "--runtime-url",
        default=None,
        help="Optional ChatData runtime URL. If set with --admin-token, publish will POST the bundle to the runtime.",
    )
    parser.add_argument(
        "--admin-token",
        default=None,
        help="Admin token for runtime publish.",
    )
    args = parser.parse_args()

    repo = Path(args.repo_path).expanduser().resolve()
    published = repo / "published"

    if published.exists():
        shutil.rmtree(published)
    published.mkdir(parents=True, exist_ok=True)

    metric_files = list_files(repo, "metrics/*.yaml")
    answer_path_files = list_files(repo, "answer-paths/*.yaml")
    trusted_query_files = list_files(repo, "queries/trusted/*.sql")
    generated_query_files = list_files(repo, "queries/generated/*.sql")
    source_files = (
        metric_files
        + answer_path_files
        + trusted_query_files
        + generated_query_files
        + list_files(repo, "artifacts/*.yaml")
        + list_files(repo, "catalog/*.yaml")
        + list_files(repo, "evals/*.yaml")
    )
    artifact_hash = sha256_for_paths(source_files, repo) if source_files else "empty-bundle"
    published_at = datetime.now(timezone.utc).isoformat()

    manifest = {
        "schemaVersion": "1.0.0",
        "bundleVersion": published_at,
        "customerId": args.customer_id,
        "workspaceId": args.workspace_id,
        "sourceCommit": "local-working-tree",
        "publishedAt": published_at,
        "artifactHash": artifact_hash,
        "compatibilityVersion": "1",
        "metricsCount": len(metric_files),
        "answerPathsCount": len(answer_path_files),
    }

    bundle = {
        "manifest": manifest,
        "pilotDomain": args.pilot_domain,
        "metrics": [build_metric(path) for path in sorted(metric_files)],
        "trustedArtifacts": build_trusted_artifacts(repo / "artifacts" / "trusted_artifacts.yaml"),
        "answerPaths": [build_answer_path(path) for path in sorted(answer_path_files)],
        "evalQuestions": build_eval_questions(repo / "evals" / "recurring_questions.yaml"),
    }

    for relative in [
        "metrics",
        "answer-paths",
        "queries",
        "artifacts",
        "catalog",
        "evals",
        "scripts",
    ]:
        copy_if_exists(repo / relative, published / relative)

    metrics_index = [
        {"path": path.relative_to(repo).as_posix(), "name": path.stem}
        for path in sorted(metric_files)
    ]
    answer_paths_index = [
        {"path": path.relative_to(repo).as_posix(), "name": path.stem}
        for path in sorted(answer_path_files)
    ]

    (published / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (published / "metrics_index.json").write_text(json.dumps(metrics_index, indent=2) + "\n", encoding="utf-8")
    (published / "answer_paths.json").write_text(
        json.dumps(answer_paths_index, indent=2) + "\n", encoding="utf-8"
    )
    (published / "slack_context.json").write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")

    maybe_post_bundle(args.runtime_url, args.admin_token, bundle)

    print(f"Published bundle at {published}")
    print(f"Metrics: {len(metric_files)}")
    print(f"Answer paths: {len(answer_path_files)}")
    print(f"Artifact hash: {artifact_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
