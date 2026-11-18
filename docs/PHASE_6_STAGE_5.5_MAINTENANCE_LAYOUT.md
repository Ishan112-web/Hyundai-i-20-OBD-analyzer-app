# Maintenance Page Redesign - Stage 5.5 ASCII Layout

**Date:** 2026-11-17  
**Phase:** 6 Stage 5.5  
**Status:** Layout Defined - Ready for Implementation

---

## Design System Component Mapping

| UI Element | Design System Component | Token Usage |
|------------|------------------------|-------------|
| Page Header | `page_header()` from layout.py | FONT_SIZE_H1, FONT_SIZE_BODY, ACCENT_PRIMARY, GAP_SECTION |
| Current Mileage Display | `card_simple()` + tokens | FONT_SIZE_H2, FONT_WEIGHT_NUMERIC, ACCENT_PRIMARY, STATUS_INFO |
| Quick-Add Buttons | `button_ghost()` in button group | BUTTON_SIZE_SM, GAP_INLINE, SURFACE_INTERACTIVE |
| Tab Navigation | Streamlit native tabs (styled via shell) | — |
| Filter/Sort Controls | `selectbox()`, `text_input()` | FORM_FIELD_PROPS, INPUT_HEIGHT, BORDER_DEFAULT |
| Record Cards | `card()` with CardProps | CARD_RADIUS, CARD_PADDING, SHADOW_SM, BORDER_DEFAULT |
| Status Badges | `badge()` with BadgeVariant | STATUS_CRITICAL (overdue), STATUS_WARNING (due_soon), STATUS_SUCCESS (up_to_date), STATUS_NEUTRAL (completed) |
| Record Actions | `button_ghost()` (edit), `button_danger()` (delete) | BUTTON_SIZE_SM, BUTTON_ICON_GAP |
| Add/Edit Form | `text_input()`, `selectbox()` | INPUT_RADIUS, INPUT_HEIGHT, FONT_SIZE_LABEL, TEXT_SECONDARY |
| Form Actions | `button_primary()` (save), `button_secondary()` (cancel) | BUTTON_MIN_HEIGHT, BUTTON_PADDING_HORIZONTAL |
| Upcoming Cards | `card()` with CardProps | CARD_RADIUS, CARD_PADDING, SHADOW_SM, GAP_FIELD |
| Upcoming Action | `button_primary()` (Record Service) | Full width variant |
| Empty States | `empty_state()` | EMPTY_STATE_PADDING, EMPTY_STATE_ICON_SIZE, TEXT_SECONDARY |
| Success/Error Alerts | `alert()` | ALERT_VARIANT.SUCCESS/WARNING/CRITICAL/INFO |
| Loading States | `skeleton_card()`, `spinner()` | SKELETON_PULSE_DURATION, SPINNER_SIZE_MD |

---

## Full Page Layout (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ GLOBAL SHELL (components/shell.py)                                                          │
│ ┌──────────────────┐ ┌──────────────────────────────────────────────────────────────────┐  │
│ │ SIDEBAR          │ │ TOP BAR                                                            │  │
│ │ (Navigation,     │ │ [Breadcrumb: Home / Maintenance]    [Status: OBD● AI● Sim○]      │  │
│ │  Vehicle Info,   │ │                                                                   │  │
│ │  Status)         │ │                                                                   │  │
│ └──────────────────┘ └──────────────────────────────────────────────────────────────────┘  │
│ ┌──────────────────────────────────────────────────────────────────────────────────────┐  │
│ │ MAIN CONTENT AREA (responsive_container)                                               │  │
│ │                                                                                       │  │
│ │ ┌────────────────────────────────────────────────────────────────────────────────┐   │  │
│ │ │ PAGE HEADER (page_header)                                                     │   │  │
│ │ │ ┌──────────────────────────────────────────┐  ┌────────────────────────────┐  │   │  │
│ │ │ │ Maintenance Tracker                      │  │ Current Mileage: 45,230 km │  │   │  │
│ │ │ │ Track service intervals, record history, │  │ ┌──────────────────────┐  │  │   │  │
│ │ │ │ and plan upcoming maintenance           │  │ │ ▼ 45,230 km (OBD)    │  │  │   │  │
│ │ │ └──────────────────────────────────────────┘  └────────────────────────────┘  │   │  │
│ │ └────────────────────────────────────────────────────────────────────────────────┘   │  │
│ │                                                                                       │  │
│ │ ┌────────────────────────────────────────────────────────────────────────────────┐   │  │
│ │ │ QUICK-ADD BAR (button group - responsive, wraps on mobile)                    │   │  │
│ │ │ [+ Oil Change] [+ Oil Filter] [+ Air Filter] [+ Cabin Filter] [+ Brake Fluid] │   │  │
│ │ │ [+ Coolant Flush]                                                              │   │  │
│ │ └────────────────────────────────────────────────────────────────────────────────┘   │  │
│ │                                                                                       │  │
│ │ ┌────────────────────────────────────────────────────────────────────────────────┐   │  │
│ │ │ TABS (Streamlit native - styled via global shell)                              │   │  │
│ │ │ ┌───────────┐ ┌────────────┐ ┌────────────┐                                    │   │  │
│ │ │ │ Records   │ │ Add / Edit │ │ Upcoming   │                                    │   │  │
│ │ │ └───────────┘ └────────────┘ └────────────┘                                    │   │  │
│ │ └────────────────────────────────────────────────────────────────────────────────┘   │  │
│ │                                                                                       │  │
│ │ ┌────────────────────────────────────────────────────────────────────────────────┐   │  │
│ │ │ TAB 1: RECORDS                                                                │   │  │
│ │ │ ┌──────────────────────────────────────────────────────────────────────────┐  │   │  │
│ │ │ │ FILTER & SORT BAR (flex, gap=GAP_FIELD, wraps)                          │  │   │  │
│ │ │ │ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐             │  │   │  │
│ │ │ │ │ Filter: ▼ All   │ │ Sort By: ▼ Due  │ │ Order: ▼ Asc    │             │  │   │  │
│ │ │ │ │   ▼ Upcoming    │ │   Date          │ │   ▼ Desc        │             │  │   │  │
│ │ │ │ │   ▼ Overdue     │ │   Service Type  │ │                 │             │  │   │  │
│ │ │ │ │   ▼ Due Soon    │ │   Date Done     │ │ [12 records]    │             │  │   │  │
│ │ │ │ │                 │ │   Mileage       │ │                 │             │  │   │  │
│ │ │ │ │                 │ │   Cost          │ │                 │             │  │   │  │
│ │ │ │ └─────────────────┘ └─────────────────┘ └─────────────────┘             │  │   │  │
│ │ │ └──────────────────────────────────────────────────────────────────────────┘  │   │  │
│ │ │                                                                               │   │  │
│ │ │ ┌──────────────────────────────────────────────────────────────────────────┐  │   │  │
│ │ │ │ RECORDS LIST (responsive grid: 1 col mobile, 2 col tablet, 3 col desktop)│  │   │  │
│ │ │ │                                                                            │  │   │  │
│ │ │ │ ┌─ RECORD CARD (card) ────────────────────────────────────────────────┐  │  │   │  │
│ │ │ │ │ ┌────────────────────────────────────────────────────────────────┐  │  │  │   │  │
│ │ │ │ │ │ Oil Change                                    ● Overdue       │  │  │  │   │  │
│ │ │ │ │ │ 2025-01-15  •  42,000 km  •  $89.99                            │  │  │  │   │  │
│ │ │ │ │ └────────────────────────────────────────────────────────────────┘  │  │  │  │   │  │
│ │ │ │ │ ┌────────────────────────────────────────────────────────────────┐  │  │  │   │  │
│ │ │ │ │ │ Next Due: 52,000 km (2025-07-15)  •  Gap: 6,770 km / 4 mo    │  │  │  │   │  │
│ │ │ │ │ │ Provider: Hyundai Dealer  •  Notes: Synthetic 5W-30           │  │  │  │   │  │
│ │ │ │ │ └────────────────────────────────────────────────────────────────┘  │  │  │  │   │  │
│ │ │ │ │ ┌────────────────────────────────────────────────────────────────┐  │  │  │   │  │
│ │ │ │ │ │ [✏ Edit] [🗑 Delete]                                    [▼]    │  │  │  │   │  │
│ │ │ │ │ └────────────────────────────────────────────────────────────────┘  │  │  │  │   │  │
│ │ │ │ └────────────────────────────────────────────────────────────────────┘  │  │  │  │   │  │
│ │ │ │                                                                            │  │   │  │
│ │ │ │ ┌─ RECORD CARD ──────────────────────────────────────────────────────┐  │  │  │   │  │
│ │ │ │ │ Air Filter                                ● Due Soon              │  │  │  │   │  │
│ │ │ │ │ 2024-06-10  •  35,000 km  •  $45.00                               │  │  │  │   │  │
│ │ │ │ │ Next Due: 65,000 km (2026-06-10)  •  Gap: 19,770 km / 8 mo       │  │  │  │   │  │
│ │ │ │ │ [✏ Edit] [🗑 Delete]                                         [▼]    │  │  │  │   │  │
│ │ │ │ └────────────────────────────────────────────────────────────────────┘  │  │  │  │   │  │
│ │ │ │                                                                            │  │   │  │
│ │ │ │ ┌─ RECORD CARD ──────────────────────────────────────────────────────┐  │  │  │   │  │
│ │ │ │ │ Brake Fluid                               ✓ Up to Date            │  │  │  │   │  │
│ │ │ │ │ 2024-12-01  •  44,000 km  •  $120.00                              │  │  │  │   │  │
│ │ │ │ │ Next Due: 84,000 km (2026-12-01)  •  Gap: 38,770 km / 13 mo      │  │  │  │   │  │
│ │ │ │ │ [✏ Edit] [🗑 Delete]                                         [▼]    │  │  │  │   │  │
│ │ │ │ └────────────────────────────────────────────────────────────────────┘  │  │  │  │   │  │
│ │ │ │                                                                            │  │   │  │
│ │ │ │ (more cards... or empty_state if filtered results empty)                │  │   │  │
│ │ │ └──────────────────────────────────────────────────────────────────────────┘  │   │  │
│ │ └────────────────────────────────────────────────────────────────────────────────┘   │  │
│ │                                                                                       │  │
│ │ ┌────────────────────────────────────────────────────────────────────────────────┐   │  │
│ │ │ TAB 2: ADD / EDIT (form in card)                                              │   │  │
│ │ │ ┌─ CARD (card, elevated=true) ────────────────────────────────────────────┐  │   │  │
│ │ │ │ ┌────────────────────────────────────────────────────────────────────┐  │  │   │  │
│ │ │ │ │ Add Maintenance Record                    [× Close]             │  │  │   │  │
│ │ │ │ └────────────────────────────────────────────────────────────────────┘  │  │   │  │
│ │ │ │                                                                            │  │   │  │
│ │ │ │ ┌─────────────────────┐ ┌─────────────────────┐  (2-col on desktop)    │  │   │  │
│ │ │ │ │ Service Type *      │ │ Date Performed *    │                         │  │   │  │
│ │ │ │ │ ▼ Oil Change        │ │ [2025-01-15]        │                         │  │   │  │
│ │ │ │ │   Oil Filter        │ │                     │                         │  │   │  │
│ │ │ │ │   Air Filter        │ │                     │                         │  │   │  │
│ │ │ │ │   Cabin Filter      │ │                     │                         │  │   │  │
│ │ │ │ │   Spark Plugs       │ │                     │                         │  │   │  │
│ │ │ │ │   Brake Fluid       │ │                     │                         │  │   │  │
│ │ │ │ │   Coolant Flush     │ │                     │                         │  │   │  │
│ │ │ │ │   Transmission Fluid│ │                     │                         │  │   │  │
│ │ │ │ │   Brake Pads (Front)│ │                     │                         │  │   │  │
│ │ │ │ │   Brake Pads (Rear) │ │                     │                         │  │   │  │
│ │ │ │ │   Other...          │ │                     │                         │  │   │  │
│ │ │ │ └─────────────────────┘ └─────────────────────┘                         │  │   │  │
│ │ │ │                                                                            │  │   │  │
│ │ │ │ ┌─────────────────────┐ ┌─────────────────────┐                         │  │   │  │
│ │ │ │ │ Mileage at Service *│ │ Cost (USD)          │                         │  │   │  │
│ │ │ │ │ [45,230]            │ │ [89.99]             │                         │  │   │  │
│ │ │ │ └─────────────────────┘ └─────────────────────┘                         │  │   │  │
│ │ │ │                                                                            │  │   │  │
│ │ │ │ ┌────────────────────────────────────────────────────────────────┐      │  │   │  │
│ │ │ │ │ Service Provider                                               │      │  │   │  │
│ │ │ │ │ [Hyundai Dealer Downtown]                                      │      │  │   │  │
│ │ │ │ └────────────────────────────────────────────────────────────────┘      │  │   │  │
│ │ │ │                                                                            │  │   │  │
│ │ │ │ ┌────────────────────────────────────────────────────────────────┐      │  │   │  │
│ │ │ │ │ Notes                                                          │      │  │   │  │
│ │ │ │ │ [Synthetic 5W-30, OEM filter]                                  │      │  │   │  │
│ │ │ │ └────────────────────────────────────────────────────────────────┘      │  │   │  │
│ │ │ │                                                                            │  │   │  │
│ │ │ │ ┌─────────────────────┐ ┌─────────────────────┐                         │  │   │  │
│ │ │ │ │ Next Due (km)       │ │ Next Due (date)     │                         │  │   │  │
│ │ │ │ │ [52,000]            │ │ [2025-07-15]        │                         │  │   │  │
│ │ │ │ └─────────────────────┘ └─────────────────────┘                         │  │   │  │
│ │ │ │                                                                            │  │   │  │
│ │ │ │ ┌────────────────────────────────────────────────────────────────┐      │  │   │  │
│ │ │ │ │ [Cancel]                                    [Save Record]      │      │  │   │  │
│ │ │ │ │ (button_secondary)                          (button_primary)   │      │  │   │  │
│ │ │ │ └────────────────────────────────────────────────────────────────┘      │  │   │  │
│ │ │ └────────────────────────────────────────────────────────────────────────┘  │   │  │
│ │ └────────────────────────────────────────────────────────────────────────────────┘   │  │
│ │                                                                                       │  │
│ │ ┌────────────────────────────────────────────────────────────────────────────────┐   │  │
│ │ │ TAB 3: UPCOMING                                                               │   │  │
│ │ │ ┌──────────────────────────────────────────────────────────────────────────┐  │   │  │
│ │ │ │ UPCOMING MAINTENANCE (responsive grid: auto-fit minmax(320px, 1fr))     │  │   │  │
│ │ │ │                                                                            │  │   │  │
│ │ │ │ ┌─ UPCOMING CARD (card) ─────────────────────────────────────────────┐  │  │   │  │
│ │ │ │ │ ┌────────────────────────────────────────────────────────────────┐  │  │  │   │  │
│ │ │ │ │ │ Oil Change                                    ● Overdue       │  │  │  │   │  │
│ │ │ │ │ │ Interval: 10,000 km / 6 months                                 │  │  │  │   │  │
│ │ │ │ │ └────────────────────────────────────────────────────────────────┘  │  │  │  │   │  │
│ │ │ │ │ ┌────────────────────────────────────────────────────────────────┐  │  │  │   │  │
│ │ │ │ │ │ Last Service: 2025-01-15 @ 42,000 km                          │  │  │  │   │  │
│ │ │ │ │ │ Due: 2025-07-15 @ 52,000 km                                   │  │  │  │   │  │
│ │ │ │ │ │ Gap: 6,770 km  •  4 months overdue                            │  │  │  │   │  │
│ │ │ │ │ └────────────────────────────────────────────────────────────────┘  │  │  │  │   │  │
│ │ │ │ │ ┌────────────────────────────────────────────────────────────────┐  │  │  │   │  │
│ │ │ │ │ │ [Record Service]  (button_primary, full_width)                │  │  │  │   │  │
│ │ │ │ │ └────────────────────────────────────────────────────────────────┘  │  │  │  │   │  │
│ │ │ │ └────────────────────────────────────────────────────────────────────┘  │  │  │  │   │  │
│ │ │ │                                                                            │  │   │  │
│ │ │ │ ┌─ UPCOMING CARD ────────────────────────────────────────────────────┐  │  │  │   │  │
│ │ │ │ │ Air Filter                                ⚠ Due Soon             │  │  │  │   │  │
│ │ │ │ │ Interval: 30,000 km / 24 months                                  │  │  │  │   │  │
│ │ │ │ │ Last Service: 2024-06-10 @ 35,000 km                             │  │  │  │   │  │
│ │ │ │ │ Due: 2026-06-10 @ 65,000 km                                      │  │  │  │   │  │
│ │ │ │ │ Gap: 19,770 km  •  8 months remaining                           │  │  │  │   │  │
│ │ │ │ │ [Record Service]                                                  │  │  │  │   │  │
│ │ │ │ └────────────────────────────────────────────────────────────────────┘  │  │  │  │   │  │
│ │ │ │                                                                            │  │   │  │
│ │ │ │ ┌─ UPCOMING CARD ────────────────────────────────────────────────────┐  │  │  │   │  │
│ │ │ │ │ Spark Plugs                               ✓ Up to Date           │  │  │  │   │  │
│ │ │ │ │ Interval: 60,000 km / 48 months                                  │  │  │  │   │  │
│ │ │ │ │ Last Service: 2022-01-15 @ 15,000 km                             │  │  │  │   │  │
│ │ │ │ │ Due: 2026-01-15 @ 75,000 km                                      │  │  │  │   │  │
│ │ │ │ │ Gap: 29,770 km  •  14 months remaining                          │  │  │  │   │  │
│ │ │ │ │ [Record Service]                                                  │  │  │  │   │  │
│ │ │ │ └────────────────────────────────────────────────────────────────────┘  │  │  │  │   │  │
│ │ │ │                                                                            │  │   │  │
│ │ │ │ (more cards for all 10 intervals... or empty_state if all up to date)   │  │   │  │
│ │ │ └──────────────────────────────────────────────────────────────────────────┘  │   │  │
│ │ └────────────────────────────────────────────────────────────────────────────────┘   │  │
│ │                                                                                       │  │
│ │ ┌────────────────────────────────────────────────────────────────────────────────┐   │  │
│ │ │ EXPANDABLE RECORD DETAIL (triggered by [▼] on record card)                   │   │  │
│ │ │ ┌─ CARD (card, bordered) ────────────────────────────────────────────────┐  │   │  │
│ │ │ │ Oil Change - Full Details                                              │  │   │  │
│ │ │ │ Date: 2025-01-15    Mileage: 42,000 km    Cost: $89.99               │  │   │  │
│ │ │ │ Provider: Hyundai Dealer Downtown                                      │  │   │  │
│ │ │ │ Next Due: 52,000 km (2025-07-15)                                       │  │   │  │
│ │ │ │ Status: Overdue (6,770 km / 4 months past due)                        │  │   │  │
│ │ │ │ Notes: Synthetic 5W-30, OEM filter                                     │  │   │  │
│ │ │ │ Created: 2025-01-15 10:30  •  Updated: 2025-01-15 10:30              │  │   │  │
│ │ │ └────────────────────────────────────────────────────────────────────────┘  │   │  │
│ │ └────────────────────────────────────────────────────────────────────────────────┘   │  │
│ │                                                                                       │  │
│ │ ┌────────────────────────────────────────────────────────────────────────────────┐   │  │
│ │ │ DELETE CONFIRMATION (alert with dismissible actions)                         │   │  │
│ │ │ ┌─ ALERT (alert, variant=CRITICAL, dismissible) ─────────────────────────┐  │   │  │
│ │ │ │ ✕  Delete Maintenance Record                                           │  │   │  │
│ │ │ │ Are you sure you want to delete "Oil Change" from 2025-01-15?         │  │   │  │
│ │ │ │ This action cannot be undone.                                          │  │   │  │
│ │ │ │ [Cancel] [Delete] (button_ghost + button_danger)                      │  │   │  │
│ │ │ └────────────────────────────────────────────────────────────────────────┘  │   │  │
│ │ └────────────────────────────────────────────────────────────────────────────────┘   │  │
│ │                                                                                       │  │
│ └──────────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Responsive Breakpoints

| Breakpoint | Records Grid | Upcoming Grid | Form Layout | Quick-Add |
|------------|-------------|---------------|-------------|-----------|
| Mobile (<640px) | 1 column | 1 column | Stacked (1 col) | Wrapped rows |
| Tablet (640-1024px) | 2 columns | 2 columns | 2-column pairs | 3 per row |
| Desktop (1024-1440px) | 3 columns | 3 columns | 2-column pairs | All in row |
| Wide (>1440px) | 3 columns | 4 columns | 2-column pairs | All in row |

---

## Component State Matrix

| Component | Default | Hover | Focus | Active | Disabled | Loading |
|-----------|---------|-------|-------|--------|----------|---------|
| `button_primary` | ACCENT_PRIMARY | ACCENT_PRIMARY_HOVER | SHADOW_FOCUS | ACCENT_PRIMARY_ACTIVE | opacity:0.5 | spinner(SM) |
| `button_secondary` | SURFACE_PRIMARY | SURFACE_INTERACTIVE | SHADOW_FOCUS | SURFACE_SECONDARY | opacity:0.5 | spinner(SM) |
| `button_ghost` | transparent | SURFACE_INTERACTIVE | SHADOW_FOCUS | SURFACE_SECONDARY | opacity:0.5 | spinner(SM) |
| `button_danger` | STATUS_CRITICAL | #c0392b | SHADOW_FOCUS | #a93226 | opacity:0.5 | spinner(SM) |
| `badge` | variant color | — | — | — | — | — |
| `card` | SURFACE_PRIMARY + SHADOW_SM | SHADOW_MD | SHADOW_FOCUS | — | — | skeleton_card |
| `text_input` | SURFACE_SECONDARY + BORDER_DEFAULT | BORDER_FOCUS | SHADOW_FOCUS + BORDER_FOCUS | — | opacity:0.5 | skeleton |
| `selectbox` | SURFACE_SECONDARY + BORDER_DEFAULT | BORDER_FOCUS | SHADOW_FOCUS + BORDER_FOCUS | — | opacity:0.5 | skeleton |

---

## Token Reference for Implementation

### Colors (semantic)
```python
# Status
STATUS_CRITICAL      # Overdue, delete actions, errors
STATUS_WARNING       # Due soon, warnings
STATUS_SUCCESS       # Up to date, save success
STATUS_INFO          # Info messages, mileage display
STATUS_NEUTRAL       # Completed, secondary info

# Surfaces
SURFACE_PRIMARY      # Card backgrounds, page background
SURFACE_SECONDARY    # Input backgrounds, hover states
SURFACE_ELEVATED     # Elevated cards, modals
SURFACE_INTERACTIVE  # Hover/active states

# Text
TEXT_PRIMARY         # Primary content, headers
TEXT_SECONDARY       # Labels, secondary content
TEXT_MUTED           # Placeholders, disabled text
TEXT_ON_ACCENT       # Text on primary/danger buttons

# Accents
ACCENT_PRIMARY       # Primary actions, links, focus
ACCENT_PRIMARY_HOVER # Primary hover
ACCENT_PRIMARY_ACTIVE# Primary active
ACCENT_SECONDARY     # Secondary accents
ACCENT_SELECTED      # Selected tab/item background

# Borders
BORDER_DEFAULT       # Default borders, inputs
BORDER_SUBTLE        # Subtle dividers
BORDER_STRONG        # Strong emphasis
BORDER_FOCUS         # Focus rings
```

### Spacing
```python
SPACE_1 = "4px"      # Tight spacing
SPACE_2 = "8px"      # Small gap
SPACE_3 = "12px"     # Medium gap
SPACE_4 = "16px"     # Standard gap (cards, sections)
SPACE_5 = "24px"     # Large gap
SPACE_6 = "32px"     # Section gap

GAP_INLINE = "8px"   # Inline element gap
GAP_FIELD = "12px"   # Form field gap
GAP_CARD = "16px"    # Card grid gap
GAP_SECTION = "24px" # Section gap
```

### Typography
```python
FONT_SIZE_H1 = "1.75rem"      # Page title
FONT_SIZE_H2 = "1.375rem"     # Section title, mileage value
FONT_SIZE_H3 = "1.125rem"     # Card title
FONT_SIZE_H4 = "1rem"         # Subtitle
FONT_SIZE_BODY = "0.9375rem"  # Body text
FONT_SIZE_BODY_SM = "0.875rem"# Small body
FONT_SIZE_LABEL = "0.75rem"   # Form labels
FONT_SIZE_CAPTION = "0.75rem" # Captions, badges
FONT_SIZE_CODE_SM = "0.75rem" # Monospace small

FONT_FAMILY_BASE = "'Inter', system-ui, sans-serif"
FONT_FAMILY_MONO = "'JetBrains Mono', 'Fira Code', monospace"
FONT_WEIGHT_LABEL = "600"
FONT_WEIGHT_BODY = "400"
FONT_WEIGHT_NUMERIC = "600"   # For numbers

LETTER_SPACING_LABEL = "0.05em"
LETTER_SPACING_CAPTION = "0.05em"
```

### Radius & Shadows
```python
RADIUS_SM = "4px"     # Badges, small inputs
RADIUS_MD = "8px"     # Cards, inputs, buttons
RADIUS_LG = "12px"    # Large cards, modals
RADIUS_PILL = "9999px"# Pills, badges

SHADOW_SM = "0 1px 2px rgba(0,0,0,0.3), 0 1px 1px rgba(0,0,0,0.2)"
SHADOW_MD = "0 4px 6px rgba(0,0,0,0.3), 0 2px 4px rgba(0,0,0,0.2)"
SHADOW_LG = "0 10px 15px rgba(0,0,0,0.3), 0 4px 6px rgba(0,0,0,0.2)"
SHADOW_FOCUS = "0 0 0 3px var(--i20-color-accent-primary-40)"
```

### Component Constants
```python
BUTTON_MIN_HEIGHT = "40px"
BUTTON_PADDING_VERTICAL = "8px"
BUTTON_PADDING_HORIZONTAL = "16px"
BUTTON_ICON_GAP = "8px"
BUTTON_RADIUS = "8px"
BUTTON_FONT_SIZE = "0.875rem"
BUTTON_FONT_WEIGHT = "600"

BADGE_PADDING_VERTICAL = "4px"
BADGE_PADDING_HORIZONTAL = "10px"
BADGE_RADIUS = "9999px"
BADGE_FONT_SIZE = "0.75rem"
BADGE_FONT_WEIGHT = "600"

CARD_RADIUS = "12px"
CARD_PADDING = "16px"
CARD_BORDER = "1px solid var(--i20-color-border-default)"

INPUT_HEIGHT = "40px"
INPUT_PADDING_VERTICAL = "8px"
INPUT_PADDING_HORIZONTAL = "12px"
INPUT_RADIUS = "8px"
INPUT_FONT_SIZE = "0.9375rem"

EMPTY_STATE_PADDING = "48px"
EMPTY_STATE_ICON_SIZE = "64px"

SKELETON_PULSE_DURATION = "1.5s"
SPINNER_SIZE_SM = "16px"
SPINNER_SIZE_MD = "24px"
SPINNER_SIZE_LG = "32px"

TRANSITION_FAST = "150ms ease"
TRANSITION_NORMAL = "200ms ease"
```

---

## Implementation Notes

### 1. Page Header
Use `page_header()` from `components.ui.layout`:
```python
page_header(
    title="Maintenance Tracker",
    subtitle="Track service intervals, record history, and plan upcoming maintenance",
    actions=[mileage_display]  # Custom mileage card as action
)
```

### 2. Quick-Add Bar
Render as flex container with `button_ghost()` for each service:
```python
for service in QUICK_ADD_SERVICES:
    button_ghost(
        label=f"+ {service}",
        icon="➕",
        size=ButtonSize.SM,
        key=f"quick_add_{service.lower().replace(' ', '_')}",
        on_click=lambda s=service: set_quick_add_form(s)
    )
```

### 3. Record Cards
Use `card()` with structured content:
```python
card(CardProps(
    title=f"{record['service_type']}  {badge_html}",
    subtitle=f"{format_date(record['date_performed'])}  •  {record['mileage_at_service']:,} km  •  {format_currency(record['cost'])}",
    content=details_html,
    footer=actions_html,
    elevated=False,
    bordered=True,
))
```

### 4. Status Badge Mapping
```python
status_badge_map = {
    "overdue": (BadgeVariant.CRITICAL, "● Overdue"),
    "due_soon": (BadgeVariant.WARNING, "⚠ Due Soon"),
    "up_to_date": (BadgeVariant.SUCCESS, "✓ Up to Date"),
    "completed": (BadgeVariant.NEUTRAL, "✓ Completed"),
}
```

### 5. Form Fields
Use `text_input()` and `selectbox()` with `FormFieldProps`:
```python
text_input(
    label="Mileage at Service",
    value=str(record.get('mileage_at_service', current_mileage)),
    placeholder="45,230",
    required=True,
    help_text="Odometer reading at time of service",
    key="maint_mileage",
)

selectbox(
    label="Service Type",
    options=SERVICE_TYPE_OPTIONS,
    index=default_index,
    required=True,
    key="maint_service_type",
)
```

### 6. Upcoming Cards
Similar card structure with "Record Service" primary action:
```python
card(CardProps(
    title=f"{item['service_type']}  {status_badge}",
    content=f"""
        <div>Interval: {item['interval_km']:,} km / {item['interval_months']} months</div>
        <div>Last Service: {format_date(item['last_date'])} @ {item['last_km']:,} km</div>
        <div>Due: {format_date(item['due_date'])} @ {item['due_km']:,} km</div>
        <div class="gap">{format_gap(item['km_gap'], item['months_gap'])}</div>
    """,
    footer=button_primary("Record Service", full_width=True, key=f"record_{item['service_type']}"),
))
```

### 7. Empty States
```python
empty_state(EmptyStateProps(
    title="No Maintenance Records",
    message="Start tracking your vehicle's maintenance by adding your first service record.",
    icon="🔧",
    action_label="Add First Record",
    action_callback=lambda: set_show_add_form(True),
    action_key="empty_add_first",
))
```

### 8. Alerts for Actions
```python
# Success after save
alert("Record Saved", "Maintenance record has been saved successfully.", AlertVariant.SUCCESS, dismissible=True, key="save_success")

# Error on delete
alert("Delete Failed", "Unable to delete record. Please try again.", AlertVariant.CRITICAL, dismissible=True, key="delete_error")

# Delete confirmation
alert("Confirm Delete", "Are you sure you want to delete this record? This cannot be undone.", AlertVariant.WARNING, dismissible=True, key="confirm_delete")
```

---

## Acceptance Criteria Checklist

### Visual Consistency
- [ ] Page header matches Dashboard/Diagnostics/Performance style
- [ ] All cards use `card()` with consistent radius, padding, shadows
- [ ] All buttons use design system variants (primary/secondary/ghost/danger)
- [ ] All badges use `badge()` with semantic variants
- [ ] All form fields use `text_input()`/`selectbox()` with consistent styling
- [ ] All empty states use `empty_state()` component
- [ ] All alerts use `alert()` component
- [ ] No custom CSS in final implementation
- [ ] All spacing uses design tokens (SPACE_1-6, GAP_*)
- [ ] All colors use semantic tokens (STATUS_*, ACCENT_*, SURFACE_*, TEXT_*)
- [ ] Typography uses token scale (FONT_SIZE_H1-H4, BODY, LABEL, CAPTION)

### Functional Preservation
- [ ] All 6 maintenance session-state keys preserved
- [ ] Filter (All/Upcoming/Overdue/Due Soon) works
- [ ] Sort (Due Date/Service Type/Date/Mileage/Cost, Asc/Desc) works
- [ ] Record cards display all fields correctly
- [ ] Status calculation matches original logic exactly
- [ ] Edit/Delete/View actions work
- [ ] Add form saves to database
- [ ] Edit form updates database
- [ ] Quick-add buttons pre-fill form correctly
- [ ] Upcoming tab calculates from intervals + records + current_mileage
- [ ] "Record Service" on upcoming opens add form pre-filled
- [ ] Delete confirmation prevents accidental deletion
- [ ] Current mileage displays from session state
- [ ] Cost formatting preserved ($X,XXX.XX)
- [ ] Date formatting preserved (YYYY-MM-DD)

### Responsive Behavior
- [ ] Mobile: single column grids, stacked forms, wrapped quick-add
- [ ] Tablet: 2-column grids, 2-column forms, 3 quick-add per row
- [ ] Desktop: 3-column grids, 2-column forms, all quick-add in row
- [ ] Wide: 3-4 column grids, 2-column forms

### Accessibility
- [ ] Semantic HTML structure maintained
- [ ] ARIA labels on interactive elements
- [ ] Focus indicators visible (SHADOW_FOCUS)
- [ ] Color contrast meets WCAG 2.1 AA (validated in design system)
- [ ] Keyboard navigation works
- [ ] Screen reader friendly (badges have text, not just icons)

---

## File Structure After Implementation

```
modules/
  maintenance.py          # Rewritten - ~800 lines (down from 1060)
docs/
  PHASE_6_STAGE_5.5_MAINTENANCE_AUDIT.md    # This audit
  PHASE_6_STAGE_5.5_MAINTENANCE_LAYOUT.md   # This layout
  PHASE_6_PROGRESS.md                       # Updated with 5.5 complete
```

---

## Dependencies to Import

```python
# Design System
from components.ui.tokens import (
    # Colors
    STATUS_SUCCESS, STATUS_WARNING, STATUS_CRITICAL, STATUS_INFO, STATUS_NEUTRAL,
    ACCENT_PRIMARY, ACCENT_PRIMARY_HOVER, ACCENT_PRIMARY_ACTIVE, ACCENT_SECONDARY,
    ACCENT_SELECTED, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ON_ACCENT,
    SURFACE_PRIMARY, SURFACE_SECONDARY, SURFACE_ELEVATED, SURFACE_INTERACTIVE,
    BORDER_DEFAULT, BORDER_SUBTLE, BORDER_STRONG, BORDER_FOCUS,
    # Spacing
    SPACE_1, SPACE_2, SPACE_3, SPACE_4, SPACE_5, SPACE_6,
    GAP_INLINE, GAP_FIELD, GAP_CARD, GAP_SECTION,
    # Radius
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_PILL,
    # Shadows
    SHADOW_SM, SHADOW_MD, SHADOW_LG, SHADOW_FOCUS,
    # Typography
    FONT_SIZE_H1, FONT_SIZE_H2, FONT_SIZE_H3, FONT_SIZE_H4,
    FONT_SIZE_BODY, FONT_SIZE_BODY_SM, FONT_SIZE_LABEL, FONT_SIZE_CAPTION,
    FONT_FAMILY_BASE, FONT_FAMILY_MONO, FONT_WEIGHT_LABEL, FONT_WEIGHT_BODY,
    FONT_WEIGHT_NUMERIC, LETTER_SPACING_LABEL, LETTER_SPACING_CAPTION,
    # Component constants
    BUTTON_MIN_HEIGHT, BUTTON_PADDING_VERTICAL, BUTTON_PADDING_HORIZONTAL,
    BUTTON_ICON_GAP, BUTTON_RADIUS, BUTTON_FONT_SIZE, BUTTON_FONT_WEIGHT,
    BADGE_PADDING_VERTICAL, BADGE_PADDING_HORIZONTAL, BADGE_RADIUS,
    BADGE_FONT_SIZE, BADGE_FONT_WEIGHT,
    CARD_RADIUS, CARD_PADDING, CARD_BORDER,
    INPUT_HEIGHT, INPUT_PADDING_VERTICAL, INPUT_PADDING_HORIZONTAL,
    INPUT_RADIUS, INPUT_FONT_SIZE,
    EMPTY_STATE_PADDING, EMPTY_STATE_ICON_SIZE,
    SKELETON_PULSE_DURATION, SPINNER_SIZE_SM, SPINNER_SIZE_MD, SPINNER_SIZE_LG,
    TRANSITION_FAST, TRANSITION_NORMAL,
)

from components.ui.components import (
    ButtonVariant, ButtonSize, ButtonProps, button, button_primary, button_secondary,
    button_ghost, button_danger,
    BadgeVariant, badge,
    AlertVariant, alert,
    CardProps, card, card_simple,
    FormFieldProps, text_input, selectbox,
    EmptyStateProps, empty_state,
    skeleton_card, spinner,
)

from components.ui.layout import page_header, responsive_container, auto_fit_grid_css, metric_row_columns
from components.shell import page_header as shell_page_header
```