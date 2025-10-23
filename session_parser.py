"""Parser for Octopus Energy session strings."""

import re
import logging
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class Session:
    """Represents a free electricity session."""

    session_str: str
    start_time: datetime
    end_time: datetime

    @property
    def duration(self) -> timedelta:
        """Get session duration."""
        return self.end_time - self.start_time


class SessionParser:
    """Parser for session strings like '12-2pm, Saturday 4th October'."""

    def __init__(self, timezone: str = 'GMT'):
        """
        Initialize parser.

        Args:
            timezone: Timezone for sessions (currently assumes GMT)
        """
        self.timezone = timezone

    def parse(self, session_str: str) -> Optional[Session]:
        """
        Parse a session string to extract start and end times.

        Args:
            session_str: Session string (e.g., '12-2pm, Saturday 4th October')

        Returns:
            Session object or None if parsing fails
        """
        parts = session_str.split(',')
        if len(parts) != 2:
            logger.warning(f"Invalid session format: {session_str}")
            return None

        time_part = parts[0].strip()  # e.g., '12-2pm'
        date_part = parts[1].strip()  # e.g., 'Saturday 4th October'

        # Parse times
        start_time = self._parse_start_time(time_part, date_part)
        end_time = self._parse_end_time(time_part, date_part)

        if start_time is None or end_time is None:
            logger.warning(f"Failed to parse times for session: {session_str}")
            return None

        return Session(
            session_str=session_str,
            start_time=start_time,
            end_time=end_time
        )

    def _parse_start_time(self, time_part: str, date_part: str) -> Optional[datetime]:
        """Parse start time from session string."""
        # Extract start time (before the dash)
        start_time_str = time_part.split('-')[0].strip()
        return self._parse_datetime(start_time_str, date_part)

    def _parse_end_time(self, time_part: str, date_part: str) -> Optional[datetime]:
        """Parse end time from session string."""
        # Extract end time (after the dash)
        end_time_str = time_part.split('-')[1].strip()
        return self._parse_datetime(end_time_str, date_part)

    def _parse_datetime(self, time_str: str, date_part: str) -> Optional[datetime]:
        """
        Parse a datetime from time and date strings.

        Args:
            time_str: Time string (e.g., '12pm' or '2pm')
            date_part: Date string (e.g., 'Saturday 4th October')

        Returns:
            datetime object or None if parsing fails
        """
        # Parse time
        match = re.match(r'(\d+)(am|pm)?', time_str.lower())
        if not match:
            return None

        hour = int(match.group(1))
        ampm = match.group(2) or ('pm' if hour == 12 else 'am')

        # Convert to 24-hour format
        if ampm == 'pm' and hour != 12:
            hour += 12
        elif ampm == 'am' and hour == 12:
            hour = 0

        minute = 0  # Assume on the hour

        # Parse date
        # Remove ordinal suffix from date
        date_part_clean = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_part, flags=re.IGNORECASE)

        # Get current year and try to parse
        current_year = datetime.now().year
        date_str_full = f"{date_part_clean} {current_year}"

        try:
            date_obj = datetime.strptime(date_str_full, '%A %d %B %Y')
        except ValueError:
            # Try next year if the date is in the past
            try:
                date_str_full = f"{date_part_clean} {current_year + 1}"
                date_obj = datetime.strptime(date_str_full, '%A %d %B %Y')
            except ValueError:
                logger.error(f"Failed to parse date: {date_part}")
                return None

        # Combine into datetime
        result = date_obj.replace(hour=hour, minute=minute)

        # If the datetime is in the past, try next year
        if result < datetime.now():
            try:
                date_str_full = f"{date_part_clean} {current_year + 1}"
                date_obj = datetime.strptime(date_str_full, '%A %d %B %Y')
                result = date_obj.replace(hour=hour, minute=minute)
            except ValueError:
                pass

        return result

    def get_upcoming_notification_time(
        self, session: Session, hours_before: int
    ) -> Optional[datetime]:
        """
        Get the time for upcoming notification.

        Args:
            session: Session object
            hours_before: Hours before session to notify

        Returns:
            datetime for notification or None if already passed
        """
        notification_time = session.start_time - timedelta(hours=hours_before)
        if notification_time <= datetime.now():
            return None
        return notification_time
