# Phase 4: Professional Reporting Engine - Technical Documentation

## Overview

The Professional Reporting Engine transforms existing vehicle, diagnostic, rule evaluation, telemetry, performance, and maintenance data into professional, downloadable PDF and HTML reports. It is designed with a modular architecture separating data assembly from rendering, enabling independent development and testing of each component.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REPORTING ENGINE ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌──────────────────┐    ┌─────────────────────────┐   │
│  │   EXISTING  │    │  REPORT DATA     │    │     RENDERERS           │   │
│  │  SERVICES   │───▶│    BUILDER       │───▶│  ┌─────────┐ ┌─────────┐ │   │
│  │             │    │                  │    │  │ HTML    │ │ PDF     │ │   │
│  │ • Database  │    │ • Build Diagnostic│   │  │Renderer │ │Renderer │ │   │
│  │ • Diagnostic│    │ • Build Health    │   │  │(Jinja2) │ │(ReportLab)│ │   │
│  │ • Rule Eng  │    │ • Build Perf      │   │  └────┬────┘ └────┬────┘ │   │
│  │ • OBD Svc   │    │ • Build Maint     │   │       │         │       │   │
│  └─────────────┘    │ • Provenance      │   │       ▼         ▼       │   │
│                     │ • Missing Data    │   │  ┌─────────────────────┐  │   │
│                     └────────┬──────────┘   │  │  TEMPLATES          │  │   │
│                              │              │  │  • base.html        │  │   │
│                              ▼              │  │  • diagnostic_*.html│  │   │
│                     ┌──────────────────┐   │  │  • health_*.html    │  │   │
│                     │  REPORT MODELS   │   │  │  • performance_*.html│  │   │
│                     │  (Pydantic)      │   │  │  • maintenance_*.html│  │   │
│                     │                  │   │  └─────────────────────┘  │   │
│                     │ • ReportMetadata │   │                            │   │
│                     │ • VehicleInfo    │   │                            │   │
│                     │ • 4 ReportData   │   │                            │   │
│                     │ • Enums          │   │                            │   │
│                     └────────┬──────────┘   └──────────────────────────┘   │
│                              │                                             │
│                              ▼                                             │
│                     ┌──────────────────┐                                   │
│                     │ REPORT GENERATOR │                                   │
│                     │  (Orchestrator)  │                                   │
│                     │                  │                                   │
│                     │ • generate_*()   │                                   │
│                     │ • generate_all() │                                   │
│                     │ • File output    │                                   │
│                     │ • Session/Dx IDs │                                   │
│                     └────────┬──────────┘                                   │
│                              │                                             │
│                              ▼                                             │
│                     ┌──────────────────┐                                   │
│                     │   STREAMLIT UI   │                                   │
│                     │  modules/reports │                                   │
│                     │                  │                                   │
│                     │ • 3 Tabs         │                                   │
│                     │   Generate       │                                   │
│                     │   Preview        │                                   │
│                     │   Download       │                                   │
│                     │ • Source Select  │                                   │
│                     │ • Format Select  │                                   │
│                     │ • Batch Generate │                                   │
│                     └──────────────────┘                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Report Models (`services/report_models.py`)

**Purpose**: Type-safe Pydantic models for all report data structures.

#### Enums
```python
class ReportType(str, Enum):
    DIAGNOSTIC = "diagnostic"
    VEHICLE_HEALTH = "vehicle_health"
    PERFORMANCE = "performance"
    MAINTENANCE = "maintenance"

class ReportFormat(str, Enum):
    HTML = "html"
    PDF = "pdf"

class DataSource(str, Enum):
    REAL = "real"
    SIMULATION = "simulation"
    MIXED = "mixed"
    UNKNOWN = "unknown"
```

#### Core Models
- **ReportMetadata**: report_id, report_type, generated_at, format, data_source, generator_version
- **ReportVehicleInfo**: make, model, year, engine, transmission, fuel_type, market, ecu_tuning, diagnostic_mode, odometer_km, vin
- **DataProvenance**: description, source (DataSource), record_count, date_range, notes
- **DiagnosticReportData**: dtcs, ai_diagnosis, rule_findings, telemetry_summary, recommendations, data_provenance, limitations
- **VehicleHealthReportData**: overall_conclusion, latest_diagnostic_summary, current_dtc_summary, latest_rule_findings, latest_ai_diagnosis, sensor_availability, telemetry_summary, component_statuses, maintenance_history, upcoming_maintenance, overdue_maintenance, safety_observations, data_provenance
- **PerformanceReportData**: session, sensor_statistics, charts_data, data_provenance
- **MaintenanceReportData**: odometer_km, summary, maintenance_history, upcoming_items, overdue_items, data_provenance

#### Union Types
```python
ReportDataUnion = Union[
    DiagnosticReportData,
    VehicleHealthReportData,
    PerformanceReportData,
    MaintenanceReportData,
]
```

---

### 2. Report Data Builder (`services/report_data_builder.py`)

**Purpose**: Assembles report data from existing services (Database, DiagnosticEngine, RuleEngine, OBD).

**Key Methods**:
```python
class ReportDataBuilder:
    def __init__(self, database: Optional[str] = None):
        # Uses existing DatabaseService
        self.db = DatabaseService(database)
    
    def build_diagnostic_report(
        self,
        metadata: ReportMetadata,
        vehicle_info: ReportVehicleInfo,
        session_id: Optional[str] = None,
        diagnosis_id: Optional[str] = None,
    ) -> DiagnosticReportData:
        # Fetches: DTCs, AI diagnoses, rule findings, telemetry
    
    def build_vehicle_health_report(
        self,
        metadata: ReportMetadata,
        vehicle_info: ReportVehicleInfo,
    ) -> VehicleHealthReportData:
        # Fetches: component statuses, maintenance history, safety observations
    
    def build_performance_report(
        self,
        metadata: ReportMetadata,
        vehicle_info: ReportVehicleInfo,
        session_id: Optional[str] = None,
    ) -> PerformanceReportData:
        # Fetches: session summary, sensor statistics
    
    def build_maintenance_report(
        self,
        metadata: ReportMetadata,
        vehicle_info: ReportVehicleInfo,
    ) -> MaintenanceReportData:
        # Fetches: maintenance records, cost analysis, upcoming/overdue
    
    def _get_vehicle_info(self) -> Dict[str, Any]:
        # Gets vehicle profile from database with defaults
    
    def _normalize_data_source(self, is_demo: bool, is_simulated: bool) -> DataSource:
        # Normalizes data source from database flags
```

**Data Provenance Handling**:
- Each data source tracked with `DataProvenance` model
- `DataSource.REAL` for actual OBD data
- `DataSource.SIMULATION` for software-generated data
- `DataSource.MIXED` for combined sources
- Record counts and date ranges included

**Missing Data Handling**:
- Empty lists for missing collections
- `None` for optional single objects
- Default values for required fields
- Limitations section documents known gaps

---

### 3. HTML Renderer (`services/report_renderers/html_renderer.py`)

**Purpose**: Renders report data to professional HTML using Jinja2 templates.

**Configuration**:
```python
self.env = Environment(
    loader=FileSystemLoader(str(self.templates_dir)),
    autoescape=select_autoescape(["html", "xml"]),  # SECURITY: Autoescape enabled
    trim_blocks=True,
    lstrip_blocks=True,
)
```

**Key Features**:
- **Autoescaping**: All `{{ variable }}` automatically HTML-escaped
- **No `|safe` filters**: Templates never use unsafe filters
- **Enum Preservation**: Enum objects passed to templates for `.value` access
- **Offline Capable**: Embedded CSS, no external dependencies
- **Print Optimized**: CSS `@media print` styles for clean PDF output

**Methods**:
```python
def render_diagnostic_report(self, report_data: DiagnosticReportData) -> str
def render_vehicle_health_report(self, report_data: VehicleHealthReportData) -> str
def render_performance_report(self, report_data: PerformanceReportData) -> str
def render_maintenance_report(self, report_data: MaintenanceReportData) -> str
def render_report(self, report_data: ReportDataUnion) -> str  # Polymorphic
def save_report(self, report_data: ReportDataUnion, output_path: Path) -> bool
```

**Security Note**: Previous implementation had `_sanitize_dict` that pre-escaped with `html.escape()`, causing double-escaping. **Removed** — Jinja2 autoescape handles all escaping correctly.

---

### 4. PDF Renderer (`services/report_renderers/pdf_renderer.py`)

**Purpose**: Renders report data to professional PDF using ReportLab (pure Python).

**Key Features**:
- **Windows Compatible**: No LaTeX, no wkhtmltopdf, no external tools
- **Professional Layout**: Title page, TOC, headers, footers, page numbers
- **Table Rendering**: Styled tables with alternating rows, headers, page breaks
- **Unicode Support**: DejaVu fonts for international characters
- **INR Currency**: ₹ symbol support

**Custom Flowables**:
- `PageNumCanvas`: Page numbering on every page
- `ReportTitlePage`: Professional title page with metadata
- `SectionHeader`: Numbered section headings
- `StyledTable`: Tables with professional styling

**Methods**:
```python
def render_report_bytes(self, report_data: ReportDataUnion) -> bytes
def render_report(self, report_data: ReportDataUnion, output_path: Path) -> bool

# Per-report content builders:
def _build_diagnostic_content(self, report_data, elements)
def _build_vehicle_health_content(self, report_data, elements)
def _build_performance_content(self, report_data, elements)
def _build_maintenance_content(self, report_data, elements)
```

---

### 5. Report Templates (`services/report_templates/`)

**Base Template** (`base.html`):
- CSS reset and professional styling
- Print media queries for PDF output
- Header/footer with report metadata
- Responsive design (mobile-friendly)

**Report Templates**:
- `diagnostic_report.html`: DTC table, AI diagnosis, rule findings, telemetry summary, recommendations, data provenance, limitations
- `vehicle_health_report.html`: Overall conclusion, component status cards, DTC summary, rule findings, AI diagnosis, maintenance history, upcoming/overdue, safety observations, data provenance
- `performance_report.html`: Session summary, sensor statistics table, charts placeholder, data provenance
- `maintenance_report.html`: Current status, manufacturer intervals, maintenance history table, upcoming/overdue tables, cost analysis by category, data provenance

**Template Security**:
- All variables use `{{ variable }}` (autoescaped)
- No `|safe` filters anywhere
- Enums accessed via `.value` (e.g., `{{ data_source.value }}`)

---

### 6. Report Generator (`services/report_generator.py`)

**Purpose**: Orchestrates report generation by combining data building and rendering.

**Key Features**:
- Unique 8-character report IDs (UUID-based)
- Safe file naming with timestamps
- Atomic writes (write to temp, then move)
- Batch generation of all 4 report types
- Vehicle info override support
- Session/Diagnosis ID selection for real data

**Methods**:
```python
def generate_diagnostic_report(
    self,
    session_id: Optional[str] = None,
    diagnosis_id: Optional[str] = None,
    format_type: ReportFormat = ReportFormat.HTML,
    output_path: Optional[Path] = None,
    vehicle_override: Optional[Dict[str, Any]] = None,
) -> Union[str, bytes, Path]

def generate_vehicle_health_report(...)
def generate_performance_report(...)
def generate_maintenance_report(...)

def generate_report(
    self,
    report_type: ReportType,
    format_type: ReportFormat = ReportFormat.HTML,
    output_path: Optional[Path] = None,
    **kwargs,
) -> Union[str, bytes, Path]

def generate_all_reports(
    self,
    format_type: ReportFormat = ReportFormat.HTML,
    output_dir: Optional[Path] = None,
    **kwargs,
) -> Dict[ReportType, Union[str, bytes, Path]]
```

**Convenience Functions**:
```python
generate_diagnostic_report(...)
generate_vehicle_health_report(...)
generate_performance_report(...)
generate_maintenance_report(...)
```

---

### 7. Streamlit UI (`modules/reports.py`)

**Purpose**: User interface for report generation, preview, and download.

**Three Tabs**:

#### Tab 1: Generate
- 4 report cards with descriptions
- Source selector per report (Simulation / Real / Mixed)
- Format selector (HTML / PDF)
- "Generate" button per report
- "Generate All Reports" batch button
- Real data options: Session ID dropdown, Diagnosis ID dropdown

#### Tab 2: Preview
- HTML preview in iframe (for HTML reports)
- Shows generated report content
- Print-to-PDF capability from browser

#### Tab 3: Download
- List of generated reports in session
- One-click download (HTML/PDF)
- File size, timestamp, report ID displayed
- Clear history button

**Integration Points**:
- Added to `NAVIGATION_ITEMS` in `components/sidebar.py`
- Registered in `app.py` page_renderers dict
- Added to `modules/__init__.py` exports

---

## Data Flow

### Diagnostic Report Generation
```
User selects Diagnostic Report + HTML
        │
        ▼
ReportGenerator.generate_diagnostic_report(format=HTML)
        │
        ├─▶ _create_metadata(ReportType.DIAGNOSTIC, DataSource.SIMULATION, HTML)
        │
        ├─▶ _create_vehicle_info(vehicle_override or db.get_vehicle_profile())
        │
        ▼
ReportDataBuilder.build_diagnostic_report(metadata, vehicle_info, session_id, diagnosis_id)
        │
        ├─▶ db.get_diagnostic_reports() → DTCs
        ├─▶ db.get_ai_diagnostic_sessions() → AI diagnosis
        ├─▶ rule_engine.get_evaluation_history() → Rule findings
        ├─▶ db.get_telemetry_sessions() → Telemetry summary
        │
        ▼
DiagnosticReportData (Pydantic validated)
        │
        ▼
HTMLRenderer.render_diagnostic_report(report_data)
        │
        ├─▶ _prepare_template_context() → Preserves enums, adds computed fields
        ├─▶ template.render(**context) → Jinja2 autoescapes all strings
        │
        ▼
HTML String → Returned or saved to file
```

---

## Security

### HTML Escaping (XSS Prevention)
- **Mechanism**: Jinja2 `select_autoescape(["html", "xml"])`
- **Coverage**: All `{{ variable }}` in templates
- **No Manual Sanitization**: Removed `_sanitize_dict` that caused double-escaping
- **Test Verified**: Input `<script>alert('xss')</script>` → Output `<script>alert('xss')</script>`

### Data Provenance Transparency
- Every report includes `DataProvenance` section
- Sources: REAL, SIMULATION, MIXED, UNKNOWN
- Record counts and date ranges shown
- Prevents misinterpretation of simulated data as real

### File Safety
- Unique report IDs prevent overwrites
- Timestamped filenames for batch generation
- Atomic writes (temp file + rename)
- Output directory configurable

---

## Testing

### Test Files
- `tests/test_report_models.py` — 50+ tests for all Pydantic models
- `tests/test_report_data_builder.py` — 12 tests for data assembly
- `tests/test_report_renderers.py` — 16 tests for HTML/PDF renderers
- `tests/test_report_generator.py` — 20 tests for orchestrator

### Key Test Coverage
- Model validation (enums, defaults, constraints)
- Data builder integration with database
- HTML rendering with all 4 report types
- PDF rendering with all 4 report types
- HTML escaping security test
- File output (HTML and PDF)
- Batch generation
- Vehicle info override
- Convenience functions

### Running Tests
```bash
# All reporting tests
pytest tests/test_report_models.py tests/test_report_data_builder.py tests/test_report_renderers.py tests/test_report_generator.py -v

# Full suite (326 tests)
pytest tests/ -v
```

---

## Dependencies

### New Dependencies (requirements.txt)
```
jinja2>=3.1.0      # HTML template engine with autoescaping
reportlab>=4.0.0   # Pure Python PDF generation
```

### Optional (for charts in PDF)
```
kaleido>=0.2.0     # Static chart image export (optional)
```

---

## Configuration

### Environment Variables
No new environment variables required. Uses existing:
- `DATABASE_PATH` (optional) — defaults to `data/i20_garage.db`

### Runtime Configuration
```python
# Custom output directory
generator = ReportGenerator(output_dir=Path("custom/reports"))

# Custom templates directory
renderer = HTMLRenderer(templates_dir=Path("custom/templates"))

# Custom database
builder = ReportDataBuilder(database="custom/path.db")
```

---

## Limitations & Known Issues

1. **Charts in PDF**: Currently table-based summaries. Static chart images require `kaleido` (optional dependency).

2. **Large Telemetry Datasets**: Reports summarize statistics. Full data available via CSV export from Performance page.

3. **No Real-Time Generation**: Reports generated on-demand, not streaming.

4. **Single Vehicle**: Reports use current vehicle profile. Multi-vehicle support would require profile selection.

5. **PDF Font Size**: DejaVu fonts included for Unicode. Custom fonts require registration.

6. **Memory**: Large reports held in memory during generation. For very large datasets, consider streaming.

---

## Future Enhancements

1. **Chart Images in PDF**: Integrate kaleido for Plotly chart export
2. **Scheduled Reports**: Automated report generation on schedule
3. **Email Delivery**: Send reports via SMTP
4. **Multi-Vehicle Support**: Profile selector in UI
5. **Custom Templates**: User-uploaded Jinja2 templates
6. **Report Comparison**: Side-by-side report diff
7. **Export Formats**: Add CSV/JSON export options

---

## File Structure

```
services/
├── report_models.py              # Pydantic models
├── report_data_builder.py        # Data assembly
├── report_generator.py           # Orchestrator
├── report_renderers/
│   ├── __init__.py              # Exports
│   ├── html_renderer.py         # Jinja2 HTML
│   └── pdf_renderer.py          # ReportLab PDF
└── report_templates/
    ├── base.html                # Base template
    ├── diagnostic_report.html   # Diagnostic template
    ├── vehicle_health_report.html
    ├── performance_report.html
    └── maintenance_report.html

modules/
└── reports.py                   # Streamlit UI

tests/
├── test_report_models.py
├── test_report_data_builder.py
├── test_report_renderers.py
└── test_report_generator.py

docs/
├── PHASE_4_PROGRESS.md
└── PHASE_4_REPORTING_ENGINE.md
```

---

## Integration Verification

All acceptance criteria verified:
- ✅ 326 tests passing (241 baseline + 85 new)
- ✅ All 4 report types generate HTML and PDF
- ✅ Data provenance visible in all reports
- ✅ HTML escaping prevents XSS
- ✅ No database schema changes
- ✅ No existing tests removed/weakened
- ✅ No physical OBD required for tests
- ✅ No LM Studio required for rendering
- ✅ Streamlit UI accessible and functional
- ✅ Professional formatting in both formats