"""Document-level HTML injection component for Streamlit."""
import streamlit.components.v1 as components

# Create the component function
_document_html = components.declare_component(
    "document_html",
    path="components/streamlit_components/document_html/frontend"
)


def document_html(html: str, key: str = None) -> None:
    """
    Inject HTML at the document level (head or body).

    This component renders a hidden div that uses JavaScript to inject
    the provided HTML into the document head or body.

    Args:
        html: HTML string to inject
        key: Optional key for the component
    """
    _document_html(html=html, key=key, default=None)