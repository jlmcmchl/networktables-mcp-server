#!/usr/bin/env python3
"""
NetworkTables MCP Server - Configuration and Usage Examples

This file demonstrates how to configure and use the NetworkTables MCP server
for different FRC scenarios.
"""

import asyncio
import json
import time
from typing import Dict, Any, List
from fastmcp import Client
from mcp.types import TextContent

def parse_result(result: List[Any]) -> List[Any]:
    output = []
    for content in result:
        if isinstance(content, TextContent):
            output.append(json.loads(content.text))
        else:
            raise ValueError(f"Unsupported content type: {type(content)}")
    return output


# Example MCP client implementation for testing
class NTMCPClient:
    """Example client for testing the NetworkTables MCP server"""

    def __init__(self, server_py: str):
        self.session = Client(server_py)

    async def connect_to_robot(self, team_number: int) -> Dict[str, Any]:
        """Connect to robot using team number"""
        if not self.session.is_connected():
            raise RuntimeError("MCP session not established")

        result = await self.session.call_tool(
            "nt_connect",
            {"team_number": team_number, "identity": "Competition-MCP-Client"},
        )
        return parse_result(result)[0]

    async def connect_to_simulator(self, ip: str = "127.0.0.1") -> Dict[str, Any]:
        """Connect to robot simulator"""
        if not self.session.is_connected():
            raise RuntimeError("MCP session not established")

        result = await self.session.call_tool(
            "nt_connect",
            {"server_ip": ip, "server_port": 5810, "identity": "Simulation-MCP-Client"},
        )
        
        return parse_result(result)[0]

    async def monitor_autonomous(self, duration: float = 15.0) -> Dict[str, Any]:
        """Monitor key autonomous topics"""
        if not self.session.is_connected():
            raise RuntimeError("MCP session not established")

        topics = [
            "/SmartDashboard/Auto Selector",
            "/SmartDashboard/Auto Running",
            "/SmartDashboard/Auto Time Remaining",
            "/Robot/Autonomous",
            "/Robot/Mode",
        ]

        result = await self.session.call_tool(
            "nt_subscribe", {"topics": topics, "duration": duration}
        )
        return parse_result(result)[0]
        

    async def get_drivetrain_status(self) -> Dict[str, Any]:
        """Get current drivetrain information"""
        if not self.session.is_connected():
            raise RuntimeError("MCP session not established")

        topics = [
            "/SmartDashboard/Left Encoder",
            "/SmartDashboard/Right Encoder",
            "/SmartDashboard/Gyro Angle",
            "/SmartDashboard/Drive Speed",
            "/SmartDashboard/Turn Rate",
        ]

        result = await self.session.call_tool("nt_get_multiple", {"topics": topics})
        return parse_result(result)[0]

    async def emergency_stop(self) -> Dict[str, bool]:
        """Emergency stop all robot systems"""
        if not self.session.is_connected():
            raise RuntimeError("MCP session not established")

        emergency_updates = {
            "/SmartDashboard/Emergency Stop": True,
            "/SmartDashboard/Drive Enable": False,
            "/SmartDashboard/Shooter Enable": False,
            "/SmartDashboard/Intake Enable": False,
        }

        result = await self.session.call_tool(
            "nt_set_multiple", {"updates": emergency_updates}
        )
        return parse_result(result)[0]

    async def set_autonomous_mode(self, auto_name: str) -> bool:
        """Set autonomous mode selection"""
        if not self.session.is_connected():
            raise RuntimeError("MCP session not established")

        result = await self.session.call_tool(
            "nt_set", {"topic": "/SmartDashboard/Auto Selector", "value": auto_name}
        )
        return parse_result(result)[0]

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health information"""
        if not self.session.is_connected():
            raise RuntimeError("MCP session not established")

        health_topics = [
            "/SmartDashboard/Battery Voltage",
            "/SmartDashboard/CPU Usage",
            "/SmartDashboard/Memory Usage",
            "/SmartDashboard/CAN Utilization",
            "/SmartDashboard/Radio Signal",
            "/SmartDashboard/FMS Connected",
            "/SmartDashboard/Robot Code",
        ]

        # Get health metrics
        values_result = await self.session.call_tool(
            "nt_get_multiple", {"topics": health_topics}
        )
        values = parse_result(values_result)[0]


        # Get connection info
        conn_result = await self.session.call_tool("nt_connection_info", {})
        conn_info = parse_result(conn_result)[0]

        # Get time sync info
        sync_result = await self.session.call_tool("nt_time_sync_info", {})
        sync_info = parse_result(sync_result)[0]

        return {
            "health_metrics": values,
            "connection": conn_info,
            "time_sync": sync_info,
            "timestamp": time.time(),
        }

    async def list_all_topics(self, filter_pattern: str = None) -> List[str]:
        """List all available topics"""
        if not self.session.is_connected():
            raise RuntimeError("MCP session not established")

        args = {"filter_pattern": filter_pattern} if filter_pattern else {}
        result = await self.session.call_tool("nt_list_topics", args)
        return parse_result(result)[0]

    async def get_topic_details(self, topic: str) -> Dict[str, Any]:
        """Get detailed information about a topic"""
        if not self.session.is_connected():
            raise RuntimeError("MCP session not established")

        result = await self.session.call_tool("nt_get_info", {"topic": topic})
        return parse_result(result)[0]

    async def close(self):
        """Close the MCP session"""
        if self.session.is_connected():
            await self.session.call_tool("nt_disconnect", {})
        await self.session.close()


# Configuration templates for different scenarios
class NTMCPConfigurations:
    """Common NetworkTables MCP configurations"""

    @staticmethod
    def competition_config(team_number: int) -> Dict[str, Any]:
        """Configuration for competition use"""
        return {
            "connection": {
                "team_number": team_number,
                "identity": f"MCP-Competition-{team_number}",
                "server_port": 5810,
            },
            "monitoring": {
                "critical_topics": [
                    "/Robot/Mode",
                    "/Robot/Enabled",
                    "/Robot/Autonomous",
                    "/SmartDashboard/Battery Voltage",
                    "/SmartDashboard/FMS Connected",
                ],
                "alert_thresholds": {
                    "/SmartDashboard/Battery Voltage": {"min": 10.0},
                    "/SmartDashboard/CPU Usage": {"max": 80.0},
                },
            },
            "subscription_duration": 0.5,  # Short durations for competition
        }

    @staticmethod
    def practice_config(team_number: int) -> Dict[str, Any]:
        """Configuration for practice/testing"""
        return {
            "connection": {
                "team_number": team_number,
                "identity": f"MCP-Practice-{team_number}",
                "server_port": 5810,
            },
            "logging": {
                "enabled": True,
                "topics": ["*"],  # Log all topics
                "format": "json",
                "rotation": "daily",
            },
            "subscription_duration": 2.0,  # Longer durations for practice
        }

    @staticmethod
    def simulation_config() -> Dict[str, Any]:
        """Configuration for simulation"""
        return {
            "connection": {
                "server_ip": "127.0.0.1",
                "server_port": 5810,
                "identity": "MCP-Simulation",
            },
            "simulation": {
                "physics_topics": [
                    "/SmartDashboard/Field/Robot",
                    "/SmartDashboard/Field/Objects",
                ],
                "inject_noise": False,
                "time_scale": 1.0,
            },
            "subscription_duration": 1.0,  # Medium duration for simulation
        }

    @staticmethod
    def scouting_config(team_number: int) -> Dict[str, Any]:
        """Configuration for match scouting"""
        return {
            "connection": {
                "team_number": team_number,
                "identity": f"MCP-Scout-{team_number}",
                "server_port": 5810,
            },
            "scouting": {
                "match_topics": [
                    "/SmartDashboard/Match Time",
                    "/SmartDashboard/Alliance",
                    "/SmartDashboard/Match Number",
                    "/SmartDashboard/Auto Points",
                    "/SmartDashboard/Teleop Points",
                    "/SmartDashboard/Endgame Points",
                ],
                "performance_topics": [
                    "/SmartDashboard/Shots Made",
                    "/SmartDashboard/Shots Attempted",
                    "/SmartDashboard/Defense Rating",
                    "/SmartDashboard/Cycle Time",
                ],
            },
            "subscription_duration": 5.0,  # Longer durations for scouting
        }


# Usage examples and patterns
class NTMCPUsageExamples:
    """Common usage patterns for the NetworkTables MCP server"""

    @staticmethod
    async def autonomous_sequence_analysis(client: NTMCPClient):
        """Analyze autonomous sequence performance"""
        print("Starting autonomous sequence analysis...")

        # Monitor autonomous execution
        auto_data = await client.monitor_autonomous(duration=15.0)

        if auto_data.get("success"):
            samples = auto_data["samples"]

            print(f"Collected {len(samples)} topic samples during autonomous")

            # Analyze each topic's data
            for topic_name, records in samples.items():
                if records:
                    print(f"\nTopic: {topic_name}")
                    print(f"  Records: {len(records)}")
                    print(f"  First value: {records[0].value}")
                    print(f"  Last value: {records[-1].value}")
                    print(f"  Value changes: {len(set(r.value for r in records))}")
        else:
            print(
                f"Autonomous monitoring failed: {auto_data.get('error', 'Unknown error')}"
            )

    @staticmethod
    async def real_time_telemetry(client: NTMCPClient):
        """Continuous telemetry monitoring"""
        print("Starting real-time telemetry...")

        for i in range(10):  # 10 iterations
            health = await client.get_system_health()
            drivetrain = await client.get_drivetrain_status()

            print(f"\n--- Telemetry Update {i+1} ---")
            print(
                f"Battery: {health['health_metrics'].get('/SmartDashboard/Battery Voltage', 'N/A')}V"
            )
            print(f"Connected: {health['connection']['connected']}")
            print(f"Connection Count: {health['connection']['connection_count']}")
            print(f"Time Sync Valid: {health['time_sync']['valid']}")
            if health["time_sync"]["valid"]:
                print(f"  Ping: {health['time_sync']['ping']}μs")
                print(f"  Drift: {health['time_sync']['drift']}μs")

            print(
                f"Left Encoder: {drivetrain.get('/SmartDashboard/Left Encoder', 'N/A')}"
            )
            print(
                f"Right Encoder: {drivetrain.get('/SmartDashboard/Right Encoder', 'N/A')}"
            )
            print(f"Gyro: {drivetrain.get('/SmartDashboard/Gyro Angle', 'N/A')}°")

            await asyncio.sleep(1.0)

    @staticmethod
    async def topic_discovery(client: NTMCPClient):
        """Discover and analyze available topics"""
        print("Discovering NetworkTables topics...")

        # List all topics
        all_topics = await client.list_all_topics()
        print(f"Found {len(all_topics)} total topics")

        # Filter by categories
        dashboard_topics = await client.list_all_topics("/SmartDashboard/*")
        robot_topics = await client.list_all_topics("/Robot/*")

        print(f"SmartDashboard topics: {len(dashboard_topics)}")
        print(f"Robot topics: {len(robot_topics)}")

        # Analyze a few interesting topics
        interesting_topics = [
            "/SmartDashboard/Battery Voltage",
            "/Robot/Mode",
            "/Robot/Enabled",
        ]

        for topic in interesting_topics:
            if topic in all_topics:
                info = await client.get_topic_details(topic)
                print(f"\nTopic: {topic}")
                print(f"  Type: {info.get('type', 'Unknown')}")
                print(f"  Properties: {info.get('properties', {})}")

    @staticmethod
    async def match_data_collection(client: NTMCPClient):
        """Collect match data for analysis"""
        print("Starting match data collection...")

        # Key topics to monitor during match
        match_topics = [
            "/SmartDashboard/Match Time",
            "/SmartDashboard/Alliance Score",
            "/SmartDashboard/Shots Made",
            "/SmartDashboard/Robot Position X",
            "/SmartDashboard/Robot Position Y",
        ]

        # Subscribe to topics for the duration of a match (150 seconds)
        print("Subscribing to match topics...")
        match_data = await client.session.call_tool(
            "nt_subscribe",
            {"topics": match_topics, "duration": 150.0},  # Full match duration
        )

        if match_data.content:
            data = json.loads(match_data.content[0].text)
            if data.get("success"):
                # Save match data
                filename = f"match_data_{int(time.time())}.json"
                with open(filename, "w") as f:
                    json.dump(data["samples"], f, indent=2, default=str)

                print(f"Match data saved to {filename}")

                # Provide summary
                for topic_name, records in data["samples"].items():
                    print(f"Topic {topic_name}: {len(records)} records")
            else:
                print(f"Match data collection failed: {data.get('error')}")

    @staticmethod
    async def system_health_monitoring(client: NTMCPClient):
        """Monitor system health with alerts"""
        print("Starting system health monitoring...")

        config = NTMCPConfigurations.competition_config(1234)
        thresholds = config["monitoring"]["alert_thresholds"]

        while True:
            try:
                health = await client.get_system_health()

                # Check thresholds
                alerts = []
                for topic, threshold in thresholds.items():
                    value = health["health_metrics"].get(topic)
                    if value is not None:
                        if "min" in threshold and value < threshold["min"]:
                            alerts.append(f"LOW {topic}: {value} < {threshold['min']}")
                        if "max" in threshold and value > threshold["max"]:
                            alerts.append(f"HIGH {topic}: {value} > {threshold['max']}")

                # Check connection health
                if not health["connection"]["connected"]:
                    alerts.append("DISCONNECTED: No NetworkTables connection")
                elif health["connection"]["connection_count"] == 0:
                    alerts.append(
                        "NO CONNECTIONS: NetworkTables has no active connections"
                    )

                # Report status
                if alerts:
                    print(f"🚨 ALERTS: {'; '.join(alerts)}")
                else:
                    print("✅ All systems nominal")

                await asyncio.sleep(1.0)

            except KeyboardInterrupt:
                print("Health monitoring stopped")
                break
            except Exception as e:
                print(f"Health monitoring error: {e}")
                await asyncio.sleep(5.0)


# Example usage functions
async def competition_example():
    """Example for competition use"""
    client = NTMCPClient("nt_mcp_server.py")

    try:
        # Connect to robot
        result = await client.connect_to_robot(1234)
        print(f"Robot connection: {result}")

        if result.get("success"):
            # Run competition monitoring
            await NTMCPUsageExamples.system_health_monitoring(client)

    except Exception as e:
        print(f"Competition example error: {e}")
    finally:
        await client.close()


async def practice_example():
    """Example for practice sessions"""
    client = NTMCPClient("nt_mcp_server.py")

    try:
        # Connect to robot
        result = await client.connect_to_robot(1234)
        print(f"Robot connection: {result}")

        if result.get("success"):
            # Discover topics
            await NTMCPUsageExamples.topic_discovery(client)

            # Run telemetry
            await NTMCPUsageExamples.real_time_telemetry(client)

            # Test autonomous
            await NTMCPUsageExamples.autonomous_sequence_analysis(client)

    except Exception as e:
        print(f"Practice example error: {e}")
    finally:
        await client.close()


async def simulation_example():
    """Example for simulation"""
    client = NTMCPClient("nt_mcp_server.py")

    try:
        async with client.session:
            # Connect to simulator
            result = await client.connect_to_simulator("127.0.0.1")
            print(f"Simulator connection: {result}")

            if result.get("success"):
                # Run simulation-specific monitoring
                await NTMCPUsageExamples.real_time_telemetry(client)

    except Exception as e:
        print(f"Simulation example error: {e}")
    finally:
        await client.close()


async def scouting_example():
    """Example for match scouting"""
    client = NTMCPClient("nt_mcp_server.py")

    try:
        # Connect to robot being scouted
        result = await client.connect_to_robot(5678)  # Different team
        print(f"Scouting connection: {result}")

        if result.get("success"):
            # Collect match data
            await NTMCPUsageExamples.match_data_collection(client)

    except Exception as e:
        print(f"Scouting example error: {e}")
    finally:
        await client.close()


async def main():
    """Main entry point - choose your scenario"""
    import sys

    if len(sys.argv) > 1:
        scenario = sys.argv[1]
    else:
        print("Available scenarios:")
        print("  competition - Competition monitoring")
        print("  practice    - Practice session")
        print("  simulation  - Robot simulation")
        print("  scouting    - Match scouting")
        scenario = input("Choose scenario: ").strip()

    if scenario == "competition":
        await competition_example()
    elif scenario == "practice":
        await practice_example()
    elif scenario == "simulation":
        await simulation_example()
    elif scenario == "scouting":
        await scouting_example()
    else:
        print(f"Unknown scenario: {scenario}")


if __name__ == "__main__":
    asyncio.run(main())
