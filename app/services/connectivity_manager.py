"""
Connectivity Manager - Handles network status and fallback modes for Raspberry Pi
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import socket


class ConnectivityManager:
    """
    Manages internet connectivity detection and fallback mode for traffic system.

    When the Raspberry Pi loses internet connection or vehicle detection fails,
    this manager handles the transition to safe offline mode.
    """

    def __init__(self, check_interval: int = 30):
        """
        Initialize connectivity manager

        Args:
            check_interval (int): Seconds between connectivity checks (default: 30)
        """
        self.logger = logging.getLogger(__name__)
        self.check_interval = check_interval
        self.is_online = True
        self.last_check_time = None
        self.connection_status_history = []
        self.max_history = 10

    async def check_internet_connection(self, test_hosts: Optional[list] = None) -> bool:
        """
        Check if internet connection is available.

        Args:
            test_hosts (list, optional): Hosts to test connectivity.
                                        Defaults to [Google DNS, Cloudflare DNS]

        Returns:
            bool: True if internet is available, False otherwise
        """
        if test_hosts is None:
            test_hosts = ["8.8.8.8", "1.1.1.1"]  # Google DNS, Cloudflare DNS

        for host in test_hosts:
            try:
                # Try to connect to the host on DNS port
                socket.create_connection((host, 53), timeout=2)
                self.logger.info(f"✅ Internet connection available (reached {host})")
                return True
            except (socket.timeout, socket.error):
                continue

        self.logger.warning("❌ No internet connection detected")
        return False

    async def check_backend_connectivity(self, backend_url: str) -> bool:
        """
        Check if backend server is reachable.

        Args:
            backend_url (str): Backend server URL to check

        Returns:
            bool: True if backend is reachable, False otherwise
        """
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{backend_url}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        self.logger.info(f"✅ Backend server reachable: {backend_url}")
                        return True
        except Exception as e:
            self.logger.warning(f"❌ Backend unreachable: {str(e)}")
            return False

        return False

    async def check_vehicle_detection_system(self, detection_endpoint: str) -> bool:
        """
        Check if vehicle detection system (via RFID/sensors) is responding.

        Args:
            detection_endpoint (str): Vehicle detection service endpoint

        Returns:
            bool: True if detection system is responsive, False otherwise
        """
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    detection_endpoint,
                    timeout=aiohttp.ClientTimeout(total=3)
                ) as response:
                    if response.status == 200:
                        self.logger.info("✅ Vehicle detection system responsive")
                        return True
        except Exception as e:
            self.logger.warning(f"❌ Vehicle detection system unresponsive: {str(e)}")
            return False

        return False

    async def update_connectivity_status(
        self,
        backend_url: Optional[str] = None,
        detection_endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive connectivity check updating overall status.

        Args:
            backend_url (str, optional): Backend server URL to check
            detection_endpoint (str, optional): Vehicle detection endpoint

        Returns:
            dict: Current connectivity status
        """
        internet_available = await self.check_internet_connection()
        backend_available = False
        detection_available = False

        if internet_available and backend_url:
            backend_available = await self.check_backend_connectivity(backend_url)

        if internet_available and detection_endpoint:
            detection_available = await self.check_vehicle_detection_system(
                detection_endpoint
            )

        # Overall status: online only if internet AND backend available
        self.is_online = internet_available and (backend_available or not backend_url)

        status = {
            "is_online": self.is_online,
            "internet_available": internet_available,
            "backend_available": backend_available,
            "detection_available": detection_available,
            "timestamp": self._get_current_time(),
            "mode": "online" if self.is_online else "offline_fallback"
        }

        # Store in history
        self._add_to_history(status)

        if not self.is_online:
            self.logger.warning(
                "⚠️ CONNECTIVITY LOST - Switching to offline/fallback mode. "
                f"Internet: {internet_available}, "
                f"Backend: {backend_available}, "
                f"Detection: {detection_available}"
            )
        else:
            self.logger.info("✅ All systems online - Using adaptive traffic timing")

        return status

    def get_connectivity_status(self) -> Dict[str, Any]:
        """
        Get current connectivity status without performing checks.

        Returns:
            dict: Latest stored connectivity status
        """
        return {
            "is_online": self.is_online,
            "timestamp": self._get_current_time(),
            "mode": "online" if self.is_online else "offline_fallback",
            "history_available": len(self.connection_status_history)
        }

    def get_connectivity_history(self) -> list:
        """
        Get connectivity status history.

        Returns:
            list: Recent connectivity status records
        """
        return self.connection_status_history

    def _add_to_history(self, status: Dict[str, Any]):
        """Store status in history, maintaining max_history limit"""
        self.connection_status_history.append(status)
        if len(self.connection_status_history) > self.max_history:
            self.connection_status_history.pop(0)

    @staticmethod
    def _get_current_time() -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_fallback_mode_info(self) -> dict:
        """
        Get information about fallback mode activation.

        Returns:
            dict: Fallback mode details and behavior
        """
        return {
            "fallback_mode_active": not self.is_online,
            "reason": "Internet/detection connectivity lost" if not self.is_online else "N/A",
            "behavior_description": (
                "All traffic lights receive maximum green time (90s) per lane. "
                "No real-time vehicle detection. "
                "Equal distribution ensures safe traffic flow."
            ),
            "safety_level": "High",
            "expected_behavior": [
                "All lanes get 90s green time",
                "5s yellow time per lane",
                "140s total cycle time per lane",
                "No adaptive optimization"
            ],
            "timestamp": self._get_current_time()
        }
