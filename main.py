"""Main entry point for Octopus Energy free electricity scraper."""

import argparse
import logging
import os
import time
import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, List, Set
from octopus_scraper import OctopusScraper
from session_parser import SessionParser, Session
from ical_generator import ICalGenerator
from notifier import Notifier


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    if not Path(config_path).exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}. "
            f"Please copy config.yaml.example to config.yaml and configure it."
        )

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f) or {}

    # Ensure output directory exists
    output_dir = Path(get_config_value(config, 'ical.output_dir', './output'))
    output_dir.mkdir(parents=True, exist_ok=True)

    # Ensure log directory exists
    log_file = get_config_value(config, 'logging.log_file')
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    return config


def get_config_value(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Get configuration value using dot notation.

    Args:
        config: Configuration dictionary
        key: Configuration key in dot notation (e.g., 'scraper.url')
        default: Default value if key not found

    Returns:
        Configuration value or default
    """
    keys = key.split('.')
    value = config

    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
            if value is None:
                return default
        else:
            return default

    return value


class SessionTracker:
    """Tracks sessions and notifications that have been sent."""

    def __init__(self, state_file: Path):
        """
        Initialize session tracker.

        Args:
            state_file: Path to state file for persistence
        """
        self.state_file = state_file
        self.seen_sessions: Set[str] = set()
        self.notified_upcoming: Set[str] = set()
        self.notified_start: Set[str] = set()
        self.notified_end: Set[str] = set()
        self._load_state()

    def _load_state(self) -> None:
        """Load state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.seen_sessions = set(data.get('seen_sessions', []))
                    self.notified_upcoming = set(data.get('notified_upcoming', []))
                    self.notified_start = set(data.get('notified_start', []))
                    self.notified_end = set(data.get('notified_end', []))
                logging.debug(f"Loaded state: {len(self.seen_sessions)} sessions")
            except Exception as e:
                logging.error(f"Failed to load state: {e}")

    def _save_state(self) -> None:
        """Save state to file."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump({
                    'seen_sessions': list(self.seen_sessions),
                    'notified_upcoming': list(self.notified_upcoming),
                    'notified_start': list(self.notified_start),
                    'notified_end': list(self.notified_end),
                }, f, indent=2)
            logging.debug("Saved state")
        except Exception as e:
            logging.error(f"Failed to save state: {e}")

    def is_new_session(self, session_str: str) -> bool:
        """Check if session is new."""
        return session_str not in self.seen_sessions

    def mark_seen(self, session_str: str) -> None:
        """Mark session as seen."""
        self.seen_sessions.add(session_str)
        self._save_state()

    def should_notify_upcoming(self, session_str: str) -> bool:
        """Check if upcoming notification should be sent."""
        return session_str not in self.notified_upcoming

    def mark_notified_upcoming(self, session_str: str) -> None:
        """Mark upcoming notification as sent."""
        self.notified_upcoming.add(session_str)
        self._save_state()

    def should_notify_start(self, session_str: str) -> bool:
        """Check if start notification should be sent."""
        return session_str not in self.notified_start

    def mark_notified_start(self, session_str: str) -> None:
        """Mark start notification as sent."""
        self.notified_start.add(session_str)
        self._save_state()

    def should_notify_end(self, session_str: str) -> bool:
        """Check if end notification should be sent."""
        return session_str not in self.notified_end

    def mark_notified_end(self, session_str: str) -> None:
        """Mark end notification as sent."""
        self.notified_end.add(session_str)
        self._save_state()


class OctopusEnergyMonitor:
    """Main application class."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize monitor.

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = load_config(config_path)

        # Setup logging
        self._setup_logging()

        # Initialize components
        scraper_url = get_config_value(self.config, 'scraper.url', 'https://octopus.energy/free-electricity/')
        timezone = get_config_value(self.config, 'ical.timezone', 'GMT')
        apprise_urls = get_config_value(self.config, 'notifications.apprise_urls', [])
        apprise_urls = [url for url in apprise_urls if url]  # Filter empty strings

        # iCal alarm configuration
        alarms_enabled = get_config_value(self.config, 'ical.alarms.enabled', True)
        alarm_times = get_config_value(self.config, 'ical.alarms.times', [60, 15, 0])

        self.scraper = OctopusScraper(scraper_url)
        self.parser = SessionParser(timezone)
        self.ical_generator = ICalGenerator(timezone, alarms_enabled, alarm_times)
        self.notifier = Notifier(
            apprise_urls=apprise_urls,
            enabled=get_config_value(self.config, 'notifications.enabled', False),
            upcoming_hours=get_config_value(self.config, 'notifications.upcoming_hours', 1),
            notify_start=get_config_value(self.config, 'notifications.notify_start', True),
            notify_end=get_config_value(self.config, 'notifications.notify_end', True)
        )

        # Initialize session tracker
        output_dir = Path(get_config_value(self.config, 'ical.output_dir', './output'))
        state_file = output_dir / 'state.json'
        self.tracker = SessionTracker(state_file)

        # Store parsed sessions
        self.sessions: List[Session] = []

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level_str = get_config_value(self.config, 'logging.level', 'INFO').upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        log_file = get_config_value(self.config, 'logging.log_file', './output/octopus_scraper.log')

        # Create log directory
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

        logging.info("=" * 60)
        logging.info("Octopus Energy Free Electricity Monitor Started")
        logging.info("=" * 60)

    def scrape_sessions(self) -> bool:
        """
        Scrape and parse sessions from website.

        Returns:
            True if new sessions were found, False otherwise
        """
        logging.info("Scraping Octopus Energy website...")
        session_type, session_strings = self.scraper.scrape()

        if not session_strings:
            logging.info("No sessions found")
            return False

        logging.info(f"Found {len(session_strings)} session(s) (type: {session_type})")

        # Parse sessions
        new_sessions_found = False
        for session_str in session_strings:
            # Check if we've seen this session before
            if self.tracker.is_new_session(session_str):
                session = self.parser.parse(session_str)
                if session:
                    self.sessions.append(session)
                    self.tracker.mark_seen(session_str)
                    new_sessions_found = True
                    logging.info(f"New session: {session_str}")

                    # Notify about new session (only if it's a "next" session type)
                    if session_type == 'next' and self.notifier.enabled:
                        self.notifier.notify_new_session(session)
                else:
                    logging.warning(f"Failed to parse session: {session_str}")
            else:
                # Session already known, add to list if not already there
                session = self.parser.parse(session_str)
                if session and not any(s.session_str == session_str for s in self.sessions):
                    self.sessions.append(session)

        return new_sessions_found

    def update_ical(self) -> None:
        """Update iCal file with current sessions."""

        # Get cleanup settings
        cleanup_enabled = get_config_value(self.config, 'ical.cleanup.enabled', True)
        days_to_keep = get_config_value(self.config, 'ical.cleanup.days_to_keep', 7)

        now = datetime.now()

        # Filter sessions based on cleanup settings
        if cleanup_enabled:
            # Remove sessions older than days_to_keep
            cutoff_date = now - timedelta(days=days_to_keep)
            filtered_sessions = [s for s in self.sessions if s.end_time > cutoff_date]
            removed_count = len(self.sessions) - len(filtered_sessions)
            if removed_count > 0:
                logging.info(f"Removed {removed_count} session(s) older than {days_to_keep} days")
        else:
            # Keep all sessions (including past ones)
            filtered_sessions = self.sessions

        # Separate upcoming and recent past sessions for logging
        upcoming_sessions = [s for s in filtered_sessions if s.end_time > now]
        past_sessions = [s for s in filtered_sessions if s.end_time <= now]

        # Get iCal output path
        output_dir = Path(get_config_value(self.config, 'ical.output_dir', './output'))
        filename = get_config_value(self.config, 'ical.filename', 'octopus_free_electricity.ics')
        ical_output_path = output_dir / filename

        if not filtered_sessions:
            logging.info("No sessions to write to iCal - generating placeholder file")
            success = self.ical_generator.generate([], ical_output_path)
            if success:
                logging.info(f"iCal placeholder updated: {ical_output_path}")
            else:
                logging.error("Failed to generate placeholder iCal file")
            return
        
        logging.info(
            "Updating iCal file with %s session(s) (%s upcoming, %s recent past)...",
            len(filtered_sessions),
            len(upcoming_sessions),
            len(past_sessions)
        )
        
        success = self.ical_generator.generate(filtered_sessions, ical_output_path)
        if success:
            logging.info(f"iCal file updated: {ical_output_path}")
        else:
            logging.error("Failed to update iCal file")

    def check_notifications(self) -> None:
        """Check if any notifications should be sent."""
        if not self.notifier.enabled:
            return

        now = datetime.now()
        upcoming_hours = get_config_value(self.config, 'notifications.upcoming_hours', 1)

        for session in self.sessions:
            # Skip past sessions
            if session.end_time < now:
                continue

            # Check upcoming notification
            if (self.tracker.should_notify_upcoming(session.session_str) and
                self.notifier.should_notify_upcoming(session)):
                self.notifier.notify_upcoming_session(session, upcoming_hours)
                self.tracker.mark_notified_upcoming(session.session_str)

            # Check start notification
            if (self.tracker.should_notify_start(session.session_str) and
                self.notifier.should_notify_start(session)):
                self.notifier.notify_session_starting(session)
                self.tracker.mark_notified_start(session.session_str)

            # Check end notification
            if (self.tracker.should_notify_end(session.session_str) and
                self.notifier.should_notify_end(session)):
                self.notifier.notify_session_ending(session)
                self.tracker.mark_notified_end(session.session_str)

    def cleanup_old_sessions(self) -> None:
        """Remove sessions that have already ended."""
        now = datetime.now()
        before_count = len(self.sessions)
        self.sessions = [s for s in self.sessions if s.end_time > now]
        removed = before_count - len(self.sessions)
        if removed > 0:
            logging.info(f"Removed {removed} past session(s)")

    def run_scrape_cycle(self) -> None:
        """Run scraping cycle (checks website for new sessions)."""
        try:
            logging.info("Running scrape cycle...")
            # Scrape for new sessions
            self.scrape_sessions()

            # Update iCal file
            self.update_ical()

            # Cleanup old sessions
            self.cleanup_old_sessions()

        except Exception as e:
            logging.error(f"Error in scrape cycle: {e}", exc_info=True)

    def run_notification_cycle(self) -> None:
        """Run notification cycle (checks if notifications should be sent)."""
        try:
            # Check for notifications
            self.check_notifications()

            # Update iCal file (in case sessions changed)
            self.update_ical()

        except Exception as e:
            logging.error(f"Error in notification cycle: {e}", exc_info=True)

    def run(self) -> None:
        """Run the monitor continuously with separate scrape and notification intervals."""
        scrape_interval = get_config_value(self.config, 'scraper.check_interval_minutes', 60)
        notification_interval = get_config_value(self.config, 'notifications.check_interval_minutes', 5)

        logging.info("=" * 60)
        logging.info(f"Scrape interval: {scrape_interval} minutes")
        logging.info(f"Notification check interval: {notification_interval} minutes")
        logging.info("=" * 60)

        # Track time since last scrape
        minutes_since_scrape = scrape_interval  # Run scrape immediately on first iteration

        # Run initial scrape
        self.run_scrape_cycle()

        while True:
            # Sleep for notification check interval
            sleep_seconds = notification_interval * 60
            logging.debug(f"Sleeping for {notification_interval} minutes...")
            time.sleep(sleep_seconds)

            minutes_since_scrape += notification_interval

            # Check if it's time to scrape
            if minutes_since_scrape >= scrape_interval:
                self.run_scrape_cycle()
                minutes_since_scrape = 0
            else:
                # Only run notification checks
                logging.debug(f"Running notification cycle ({minutes_since_scrape}/{scrape_interval} min until next scrape)...")
                self.run_notification_cycle()


def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Octopus Energy Free Electricity Scraper'
    )
    parser.add_argument(
        '--config',
        default=None,
        help='Path to configuration file (default: auto-detect)'
    )
    parser.add_argument(
        '--single-run',
        action='store_true',
        help='Run once and exit (useful for cron/GitHub Actions)'
    )
    args = parser.parse_args()

    # Determine config file
    config_path = args.config
    if config_path is None:
        # Auto-detect GitHub Actions or CI environment
        if os.getenv('GITHUB_ACTIONS') or os.getenv('CI'):
            config_path = 'config.yaml.example'
            print(f"GitHub Actions/CI detected - using {config_path}")
        else:
            config_path = 'config.yaml'

    try:
        monitor = OctopusEnergyMonitor(config_path)

        if args.single_run:
            # Run once and exit
            logging.info("Running in single-run mode...")
            monitor.run_scrape_cycle()
            logging.info("Single run completed successfully")
        else:
            # Run continuously
            monitor.run()

    except KeyboardInterrupt:
        logging.info("Shutting down...")
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
    