#!/usr/bin/env python3
"""
Quick demo script for the Electric Meter Simulator
This script demonstrates the key functionality of the electric meter simulator.
"""

from pymodbus.client.sync import ModbusTcpClient
import time


def main():
    print("🔌 Electric Meter Simulator Demo")
    print("=" * 50)

    # Connect to the simulator
    client = ModbusTcpClient("127.0.0.1", port=5020)
    if not client.connect():
        print("❌ Failed to connect to simulator. Make sure it's running:")
        print("   cargo run")
        return

    print("✅ Connected to electric meter simulator")

    try:
        # Read and display current meter values
        print("\n📊 Current Meter Readings:")
        print("-" * 30)

        # Read cumulative energy (32-bit value in registers 0-1)
        result = client.read_holding_registers(0, 2)
        consumption = (result.registers[1] << 16) | result.registers[0]
        print(f"⚡ Energy consumed: {consumption / 100.0:.2f} kWh")

        # Read instantaneous power (32-bit value in registers 2-3)
        result = client.read_holding_registers(2, 2)
        power = (result.registers[3] << 16) | result.registers[2]
        print(f"🔋 Current power: {power / 10.0:.1f} W")

        # Read all electrical parameters
        result = client.read_holding_registers(10, 8)
        voltage_l1 = result.registers[0] / 10.0
        voltage_l2 = result.registers[1] / 10.0
        voltage_l3 = result.registers[2] / 10.0
        current_l1 = result.registers[3] / 100.0
        current_l2 = result.registers[4] / 100.0
        current_l3 = result.registers[5] / 100.0
        frequency = result.registers[6] / 100.0
        power_factor = result.registers[7] / 1000.0

        print(
            f"📈 Voltage: L1={voltage_l1:.1f}V, L2={voltage_l2:.1f}V, L3={voltage_l3:.1f}V"
        )
        print(
            f"⚡ Current: L1={current_l1:.2f}A, L2={current_l2:.2f}A, L3={current_l3:.2f}A"
        )
        print(f"🎵 Frequency: {frequency:.2f} Hz")
        print(f"📐 Power factor: {power_factor:.3f}")

        # Show status
        print("\n🔍 System Status:")
        print("-" * 20)

        # Read coils (digital status)
        result = client.read_coils(0, 3)
        print(f"🟢 Meter online: {'Yes' if result.bits[0] else 'No'}")
        print(f"🔔 No alarms: {'Yes' if result.bits[1] else 'No'}")
        print(f"📡 Communication OK: {'Yes' if result.bits[2] else 'No'}")

        print("\n✨ Demo completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        client.close()


if __name__ == "__main__":
    main()
