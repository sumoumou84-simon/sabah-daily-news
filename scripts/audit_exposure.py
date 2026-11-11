import subprocess
import re
import json
import os

commit_sha = "30ee6ae2aab6d4ecb99dd7535aa74f7ca6ccd2f4"
files = subprocess.check_output(
    ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_sha]
).decode("utf-8").splitlines()

secret_patterns = {
    "generic_secret": re.compile(r'(?i)(?:api_key|token|password|secret|bearer)\s*[:=]\s*[\'"][A-Za-z0-9_\-\.]{8,}[\'"]'),
    "github_pat": re.compile(r'ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82}'),
    "google_api_key": re.compile(r'AIza[0-9A-Za-z\-_]{35}'),
    "openai_api_key": re.compile(r'sk-[a-zA-Z0-9]{20,}'),
    "email_address": re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'),
    "phone_number": re.compile(r'(\+?60[- ]?[1-9]\d{1,2}[- ]?\d{6,8})')
}

audit_results = {}
for f in files:
    content = subprocess.check_output(["git", "show", f"{commit_sha}:{f}"]).decode("utf-8", errors="ignore")
    audit_results[f] = {
        "file_size": len(content),
        "patterns_found": {}
    }
    for name, pat in secret_patterns.items():
        matches = pat.findall(content)
        if matches:
            audit_results[f]["patterns_found"][name] = len(matches)

print(f"Audited {len(files)} files in commit {commit_sha}")
for f, data in audit_results.items():
    if data["patterns_found"]:
        print(f"File {f}: {data['patterns_found']}")

with open("reports/phase361_scan_raw.json", "w", encoding="utf-8") as fp:
    json.dump(audit_results, fp, indent=2)
