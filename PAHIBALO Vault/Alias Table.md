---
title: "Alias Table"
type: "meta"
tags: ["pahibalo"]
date: "2026-11-23"
last_updated: "2026-11-23"
---

# Alias Table

Back to [[Home]]

Generated view (D32). Aliases live in each note's `aliases` property; edit them there.

```base
filters:
  and:
    - aliases.length > 0
views:
  - type: table
    name: Aliases
    order: [file.name, type, aliases]
```

Rule: every acronym (APF, FAD, SRF, AR, SSD, CID, SAU, ALA, SCALE, LEAP, SIP, GWA, PMO, PBO, DSPC, RSPC, MUN, SA, SDC) must appear in some note's aliases.

Maintenance: [[How to Maintain PAHIBALO]]
