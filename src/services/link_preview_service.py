"""Link Preview and YouTube Video Thumbnail Service for Mis Apuntes application.

Extracts YouTube video IDs and generates styled HTML preview cards with high-res thumbnails,
as well as generic web link preview cards.
"""

import re
from typing import Optional
from urllib.parse import parse_qs, urlparse


class LinkPreviewService:
    """Helper service to detect URLs, extract YouTube metadata, and render HTML link cards."""

    YOUTUBE_REGEX = re.compile(
        r"(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)([a-zA-Z0-9_-]{11})"
    )

    @classmethod
    def extract_youtube_id(cls, url: str) -> Optional[str]:
        """Extracts 11-character YouTube video ID from various URL formats."""
        match = cls.YOUTUBE_REGEX.search(url)
        if match:
            return match.group(1)

        # Fallback query param parsing
        parsed = urlparse(url)
        if "youtube.com" in parsed.netloc:
            qs = parse_qs(parsed.query)
            if "v" in qs and qs["v"]:
                return qs["v"][0]
        return None

    @classmethod
    def is_youtube_url(cls, url: str) -> bool:
        """Returns True if input string is a valid YouTube video link."""
        return cls.extract_youtube_id(url) is not None

    @classmethod
    def generate_youtube_card_html(
        cls, url: str, custom_title: Optional[str] = None
    ) -> Optional[str]:
        """Generates HTML snippet for a YouTube preview card with thumbnail."""
        video_id = cls.extract_youtube_id(url)
        if not video_id:
            return None

        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        display_title = custom_title or f"Ver Video en YouTube ({video_id})"

        html_card = (
            f'<div style="background: rgba(0, 0, 0, 0.05); border: 1px solid rgba(0, 0, 0, 0.12); '
            f'border-radius: 10px; padding: 8px; margin: 8px 0; width: 250px;">'
            f'<a href="{url}" style="text-decoration: none; color: inherit;">'
            f'<img src="{thumbnail_url}" width="234" style="border-radius: 6px; display: block; margin-bottom: 6px;">'
            f'<div style="font-weight: bold; font-size: 12px; margin-bottom: 2px; color: #1E293B;">▶️ {display_title}</div>'
            f'<div style="font-size: 10px; color: #64748B;">YouTube • youtube.com</div>'
            f"</a>"
            f"</div>"
        )
        return html_card

    @classmethod
    def generate_web_card_html(
        cls, url: str, custom_title: Optional[str] = None
    ) -> str:
        """Generates HTML snippet for a generic web page preview link card."""
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        domain = parsed.netloc or url
        display_title = custom_title or domain

        html_card = (
            f'<div style="background: rgba(59, 130, 246, 0.08); border-left: 4px solid #3B82F6; '
            f'border-radius: 6px; padding: 6px 10px; margin: 6px 0; width: 240px;">'
            f'<a href="{url}" style="text-decoration: none; color: #1E40AF; font-weight: bold; font-size: 12px;">🌐 {display_title}</a>'
            f'<div style="font-size: 10px; color: #475569; margin-top: 2px;">{domain}</div>'
            f"</div>"
        )
        return html_card
