---
title: "Review Calendar"
type: "meta"
tags: ["pahibalo"]
date: "2026-11-23"
last_updated: "2026-11-23"
---

# Review Calendar

Back to [[Home]]

Pages sorted by `last_updated`, oldest first. Review ages: forms and policies 6 months, stable guides 12 months, commute fares 6 months.

```base
filters:
  and:
    - last_updated != ""
    - type != "meta"
    - type != "hub"
    - type != "template"
views:
  - type: table
    name: Due
    order: [file.name, type, status, last_updated]
    sort:
      - property: last_updated
        direction: ASC
```

Maintenance: [[How to Maintain PAHIBALO]]
