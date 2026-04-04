"""
livekit_manager.py
Handles LiveKit room management, token generation, and
room/participant event hooks outside the main agent loop.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class LiveKitManager:
    """
    Utility class for LiveKit room management and access token generation.
    Used for administrative tasks and testing; the production agent lifecycle
    is managed by the livekit-agents SDK in main.py.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("LIVEKIT_API_KEY")
        self.api_secret = os.getenv("LIVEKIT_API_SECRET")
        self.livekit_url = os.getenv("LIVEKIT_URL", "wss://your-project.livekit.cloud")

        if not self.api_key or not self.api_secret:
            raise EnvironmentError(
                "LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set in .env"
            )
        logger.info("LiveKitManager initialised | url=%s", self.livekit_url)

    def generate_token(
        self,
        room_name: str,
        participant_identity: str,
        participant_name: Optional[str] = None,
        ttl_seconds: int = 3600,
    ) -> str:
        """
        Generate a LiveKit access token for a participant.

        Parameters
        ----------
        room_name : str
            The room the participant will join.
        participant_identity : str
            Unique identity string for the participant.
        participant_name : str, optional
            Display name shown in the room.
        ttl_seconds : int
            Token time-to-live in seconds (default 1 hour).

        Returns
        -------
        str
            Signed JWT access token.
        """
        try:
            from livekit.api import AccessToken, VideoGrants

            token = (
                AccessToken(self.api_key, self.api_secret)
                .with_identity(participant_identity)
                .with_name(participant_name or participant_identity)
                .with_grants(
                    VideoGrants(
                        room_join=True,
                        room=room_name,
                        can_publish=True,
                        can_subscribe=True,
                    )
                )
                .with_ttl(ttl_seconds)
                .to_jwt()
            )
            logger.info(
                "Token generated | room=%s | identity=%s | ttl=%ds",
                room_name,
                participant_identity,
                ttl_seconds,
            )
            return token

        except ImportError as exc:
            raise ImportError(
                "livekit package not installed. Run: pip install livekit"
            ) from exc

    async def list_rooms(self) -> list[dict]:
        """List all active rooms via LiveKit server API."""
        try:
            from livekit.api import LiveKitAPI

            async with LiveKitAPI(
                url=self.livekit_url,
                api_key=self.api_key,
                api_secret=self.api_secret,
            ) as api:
                rooms = await api.room.list_rooms()
                result = [
                    {
                        "name": r.name,
                        "num_participants": r.num_participants,
                        "creation_time": r.creation_time,
                    }
                    for r in rooms.rooms
                ]
                logger.info("Found %d active rooms.", len(result))
                return result
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to list rooms: %s", exc)
            return []

    async def delete_room(self, room_name: str) -> bool:
        """Delete a LiveKit room by name."""
        try:
            from livekit.api import LiveKitAPI

            async with LiveKitAPI(
                url=self.livekit_url,
                api_key=self.api_key,
                api_secret=self.api_secret,
            ) as api:
                await api.room.delete_room(room=room_name)
                logger.info("Room deleted: %s", room_name)
                return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to delete room %s: %s", room_name, exc)
            return False
