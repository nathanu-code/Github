#!/usr/bin/env python3
"""
Quick test — generate a single ultra-realistic young woman model image.
Run: python quickstart.py
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

import httpx
import json


HIGGSFIELD_KEY    = os.environ["HIGGSFIELD_API_KEY"]
HIGGSFIELD_SECRET = os.environ["HIGGSFIELD_API_SECRET"]
BASE_URL          = "https://platform.higgsfield.ai"

PROMPT = (
    "Ultra-photorealistic portrait of a stunning 23-year-old woman, "
    "flawless smooth skin with natural pores and subtle freckles, "
    "long dark wavy hair catching golden light, deep hazel eyes with natural catchlights, "
    "wearing an oversized cream linen shirt, sitting by a sun-drenched window, "
    "golden hour backlight, 85mm f/1.4 portrait lens, shallow depth of field, "
    "warm film grain, Kodak Portra 400 color grade, "
    "hyperrealistic skin texture, 8K resolution, indistinguishable from a photograph"
)


async def generate():
    headers = {
        "hf-api-key":  HIGGSFIELD_KEY,
        "hf-secret":   HIGGSFIELD_SECRET,
        "Content-Type": "application/json",
        "Accept":       "application/json",
    }

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=60) as client:

        # 1. Submit generation job
        print("Submitting Soul 2.0 generation...")
        r = await client.post("/v1/text2image/soul", json={
            "params": {
                "prompt":          PROMPT,
                "width_and_height": "PORTRAIT_1072x1920",
                "quality":         "1080p",
                "batch_size":      "SINGLE",
                "enhance_prompt":  True,
            }
        })
        r.raise_for_status()
        data = r.json()
        print(f"Response: {json.dumps(data, indent=2)}")

        job_id = data.get("job_set_id") or data.get("id") or data.get("job_id")
        if not job_id:
            print("ERROR: No job ID in response")
            return

        print(f"\nJob ID: {job_id}")
        print("Polling for result", end="", flush=True)

        # 2. Poll until done
        for _ in range(120):  # up to 10 min
            await asyncio.sleep(5)
            print(".", end="", flush=True)

            poll = await client.get(f"/v1/job-sets/{job_id}")
            poll.raise_for_status()
            status_data = poll.json()
            status = status_data.get("status", "")

            if status in ("completed", "succeeded", "done"):
                print(" Done!\n")
                # Extract image URL
                jobs = status_data.get("jobs") or status_data.get("results") or []
                url = None
                for j in jobs:
                    url = j.get("url") or j.get("output_url") or j.get("media_url")
                    if url:
                        break
                if not url:
                    url = status_data.get("url") or status_data.get("output_url")

                print(f"Image URL: {url}")

                # 3. Download
                if url:
                    out = Path("output/models")
                    out.mkdir(parents=True, exist_ok=True)
                    dest = out / f"{job_id}.png"
                    async with httpx.AsyncClient() as dl:
                        img = await dl.get(url)
                        dest.write_bytes(img.content)
                    print(f"\nSaved to: {dest.resolve()}")
                return

            elif status in ("failed", "error", "nsfw", "cancelled"):
                print(f"\nJob failed: {status_data}")
                return

        print("\nTimed out")


if __name__ == "__main__":
    asyncio.run(generate())
