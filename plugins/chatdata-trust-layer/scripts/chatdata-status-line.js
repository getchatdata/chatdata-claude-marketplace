#!/usr/bin/env node
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");

function readJson(filePath, fallback) {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return fallback;
  }
}

function countLines(filePath) {
  try {
    return fs
      .readFileSync(filePath, "utf8")
      .split(/\r?\n/)
      .filter((line) => line.trim()).length;
  } catch {
    return 0;
  }
}

function readJsonl(filePath) {
  try {
    return fs
      .readFileSync(filePath, "utf8")
      .split(/\r?\n/)
      .filter((line) => line.trim())
      .map((line) => {
        try {
          return JSON.parse(line);
        } catch {
          return null;
        }
      })
      .filter(Boolean);
  } catch {
    return [];
  }
}

function formatHours(minutes) {
  const hours = minutes / 60;
  if (hours < 1) {
    return `${Math.round(minutes)}m`;
  }
  return `${hours.toFixed(hours >= 10 ? 0 : 1)}h`;
}

function formatUsd(value) {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(value >= 10000000 ? 0 : 1)}M`;
  }
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(value >= 10000 ? 0 : 1)}K`;
  }
  return `$${Math.round(value)}`;
}

function proofImpact(entries) {
  const minutes = entries.reduce((sum, entry) => sum + Number(entry.estimated_time_saved_minutes || 0), 0);
  const recordedValue = entries.reduce((sum, entry) => sum + Number(entry.estimated_value_usd || 0), 0);
  const analystHourlyRate = Number(process.env.CHATDATA_STATUSLINE_HOURLY_RATE || 120);
  const value = recordedValue > 0 ? recordedValue : (minutes / 60) * analystHourlyRate;
  return {
    loops: entries.length,
    minutes,
    value,
    valueIsEstimated: recordedValue <= 0 && minutes > 0,
  };
}

function walkUpForProjectState(startDir) {
  let current = path.resolve(startDir || process.cwd());
  while (true) {
    const candidate = path.join(current, ".chatdata");
    if (fs.existsSync(candidate)) {
      return candidate;
    }
    const next = path.dirname(current);
    if (next === current) {
      return path.join(path.resolve(startDir || process.cwd()), ".chatdata");
    }
    current = next;
  }
}

function daysRemaining(license) {
  const end = license && license.trial_ends_at;
  if (!end) {
    return "trial";
  }
  const diffMs = new Date(end).getTime() - Date.now();
  if (!Number.isFinite(diffMs)) {
    return "trial";
  }
  return `${Math.max(0, Math.ceil(diffMs / 86400000))}d`;
}

function metricCount(repoPath, projectStatePath) {
  const repoMetrics = repoPath ? path.join(repoPath, "metrics") : "";
  const localMetrics = path.join(projectStatePath, "metrics");
  const metricsDir = fs.existsSync(repoMetrics) ? repoMetrics : localMetrics;
  try {
    return fs.readdirSync(metricsDir).filter((name) => name.endsWith(".yaml")).length;
  } catch {
    return 0;
  }
}

function color(text, code) {
  if (process.env.NO_COLOR || process.env.CHATDATA_STATUSLINE_COLOR === "false") {
    return text;
  }
  return `\u001b[${code}m${text}\u001b[0m`;
}

function main() {
  const home = path.join(os.homedir(), ".chatdata");
  const projectState = walkUpForProjectState(process.cwd());
  const license = readJson(path.join(home, "license.json"), {});
  const companyRepo = readJson(path.join(projectState, "company-repo.json"), {});
  const onboarding = readJson(path.join(projectState, "onboarding.json"), {});
  const repoPath = companyRepo && companyRepo.path ? String(companyRepo.path) : "";
  const proofPath = repoPath
    ? path.join(repoPath, "proof", "impact-log.jsonl")
    : path.join(projectState, "impact-log.jsonl");
  const impact = proofImpact(readJsonl(proofPath));
  const repoState = repoPath ? "repo:on" : "repo:missing";
  const syncState = companyRepo && companyRepo.last_sync_status === "synced" ? "sync:on" : "sync:check";
  const onboardingState =
    onboarding && onboarding.complete
      ? "onboarded"
      : onboarding && onboarding.total
        ? `setup:${onboarding.completed || 0}/${onboarding.total}`
        : "setup";
  const metricTotal = metricCount(repoPath, projectState);

  if (impact.loops > 0) {
    const valueLabel = `${formatUsd(impact.value)}${impact.valueIsEstimated ? " est" : ""}`;
    console.log(
      `${color("CHATDATA", "1;32")} blocked ${color(String(impact.loops), "1;36")} AI analytics slop loops` +
        ` | saved:${color(formatHours(impact.minutes), "1;36")}` +
        ` | cost avoided:${color(valueLabel, "1;32")}` +
        ` | trust:${metricTotal} metric${metricTotal === 1 ? "" : "s"}` +
        ` | ${syncState} | trial:${daysRemaining(license)}`,
    );
    return;
  }

  console.log(
    `${color("CHATDATA", "1;32")} stops AI analytics slop` +
      ` | ${repoState} | ${syncState} | metrics:${metricTotal}` +
      ` | proof:${countLines(proofPath)} | ${onboardingState} | trial:${daysRemaining(license)}`,
  );
}

main();
