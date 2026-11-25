---
title: "Health Services Unit"
type: "office"
icon: "health"
tags: []
grade: []
area: ["health"]
summary: "The school clinic, with a physician and a nurse. Go here when you feel sick, for your yearly check-up, or to get your admission slip certified after an absence."
last_updated: "2026-11-24"
source: "PSHS-WVC Student Handbook 2018 ([[Src - WVC Student Handbook 2018]]); Info systems portal ([[Src - Info Systems Portal]]); PSHS-WVC Virtual Campus Tour video (PISAY-WVC TV on YouTube, December 2021)"
status: "needs-check"
aliases: ["Clinic", "HSU", "nurse", "doctor"]
owner_office: "Office - Health Services Unit"
date: "2026-11-23"
location: "First floor of the new academic building"
header_photo: "clinic-door"
photos:
  - "clinic-door|The clinic door marked CLINIC AB2 102, along a covered walkway|The clinic door"
  - "tour-clinic-beds|Two hospital beds with green curtains in the school clinic|Beds in the clinic (2021 virtual campus tour)"
  - "tour-clinic-dental|A dental chair with its lamp and tray in the clinic|The clinic also has a dental chair (2021 virtual campus tour)"
---

# Health Services Unit

Back to [[Home]]

> [!summary] In short
> The school clinic, with a physician and a nurse. Go here when you feel sick, for your yearly check-up, or to get your admission slip certified after an absence.

## What it handles
- A physician and a nurse.
- Physical exam for new students at the start of the year; annual check-up for upper levels.
- Some medicines: first dose free.
- Reservations go through the Medifast system ([[Kit - School Online Systems]]).

## Where it is
The first floor of the new academic building. The door sign says CLINIC.

The 2021 virtual campus tour says the clinic is in the new academic building. It shows beds for students who need to lie down and a dental chair.

## When to go
7:30 AM to 4:30 PM, Monday to Friday (2018).

## Forms it owns
```base
filters:
  and:
    - type == "form"
    - owner_office == "Office - Health Services Unit"
views:
  - type: table
    name: Forms
    order: [file.name, summary, template_status]
```

## Related
[[Hub - Offices]] · [[Kit - Who to Ask]]

---
Last updated: 2026-11-24. Details can change, so confirm with the office if unsure. Report an error: (form link unknown).
