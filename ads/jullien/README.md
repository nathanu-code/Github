# Jullien Stellar — Meta ad set

Five 1080×1350 Meta/Instagram feed ads for **Jullien Stellar Beauty**, adapting the
structure of five ad concepts from a reference reel to Jullien's own catalogue,
claims and voice.

**Live canvas:** https://claude.ai/code/artifact/5ac2e778-9ec2-448c-9bb2-5dfd1be48d13
**Production sheet:** [`jullien_ad_production_sheet.md`](./jullien_ad_production_sheet.md) — copy decks, asset list, claim substantiation, Meta policy notes, A/B plan.

## What's here

| File | |
| :-- | :-- |
| `Main.dc.html` | Board 01 — System / Hook |
| `Solutions.dc.html` | Board 02 — Our Solutions |
| `Transformation.dc.html` | Board 03 — Testimonial + Proof |
| `Guarantee.dc.html` | Board 04 — Return Policy |
| `SocialProof.dc.html` | Board 05 — Women Over 40 |
| `canvas.json` | Artboard layout and production notes on the canvas |
| `previews/` | Reference renders (see caveat below) |

## Two things to know before these run

1. **Board 03 ships with empty before/after frames.** They need real, consented
   customer photos. Details in §5 and §7 of the production sheet.
2. **Board 04 does not promise a money-back guarantee**, because Jullien doesn't
   offer one. It states the real policy. Alternative copy, for if you institute
   a guarantee, is in §4 of the production sheet.

## Previews

`previews/*.png` are reference renders only. They use the **fallback** faces
(Georgia / Helvetica), not Marcellus and Jost, and are scaled slightly by the
capture tool. For production files, open the canvas and use Export.

## Editing

Edit the `.dc.html` files, then re-seed and republish to the same URL. The
artboards are plain HTML with inline styles — the product artwork is inline SVG,
so it rescales for any placement without new assets.
