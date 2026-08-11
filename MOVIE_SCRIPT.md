# Advance Party — Movie Hero Script & Timing

## Current Implementation

### Architecture
- 3 scenes in a fixed full-screen hero (`div.movie-stage`)
- Scene transitions: horizontal slide (0.7s, power3.inOut)
- Auto-cycle timer: 12s per scene
- Navigation dots at bottom of screen
- Background: dark red/black gradient with floating particle canvas
- Scroll indicator appears on last scene

### Scene 1 — "Tilley + ADVANCE" (12s hold)

| Time | Element | Animation | Notes |
|------|---------|-----------|-------|
| 0.0s | Edward Tilley image (right, 55% width) | Slide in from right + fade | `x: 200 → 0, opacity: 0→1, 1.2s` |
| 0.2s | "ADVANCE" brand text (left side) | Drop down | `y: -60→0, opacity: 0→1, 0.8s` |
| 0.5s | Quote: "Canadians should be richest... collapsing instead" | Fade up | `y: 40→0, opacity: 0→1, 0.8s` |
| 0.8s | CTA buttons (Our Plan, Join Us) | Fade up | `y: 40→0, opacity: 0→1, 0.6s` |
| 12s | → Auto-transition to Scene 2 | Slide left (0.7s) | |

### Scene 2 — "Problems + ACT OF WAR" (12s hold)

| Time | Element | Animation | Notes |
|------|---------|-----------|-------|
| 0.2s | 6 bullet items (appear together, not staggered) | Fade in | `opacity: 0→1, x: -30→0, 0.5s` |
| 0.3s | "ACT OF WAR" (large yellow text, right side) | Scale burst | `scale: 0.5→1, opacity: 0→1, 0.7s, back.out` |
| 0.6s | "ETHNIC CLEANSING" (large red text) | Scale burst | `scale: 0.5→1, opacity: 0→1, 0.7s, back.out` |
| 0.9s | "Against the Canadian People" subtitle | Fade up | `y: 30→0, opacity: 0→1, 0.5s` |
| 1.1s | Stats line (138th suicide, 1930s productivity) | Fade up | `y: 20→0, opacity: 0→1, 0.5s` |
| 12s | → Auto-transition to Scene 3 | Slide left (0.7s) | |

Bullet items in Scene 2:
1. 6.6 Million election fraud immigrants brought in to swing ridings
2. Wars are measured by depopulation, workplace equality laws guarantee depopulation, an Act of War - against the Canadian people
3. Gender Theory, Economic Treason — lowest GDP growth since the 1930s, lowest GDP per Capita in the G20
4. 980,000 children lost per year to fertility collapse, 300 abortions daily
5. Criminal legislatures — High Treason under Canada's Criminal Code 46(1)
6. Hate and Survillance laws used to silence opposition to election fraud

### Scene 3 — "Stats Evidence" (12s hold)

| Time | Element | Animation | Notes |
|------|---------|-----------|-------|
| 0.0s | 4 stat blocks | Fade up together | `opacity: 0→1, y: 40→0, 0.6s` |
| 0.4s | Counters animate | Count up 0→target over 2.5s | `power2.out` |
| 12s | → Loops back to Scene 1 | Slide right (0.7s) | |

Stat blocks:
1. $4,000,000,000/day — Lost Daily — Canada's GDP growth is lowest in G20
2. 860,000/yr — Children Lost — To abortion & fertility collapse every year
3. 138th — World Suicide Rank — Canada has the 138th highest suicide rate globally
4. 1930s — Productivity Level — Canadian productivity has fallen to 1930s levels

---

## Proposed Revised Script (6 Scenes)

A single continuous narrative video that walks through the serious problems facing Canada today. The ADVANCE brand stays fixed on screen throughout. Each scene's bullet points appear together, hold, then fade out as the next scene fades in.

### Scene 1 — "The Vision" (8s)

**Layout:** Left text, right Tilley image
- "ADVANCE" title (persistent, stays at top)
- Tagline: "The Advance Party of Canada"
- Photo: Edward Tilley, right-aligned, looking left
- Quote: "Canadians should be the richest citizens in the world!"
  — Edward Tilley, President, Advance Canada

**Timing:**
| Time | Action |
|------|--------|
| 0.0s | Tilley image slides in from right |
| 0.0s | "ADVANCE" title drops in (stays fixed) |
| 0.3s | Tagline fades in |
| 0.6s | Quote + attribution fade in |
| 8s | → Fade to Scene 2 |

### Scene 2 — "Sovereignty Stolen" (12s)

**Layout:** Bullet list left, nothing right
- "Canada's sovereignty is the second largest resource in the world, and now IT HAS BEEN TAKEN FROM CANADIANS"
- Bullet group (appear together):
  - An army of millions of low-compatibility migrants herded into swing ridings
  - 22,000 immigration consultancies paid by federal debt
  - OUR CURRENT CRIMINAL LEGISLATURES CAN NEVER LOSE AN ELECTION
  - This Election Fraud is protected by new Hate Laws too
- Subtitle: "The Most Important Political Party You NEVER Heard Of"

**Timing:**
| Time | Action |
|------|--------|
| 0.0s | Header statement fades in |
| 0.8s | All 4 bullets appear together |
| 2.5s | Subtitle fades in |
| 12s | → Fade to Scene 3 |

### Scene 3 — "The Economic Collapse" (12s)

**Layout:** Stat blocks grid, 2x2
- "Our lowest GDP Growth in the G20 has us collapsing"
- WITH ZERO CENTRAL PLANNING
- Stat grid:
  - $4 BILLION lost daily — Lowest GDP Growth in G20
  - 860,000 Canadians lost annually — Depopulation at double WWII rates
  - 1930s PRODUCTION GROWTH LEVELS — Productivity collapsed
  - 1990s SALARIES — Wages stagnant for 30+ years
- "Canadians are not waking up to the security threat quickly enough"

**Timing:**
| Time | Action |
|------|--------|
| 0.0s | Header fades in |
| 0.5s | "WITH ZERO CENTRAL PLANNING" appears (red highlight) |
| 1.0s | 4 stat blocks appear together |
| 2.0s | Counters animate |
| 4.0s | Warning subtitle fades in |
| 12s | → Fade to Scene 4 |

### Scene 4 — "Human Rights Crisis" (10s)

**Layout:** Left: NO list, Right: statistics
- "NO HUMAN RIGHTS — Our kids have no security and NO LAW or GOOD VALUES"
- Left column: NO list (appear together)
  - NO Homes
  - NO Children
  - NO Families
  - NO Old Age Security
  - NO Education
- Right column: "Mental Illness is exploding" + 138th in suicide worldwide
- "Corrupt Politicians can lie, teach our children poor values, and collapse the country while appearing very affable and eloquent"

**Timing:**
| Time | Action |
|------|--------|
| 0.0s | Header statement fades in |
| 0.5s | NO list appears on left (all together) |
| 0.5s | Stats appear on right (all together) |
| 2.0s | Corruption quote fades in at bottom |
| 10s | → Fade to Scene 5 |

### Scene 5 — "ACT OF WAR" (10s)

**Layout:** Left: bullet list, Right: large WAR headlines
- Left bullets (appear together):
  - Criminal Globalist Legislatures bring an Ideology War and an Army to Canada
  - That is the very definition of High Treason in Canada's Criminal Code 46(1)
  - Wars are measured by depopulation — we are losing almost an entire generation of Canadians
  - Europe is rioting, burning down migrant hotels, shooting border crossers — CBC reports nothing
- Right side (large text):
  - ACT OF WAR (yellow, #FFD700)
  - ETHNIC CLEANSING (red, #CC0000)
  - Against the Canadian People
- "Where are our Dark Factories and Self-Sufficiency?"

**Timing:**
| Time | Action |
|------|--------|
| 0.0s | Left bullets appear together |
| 0.3s | "ACT OF WAR" scales in (yellow) |
| 0.6s | "ETHNIC CLEANSING" scales in (red) |
| 1.0s | "Against the Canadian People" fades in |
| 2.0s | "Where are our Dark Factories?" fades in |
| 10s | → Fade to Scene 6 |

### Scene 6 — "The Solution / Call to Action" (12s)

**Layout:** Full screen, centered
- "ADVANCE says — This Collapse Stops NOW" (large, bold, centered)
- Civic Science ACT Parties — Certified Professional Civic Scientists who can lose their license
- "The Most Important Political Party You NEVER Heard Of"
- Tens of millions of dollars annually give political groups a voice — headline parties are NOT WORKING FOR US
- Advance accepts NO Corporate SuperPAC Contributions
- Donate buttons: $5 or $10 per month — Your Donation 100% makes Advance possible
- "Take back your country — INVEST in Advance"

**Timing:**
| Time | Action |
|------|--------|
| 0.0s | "ADVANCE says — This Collapse Stops NOW" fades in |
| 0.8s | Civic Science description fades in |
| 1.5s | "Most Important Party" line fades in |
| 2.5s | Corporate money fact fades in |
| 3.5s | "NO Corporate SuperPAC" highlight fades in |
| 5.0s | CTA buttons + donate line fades in |
| 12s | → Loops back to Scene 1 |

---

## Configuration Variables (for pacing adjustments)

```
sceneDurations = [8, 12, 12, 10, 10, 12]  // seconds per scene
transitionSpeed = 0.7                        // seconds for slide transition
bulletFadeDuration = 0.5                     // seconds for bullet/text fades
counterDuration = 2.5                        // seconds for stat counter animation
```

All timings use `ease: 'power3.out'` for smooth natural motion. Headline bursts use `ease: 'back.out(2)'` for dramatic pop-in.
