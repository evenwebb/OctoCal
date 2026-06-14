"""History logger for Octopus Energy free electricity sessions."""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Set
from session_parser import Session


logger = logging.getLogger(__name__)


class HistoryLogger:
    """Logger for tracking session history and calculating statistics."""

    def __init__(self, history_file: Path):
        """
        Initialize history logger.

        Args:
            history_file: Path to history JSON file
        """
        self.history_file = history_file
        self.history: Dict[str, Any] = {"sessions": [], "last_updated": None}
        self._session_ids: Set[str] = set()  # Cache for O(1) lookups
        self._dirty = False  # Track if history needs saving
        self._load_history()

    def _load_history(self) -> None:
        """Load history from JSON file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
                # Ensure sessions list exists
                if "sessions" not in self.history:
                    self.history["sessions"] = []
                # Build session ID cache for O(1) lookups
                self._session_ids = {
                    self._get_session_id_from_dict(s) for s in self.history["sessions"]
                }
                logger.debug(f"Loaded history: {len(self.history['sessions'])} sessions")
            except Exception as e:
                logger.error(f"Failed to load history: {e}")
                self.history = {"sessions": [], "last_updated": None}
                self._session_ids = set()  # Reset cache on error

    def _save_history(self) -> None:
        """Save history to JSON file."""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            self.history["last_updated"] = datetime.now().isoformat()
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
            self._dirty = False  # Mark as saved
            logger.debug("Saved history")
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def flush(self) -> None:
        """
        Flush any pending history saves.
        Call this at the end of processing to ensure all changes are saved.
        """
        if self._dirty:
            self._save_history()

    def _get_session_id(self, session: Session) -> str:
        """
        Generate unique identifier for a session.

        Args:
            session: Session object

        Returns:
            Unique session identifier string
        """
        # Use code if available (more reliable), otherwise fall back to session_str + start_time
        if session.code:
            return session.code
        return f"{session.session_str}|{session.start_time.isoformat()}"

    def _session_exists(self, session: Session) -> bool:
        """
        Check if session already exists in history.

        Args:
            session: Session object

        Returns:
            True if session exists, False otherwise
        """
        session_id = self._get_session_id(session)
        return session_id in self._session_ids  # O(1) lookup instead of O(n)

    def _get_session_id_from_dict(self, session_dict: Dict[str, Any]) -> str:
        """Get session ID from dictionary representation."""
        # Use code if available (more reliable), otherwise fall back to session_str + start_time
        code = session_dict.get("code")
        if code:
            return code
        session_str = session_dict.get("session_str", "")
        start_time = session_dict.get("start_time", "")
        return f"{session_str}|{start_time}"

    def add_session(self, session: Session) -> bool:
        """
        Add a session to history if it doesn't already exist.

        Args:
            session: Session object

        Returns:
            True if session was added, False if it already existed
        """
        if self._session_exists(session):
            logger.debug(f"Session already in history: {session.session_str}")
            return False

        session_dict = {
            "session_str": session.session_str,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat(),
            "duration_hours": session.duration.total_seconds() / 3600,
            "discovered_at": datetime.now().isoformat()
        }
        
        # Add code if available (from API)
        if session.code:
            session_dict["code"] = session.code

        session_id = self._get_session_id(session)
        self.history["sessions"].append(session_dict)
        self._session_ids.add(session_id)  # Update cache
        self._dirty = True  # Mark as needing save, but don't save yet
        logger.info(f"Added session to history: {session.session_str}")
        return True

    def get_upcoming_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all upcoming sessions (end_time > now).

        Returns:
            List of upcoming session dictionaries
        """
        now = datetime.now()
        upcoming = []
        for session_dict in self.history["sessions"]:
            end_time_str = session_dict.get("end_time")
            if end_time_str:
                try:
                    end_time = datetime.fromisoformat(end_time_str)
                    if end_time > now:
                        upcoming.append(session_dict)
                except ValueError:
                    logger.warning(f"Invalid end_time format: {end_time_str}")
        return sorted(upcoming, key=lambda x: x.get("start_time", ""))

    def get_historic_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all historic sessions (end_time <= now).

        Returns:
            List of historic session dictionaries
        """
        now = datetime.now()
        historic = []
        for session_dict in self.history["sessions"]:
            end_time_str = session_dict.get("end_time")
            if end_time_str:
                try:
                    end_time = datetime.fromisoformat(end_time_str)
                    if end_time <= now:
                        historic.append(session_dict)
                except ValueError:
                    logger.warning(f"Invalid end_time format: {end_time_str}")
        return sorted(historic, key=lambda x: x.get("start_time", ""), reverse=True)

    def export_upcoming_sessions(self, output_file: Path) -> None:
        """
        Export upcoming sessions to a separate JSON file for web display.

        Args:
            output_file: Path to output JSON file
        """
        upcoming = self.get_upcoming_sessions()
        # Remove discovered_at field for lighter JSON
        upcoming_clean = [
            {
                "session_str": s["session_str"],
                "start_time": s["start_time"],
                "end_time": s["end_time"],
                "duration_hours": s["duration_hours"]
            }
            for s in upcoming
        ]

        data = {
            "upcoming_sessions": upcoming_clean,
            "last_updated": datetime.now().isoformat()
        }

        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Exported {len(upcoming_clean)} upcoming sessions to {output_file}")
        except Exception as e:
            logger.error(f"Failed to export upcoming sessions: {e}")
