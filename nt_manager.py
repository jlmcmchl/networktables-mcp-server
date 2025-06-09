#!/usr/bin/env python3
"""
NetworkTables Manager Module

This module provides a high-level interface for managing NetworkTables connections and operations
in FRC robotics applications. It handles connection management, topic subscription, value reading/writing,
and real-time monitoring of NetworkTables data.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional
import threading
from dataclasses import dataclass, asdict
from typing_extensions import Buffer

import ntcore

logger = logging.getLogger(__name__)


@dataclass
class ConnectionConfig:
    """NetworkTables connection configuration"""

    team_number: Optional[int] = None
    server_ip: Optional[str] = None
    server_port: int = 5810
    identity: str = "MCP-NT-Server"


@dataclass
class ValueRecord:
    """NetworkTables value record"""

    valid: bool
    last_change: str
    server_time: str
    local_time: str
    type: str
    size: int
    value: Any

    def __init__(self, value: ntcore.ValueEventData):
        self.valid = value.value.isValid()
        self.last_change = time.strftime(
            "%Y-%m-%d %H:%M:%S.%f",
            time.localtime(value.value.last_change() / 1e6),
        )
        self.server_time = time.strftime(
            "%Y-%m-%d %H:%M:%S.%f",
            time.localtime(value.value.server_time() / 1e6),
        )
        self.local_time = time.strftime(
            "%Y-%m-%d %H:%M:%S.%f",
            time.localtime(value.value.time() / 1e6),
        )
        self.type = value.topic.getTypeString()
        self.size = value.value.size()
        self.value = value.value.value()


class NetworkTablesManager:
    """Manages NetworkTables connection and operations"""

    def __init__(self):
        self.inst = ntcore.NetworkTableInstance.getDefault()
        self.connected = False
        self.config = ConnectionConfig()
        self.topics: Dict[str, ntcore.TopicInfo] = {}
        self.values: Dict[str, ValueRecord] = {}
        self.subscribers: Dict[str, ntcore.NetworkTableEntry] = {}
        self.publishers: Dict[str, ntcore.NetworkTableEntry] = {}
        self.connection_lock = threading.Lock()
        self.time_sync_data = ntcore.TimeSyncEventData(0, 0, False)

        self.inst.configPythonLogging(
            min=ntcore.NetworkTableInstance.LogLevel.kLogDebug4,
            max=ntcore.NetworkTableInstance.LogLevel.kLogCritical,
            name="ntcore",
        )

        # Set up connection listener
        self.inst.addListener(
            [""],
            ntcore.EventFlags.kTopic | ntcore.EventFlags.kImmediate,
            self._topic_listener,
        )
        self.inst.addListener(
            [""],
            ntcore.EventFlags.kValueAll,
            self._value_listener,
        )
        self.inst.addConnectionListener(True, self._connection_listener)
        self.inst.addTimeSyncListener(True, self._time_sync_listener)

    def _connection_listener(self, event: ntcore.Event):
        """Handle connection state changes"""
        data: ntcore.ConnectionInfo = event.data
        if event.flags & ntcore.EventFlags.kConnected:
            logger.info("Connected to NetworkTables server")
            self.connected = True
        else:
            logger.warning("Disconnected from NetworkTables server")
            self.connected = False

    def _time_sync_listener(self, event: ntcore.Event):
        """Handle time sync state changes"""

        if not event.flags & ntcore.EventFlags.kTimeSync:
            return

        data: ntcore.TimeSyncEventData = event.data
        self.time_sync_data = data

        if data.valid:
            logger.info(
                f"Time sync established: ping: {data.rtt2} drift: {data.serverTimeOffset}"
            )
        else:
            logger.warning("Time sync lost")

    def _topic_listener(self, event: ntcore.Event):
        """Handle topic state changes"""

        data: ntcore.TopicInfo = event.data
        if event.flags & ntcore.EventFlags.kPublish:
            self.topics[data.name] = data
        elif event.flags & ntcore.EventFlags.kUnpublish:
            self.topics.pop(data.name, None)
        elif event.flags & ntcore.EventFlags.kProperties:
            self.topics[data.name].properties = data.properties

    def _value_listener(self, event: ntcore.Event):
        """Handle value changes"""
        data: ntcore.ValueEventData = event.data
        self.values[data.topic.getName()] = ValueRecord(data)

    def configure_connection(
        self,
        team_number: Optional[int] = None,
        server_ip: Optional[str] = None,
        server_port: int = 5810,
        identity: str = "MCP-NT-Server",
    ):
        """Configure NetworkTables connection"""
        with self.connection_lock:
            self.config.team_number = team_number
            self.config.server_ip = server_ip
            self.config.server_port = server_port
            self.config.identity = identity

            if server_ip:
                self.inst.setServer(server_ip, server_port)
            elif team_number:
                self.inst.setServerTeam(team_number)

            self.inst.stopClient()
            self.inst.startClient4(identity)

    def disconnect(self):
        """Disconnect from NetworkTables"""
        with self.connection_lock:
            self.inst.stopClient()
            self.connected = False

    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection information"""
        connections = self.inst.getConnections()
        return {
            "connected": self.connected,
            "connection_count": len(connections),
            "connections": [
                {
                    "remote_id": conn.remote_id,
                    "remote_ip": conn.remote_ip,
                    "remote_port": conn.remote_port,
                    "protocol_version": conn.protocol_version,
                    "last_updated": conn.last_update,
                }
                for conn in connections
            ],
            "config": asdict(self.config),
        }

    def get_time_sync_info(self) -> Dict[str, Any]:
        """Get current time sync information"""
        return {
            "valid": self.time_sync_data.valid,
            "ping": self.time_sync_data.rtt2,
            "drift": self.time_sync_data.serverTimeOffset,
        }

    def list_topics(self, topic_prefix: Optional[str] = None) -> List[str]:
        """List all available topics, optionally filtered"""

        return [
            name
            for name in self.topics.keys()
            if topic_prefix is None or name.startswith(topic_prefix)
        ]

    def get_topic_info(self, topic_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a topic"""

        if topic_name not in self.topics:
            return None

        topic = self.topics[topic_name]
        return {
            "name": topic.name,
            "type": topic.type_str,
            "properties": json.loads(topic.properties),
        }

    def get_value(self, topic_name: str) -> ValueRecord:
        """Get value from a NetworkTables topic"""

        # Get fresh value
        return self.values.get(topic_name)

    def get_multiple_values(self, topic_names: List[str]) -> Dict[str, ValueRecord]:
        """Get values from multiple topics efficiently"""
        return {
            topic_name: self.values[topic_name]
            for topic_name in topic_names
            if topic_name in self.values
        }

    def set_value(self, topic_name: str, value: Any) -> bool:
        """Set value to a NetworkTables topic"""
        try:
            entry = self.inst.getEntry(topic_name)

            # Convert value to appropriate NT type
            if isinstance(value, bool):
                return entry.setBoolean(value)
            elif isinstance(value, int):
                return entry.setInteger(value)
            elif isinstance(value, float):
                return entry.setDouble(value)
            elif isinstance(value, str):
                return entry.setString(value)
            elif isinstance(value, list):
                # Handle arrays based on content type
                if all(isinstance(x, bool) for x in value):
                    return entry.setBooleanArray(value)
                elif all(isinstance(x, int) for x in value):
                    return entry.setIntegerArray(value)
                elif all(isinstance(x, float) for x in value):
                    return entry.setDoubleArray(value)
                elif all(isinstance(x, str) for x in value):
                    return entry.setStringArray(value)
            elif isinstance(value, Buffer):
                return entry.setRaw(value)

            logger.error(
                f"Inapplicable value type for topic {topic_name}: {type(value)}"
            )
            return False

        except Exception as e:
            logger.error(f"Error setting value for topic {topic_name}: {e}")
            return False

    def set_multiple_values(self, updates: Dict[str, Any]) -> Dict[str, bool]:
        """Set multiple values efficiently"""
        results = {}

        for topic_name, value in updates.items():
            results[topic_name] = self.set_value(topic_name, value)

        return results

    async def subscribe(
        self, topic_prefixes: List[str], duration: float = 10.0
    ) -> Dict[str, list[ValueRecord]]:
        """Subscribe to topics for real-time monitoring"""
        records: Dict[str, list[ValueRecord]] = defaultdict(list)

        options = ntcore.PubSubOptions()
        options.sendAll = True
        subscriber = ntcore.MultiSubscriber(self.inst, topic_prefixes, options)

        poller = ntcore.NetworkTableListenerPoller(self.inst)
        handle = poller.addListener(
            subscriber, ntcore.EventFlags.kValueAll | ntcore.EventFlags.kImmediate
        )

        start_time = time.time()
        while time.time() - start_time < duration:
            await asyncio.sleep(0.1)
            for event in poller.readQueue():
                data: ntcore.ValueEventData = event.data
                records[data.topic.getName()].append(
                    ValueRecord(
                        valid=data.value.isValid(),
                        last_change=time.strftime(
                            "%Y-%m-%d %H:%M:%S.%f",
                            time.localtime(data.value.last_change() / 1e6),
                        ),
                        server_time=time.strftime(
                            "%Y-%m-%d %H:%M:%S.%f",
                            time.localtime(data.value.server_time() / 1e6),
                        ),
                        local_time=time.strftime(
                            "%Y-%m-%d %H:%M:%S.%f",
                            time.localtime(data.value.time() / 1e6),
                        ),
                        type=data.topic.getTypeString(),
                        size=data.value.size(),
                        value=data.value.value(),
                    )
                )

        poller.removeListener(handle)
        subscriber.close()
        poller.close()

        return records
