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

## Installation

```bash
uv run fastmcp install --with pyntcore nt_mcp_server.py
```

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


## API Reference

### Connection Tools

- `nt_connect(team_number?, server_ip?, server_port?, identity?)` - Connect to NT server
- `nt_disconnect()` - Disconnect from NT server  
- `nt_connection_info()` - Get connection info
- `nt_time_sync_info()` - Get time sync info

### Data Access Tools

- `nt_get(topic)` - Get single topic value
- `nt_get_multiple(topics[])` - Get multiple topic values
- `nt_set(topic, value)` - Set single topic value
- `nt_set_multiple(updates{})` - Set multiple topic values

### Discovery Tools

- `nt_list_topics(topic_prefix?)` - List available topics
- `nt_get_info(topic)` - Get detailed topic information

### Monitoring Tools

- `nt_subscribe(topics[], duration)` - Record all data in topics for a period of time

### Resource URIs

- `nt://topics` - List all available topics
- `nt:///path/to/topic` - Access specific topic as resource


## Troubleshooting

### Common Issues

**Connection Failed**
- Verify robot/simulator is running
- Check team number or IP address
- Ensure NetworkTables port (5810) is accessible

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

```bash
uv run fastmcp dev --with pyntcore nt_mcp_server.py 
```

## License

This project is released under the MIT License, making it freely available for FRC teams and educational use.