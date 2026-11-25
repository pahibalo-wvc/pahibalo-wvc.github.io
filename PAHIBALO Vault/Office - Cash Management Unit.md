---
title: "Cash Management Unit"
type: "office"
icon: "cash"
tags: []
grade: []
area: ["finance"]
summary: "The cashier, where you pay school fees like the ID replacement fee. It also releases allowances, which you need to claim before your year-end clearance."
location: "Administration Building"
last_updated: "2026-11-24"
source: "PSHS-WVC Student Handbook 2018 ([[Src - WVC Student Handbook 2018]])"
status: "needs-check"
aliases: ["Cashier"]
owner_office: "Office - Cash Management Unit"
date: "2026-11-23"
---

# Cash Management Unit

Back to [[Home]]

> [!summary] In short
> The cashier, where you pay school fees like the ID replacement fee. It also releases allowances, which you need to claim before your year-end clearance.

## What it handles
Payments (for example the ID replacement fee) and allowances. Clearance needs all allowances claimed and proof of travel or waiver for transport reimbursement (2018).

## Where it is
The Administration Building.

## Forms it owns
```base
filters:
  and:
    - type == "form"
    - owner_office == "Office - Cash Management Unit"
views:
  - type: table
    name: Forms
    order: [file.name, summary, template_status]
```

## Related
[[Hub - Offices]] · [[Kit - Who to Ask]]

---
Last updated: 2026-11-23. Details can change, so confirm with the office if unsure. Report an error: (form link unknown).
