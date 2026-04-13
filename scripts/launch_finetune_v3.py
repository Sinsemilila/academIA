#!/usr/bin/env python3
"""
1. Download batch output file-TFmWyoaqyJoyBjCC82yCdG
2. Parse responses → fine-tuning JSONL format
3. Train/val split (90/10)
4. Upload to OpenAI files API
5. Launch fine-tune v3 on gpt-4o-mini
"""

import json
import os
import random
import sys
import urllib.request
import urllib.error

BATCH_OUTPUT_FILE_ID = "file-TFmWyoaqyJoyBjCC82yCdG"
SYSTEM_FT = "You analyze English errors by French speakers. Identify every USER error. Output valid JSON."


def get_api_key():
    """Extract OpenAI key from litellm config."""
    try:
        with open("/opt/litellm/config.yaml") as f:
            for line in f:
                line = line.strip()
                if "sk-proj-" in line or ("api_key" in line and "sk-" in line):
                    # Extract value after api_key: (quoted or not)
                    import re
                    m = re.search(r'["\']?(sk-[A-Za-z0-9_\-]+)["\']?', line)
                    if m:
                        return m.group(1)
    except Exception:
        pass
    key = os.environ.get("OPENAI_API_KEY", "")
    if key:
        return key
    raise RuntimeError("Cannot find OpenAI API key")


def openai_get(path, api_key):
    req = urllib.request.Request(
        f"https://api.openai.com/v1{path}",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def openai_post_json(path, data, api_key):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"https://api.openai.com/v1{path}",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def openai_upload_file(path, content_bytes, purpose, api_key):
    """Multipart upload."""
    import io
    boundary = b"----FormBoundary7MA4YWxkTrZu0gW"

    def field(name, value, filename=None, content_type=None):
        disp = f'Content-Disposition: form-data; name="{name}"'
        if filename:
            disp += f'; filename="{filename}"'
        parts = [b"--" + boundary, disp.encode()]
        if content_type:
            parts.append(f"Content-Type: {content_type}".encode())
        parts.append(b"")
        if isinstance(value, str):
            value = value.encode()
        parts.append(value)
        return b"\r\n".join(parts)

    body = b"\r\n".join([
        field("purpose", purpose),
        field("file", content_bytes, filename=path, content_type="application/octet-stream"),
        b"--" + boundary + b"--",
    ])

    req = urllib.request.Request(
        "https://api.openai.com/v1/files",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary.decode()}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def to_finetune_format(category, example):
    """Convert a generated example to OpenAI fine-tuning JSONL format."""
    sentence = example.get("sentence", "")
    original = example.get("original", "")
    correction = example.get("correction", "")
    reasoning = example.get("reasoning", "")

    if not sentence or not original:
        return None

    user_content = f"Analyze errors:\n--- Turn 1 ---\nUSER: {sentence}\nTEACHER: Good try!"
    assistant_content = json.dumps({
        "errors": [{
            "turn": 1,
            "original": original,
            "correction": correction,
            "codes": [category],
            "reasoning": reasoning,
        }]
    })

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_FT},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content},
        ]
    }


def parse_batch_output(raw_bytes):
    """Parse JSONL batch output → list of fine-tuning examples."""
    examples = []
    failed = 0
    category_counts = {}

    lines = raw_bytes.decode("utf-8").strip().split("\n")
    print(f"  {len(lines)} response lines to parse")

    for line in lines:
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            failed += 1
            continue

        # Extract custom_id → category
        custom_id = record.get("custom_id", "")
        # Format: CATEGORY_batchN_Xex  e.g. V:TENSE_batch0_40ex
        # Split on _batch to get category
        if "_batch" not in custom_id:
            failed += 1
            continue
        category = custom_id.split("_batch")[0]

        # Extract response content
        try:
            content = record["response"]["body"]["choices"][0]["message"]["content"]
            parsed = json.loads(content)
        except (KeyError, json.JSONDecodeError, IndexError):
            failed += 1
            continue

        # Handle {"examples": [...]} or [...]
        if isinstance(parsed, dict):
            for key in ["examples", "sentences", "errors", "data", "items"]:
                if key in parsed and isinstance(parsed[key], list):
                    parsed = parsed[key]
                    break
            else:
                # Try first list value
                for v in parsed.values():
                    if isinstance(v, list):
                        parsed = v
                        break
                else:
                    failed += 1
                    continue

        if not isinstance(parsed, list):
            failed += 1
            continue

        for ex in parsed:
            ft = to_finetune_format(category, ex)
            if ft:
                examples.append(ft)
                category_counts[category] = category_counts.get(category, 0) + 1

    print(f"  Parsed: {len(examples)} examples, {failed} failed responses")
    print(f"  Categories covered: {len(category_counts)}/63")

    # Show under-represented
    under = [(c, n) for c, n in sorted(category_counts.items()) if n < 30]
    if under:
        print(f"  Under-represented (<30 examples):")
        for c, n in under:
            print(f"    {c}: {n}")

    return examples


def main():
    print("=== Fine-tune v3 launch pipeline ===\n")

    api_key = get_api_key()
    print(f"API key: sk-...{api_key[-6:]}")

    # Step 1: Download batch output
    print(f"\n[1/5] Downloading batch output {BATCH_OUTPUT_FILE_ID}...")
    raw = openai_get(f"/files/{BATCH_OUTPUT_FILE_ID}/content", api_key)
    print(f"  Downloaded: {len(raw):,} bytes")

    # Step 2: Parse
    print("\n[2/5] Parsing responses...")
    examples = parse_batch_output(raw)
    print(f"  Total fine-tune examples: {len(examples)}")

    if len(examples) < 500:
        print("ERROR: Too few examples parsed. Aborting.")
        sys.exit(1)

    # Step 3: Shuffle + split
    print("\n[3/5] Splitting train/val (90/10)...")
    random.seed(42)
    random.shuffle(examples)
    split = int(len(examples) * 0.9)
    train = examples[:split]
    val = examples[split:]
    print(f"  Train: {len(train)}, Val: {len(val)}")

    # Write to disk for reference
    train_path = "/tmp/train_v3.jsonl"
    val_path = "/tmp/val_v3.jsonl"
    with open(train_path, "w") as f:
        for ex in train:
            f.write(json.dumps(ex) + "\n")
    with open(val_path, "w") as f:
        for ex in val:
            f.write(json.dumps(ex) + "\n")
    print(f"  Saved: {train_path}, {val_path}")

    # Step 4: Upload files
    print("\n[4/5] Uploading to OpenAI files API...")
    with open(train_path, "rb") as f:
        train_bytes = f.read()
    with open(val_path, "rb") as f:
        val_bytes = f.read()

    print("  Uploading train file...")
    train_resp = openai_upload_file("train_v3.jsonl", train_bytes, "fine-tune", api_key)
    train_file_id = train_resp["id"]
    print(f"  Train file ID: {train_file_id}")

    print("  Uploading val file...")
    val_resp = openai_upload_file("val_v3.jsonl", val_bytes, "fine-tune", api_key)
    val_file_id = val_resp["id"]
    print(f"  Val file ID: {val_file_id}")

    # Step 5: Launch fine-tune
    print("\n[5/5] Launching fine-tune v3...")
    ft_payload = {
        "training_file": train_file_id,
        "validation_file": val_file_id,
        "model": "gpt-4o-mini-2024-07-18",
        "suffix": "academie-errors-v3",
        "hyperparameters": {
            "n_epochs": 3,
        },
    }
    ft_resp = openai_post_json("/fine_tuning/jobs", ft_payload, api_key)
    ft_job_id = ft_resp["id"]
    ft_status = ft_resp.get("status", "unknown")

    print(f"\n{'='*50}")
    print(f"Fine-tune v3 launched!")
    print(f"  Job ID: {ft_job_id}")
    print(f"  Status: {ft_status}")
    print(f"  Model: gpt-4o-mini-2024-07-18:academie-errors-v3")
    print(f"\nMonitor:")
    print(f"  curl -s https://api.openai.com/v1/fine_tuning/jobs/{ft_job_id} -H 'Authorization: Bearer $KEY'")
    print(f"\nNext: once status=succeeded, copy model ID and test on 189 cases.")


if __name__ == "__main__":
    main()
