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

### Electric Meter Registers

| Address | Description | Unit | Scale Factor |
|---------|-------------|------|--------------|
| 0-1 | Cumulative consumption (32-bit) | kWh | ×100 |
| 2-3 | Instantaneous power (32-bit) | W | ×10 |
| 10 | Voltage L1 | V | ×10 |
| 11 | Voltage L2 | V | ×10 |
| 12 | Voltage L3 | V | ×10 |
| 13 | Current L1 | A | ×100 |
| 14 | Current L2 | A | ×100 |
| 15 | Current L3 | A | ×100 |
| 16 | Frequency | Hz | ×100 |
| 17 | Power factor | - | ×1000 |

### Coils (Digital Outputs)

| Address | Description | Type |
|---------|-------------|------|
| 0 | Meter online | Status |
| 10 | Reset command | Control |

### Discrete Inputs (Digital Inputs)

| Address | Description | Type |
|---------|-------------|------|
| 0 | Power outage alarm | Alarm |
| 1 | Over-voltage alarm | Alarm |
| 2 | Under-voltage alarm | Alarm |

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

# Start on specific address and port
cargo run -- --address 0.0.0.0 --port 5020
```

### Command Line Options

- `--port, -p`: Modbus TCP port (default: 5020)
- `--address, -a`: Bind address (default: 127.0.0.1)

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

# Read voltage readings
result = client.read_holding_registers(10, 3)
voltage_l1 = result.registers[0] / 10.0
voltage_l2 = result.registers[1] / 10.0
voltage_l3 = result.registers[2] / 10.0
print(f"Voltages: L1={voltage_l1}V, L2={voltage_l2}V, L3={voltage_l3}V")

# Read current readings
result = client.read_holding_registers(13, 3)
current_l1 = result.registers[0] / 100.0
current_l2 = result.registers[1] / 100.0
current_l3 = result.registers[2] / 100.0
print(f"Currents: L1={current_l1}A, L2={current_l2}A, L3={current_l3}A")

client.close()
```

### Comprehensive Testing

The project includes comprehensive test scripts:

```bash
# Run the basic test
python test_meter.py

# Run comprehensive tests (all functions)
python test_comprehensive.py
```

## Supported Modbus Functions

The Modbus server supports the following function codes:

- **Read Holding Registers (0x03)** - Read meter values
- **Read Input Registers (0x04)** - Read meter values (same as holding registers)
- **Read Coils (0x01)** - Read digital outputs/status
- **Read Discrete Inputs (0x02)** - Read digital inputs/alarms
- **Write Single Coil (0x05)** - Write control commands
- **Write Single Register (0x06)** - Write configuration values

## Development

### Project Structure

```
src/
├── main.rs           # Application entry point and CLI
├── meter.rs          # Electric meter simulation logic
└── modbus_server.rs  # Custom Modbus TCP server implementation
```

### Key Features

- **Real-time simulation**: Values update continuously with realistic variations
- **Custom Modbus server**: Built from scratch due to tokio-modbus limitations
- **Realistic electrical data**: Simulates actual electric meter behavior
- **Error handling**: Robust error handling for network and protocol issues

### Extending the Simulator

The simulator can be extended by:

1. **Adding new registers**: Modify the register mapping in `meter.rs`
2. **Adding new Modbus functions**: Extend the `handle_modbus_request` function
3. **Improving simulation**: Add more realistic electrical behaviors
4. **Adding logging**: Enhance the logging capabilities

## Example Output

When running the simulator, you'll see output like:

```
Electric meter simulator starting...
Modbus TCP server listening on 127.0.0.1:5020
Meter data updating every second...
[2024-01-20 10:30:15] Consumption: 1234.56 kWh, Power: 5123.4 W
[2024-01-20 10:30:16] Consumption: 1234.57 kWh, Power: 4987.2 W
```

## Quick Start Example

1. **Start the simulator**:
   ```bash
   cargo run
   ```

2. **Test with Python** (install pymodbus first: `pip install pymodbus`):
   ```python
   from pymodbus.client.sync import ModbusTcpClient
   
   client = ModbusTcpClient('127.0.0.1', port=5020)
   client.connect()
   
   # Read all basic electric meter values
   result = client.read_holding_registers(0, 18)
   consumption = (result.registers[1] << 16) | result.registers[0]
   power = (result.registers[3] << 16) | result.registers[2]
   voltage_l1 = result.registers[10] / 10.0
   
   print(f"Energy: {consumption/100.0} kWh")
   print(f"Power: {power/10.0} W") 
   print(f"Voltage L1: {voltage_l1} V")
   
   client.close()
   ```

## License

This project is open source. Feel free to use and modify as needed.
