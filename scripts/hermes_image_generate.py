#!/usr/bin/env python3
"""Generate an image via Hermes agent CLI (subprocess bridge).

Usage:
    python3 scripts/hermes_image_generate.py "prompt text" [--aspect landscape|portrait|square]

Returns JSON: {"url": "...", "path": "..."} or {"error": "..."}
"""

import argparse
import json
import os
import re
import subprocess


def generate_image(prompt: str, aspect: str = "portrait") -> dict:
    """Call hermes chat to generate an image via image_generate tool."""
    # Build the query — instruct hermes to use image_generate and return the URL
    query = (
        f"Use the image_generate tool to generate an image with this prompt. "
        f"Use aspect_ratio={aspect}. "
        f"After generating, output ONLY the result as JSON: "
        f'{{"url": "<the url or path returned by image_generate>"}}. '
        f"Do not add any explanation. Just the JSON.\n\n"
        f"Prompt:\n{prompt}"
    )

    # Find hermes binary
    hermes_bin = os.environ.get("HERMES_BIN", "hermes")

    try:
        result = subprocess.run(
            [
                hermes_bin,
                "chat",
                "-q", query,
                "-Q",  # quiet mode — only final response
                "--max-turns", "3",
            ],
            capture_output=True,
            text=True,
            timeout=300,  # image gen can take a while (complex prompts need more time)
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
    except FileNotFoundError:
        return {"error": "hermes CLI not found. Install with: pip install hermes-agent"}
    except subprocess.TimeoutExpired:
        return {"error": "Image generation timed out (300s)"}

    if result.returncode != 0:
        return {"error": f"hermes exited with code {result.returncode}: {result.stderr[:500]}"}

    stdout = result.stdout.strip()

    # Try to parse JSON from the output
    try:
        # Look for JSON block in output
        json_match = re.search(r'\{[^{}]*"url"[^{}]*\}', stdout)
        if json_match:
            data = json.loads(json_match.group())
            return data

        # Try the whole output as JSON
        data = json.loads(stdout)
        return data
    except json.JSONDecodeError:
        pass

    # Fallback: look for URL patterns
    url_match = re.search(r'(https?://\S+\.(?:png|jpg|jpeg|webp))', stdout)
    if url_match:
        return {"url": url_match.group(1)}

    path_match = re.search(r'(/[\w/.-]+\.(?:png|jpg|jpeg|webp))', stdout)
    if path_match:
        return {"path": path_match.group(1)}

    return {"error": "Could not parse image URL from hermes output", "raw_output": stdout[:1000]}


def main():
    parser = argparse.ArgumentParser(description="Generate image via Hermes CLI")
    parser.add_argument("prompt", help="Image generation prompt")
    parser.add_argument("--aspect", default="portrait", choices=["landscape", "portrait", "square"])
    args = parser.parse_args()

    result = generate_image(args.prompt, args.aspect)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
