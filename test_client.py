#!/usr/bin/env python3
"""
Simple test client for the NetworkTables MCP Server

This client directly calls the MCP tools to test functionality.
"""

import asyncio
import json
import time
import sys
import traceback

# Import the MCP server directly for testing
from nt_manager import NetworkTablesManager


class DirectMCPTester:
    """Direct tester for MCP tools without external client"""
    
    def __init__(self):
        self.nt_manager = NetworkTablesManager()
        
    async def test_connection(self, team_number: int = None, server_ip: str = None):
        """Test NetworkTables connection"""
        print(f"Testing connection: team={team_number}, ip={server_ip}")
        
        try:
            if server_ip:
                result = self.nt_manager.configure_connection(
                    server_ip=server_ip,
                    identity="Test-Client"
                )
            elif team_number:
                result = self.nt_manager.configure_connection(
                    team_number=team_number,
                    identity="Test-Client"
                )
            else:
                print("Must provide either team_number or server_ip")
                return False
                
            # Wait for connection
            await asyncio.sleep(1.0)
            
            # Check connection status
            info = self.nt_manager.get_connection_info()
            print(f"Connection info: {json.dumps(info, indent=2)}")
            
            return info["connected"]
            
        except Exception as e:
            print(f"Connection test failed: {e}")
            print(traceback.format_exc())
            return False
    
    async def test_topics(self):
        """Test topic listing and info"""
        print("\n=== Testing Topics ===")
        
        try:
            # List all topics
            topics = self.nt_manager.list_topics()
            print(f"Found {len(topics)} topics")
            
            if topics:
                print("Sample topics:")
                for topic in topics[:5]:  # Show first 5
                    print(f"  {topic}")
                    
                    # Get topic info
                    info = self.nt_manager.get_topic_info(topic)
                    if info:
                        print(f"    Type: {info.get('type', 'Unknown')}")
                        print(f"    Properties: {info.get('properties', {})}")
            else:
                print("No topics found - robot may not be publishing data")
                
        except Exception as e:
            print(f"Topic test failed: {e}")
            print(traceback.format_exc())
    
    async def test_values(self):
        """Test reading and writing values"""
        print("\n=== Testing Values ===")
        
        try:
            # Try to read some common topics
            common_topics = [
                "/SmartDashboard/Test",
                "/Robot/Mode",
                "/Robot/Enabled",
                "/SmartDashboard/Battery Voltage"
            ]
            
            print("Reading values:")
            values = self.nt_manager.get_multiple_values(common_topics)
            for topic, value in values.items():
                print(f"  {topic}: {value}")
            
            # Test writing a value
            test_topic = "/SmartDashboard/MCP_Test"
            test_value = f"Test_{int(time.time())}"
            
            print(f"\nWriting test value: {test_topic} = {test_value}")
            success = self.nt_manager.set_value(test_topic, test_value)
            print(f"Write success: {success}")
            
            # Read it back
            read_value = self.nt_manager.get_value(test_topic)
            print(f"Read back: {read_value}")
            
            if read_value == test_value:
                print("✅ Read/write test passed")
            else:
                print("❌ Read/write test failed")
                
        except Exception as e:
            print(f"Value test failed: {e}")
            print(traceback.format_exc())
    
    async def test_subscription(self, duration: float = 5.0):
        """Test topic subscription"""
        print(f"\n=== Testing Subscription ({duration}s) ===")
        
        try:
            # Subscribe to some topics
            topics = [
                "/SmartDashboard/MCP_Test",
                "/Robot/Mode"
            ]
            
            print(f"Subscribing to: {topics}")
            records = await self.nt_manager.subscribe(topics, duration)
            
            print("Subscription results:")
            for topic, topic_records in records.items():
                print(f"  {topic}: {len(topic_records)} records")
                if topic_records:
                    print(f"    First: {topic_records[0].value} at {topic_records[0].local_time}")
                    print(f"    Last: {topic_records[-1].value} at {topic_records[-1].local_time}")
                    
        except Exception as e:
            print(f"Subscription test failed: {e}")
            print(traceback.format_exc())
    
    async def test_time_sync(self):
        """Test time synchronization"""
        print("\n=== Testing Time Sync ===")
        
        try:
            sync_info = self.nt_manager.get_time_sync_info()
            print(f"Time sync info: {json.dumps(sync_info, indent=2)}")
            
            if sync_info["valid"]:
                print(f"✅ Time sync established")
                print(f"  Ping: {sync_info['ping']}μs")
                print(f"  Drift: {sync_info['drift']}μs")
            else:
                print("⚠️ Time sync not established")
                
        except Exception as e:
            print(f"Time sync test failed: {e}")
            print(traceback.format_exc())
    
    async def run_full_test(self, team_number: int = None, server_ip: str = None):
        """Run complete test suite"""
        print("🚀 Starting NetworkTables MCP Server Tests")
        print("=" * 50)
        
        try:
            # Test connection
            connected = await self.test_connection(team_number, server_ip)
            
            if connected:
                print("✅ Connection successful")
                
                # Run tests
                await self.test_time_sync()
                await self.test_topics()
                await self.test_values()
                await self.test_subscription(5.0)
                
                print("\n✅ All tests completed")
            else:
                print("❌ Connection failed - skipping other tests")
                
        except Exception as e:
            print(f"Test suite failed: {e}")
            print(traceback.format_exc())
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.nt_manager.disconnect()
            print("\n🧹 Cleanup completed")
        except Exception as e:
            print(f"Cleanup error: {e}")


async def interactive_test():
    """Interactive test mode"""
    tester = DirectMCPTester()
    
    print("NetworkTables MCP Server Interactive Tester")
    print("=" * 40)
    
    # Get connection details
    print("\nConnection options:")
    print("1. Connect by team number")
    print("2. Connect to specific IP")
    print("3. Connect to localhost (simulation)")
    
    choice = input("Choose option (1-3): ").strip()
    
    if choice == "1":
        team_num = int(input("Enter team number: "))
        await tester.run_full_test(team_number=team_num)
    elif choice == "2":
        ip = input("Enter server IP: ").strip()
        await tester.run_full_test(server_ip=ip)
    elif choice == "3":
        await tester.run_full_test(server_ip="127.0.0.1")
    else:
        print("Invalid choice")


async def quick_test():
    """Quick test with localhost"""
    print("Running quick test with localhost...")
    tester = DirectMCPTester()
    await tester.run_full_test(server_ip="127.0.0.1")


async def team_test(team_number: int):
    """Test with specific team number"""
    print(f"Running test with team {team_number}...")
    tester = DirectMCPTester()
    await tester.run_full_test(team_number=team_number)


def print_usage():
    """Print usage information"""
    print("NetworkTables MCP Server Test Client")
    print("\nUsage:")
    print("  python nt_test_client.py                    # Interactive mode")
    print("  python nt_test_client.py quick              # Quick localhost test")
    print("  python nt_test_client.py team <number>      # Test with team number")
    print("  python nt_test_client.py ip <address>       # Test with specific IP")
    print("\nExamples:")
    print("  python nt_test_client.py team 1234")
    print("  python nt_test_client.py ip 10.12.34.2")
    print("  python nt_test_client.py quick")


async def main():
    """Main entry point"""
    if len(sys.argv) == 1:
        # Interactive mode
        await interactive_test()
    elif len(sys.argv) == 2:
        if sys.argv[1] == "quick":
            await quick_test()


if __name__ == "__main__":
    asyncio.run(main())