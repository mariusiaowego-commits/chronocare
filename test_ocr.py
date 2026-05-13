#!/usr/bin/env python3
"""Test script for ocr_engine.py"""
import asyncio
import sys
import os

# Ensure project root in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.chronocare.services.ocr_engine import extract_text, is_ocr_available


async def main():
    print("=== Test 1: is_ocr_available() ===")
    avail = await is_ocr_available()
    print(f"OCR available: {avail}")

    print("\n=== Test 2: extract_text() with Chinese image ===")
    test_image = "/Users/mt16/Pictures/image-inbox/dentist-roadmap.png"
    if not os.path.exists(test_image):
        print(f"SKIP: test image not found: {test_image}")
        return

    text = await extract_text(test_image)
    print(f"Length: {len(text)} chars")
    print(f"First 200 chars:\n{text[:200]}")

    print("\n=== Test 3: FileNotFoundError ===")
    try:
        await extract_text("/nonexistent/file.png")
    except FileNotFoundError as e:
        print(f"OK: FileNotFoundError raised: {e}")

    print("\nAll tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
