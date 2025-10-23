"""iCal file generator for Octopus Energy free electricity sessions."""

import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List
from icalendar import Calendar, Event, Alarm, vText
from session_parser import Session


logger = logging.getLogger(__name__)


class ICalGenerator:
    """Generator for iCal calendar files."""

    def __init__(self, timezone: str = 'GMT', alarms_enabled: bool = True, alarm_times: List[int] = None):
        """
        Initialize iCal generator.

        Args:
            timezone: Timezone for events
            alarms_enabled: Whether to add alarms to events
            alarm_times: List of minutes before event to add alarms (e.g., [60, 15, 0])
        """
        self.timezone = timezone
        self.alarms_enabled = alarms_enabled
        self.alarm_times = alarm_times or [60, 15, 0]

    def generate(self, sessions: List[Session], output_path: Path) -> bool:
        """
        Generate iCal file from sessions.

        Args:
            sessions: List of Session objects
            output_path: Path to save iCal file

        Returns:
            True if successful, False otherwise
        """
        if not sessions:
            logger.warning("No sessions to generate iCal file")
            return False

        # Create calendar
        cal = Calendar()
        cal.add('prodid', '-//Octopus Energy Free Electricity//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('x-wr-calname', vText('Octopus Free Electricity'))
        cal.add('x-wr-timezone', vText(self.timezone))
        cal.add('x-wr-caldesc', vText('Free electricity sessions from Octopus Energy'))

        # Add events for each session
        for session in sessions:
            event = Event()

            # Set event properties
            event.add('summary', vText('Octopus Free Electricity'))
            event.add('dtstart', session.start_time)
            event.add('dtend', session.end_time)
            event.add('dtstamp', datetime.now())

            # Generate unique UID based on session string and start time
            uid = f"{session.start_time.strftime('%Y%m%d%H%M')}@octopus.energy"
            event.add('uid', uid)

            # Add description
            description = (
                f"Free electricity session: {session.session_str}\n"
                f"Duration: {session.duration}\n"
                f"Make sure to use electricity during this period!"
            )
            event.add('description', vText(description))

            # Add location
            event.add('location', vText('UK'))

            # Add status and other properties
            event.add('status', vText('CONFIRMED'))
            event.add('transp', vText('TRANSPARENT'))

            # Add categories
            event.add('categories', vText('Free Electricity,Octopus Energy'))

            # Add alarms if enabled
            if self.alarms_enabled and self.alarm_times:
                for minutes in self.alarm_times:
                    alarm = Alarm()
                    alarm.add('action', vText('DISPLAY'))

                    # Custom description based on timing
                    if minutes == 0:
                        alarm_desc = 'Free electricity session starting NOW!'
                    elif minutes < 60:
                        alarm_desc = f'Free electricity session in {minutes} minutes!'
                    else:
                        hours = minutes // 60
                        alarm_desc = f'Free electricity session in {hours} hour{"s" if hours > 1 else ""}!'

                    alarm.add('description', vText(alarm_desc))

                    # Set trigger as timedelta (negative for before the event)
                    if minutes == 0:
                        trigger = timedelta(0)  # At start time
                    else:
                        trigger = -timedelta(minutes=minutes)  # Negative = before event

                    alarm.add('trigger', trigger)

                    event.add_component(alarm)
                    logger.debug(f"Added {minutes}-minute alarm for session: {session.session_str}")

            # Add event to calendar
            cal.add_component(event)
            logger.debug(f"Added event for session: {session.session_str}")

        # Write to file
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(cal.to_ical())
            logger.info(f"Generated iCal file: {output_path} ({len(sessions)} event(s))")
            return True
        except Exception as e:
            logger.error(f"Failed to write iCal file: {e}")
            return False

    def update_or_create(
        self, sessions: List[Session], output_path: Path
    ) -> bool:
        """
        Update existing iCal file or create new one.

        This will replace the entire calendar file with new sessions.

        Args:
            sessions: List of Session objects
            output_path: Path to save iCal file

        Returns:
            True if successful, False otherwise
        """
        return self.generate(sessions, output_path)
