---
title: "Dorm"
type: "hub"
tags: ["pahibalo"]
summary: "Everything for dormers."
date: "2026-11-23"
last_updated: "2026-11-23"
---

# Dorm

Back to [[Home]]

> [!summary] In short
> Everything for dormers.

```base
filters:
  and:
    - type == "dorm"
views:
  - type: table
    name: List
    order: [file.name, summary]
```

## Also for dormers
```base
filters:
  and:
    - tags.contains("dormer")
    - type != "dorm"
views:
  - type: table
    name: Also for dormers
```

## Places nearby
```base
filters:
  and:
    - type == "place"
views:
  - type: table
    name: Places nearby
```
