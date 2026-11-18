"""
i20 AI Garage - Components Package

Reusable UI components for the i20 AI Garage dashboard application.
All components use the centralized THEME from config.py for consistent styling.
"""

from components.sidebar import (
    create_sidebar,
    create_navigation_menu,
    create_vehicle_status_summary,
    create_connection_indicators,
    create_simulation_status,
)

from components.status_cards import (
    create_kpi_card,
    create_connection_status_card,
    create_alert_card,
)

from components.charts import (
    create_gauge_chart,
    create_line_chart,
    create_multi_series_chart,
)

__all__ = [
    # Sidebar components
    "create_sidebar",
    "create_navigation_menu",
    "create_vehicle_status_summary",
    "create_connection_indicators",
    "create_simulation_status",
    # Status card components
    "create_kpi_card",
    "create_connection_status_card",
    "create_alert_card",
    # Chart components
    "create_gauge_chart",
    "create_line_chart",
    "create_multi_series_chart",
]

__version__ = "1.0.0"