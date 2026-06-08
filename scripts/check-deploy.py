#!/usr/bin/env python3
"""
check-deploy.py — verify the latest CF Pages deployment for spiritvale-site succeeded.

Usage:
    make check-deploy
    python3 scripts/check-deploy.py

Requires:
    CLOUDFLARE_API_TOKEN env var (set in your shell or .env).
    CLOUDFLARE_ACCOUNT_ID env var (defaults to the spiritvale-site account).

Exit codes:
    0 — latest deploy succeeded, or CF Pages not yet connected (skip)
    1 — latest deploy failed or API error
"""

import json
import os
import sys
import urllib.request

CF_API = "https://api.cloudflare.com/client/v4"
ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "42c24507d806846e4d204f531a14007a")
PROJECT = "spiritvale-site"


def main() -> None:
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not token:
        print("SKIP: CLOUDFLARE_API_TOKEN not set — cannot verify CF Pages deploy status", file=sys.stderr)
        print("      Set the token in your shell to enable post-push deploy checks.")
        sys.exit(0)

    url = f"{CF_API}/accounts/{ACCOUNT_ID}/pages/projects/{PROJECT}/deployments?per_page=1"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as exc:
        print(f"ERROR: CF Pages API request failed: {exc}", file=sys.stderr)
        sys.exit(1)

    if not data.get("success"):
        errors = data.get("errors", [])
        print(f"ERROR: CF Pages API returned errors: {errors}", file=sys.stderr)
        sys.exit(1)

    deployments = data.get("result", [])
    if not deployments:
        print("SKIP: No CF Pages deployments found — project not yet connected to GitHub (Blocker #1).")
        print("      Go to dash.cloudflare.com → Pages → New → connect Tam4shii/spiritvale-site")
        sys.exit(0)

    dep = deployments[0]
    stage = dep.get("latest_stage", {})
    stage_name = stage.get("name", "?")
    stage_status = stage.get("status", "unknown")
    commit_hash = (dep.get("deployment_trigger", {}).get("metadata") or {}).get("commit_hash", "?")[:8]
    branch = (dep.get("deployment_trigger", {}).get("metadata") or {}).get("branch", "?")
    created_at = dep.get("created_on", "?")
    deploy_url = dep.get("url", "")

    print(f"CF Pages latest deployment:")
    print(f"  stage   : {stage_name} ({stage_status})")
    print(f"  commit  : {commit_hash} on {branch}")
    print(f"  created : {created_at}")
    if deploy_url:
        print(f"  url     : {deploy_url}")

    if stage_status == "success":
        print("CF Pages deploy: OK ✓")
        return

    if stage_status in ("active", "idle"):
        print(f"WARN: Deployment still in progress (status={stage_status}). Re-run in ~30s.", file=sys.stderr)
        sys.exit(1)

    # failure or unknown
    print(f"ERROR: Deployment did not succeed — status={stage_status}", file=sys.stderr)
    print("       Check https://dash.cloudflare.com/pages for the full build log.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
