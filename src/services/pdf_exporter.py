"""PDF Exporter service for Mis Apuntes application.

Generates styled PDF files from note content, title, and pastel theme styling using Qt QPdfWriter.
"""

from typing import Optional
from PyQt6.QtGui import QPageLayout, QPageSize, QPdfWriter, QTextDocument
from src.views.styles import get_theme


class PDFExporter:
    """Exports note HTML/text to styled PDF files."""

    @staticmethod
    def export_note_to_pdf(
        title: str, content_html: str, theme_name: str, output_path: str
    ) -> bool:
        """Renders styled note HTML into a PDF file at output_path."""
        theme = get_theme(theme_name)
        display_title = title if title.strip() else "Mis Apuntes"

        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    background-color: {theme.background};
                    color: {theme.text_color};
                    font-family: 'Inter', 'SF Pro Text', 'Helvetica', sans-serif;
                    padding: 24px;
                }}
                h1 {{
                    color: {theme.accent};
                    font-size: 24px;
                    border-bottom: 2px solid {theme.border};
                    padding-bottom: 8px;
                }}
                .content {{
                    font-size: 14px;
                    line-height: 1.6;
                    margin-top: 16px;
                }}
            </style>
        </head>
        <body>
            <h1>{display_title}</h1>
            <div class="content">{content_html}</div>
        </body>
        </html>
        """

        doc = QTextDocument()
        doc.setHtml(full_html)

        writer = QPdfWriter(output_path)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        writer.setPageOrientation(QPageLayout.Orientation.Portrait)

        doc.print(writer)
        return True
