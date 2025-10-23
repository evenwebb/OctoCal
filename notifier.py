"""Notification system using Apprise."""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from session_parser import Session


logger = logging.getLogger(__name__)


class Notifier:
    """Notification handler using Apprise."""

    def __init__(
        self,
        apprise_urls: List[str],
        enabled: bool = True,
        upcoming_hours: int = 1,
        notify_start: bool = True,
        notify_end: bool = True
    ):
        """
        Initialize notifier.

        Args:
            apprise_urls: List of Apprise notification URLs
            enabled: Whether notifications are enabled
            upcoming_hours: Hours before session to send upcoming notification
            notify_start: Whether to notify when session starts
            notify_end: Whether to notify when session ends
        """
        self.apprise_urls = apprise_urls
        self.enabled = enabled
        self.upcoming_hours = upcoming_hours
        self.notify_start = notify_start
        self.notify_end = notify_end
        self.apprise = None

        if self.enabled and self.apprise_urls:
            self._initialize_apprise()

    def _initialize_apprise(self) -> None:
        """Initialize Apprise instance."""
        try:
            import apprise
            self.apprise = apprise.Apprise()

            # Add all URLs
            for url in self.apprise_urls:
                if url:
                    self.apprise.add(url)

            logger.info(f"Initialized Apprise with {len(self.apprise_urls)} service(s)")
        except ImportError:
            logger.error(
                "Apprise not installed. Install it with: pip install apprise"
            )
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize Apprise: {e}")
            self.enabled = False

    def send_notification(self, title: str, body: str) -> bool:
        """
        Send a notification.

        Args:
            title: Notification title
            body: Notification body

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Notifications disabled, skipping")
            return False

        if not self.apprise:
            logger.warning("Apprise not initialized, cannot send notification")
            return False

        try:
            self.apprise.notify(
                title=title,
                body=body
            )
            logger.info(f"Sent notification: {title}")
            return True
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

    def notify_new_session(self, session: Session) -> bool:
        """
        Notify about a new session being scheduled.

        Args:
            session: Session object

        Returns:
            True if sent successfully
        """
        title = "⚡ New Free Electricity Session Scheduled"
        body = (
            f"Session: {session.session_str}\n"
            f"Start: {session.start_time.strftime('%A, %d %B %Y at %I:%M %p')}\n"
            f"End: {session.end_time.strftime('%I:%M %p')}\n"
            f"Duration: {session.duration}"
        )
        return self.send_notification(title, body)

    def notify_upcoming_session(self, session: Session, hours: int) -> bool:
        """
        Notify about an upcoming session.

        Args:
            session: Session object
            hours: Hours until session starts

        Returns:
            True if sent successfully
        """
        title = f"⏰ Free Electricity in {hours} hour{'s' if hours != 1 else ''}"
        body = (
            f"Session: {session.session_str}\n"
            f"Starts: {session.start_time.strftime('%A, %d %B %Y at %I:%M %p')}\n"
            f"Ends: {session.end_time.strftime('%I:%M %p')}\n"
            f"Get ready to use electricity!"
        )
        return self.send_notification(title, body)

    def notify_session_starting(self, session: Session) -> bool:
        """
        Notify that a session is starting now.

        Args:
            session: Session object

        Returns:
            True if sent successfully
        """
        title = "🎉 Free Electricity Starting NOW!"
        body = (
            f"Session: {session.session_str}\n"
            f"Ends: {session.end_time.strftime('%I:%M %p')}\n"
            f"Duration: {session.duration}\n"
            f"Start using electricity now!"
        )
        return self.send_notification(title, body)

    def notify_session_ending(self, session: Session) -> bool:
        """
        Notify that a session is ending now.

        Args:
            session: Session object

        Returns:
            True if sent successfully
        """
        title = "⏱️ Free Electricity Ending NOW"
        body = (
            f"Session: {session.session_str}\n"
            f"The free electricity period is ending.\n"
            f"Reduce your electricity usage."
        )
        return self.send_notification(title, body)

    def should_notify_upcoming(self, session: Session) -> bool:
        """
        Check if we should send upcoming notification for this session.

        Args:
            session: Session object

        Returns:
            True if notification should be sent
        """
        if not self.enabled:
            return False

        now = datetime.now()
        notification_time = session.start_time - timedelta(hours=self.upcoming_hours)

        # Check if we're within the notification window (5 minute tolerance)
        time_diff = abs((now - notification_time).total_seconds())
        return time_diff < 300  # 5 minutes in seconds

    def should_notify_start(self, session: Session) -> bool:
        """
        Check if we should send start notification for this session.

        Args:
            session: Session object

        Returns:
            True if notification should be sent
        """
        if not self.enabled or not self.notify_start:
            return False

        now = datetime.now()
        # Check if we're within 5 minutes of start time
        time_diff = abs((now - session.start_time).total_seconds())
        return time_diff < 300  # 5 minutes in seconds

    def should_notify_end(self, session: Session) -> bool:
        """
        Check if we should send end notification for this session.

        Args:
            session: Session object

        Returns:
            True if notification should be sent
        """
        if not self.enabled or not self.notify_end:
            return False

        now = datetime.now()
        # Check if we're within 5 minutes of end time
        time_diff = abs((now - session.end_time).total_seconds())
        return time_diff < 300  # 5 minutes in seconds
