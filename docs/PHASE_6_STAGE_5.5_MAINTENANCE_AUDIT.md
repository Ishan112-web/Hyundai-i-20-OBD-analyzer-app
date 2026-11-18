# Maintenance Page Redesign - Stage 5.5 Read-Only Audit

**Date:** 2026-11-17  
**Phase:** 6 Stage 5.5  
**Status:** Audit Complete - Ready for Implementation

---

## 1. Existing Session State Keys (Maintenance-Specific)

The following session state keys are initialized and managed by `modules/maintenance.py`:

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `maintenance_editing_id` | int | `None` | ID of record being edited |
| `maintenance_form_data` | dict | `{}` | Form data for add/edit operations |
| `maintenance_show_add` | bool | `False` | Show add record form |
| `maintenance_filter_status` | str | `"all"` | Filter: all/upcoming/overdue/due_soon |
| `maintenance_sort_by` | str | `"due_date"` | Sort field for records table |
| `maintenance_sort_order` | str | `"asc"` | Sort order: asc/desc |

**Total Maintenance-specific keys: 6**

These must be preserved exactly - no renaming, deletion, or structure changes.

### Shared Session State Keys (Used by Maintenance)
- `vehicle_vin` - Vehicle identification
- `vehicle_year`, `vehicle_make`, `vehicle_model`, `vehicle_engine` - Vehicle specs
- `current_mileage` - Current odometer reading (used for due calculations)

---

## 2. Existing Functions & Callbacks

### Core Render Functions
- `render_maintenance()` - Main entry point, orchestrates 3-tab layout
- `get_maintenance_css()` - Returns ~260 lines of custom CSS
- `render_records_tab(db)` - Records tab with filter, sort, and table
- `render_add_edit_tab(db)` - Add/Edit tab with form
- `render_upcoming_tab(db)` - Upcoming maintenance tab

### Records Tab Functions
- `get_status(due_date_km, due_date_months, current_km, current_date)` - Calculates status: overdue/due_soon/up_to_date
- `render_record_row(record, db)` - Renders single record as expandable card with actions

### Add/Edit Tab Functions
- `get_service_types(db)` - Returns list of service types from intervals + custom records
- `render_add_form(db)` - Render add maintenance record form
- `render_edit_form(db, record)` - Render edit maintenance record form

### Upcoming Tab Functions
- `calculate_upcoming_maintenance(db)` - Calculates upcoming/overdue maintenance from intervals + records
- `render_upcoming_card(item)` - Renders upcoming maintenance item as card

### Data Helpers
- `format_currency(amount)` - Format as $X,XXX.XX
- `format_date(date_val)` - Format date as YYYY-MM-DD or N/A
- `parse_date(date_str)` - Parse date string to date object

### Quick-Add Buttons (6 common services)
- Oil Change
- Oil Filter
- Air Filter
- Cabin Filter
- Brake Fluid
- Coolant Flush

### Database CRUD Operations (via services/database.py)
- `add_maintenance_record(record)` - Create new record
- `get_maintenance_records()` - Get all records (with filters)
- `update_maintenance_record(record_id, updates)` - Update record
- `delete_maintenance_record(record_id)` - Delete record
- `get_upcoming_maintenance(current_km)` - Get calculated upcoming maintenance

### Maintenance Intervals (from config.py - MAINTENANCE_INTERVALS)
| Service | Interval (km) | Interval (months) |
|---------|---------------|-------------------|
| Oil Change | 10,000 | 6 |
| Oil Filter | 10,000 | 6 |
| Air Filter | 30,000 | 24 |
| Cabin Filter | 20,000 | 12 |
| Spark Plugs | 60,000 | 48 |
| Brake Fluid | 40,000 | 24 |
| Coolant Flush | 80,000 | 60 |
| Transmission Fluid | 100,000 | 72 |
| Brake Pads (Front) | 50,000 | 36 |
| Brake Pads (Rear) | 70,000 | 48 |

---

## 3. Backend Service Dependencies

| Service | Methods Used | Purpose |
|---------|-------------|---------|
| `get_database()` | `get_maintenance_records()`, `add_maintenance_record()`, `update_maintenance_record()`, `delete_maintenance_record()`, `get_upcoming_maintenance()` | Maintenance records persistence & calculation |

### Database Schema (maintenance_records)
- `id` - Primary key
- `service_type` - Service name (e.g., "Oil Change")
- `date_performed` - Date service was done
- `mileage_at_service` - Odometer at time of service
- `cost` - Cost in USD
- `notes` - Free text notes
- `service_provider` - Workshop/dealer name
- `next_due_km` - Next due mileage
- `next_due_date` - Next due date
- `created_at` - Record creation timestamp
- `updated_at` - Record update timestamp

---

## 4. UI Layout Structure (Current)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ HEADER: "Maintenance Tracker" + Current Mileage Display + Quick-Add Buttons │
├─────────────────────────────────────────────────────────────────────────────┤
│  THREE TABS                                                                 │
│ ┌────────────┐ ┌────────────┐ ┌──────────────────┐                         │
│ │ Records    │ │ Add / Edit │ │ Upcoming         │                         │
│ └────────────┘ └────────────┘ └──────────────────┘                         │
│                                                                             │
│ Tab 1 - Records: Filter (All/Upcoming/Overdue/Due Soon) + Sort controls   │
│         + Records list as expandable cards with:                          │
│         Service Type | Date | Mileage | Cost | Status Badge | Actions      │
│         Actions: Edit | Delete | View Details                              │
│                                                                             │
│ Tab 2 - Add/Edit: Form with fields:                                       │
│         Service Type (select + custom) | Date | Mileage | Cost            │
│         Service Provider | Notes | Next Due (km) | Next Due (date)        │
│         Quick-add buttons for 6 common services                           │
│         Buttons: Save (primary) / Cancel (secondary)                      │
│                                                                             │
│ Tab 3 - Upcoming: Calculated upcoming maintenance from intervals          │
│         + service history. Cards showing:                                 │
│         Service Type | Status Badge | Due (km/date) | Last Service       │
│         | Mileage Gap | Time Gap | Quick Action: "Record Service"         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Custom CSS (To Be Replaced with Design System)

The current implementation has **~260 lines of custom CSS** in `get_maintenance_css()` covering:

- Header styling (`.maint-header`, `.maint-title`, `.maint-subtitle`, `.maint-mileage`)
- Tab styling (`.stTabs` overrides)
- Record cards (`.record-card`, `.record-header`, `.record-body`, `.record-footer`)
- Status badges (`.status-badge`, `.overdue`, `.due-soon`, `.up-to-date`, `.completed`)
- Form styling (`.maint-form`, `.form-row`, `.form-group`, `.form-label`, `.form-input`)
- Quick-add buttons (`.quick-add-btn`, `.quick-add-btn:hover`)
- Action buttons (`.action-btn`, `.action-btn-secondary`, `.action-btn-danger`)
- Upcoming cards (`.upcoming-card`, `.upcoming-header`, `.upcoming-body`, `.upcoming-footer`)
- Empty state (`.empty-state`)
- Metric cards (`.metric-card`, `.metric-value`, `.metric-label`)
- Responsive adjustments
- Block container padding

---

## 6. Design System Integration Points (Available)

### UI Components (components/ui/components.py) - USE THESE
- `button_primary()`, `button_secondary()`, `button_ghost()`, `button_danger()` - Action buttons
- `badge()` / `BadgeVariant` - Status badges (overdue=CRITICAL, due_soon=WARNING, up_to_date=SUCCESS, completed=NEUTRAL)
- `alert()` / `AlertVariant` - Status messages (empty states, warnings, success messages)
- `card()` / `card_simple()` / `CardProps` - Panel containers for records, upcoming items
- `empty_state()` / `EmptyStateProps` - Empty records, no upcoming maintenance
- `table()` / `TableProps` / `TableColumn` - Records list (alternative to card layout)
- `text_input()`, `selectbox()` - Form fields
- `spinner()`, `skeleton()`, `skeleton_card()` - Loading states

### Design Tokens (components/ui/tokens.py) - USE THESE
- **Colors**: STATUS_SUCCESS, STATUS_WARNING, STATUS_CRITICAL, STATUS_INFO, STATUS_NEUTRAL, ACCENT_PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, SURFACE_PRIMARY, SURFACE_SECONDARY, BORDER_DEFAULT, BORDER_SUBTLE
- **Typography**: FONT_SIZE_H1-H4, FONT_SIZE_BODY, FONT_SIZE_LABEL, FONT_SIZE_CAPTION, FONT_FAMILY_BASE, FONT_WEIGHT_LABEL, FONT_WEIGHT_NUMERIC
- **Spacing**: SPACE_1-6, GAP_INLINE, GAP_FIELD, GAP_CARD, GAP_SECTION
- **Radius**: RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_PILL
- **Shadows**: SHADOW_SM, SHADOW_MD, SHADOW_LG

### Layout (components/ui/layout.py) - USE THESE
- `page_header()` - Page header with title, subtitle, actions
- `responsive_container()` - Responsive content container
- `responsive_grid_css()`, `auto_fit_grid_css()` - Grid layouts for metric/upcoming cards
- `metric_row_columns()` - Column helpers for metric displays

### Global Shell (components/shell.py) - ALREADY INTEGRATED
- `page_header` from layout already used
- Sidebar navigation, top bar, vehicle context automatically handled by app.py

---

## 7. Functionality Preservation Checklist

### Records Tab
- [ ] Filter dropdown: All / Upcoming / Overdue / Due Soon
- [ ] Sort controls: By Due Date / Service Type / Date Performed / Mileage / Cost (asc/desc)
- [ ] Records displayed as cards with: Service Type, Date, Mileage, Cost, Status Badge, Actions
- [ ] Status calculation: Overdue (>0km or >0 months past due), Due Soon (≤1000km or ≤1 month), Up to Date
- [ ] Actions per record: Edit (opens edit form), Delete (with confirmation), View Details (expander)
- [ ] Empty state when no records match filter
- [ ] Total records count displayed

### Add/Edit Tab
- [ ] Form fields: Service Type (select from intervals + custom), Date, Mileage, Cost, Service Provider, Notes, Next Due KM, Next Due Date
- [ ] Quick-add buttons for 6 common services (pre-fill form)
- [ ] Service Type "Other" option allows custom text input
- [ ] Date defaults to today, Mileage defaults to current_mileage from session state
- [ ] Save button (primary), Cancel button (secondary/ghost)
- [ ] Form validation: required fields, numeric validation for mileage/cost
- [ ] Edit mode: pre-populates form with existing record data
- [ ] On save: calls database add/update, refreshes records, closes form

### Upcoming Tab
- [ ] Calculates upcoming maintenance from: MAINTENANCE_INTERVALS + existing records + current_mileage
- [ ] For each interval: finds last service record, calculates next due (km + months)
- [ ] Displays cards with: Service Type, Status Badge, Due KM, Due Date, Last Service Date/Mileage
- [ ] Shows gaps: km until due, months until due
- [ ] "Record Service" quick action button per item (opens Add form pre-filled)
- [ ] Empty state when all maintenance up to date
- [ ] Sorts by urgency: Overdue first, then Due Soon, then Upcoming

### Data Provenance
- [ ] All records show date performed and mileage at service
- [ ] Cost tracking with currency formatting
- [ ] Service provider tracking
- [ ] Next due calculation preserved (km + months from last service)
- [ ] Custom service types supported alongside predefined intervals

### Error Handling
- [ ] Database errors caught and displayed via alert
- [ ] Form validation errors shown inline
- [ ] Invalid date/mileage handled gracefully
- [ ] Delete confirmation prevents accidental deletion

---

## 8. Special Considerations

### Mileage-Based Calculations
- Uses `current_mileage` from shared session state (updated from OBD or manual entry)
- Intervals have both km and month components - whichever comes first
- Next due = last_service_mileage + interval_km (for km), last_service_date + interval_months (for date)

### Quick-Add Services
- 6 predefined services matching MAINTENANCE_INTERVALS keys
- Pre-fill form with service type, set date to today, mileage to current_mileage
- User still reviews and saves

### Filter/Sort Persistence
- Filter and sort preferences stored in session state
- Persist across tab switches and page navigation

### Responsive Behavior
- Record cards stack on mobile
- Form fields stack on mobile
- Upcoming cards stack on mobile

---

## 9. Next Steps: Implementation Plan

### Phase 0: Audit Complete ✓

### Phase 1: Design System Integration
- Replace 260 lines of custom CSS with design system tokens/components
- Migrate record cards to `card()` / `card_simple()` with design tokens
- Migrate status badges to `badge()` with BadgeVariant (CRITICAL/WARNING/SUCCESS/NEUTRAL)
- Migrate form to `text_input()`, `selectbox()` with FormFieldProps
- Migrate quick-add buttons to `button_secondary()` / `button_ghost()`
- Migrate action buttons to `button_primary()`, `button_secondary()`, `button_danger()`
- Migrate empty states to `empty_state()` component
- Migrate upcoming cards to `card()` component

### Phase 2: Layout Restructure
- Use `page_header()` for consistent header with title, subtitle, current mileage display
- Use responsive grid for upcoming maintenance cards (`auto_fit_grid_css` or `metric_row_columns`)
- Consistent spacing via `GAP_CARD`, `GAP_SECTION`, `SPACE_4`, `SPACE_6`
- Use `responsive_container()` for content area

### Phase 3: Component Replacement
- Record cards → `card()` with header (service type + status badge), body (details), footer (actions)
- Filter/sort controls → design system form components
- Quick-add → button group with `button_ghost()` for each service
- Upcoming cards → `card()` with structured content
- Form → `text_input()`, `selectbox()` with proper validation styling

### Phase 4: Enhanced UX
- Add `skeleton_card()` loading states for records/upcoming tabs
- Use `alert()` for success/error messages after save/delete
- Consider `table()` component for records tab as alternative view (toggle)
- Add confirmation dialogs via `alert()` with dismissible actions for delete

### Phase 5: Testing & Verification
- Run full test suite (target: all passing)
- Manual functional verification of all 3 tabs
- Visual verification against Dashboard/Diagnostics/Performance design consistency
- Verify all 6 maintenance session-state keys preserved
- Verify database CRUD operations work correctly
- Verify upcoming calculation logic unchanged
- Verify quick-add buttons pre-fill correctly