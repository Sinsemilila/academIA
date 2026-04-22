"""Run Groq llama-3.3-70b as κ-judge on the mega_prompt scenarios."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

PROMPT = Path("/opt/academie/scripts/oracle/kappa/mega_prompt.txt").read_text()
OUT = Path("/opt/academie/scripts/oracle/kappa/scores_groq_llama70b.json")

payload = {
    "model": "groq-standard",  # llama-3.3-70b-versatile
    "messages": [{"role": "user", "content": PROMPT}],
    "temperature": 0.0,
    "max_tokens": 4000,
}

result = subprocess.run(
    [
        "curl", "-s", "--max-time", "120", "-X", "POST",
        "http://localhost:4000/v1/chat/completions",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload),
    ],
    capture_output=True, text=True, check=True,
)

resp = json.loads(result.stdout)
content = resp["choices"][0]["message"]["content"]

# Strip ```json fences if present
if content.strip().startswith("```"):
    content = content.strip().strip("`")
    if content.startswith("json"):
        content = content[4:]
    content = content.strip()
    if content.endswith("```"):
        content = content[:-3].strip()

try:
    scores = json.loads(content)
except json.JSONDecodeError as e:
    print(f"Parse failed: {e}")
    print(f"Raw content (first 500 chars):")
    print(content[:500])
    raise

OUT.write_text(json.dumps(scores, indent=2))
print(f"✓ {len(scores.get('scores', []))} scores → {OUT}")
print(f"Model used: {resp.get('model')}")
print(f"Usage: {resp.get('usage')}")
