#!/usr/bin/env python3
"""Merge Tenant Configurations.

Merges all JSON files from config/tenants/ into a single config/init.json
that the MinIO init container processes on startup.

Usage: python scripts/merge-tenant-configs.py

Prerequisites: Python 3.6+ (no external dependencies)
"""

import json
import sys
from pathlib import Path

SECTIONS = ["buckets", "policies", "users", "groups", "service_accounts", "notifications"]

project_dir = Path(__file__).resolve().parent.parent
tenants_dir = project_dir / "config" / "tenants"
output_file = project_dir / "config" / "init.json"


# ── Preflight checks ────────────────────────────────────────────────────────

if not tenants_dir.is_dir():
    print(f"Error: Tenant config directory not found: {tenants_dir}")
    sys.exit(1)

json_files = sorted(tenants_dir.glob("*.json"))

if not json_files:
    print(f"Error: No JSON files found in {tenants_dir}")
    sys.exit(1)


# ── Load and validate each tenant config ─────────────────────────────────────

tenants: list[dict] = []

for path in json_files:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: Invalid JSON in {path.name}: {exc}")
        sys.exit(1)

    tenants.append(data)


# ── Merge all tenant configs ─────────────────────────────────────────────────

merged = {section: [] for section in SECTIONS}

for data in tenants:
    for section in SECTIONS:
        merged[section].extend(data.get(section, []))


# ── Write output ─────────────────────────────────────────────────────────────

output_file.write_text(
    json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)


# ── Summary ──────────────────────────────────────────────────────────────────

print(f"Merged {len(json_files)} tenant config(s) into {output_file.relative_to(project_dir)}")
for section in SECTIONS:
    label = section.replace("_", " ").title()
    print(f"  {label + ':':<20s} {len(merged[section])}")
