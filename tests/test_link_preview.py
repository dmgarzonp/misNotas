"""Unit tests for LinkPreviewService YouTube video thumbnail extraction and web link preview cards."""

import pytest
from src.services.link_preview_service import LinkPreviewService


def test_youtube_id_extraction_standard():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert LinkPreviewService.extract_youtube_id(url) == "dQw4w9WgXcQ"
    assert LinkPreviewService.is_youtube_url(url) is True


def test_youtube_id_extraction_short_link():
    url = "https://youtu.be/dQw4w9WgXcQ?t=42"
    assert LinkPreviewService.extract_youtube_id(url) == "dQw4w9WgXcQ"
    assert LinkPreviewService.is_youtube_url(url) is True


def test_youtube_id_extraction_shorts():
    url = "https://www.youtube.com/shorts/abcdefghijk"
    assert LinkPreviewService.extract_youtube_id(url) == "abcdefghijk"
    assert LinkPreviewService.is_youtube_url(url) is True


def test_generate_youtube_card_html():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    card_html = LinkPreviewService.generate_youtube_card_html(url, "Mi Video Favorito")
    assert card_html is not None
    assert "https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg" in card_html
    assert "Mi Video Favorito" in card_html


def test_generate_web_card_html():
    url = "https://github.com/proyectosAI/misNotas"
    card_html = LinkPreviewService.generate_web_card_html(url)
    assert "github.com" in card_html
    assert 'href="https://github.com/proyectosAI/misNotas"' in card_html
