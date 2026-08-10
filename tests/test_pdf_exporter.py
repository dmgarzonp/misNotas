"""Unit tests for PDFExporter service."""

import os
import tempfile
from PyQt6.QtWidgets import QApplication
import pytest

from src.services.pdf_exporter import PDFExporter


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_export_note_to_pdf_success(qapp):
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_pdf = os.path.join(tmp_dir, "test_note.pdf")
        success = PDFExporter.export_note_to_pdf(
            title="Nota de Prueba",
            content_html="<p>Este es un texto de prueba en PDF</p>",
            theme_name="honey",
            output_path=output_pdf,
        )
        assert success is True
        assert os.path.exists(output_pdf)
        assert os.path.getsize(output_pdf) > 0
