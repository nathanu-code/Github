# Third-Party Licenses

This repository vendors a curated subset of agent skills, agents, and rules from
[affaan-m/ECC](https://github.com/affaan-m/ECC), pinned at upstream commit
`c9de8f5b2b3a225bca9befa2b7700aa5e3a4d1b8`.

Vendored files live under `.claude/skills/`, `.claude/agents/`, and
`.claude/rules/`. Original YAML frontmatter — including `license`, `author`,
and `metadata.origin` fields — was preserved unmodified in every file.

See [`docs/ECC-EVALUATION.md`](docs/ECC-EVALUATION.md) for what was selected and
why.

---

## 1. ECC — MIT License

Applies to all vendored material except the seven skills listed in section 2.

> MIT License
>
> Copyright (c) 2026 Affaan Mustafa
>
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.

### Covered files

**Skills** (`.claude/skills/`): `brand-voice`, `coding-standards`,
`competitive-platform-analysis`, `context-budget`, `customer-billing-ops`,
`deep-research`, `documentation-lookup`, `git-workflow`, `github-ops`,
`lead-intelligence`, `market-research`, `marketing-campaign`, `research-ops`,
`security-review`, `seo`, `skill-scout`, `skill-stocktake`,
`token-budget-advisor`, `verification-loop`

**Agents** (`.claude/agents/`): `chief-of-staff`, `code-reviewer`,
`docs-lookup`, `marketing-agent`, `planner`, `security-reviewer`,
`seo-specialist`

**Rules** (`.claude/rules/common/`): `coding-style.md`, `security.md`

---

## 2. Operations skills — Apache License 2.0

Seven vendored skills carry `license: Apache-2.0` in their own frontmatter and
are attributed upstream to `author: evos`. They are redistributed here under the
Apache License, Version 2.0.

### Covered files

| Skill | Path |
| --- | --- |
| `carrier-relationship-management` | `.claude/skills/carrier-relationship-management/` |
| `customs-trade-compliance` | `.claude/skills/customs-trade-compliance/` |
| `inventory-demand-planning` | `.claude/skills/inventory-demand-planning/` |
| `logistics-exception-management` | `.claude/skills/logistics-exception-management/` |
| `production-scheduling` | `.claude/skills/production-scheduling/` |
| `quality-nonconformance` | `.claude/skills/quality-nonconformance/` |
| `returns-reverse-logistics` | `.claude/skills/returns-reverse-logistics/` |

### Notice

```
Copyright (c) ECC contributors (attributed upstream to "evos")

Licensed under the Apache License, Version 2.0 (the "License");
you may not use these files except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

The full license text is available at
<https://www.apache.org/licenses/LICENSE-2.0>.

Apache-2.0 requires that modifications to these files carry prominent change
notices. As of this commit they are unmodified copies. If you edit one, add a
note to that effect at the top of the file and record it in the table below.

### Modification log

| Date | Skill | Change |
| --- | --- | --- |
| — | — | No modifications to date |

---

## Disclaimer on domain content

The trade, logistics, quality, and manufacturing skills encode professional
practice, including references to specific regulations (19 CFR, 19 USC, FDA,
IATF 16949, AS9100, Incoterms 2020). They are decision-support material, not
legal or regulatory advice, and they are not maintained by the agencies whose
rules they describe. Verify against current primary sources before relying on
them for filings, claims, or compliance decisions.
