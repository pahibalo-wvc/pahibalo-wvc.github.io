---
title: "Site Areas"
type: "meta"
tags: ["pahibalo"]
date: "2026-11-23"
last_updated: "2026-11-25"
---

# Site Areas

Back to [[Home]]

Every area of the website comes from one row of this table. A note shows up on the site when its `type` property matches a row. Rows are listed in menu order.

| Type | Name | Folder | Hub note | Tag | Icon | Colour | Border | Photo | Menu | Count word | Card facts |
|---|---|---|---|---|---|---|---|---|---|---|---|
| kit | Starter Kit | starter-kit | [[Hub - Starter Kit]] | starter | kit | #F8C9BC | #D9503A | quad-wide | 10 | guides | |
| office | Offices | offices | [[Hub - Offices]] | office | office | #C9D8F2 | #3F78D1 | building | 2 | offices | Where = location; Open = hours; Contact = contact |
| form | Forms | forms | [[Hub - Forms]] | form | form | #F7D774 | #D9A400 | walkway | 3 | forms | Form code = form_code; Who signs = needs_signature_from; Submit to = submit_to |
| org | Orgs | orgs | [[Hub - Orgs]] | org | org | #BFE3C9 | #4EAA6A | garden | 4 | orgs | Find them = contact_link; How to join = join_info |
| event | Events | events | [[Hub - Events]] | event | pin | #F9D2B4 | #E57A2E | grounds | 5 | events | When = when; Who = who; Run by = run_by |
| competition | Competitions | competitions | [[Hub - Competitions]] | comp | competition | #F5C6D6 | #D2557F | quad-tower | 7 | competitions | Level = level; Find it = contact_link |
| dorm | Dorm | dorm | [[Hub - Dorm]] | dorm | dorm | #BEE6E1 | #2F9C8F | garden | 9 | pages | |
| commute | Dorm | dorm | [[Hub - Dorm]] | commute | commute | #BEE6E1 | #2F9C8F | garden | no | pages | |
| place | Places nearby | places | [[Hub - Places Nearby]] | place | map | #EAD7C2 | #A06A3E | grounds | no | places | Address = address; Open = hours; Try = bestsellers |
| guide | Guides | guides | [[Hub - Guides]] | guide | guide | #E1D7F5 | #8460C9 | building | 6 | guides | |
| tool | Tools | tools | - | tool | tool | #DDE1E7 | #5E6B7D | building | no | tools | |

Journeymap is a single page, not an area. It sits 8th in the menu through `menu_order: 8` in [[Journeymap]]. The top menu shows only the first `menu_top_count` tabs (6, set in [[Site Settings]]); a More tab opens every section.

## Picture borders
Every picture on the site gets a coloured border that says what the picture is about. The colour is the Border column above.
- Forms: yellow
- Offices: blue
- Orgs: pastel green
- Events: orange
- Competitions: pink
- Starter Kit: coral red
- Dorm and commute: teal
- Places nearby: kraft brown
- Guides: violet
- Tools: graphite grey

A picture takes the colour of its own page unless its `photos` line names another area at the end, like `registrar-counter|alt|caption|office` on a form page.

## Grade groups
Pages carry a `grade` property (g7 to g12). The site turns it into one or more of these three tags, shown on cards, page headers, hub filters, search and the [[Journeymap]]. A page with no grade is for every year.

| Group | Grades | Also called | Colour |
|---|---|---|---|
| Freshies | g7, g8 | | #FFE08A |
| Juniors | g9, g10 | | #A8E6CF |
| Seniors | g11, g12 | SYP (Specialization Years Program) | #C3B5FF |

## How to add a new area
1. Add a row. **Type** is the value you put in each note's `type` property.
2. **Hub note**: a link to a hub note, `auto` to make a plain list page without a note, or `-` for no list page.
3. **Folder** is the web address part, like `events` for `/events/`.
4. **Icon**: a symbol name from `Site\templates\_icons.svg`. A note can also set its own `icon` property, so every form and office has its own.
5. **Colour** is the light fill for cards. Card text on it is dark navy, so keep it light. **Border** is the darker frame colour for pictures and card edges.
6. **Photo**: a name from `Site\tools\prep_photos.py`. It is used blurred behind the page header. A note can set `header_photo` for its own sharp header picture.
7. **Menu**: a number puts the hub in the top menu in that order; `no` leaves it out.
8. **Card facts**: properties shown in the summary card at the top of each page, as `Label = property`, separated by `;`. Empty or missing ones are skipped.

## Pages under another page
A note can sit under another note of its area with `parent: "[[Note name]]"`. The hub then leaves it off its list, and the page's back link goes to the parent instead of the hub. The competitions area uses this: the hub shows the five subject pages ([[Comp - Biology]], [[Comp - Chemistry]], [[Comp - Mathematics]], [[Comp - Physics]], [[Comp - Humanities]]), and each contest page names its subject as its parent. Link each child from its parent's text so readers can reach it.

## How to add a single page
Make a note and give it a `publish` property with its web address, like `publish: "exam-week.html"`. Optional: `layout` (page, tasks, about, gwa or journey), `footer: yes` to link it in the footer, and `menu_order` to put it in the top menu.

Rows with the same hub note share one list page (Dorm lists both dorm and commute notes).
