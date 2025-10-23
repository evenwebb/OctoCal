"""Scraper for Octopus Energy free electricity sessions."""

import re
import logging
from typing import List, Optional, Tuple
import requests


logger = logging.getLogger(__name__)


class OctopusScraper:
    """Scraper for Octopus Energy free electricity page."""

    def __init__(self, url: str):
        """
        Initialize scraper.

        Args:
            url: URL of the Octopus Energy free electricity page
        """
        self.url = url

    def fetch_page_content(self) -> Optional[str]:
        """
        Fetch HTML content from the page.

        Returns:
            HTML content as string, or None if fetch fails
        """
        try:
            response = requests.get(self.url, timeout=30)
            response.raise_for_status()
            logger.debug(f"Fetched page content: {len(response.text)} bytes")
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching page: {e}")
            return None

    def extract_sessions(self, html_content: str) -> Tuple[Optional[str], List[str]]:
        """
        Extract session information from HTML content.

        Args:
            html_content: HTML content to parse

        Returns:
            Tuple of (session_type, sessions_list)
            session_type: 'next', 'last', or None
            sessions_list: List of session strings
        """
        sessions = []
        session_type = None

        # Try to find "Next Sessions:" first (for multiple)
        match = re.search(r'Next\s+Sessions?:', html_content, re.IGNORECASE)
        if match:
            session_type = 'next'
            start_pos = match.end()
            # Find the end of this section (next heading or double newline or end)
            end_match = re.search(r'<h\d[^>]*>', html_content[start_pos:], re.IGNORECASE)
            end_pos = end_match.start() if end_match else len(html_content) - start_pos
            block = html_content[start_pos:start_pos + end_pos]

            # Replace <br> with \n to handle line breaks
            block = re.sub(r'<br\s*/?>', '\n', block, flags=re.IGNORECASE)
            # Remove HTML tags
            text_block = re.sub(r'<[^>]+>', '', block).strip()

            # Split by newlines or common separators to avoid concatenation
            potential_sessions = re.split(r'\n|Next|Power Tower', text_block)
            for part in potential_sessions:
                part = part.strip()
                if part:
                    # Use regex findall to extract valid session strings from each part
                    found = re.findall(
                        r'\d+(?:am|pm)?-\d+(?:am|pm)?,\s*\w+\s*\d+(?:st|nd|rd|th)?\s*\w+',
                        part,
                        re.IGNORECASE
                    )
                    sessions.extend(found)
        else:
            # Check for "Last Session:"
            match = re.search(r'Last\s+Session:', html_content, re.IGNORECASE)
            if match:
                session_type = 'last'
                start_pos = match.end()
                # Find the end (next heading, "Next Power Tower", or end)
                end_match = re.search(
                    r'<h\d[^>]*>|Next Power Tower',
                    html_content[start_pos:],
                    re.IGNORECASE
                )
                end_pos = end_match.start() if end_match else len(html_content) - start_pos
                block = html_content[start_pos:start_pos + end_pos]

                # Replace <br> with \n
                block = re.sub(r'<br\s*/?>', '\n', block, flags=re.IGNORECASE)
                # Remove HTML tags
                text_block = re.sub(r'<[^>]+>', '', block).strip()

                # Extract session string
                found = re.findall(
                    r'\d+(?:am|pm)?-\d+(?:am|pm)?,\s*\w+\s*\d+(?:st|nd|rd|th)?\s*\w+',
                    text_block,
                    re.IGNORECASE
                )
                sessions.extend(found)
            else:
                # Fallback to old single session logic
                match = re.search(
                    r'Next(?:\s+\w+)*\s+Sessions?:\s*([^<\n]+)',
                    html_content,
                    re.IGNORECASE
                )
                if match:
                    session_type = 'next'
                    session_raw = match.group(1).strip()
                    session_clean = re.sub(r'<[^>]+>', '', session_raw)
                    # Split if multiple are concatenated
                    found = re.findall(
                        r'\d+(?:am|pm)?-\d+(?:am|pm)?,\s*\w+\s*\d+(?:st|nd|rd|th)?\s*\w+',
                        session_clean,
                        re.IGNORECASE
                    )
                    sessions.extend(found)

        # Remove duplicates and clean
        sessions = list(set(sessions))
        logger.info(f"Extracted {len(sessions)} session(s) (type: {session_type})")

        return session_type, sessions

    def scrape(self) -> Tuple[Optional[str], List[str]]:
        """
        Scrape the page and extract sessions.

        Returns:
            Tuple of (session_type, sessions_list)
        """
        html_content = self.fetch_page_content()
        if html_content is None:
            return None, []

        return self.extract_sessions(html_content)
