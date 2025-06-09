# NetworkTables MCP Server

A Model Context Protocol (MCP) server that provides AI agents with access to FRC robot data through NetworkTables.

## Features

### 🔌 **Resource Management**
- **Topics as Resources**: Each NT topic exposed as MCP resource with `nt://table/key` URI scheme
- **Hierarchical Discovery**: Resources organized by NetworkTables structure (SmartDashboard, LiveWindow, subsystems)
- **Dynamic Registration**: New topics automatically become available resources as they're published
- **Resource Metadata**: Type information, update frequency, publisher info for each topic

### 🛠️ **Tool Design Patterns**
- **Read Tools**: `nt_get(topic)`, `nt_get_multiple(topics[])` for value retrieval
- **Write Tools**: `nt_set(topic, value)`, `nt_set_multiple(updates{})` for publishing
- **Subscription Tools**: `nt_subscribe(topics[], duration)` for real-time monitoring
- **Discovery Tools**: `nt_list_topics(filter?)`, `nt_get_info(topic)` for exploration

### 🌐 **Connection State Management**
- **Connection as Context**: MCP server maintains NT connection state across tool calls
- **Automatic Reconnection**: Handle robot disconnections gracefully
- **Connection Configuration**: Team number, IP, port configuration through MCP
- **Health Monitoring**: Connection quality and latency as accessible metrics

### 📊 **Data Type Handling**
- **Type Coercion**: Automatic conversion between NT types and JSON for MCP transport
- **Schema Validation**: Ensure data types match NT topic expectations
- **Array Handling**: Proper serialization of NT arrays, structs, and complex types

### ⚡ **Performance Considerations**
- **Batching**: Group multiple operations to reduce MCP overhead
- **Caching**: Intelligent caching of frequently accessed values with configurable TTL
- **Delta Updates**: Only transmit changed values for efficiency
- **Rate Limiting**: Prevent overwhelming the NT network

## Installation

### Requirements

```bash
pip install fastmcp pyntcore
```

### Dependencies

Create a `requirements.txt` file:

```txt
fastmcp>=2.7.1
pyntcore>=2025.3.2.3
```

### Quick Setup

1. **Clone or download** the server files
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Run the server**: `python mcp-nt2.py`

## Usage Examples

### Basic Connection

```python
# Connect to robot by team number
result = await mcp.call_tool("nt_connect", {
    "team_number": 1234,
    "identity": "Competition-Agent"
})

# Connect to simulation
result = await mcp.call_tool("nt_connect", {
    "server_ip": "127.0.0.1",
    "server_port": 5810,
    "identity": "Sim-Agent"
})
```

### Reading Data

```python
# Get single value
battery_voltage = await mcp.call_tool("nt_get", {
    "topic": "/SmartDashboard/Battery Voltage"
})

# Get multiple values efficiently
drivetrain_data = await mcp.call_tool("nt_get_multiple", {
    "topics": [
        "/SmartDashboard/Left Encoder",
        "/SmartDashboard/Right Encoder",
        "/SmartDashboard/Gyro Angle"
    ]
})
```

### Writing Data

```python
# Set single value
success = await mcp.call_tool("nt_set", {
    "topic": "/SmartDashboard/Auto Selector",
    "value": "Center Auto"
})

# Set multiple values atomically
results = await mcp.call_tool("nt_set_multiple", {
    "updates": {
        "/SmartDashboard/Drive Speed": 0.5,
        "/SmartDashboard/Turn Rate": 0.0,
        "/SmartDashboard/Target Acquired": True
    }
})
```

### Real-time Monitoring

```python
# Subscribe to topics for duration
monitoring_data = await mcp.call_tool("nt_subscribe", {
    "topics": [
        "/Robot/Mode",
        "/Robot/Enabled",
        "/SmartDashboard/Match Time"
    ],
    "duration": 15.0  # 15 seconds
})

# Process samples
for sample in monitoring_data["samples"]:
    timestamp = sample["timestamp"]
    values = sample["values"]
    print(f"T+{timestamp}: {values}")
```

### Topic Discovery

```python
# List all topics
all_topics = await mcp.call_tool("nt_list_topics")

# Filter topics by pattern
dashboard_topics = await mcp.call_tool("nt_list_topics", {
    "filter_pattern": "/SmartDashboard/*"
})

# Get detailed topic information
topic_info = await mcp.call_tool("nt_get_info", {
    "topic": "/SmartDashboard/Battery Voltage"
})
```

## Configuration Scenarios

### Competition Configuration

For competition use with optimized performance:

```python
server = create_server_for_competition(team_number=1234)
```

**Features:**
- 50ms cache TTL for responsiveness
- High-priority topic monitoring
- Connection health alerts
- Minimal latency settings

### Practice Configuration

For practice sessions with enhanced logging:

```python
server = create_server_for_practice(team_number=1234)
```

**Features:**
- 100ms cache TTL
- Full topic logging
- Extended diagnostics
- Performance metrics

### Simulation Configuration

For robot simulation and testing:

```python
server = create_server_for_simulation()
```

**Features:**
- 200ms cache TTL
- Localhost connection
- Physics topic support
- Development-friendly settings

### Scouting Configuration

For match data collection and analysis:

```python
server = create_server_for_scouting(team_number=1234)
```

**Features:**
- Match-specific topics
- Performance metrics collection
- 1Hz data recording
- Analysis-ready output

## Advanced Usage

### Resource Access

NetworkTables topics are automatically exposed as MCP resources:

```python
# List all NT resources
resources = await mcp.list_resources()

# Access topic as resource
topic_resource = await mcp.get_resource("nt:///SmartDashboard/Auto Selector")
```

### Batch Operations

Efficiently handle multiple operations:

```python
# Batch read critical telemetry
health_check = await mcp.call_tool("nt_get_multiple", {
    "topics": [
        "/SmartDashboard/Battery Voltage",
        "/SmartDashboard/CPU Usage", 
        "/SmartDashboard/CAN Utilization",
        "/SmartDashboard/FMS Connected"
    ],
    "use_cache": False  # Force fresh reads
})
```

### Error Handling

Robust error handling for competition reliability:

```python
try:
    result = await mcp.call_tool("nt_get", {"topic": "/critical/topic"})
    if result is None:
        # Handle missing topic
        await fallback_behavior()
except Exception as e:
    logger.error(f"NT operation failed: {e}")
    # Implement retry logic
```

## API Reference

### Connection Tools

- `nt_connect(team_number?, server_ip?, server_port?, identity?)` - Connect to NT server
- `nt_disconnect()` - Disconnect from NT server  
- `nt_connection_info()` - Get connection status and info

### Data Access Tools

- `nt_get(topic, use_cache?)` - Get single topic value
- `nt_get_multiple(topics[], use_cache?)` - Get multiple topic values
- `nt_set(topic, value)` - Set single topic value
- `nt_set_multiple(updates{})` - Set multiple topic values

### Discovery Tools

- `nt_list_topics(filter_pattern?)` - List available topics
- `nt_get_info(topic)` - Get detailed topic information

### Monitoring Tools

- `nt_subscribe(topics[], duration)` - Monitor topics for duration

### Resource URIs

- `nt://topics` - List all available topics
- `nt:///path/to/topic` - Access specific topic as resource

## Performance Tuning

### Cache Configuration

```python
# Adjust cache TTL based on use case
server.nt_manager.cache_ttl = 0.05  # 50ms for competition
server.nt_manager.cache_ttl = 0.1   # 100ms for practice  
server.nt_manager.cache_ttl = 0.2   # 200ms for simulation
```

### Batch Size Optimization

```python
# Use batch operations for multiple related topics
topics = [f"/subsystem/sensor_{i}" for i in range(10)]
all_values = await mcp.call_tool("nt_get_multiple", {"topics": topics})
```

### Connection Optimization

```python
# Optimize for competition network conditions
await mcp.call_tool("nt_connect", {
    "team_number": 1234,
    "identity": "MCP-Competition",
    # Connection will auto-discover robot IP
})
```

## Troubleshooting

### Common Issues

**Connection Failed**
- Verify robot/simulator is running
- Check team number or IP address
- Ensure NetworkTables port (5810) is accessible

**Slow Performance** 
- Reduce cache TTL for real-time data
- Use batch operations for multiple topics
- Check network latency to robot

**Missing Topics**
- Topics must be published by robot code first
- Use `nt_list_topics()` to see available topics
- Check topic name spelling and case

**Type Errors**
- Verify data types match NT topic expectations
- Use `nt_get_info()` to check topic type
- Handle type coercion in your code

### Logging

Enable detailed logging for debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Development Mode

For development and testing:

```python
# Enable additional diagnostics
server = NetworkTablesMCPServer()
server.nt_manager.cache_ttl = 0.0  # Disable caching
# Run with verbose logging
```

## Integration Examples

### With Competition Software

```python
# Monitor autonomous sequence
auto_data = await mcp.call_tool("nt_subscribe", {
    "topics": ["/Robot/Autonomous", "/SmartDashboard/Auto Selector"],
    "duration": 15.0
})

# Analyze performance
analysis = analyze_autonomous_performance(auto_data)
```

### With Scouting Systems

```python
# Collect match data
match_topics = [
    "/SmartDashboard/Match Time",
    "/SmartDashboard/Alliance Score", 
    "/SmartDashboard/Robot Performance"
]

match_data = await mcp.call_tool("nt_subscribe", {
    "topics": match_topics,
    "duration": 150.0  # Full match duration
})

# Export for analysis
export_match_data(match_data, "match_001.json")
```

### With Dashboard Applications

```python
# Real-time dashboard updates
while competition_active:
    telemetry = await mcp.call_tool("nt_get_multiple", {
        "topics": DASHBOARD_TOPICS,
        "use_cache": True
    })
    
    update_dashboard(telemetry)
    await asyncio.sleep(0.1)  # 10Hz updates
```

## License

This project is released under the MIT License, making it freely available for FRC teams and educational use.