---
title: "Forms"
type: "hub"
tags: ["pahibalo"]
summary: "Every form and document, in one Documents Library."
date: "2026-11-23"
last_updated: "2026-11-23"
---

# Forms

Back to [[Home]]

> [!summary] In short
> Every form and document, in one Documents Library.

```base
filters:
  and:
    - type == "form"
views:
  - type: table
    name: List
    order: [file.name, summary, owner_office, template_status, last_updated]
```

%% Cards live once; other pages list them by property (D34). Missing templates show `template_status: missing`. %%

Start from a task instead: [[I Need To]]. Lost something: [[Guide - SA Locate]]. School records like Form 137 are requested at the [[Office - Registrar Unit]].
