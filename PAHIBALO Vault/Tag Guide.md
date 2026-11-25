---
title: "Tag Guide"
type: "meta"
tags: ["pahibalo"]
date: "2026-11-23"
last_updated: "2026-11-23"
---

# Tag Guide

Back to [[Home]]

## Properties (each fact stored once, D31)
- `type`: form, org, office, competition, guide, kit, dorm, commute, place, event, tool, story, hub, meta, template, src. (Kept as a property, not a tag, so it isn't stored twice.)
- `grade`: g7, g8, g9, g10, g11, g12
- `area`: research, academics, discipline, dorm, health, finance, clearance, competition, clubs, publications, student-government
- `status`: verified, needs-check, unknown
- `owner_office`: the office note's file name
- `icon`: the page's own icon (each form and office has one, from `Site\templates\_icons.svg`)
- `photos`: pictures on the page, one per line as `file|alt|caption` (optional `|area` at the end for the border colour)
- `header_photo`: a sharp photo for the page header
- `parent`: `"[[Note name]]"` puts a page under another page of its area; the hub leaves it out and its back link goes to the parent (see [[Site Areas]])
- `logo`: an org's logo file
- `template_status`: have, drive-private, waiting-upload, missing

## Tags
- audience: new (new scholars), dormer, officer, participant, applicant
- grade groups (from `grade`, see [[Site Areas]]): Freshies g7 to g8, Juniors g9 to g10, Seniors g11 to g12
- office and org tags: add when needed

## Rule
Every page has `type`, `area`, and `grade` or an audience tag when relevant.

Maintenance: [[How to Maintain PAHIBALO]]
