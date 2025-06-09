# Electric Meter Simulator

A virtual electric meter simulator built in Rust that simulates an electric meter via Modbus TCP protocol.

## Features

- **Electric meter simulation**: Realistic electrical meter readings with live data updates
- **Modbus TCP server**: Industry-standard protocol for industrial automation
- **Real-time data**: Continuously updated meter readings with realistic variations
- **Command-line interface**: Easy to use with configurable network settings

## Electric Meter Simulation

The simulator provides realistic electrical meter readings including:
- **Cumulative energy consumption** (kWh) - Total energy consumed over time
- **Instantaneous power** (W) - Current power consumption
- **3-phase voltage measurements** (V) - Voltage readings for all three phases
- **3-phase current measurements** (A) - Current readings for all three phases
- **Frequency** (Hz) - Grid frequency
- **Power factor** - Power factor measurement

## Modbus Register Map

### Common Registers (All Meter Types)
| Address | Description | Unit | Scale Factor |
|---------|-------------|------|--------------|
| 0-1 | Cumulative consumption (32-bit) | kWh/m³ | ×100 |
| 2-3 | Instantaneous power/flow (32-bit) | W/L/min | ×10 |

### Electric Meter Specific Registers
| Address | Description | Unit | Scale Factor |
|---------|-------------|------|--------------|
| 10 | Voltage L1 | V | ×10 |
| 11 | Voltage L2 | V | ×10 |
| 12 | Voltage L3 | V | ×10 |
| 13 | Current L1 | A | ×100 |
| 14 | Current L2 | A | ×100 |
| 15 | Current L3 | A | ×100 |
| 16 | Frequency | Hz | ×100 |
| 17 | Power Factor | - | ×1000 |

### Water/Gas Meter Specific Registers
| Address | Description | Unit | Scale Factor |
|---------|-------------|------|--------------|
| 20 | Flow rate | L/min | ×10 |
| 21 | Temperature | °C | ×10 (+50 offset) |
| 22 | Pressure | bar/mbar | ×100 |

### Status Registers
| Address | Description | Values |
|---------|-------------|--------|
| 100 | Meter online status | 1 = Online, 0 = Offline |
| 101 | Meter type | 0 = Electric, 1 = Water, 2 = Gas |

### Coils (Digital Outputs)
| Address | Description |
|---------|-------------|
| 0 | Meter online |
| 1 | No alarms |
| 2 | Communication OK |
| 10 | Reset command (write) |

## Installation

1. Make sure you have Rust installed. If not, install it from [rustup.rs](https://rustup.rs/)

2. Clone or create the project directory

3. Build the project:
```bash
cargo build --release
```

## Usage

### Basic Usage
```bash
# Start electric meter simulator on default port (5020)
cargo run

# Start water meter simulator
cargo run -- --meter-type water

# Start gas meter simulator on custom port
cargo run -- --meter-type gas --port 5021

# Start on specific address and port
cargo run -- --address 0.0.0.0 --port 5020
```

### Command Line Options
- `--port, -p`: Modbus TCP port (default: 5020)
- `--address, -a`: Bind address (default: 127.0.0.1)
- `--meter-type, -t`: Type of meter (electric, water, gas, default: electric)

### Example: Multiple Meter Simulation
You can run multiple instances to simulate different meters:

```bash
# Terminal 1: Electric meter
cargo run -- --meter-type electric --port 5020

# Terminal 2: Water meter
cargo run -- --meter-type water --port 5021

# Terminal 3: Gas meter
cargo run -- --meter-type gas --port 5022
```

## Testing with Modbus Client

You can test the simulator using any Modbus TCP client. Here are some popular options:

### Using mbpoll (Linux/macOS)
```bash
# Install mbpoll
# On Ubuntu: sudo apt-get install mbpoll
# On macOS: brew install mbpoll

# Read holding registers 0-5 (cumulative and instantaneous values)
mbpoll -t 4 -r 1 -c 6 127.0.0.1:5020

# Read electric meter specific registers
mbpoll -t 4 -r 11 -c 8 127.0.0.1:5020

# Read status registers
mbpoll -t 4 -r 101 -c 2 127.0.0.1:5020
```

### Using Python with pymodbus
```python
from pymodbus.client.sync import ModbusTcpClient

client = ModbusTcpClient('127.0.0.1', port=5020)
client.connect()

# Read cumulative consumption (registers 0-1, 32-bit value)
result = client.read_holding_registers(0, 2)
consumption = (result.registers[1] << 16) | result.registers[0]
print(f"Cumulative consumption: {consumption / 100.0} kWh")

# Read instantaneous power (registers 2-3, 32-bit value)
result = client.read_holding_registers(2, 2)
power = (result.registers[1] << 16) | result.registers[0]
print(f"Instantaneous power: {power / 10.0} W")

client.close()
```

## Development

### Project Structure
```
src/
├── main.rs           # Application entry point and CLI
├── meter.rs          # Meter simulation logic
└── modbus_server.rs  # Modbus TCP server implementation
```

### Adding New Meter Types
1. Add new variant to `MeterType` enum in `meter.rs`
2. Implement specific readings in `initialize_type_specific_readings()`
3. Add update logic in `update_readings()`
4. Map registers in `get_register_value()`

### Extending Modbus Functionality
The Modbus server supports:
- Read Holding Registers (0x03)
- Read Input Registers (0x04)
- Read Coils (0x01)
- Read Discrete Inputs (0x02)
- Write Single Coil (0x05)
- Write Single Register (0x06)

Additional functions can be added in the `MeterService::call()` method.

## License

This project is open source. Feel free to use and modify as needed.
