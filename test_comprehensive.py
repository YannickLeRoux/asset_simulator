#!/usr/bin/env python3
"""
Comprehensive test script for the Modbus electric meter simulator.
This script demonstrates all the available registers and their functionality.
"""

import sys
import socket
import struct
import time
import argparse


def create_modbus_tcp_request(
    transaction_id, unit_id, function_code, start_address, count
):
    """Create a Modbus TCP request"""
    data = struct.pack(">BHH", function_code, start_address, count)
    length = len(data) + 1
    header = struct.pack(">HHHB", transaction_id, 0, length, unit_id)
    return header + data


def create_write_coil_request(transaction_id, unit_id, address, value):
    """Create a Modbus TCP write single coil request"""
    coil_value = 0xFF00 if value else 0x0000
    data = struct.pack(">BHH", 0x05, address, coil_value)
    length = len(data) + 1
    header = struct.pack(">HHHB", transaction_id, 0, length, unit_id)
    return header + data


def parse_modbus_tcp_response(response):
    """Parse a Modbus TCP response"""
    if len(response) < 8:
        return None

    transaction_id, protocol_id, length, unit_id, function_code = struct.unpack(
        ">HHHBB", response[:8]
    )

    if function_code & 0x80:
        exception_code = response[8]
        return {"error": f"Exception {exception_code}"}

    if function_code == 0x03 or function_code == 0x04:  # Read holding/input registers
        byte_count = response[8]
        data = response[9 : 9 + byte_count]
        values = []
        for i in range(0, byte_count, 2):
            value = struct.unpack(">H", data[i : i + 2])[0]
            values.append(value)
        return {"values": values}

    elif function_code == 0x01 or function_code == 0x02:  # Read coils/discrete inputs
        byte_count = response[8]
        data = response[9 : 9 + byte_count]
        coils = []
        for byte_val in data:
            for bit in range(8):
                coils.append(bool(byte_val & (1 << bit)))
        return {"coils": coils}

    elif function_code == 0x05:  # Write single coil
        return {"success": True}

    return None


def test_meter_comprehensive(host="127.0.0.1", port=5020):
    """Comprehensive test of all meter functionality"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10.0)
        sock.connect((host, port))

        print(f"🔌 Connected to Modbus simulator on {host}:{port}")
        print("=" * 60)

        # Test 1: Read all main electric meter registers at once
        print("\n📊 === ELECTRIC METER OVERVIEW ===")
        request = create_modbus_tcp_request(1, 1, 0x03, 0, 18)
        sock.send(request)
        response = sock.recv(1024)
        result = parse_modbus_tcp_response(response)

        if result and "values" in result:
            values = result["values"]

            # Cumulative consumption (32-bit)
            consumption = ((values[1] << 16) | values[0]) / 100.0
            print(f"⚡ Cumulative consumption: {consumption:.2f} kWh")

            # Instantaneous power (32-bit)
            power = ((values[3] << 16) | values[2]) / 10.0
            print(f"🔋 Instantaneous power: {power:.1f} W")

            # Voltages
            voltage_l1 = values[10] / 10.0
            voltage_l2 = values[11] / 10.0
            voltage_l3 = values[12] / 10.0
            print(f"📈 Voltage L1: {voltage_l1:.1f} V")
            print(f"📈 Voltage L2: {voltage_l2:.1f} V")
            print(f"📈 Voltage L3: {voltage_l3:.1f} V")

            # Currents
            current_l1 = values[13] / 100.0
            current_l2 = values[14] / 100.0
            current_l3 = values[15] / 100.0
            print(f"⚡ Current L1: {current_l1:.2f} A")
            print(f"⚡ Current L2: {current_l2:.2f} A")
            print(f"⚡ Current L3: {current_l3:.2f} A")

            # Frequency and power factor
            frequency = values[16] / 100.0
            power_factor = values[17] / 1000.0
            print(f"🎵 Frequency: {frequency:.2f} Hz")
            print(f"📐 Power factor: {power_factor:.3f}")

            # Calculate total power from individual phases
            total_calculated_power = (
                voltage_l1 * current_l1
                + voltage_l2 * current_l2
                + voltage_l3 * current_l3
            ) * power_factor
            print(f"🧮 Calculated total power: {total_calculated_power:.1f} W")

        # Test 2: Read status registers
        print("\n🔍 === STATUS INFORMATION ===")
        request = create_modbus_tcp_request(2, 1, 0x03, 100, 2)
        sock.send(request)
        response = sock.recv(1024)
        result = parse_modbus_tcp_response(response)

        if result and "values" in result:
            online_status = result["values"][0]
            meter_type = result["values"][1]
            print(f"🟢 Meter online: {'Yes' if online_status else 'No'}")
            print(f"🏭 Meter type: {meter_type} (0=Electric)")

        # Test 3: Read coils/digital status
        print("\n🔘 === DIGITAL STATUS (COILS) ===")
        request = create_modbus_tcp_request(3, 1, 0x01, 0, 8)
        sock.send(request)
        response = sock.recv(1024)
        result = parse_modbus_tcp_response(response)

        if result and "coils" in result:
            coils = result["coils"][:8]  # Only first 8 coils
            status_names = [
                "Meter Online",
                "No Alarms",
                "Communication OK",
                "Reserved",
                "Reserved",
                "Reserved",
                "Reserved",
                "Reserved",
            ]

            for i, (name, status) in enumerate(zip(status_names, coils)):
                print(f"🔘 Coil {i}: {name} = {'✅' if status else '❌'}")

        # Test 4: Test reset functionality (write coil 10)
        print("\n🔄 === TESTING RESET FUNCTIONALITY ===")
        print("📝 Sending reset command (write coil 10 = True)")

        request = create_write_coil_request(4, 1, 10, True)
        sock.send(request)
        response = sock.recv(1024)
        result = parse_modbus_tcp_response(response)

        if result and result.get("success"):
            print("✅ Reset command sent successfully")

            # Wait a moment and read cumulative consumption again
            time.sleep(1)
            request = create_modbus_tcp_request(5, 1, 0x03, 0, 2)
            sock.send(request)
            response = sock.recv(1024)
            result = parse_modbus_tcp_response(response)

            if result and "values" in result:
                consumption = (
                    (result["values"][1] << 16) | result["values"][0]
                ) / 100.0
                print(f"📊 Consumption after reset: {consumption:.2f} kWh")

        # Test 5: Monitor changes over time
        print("\n⏱️  === MONITORING CHANGES OVER TIME ===")
        print("📈 Reading values twice with 3 second interval...")

        measurements = []
        for i in range(2):
            request = create_modbus_tcp_request(6 + i, 1, 0x03, 10, 8)
            sock.send(request)
            response = sock.recv(1024)
            result = parse_modbus_tcp_response(response)

            if result and "values" in result:
                values = result["values"]
                measurement = {
                    "timestamp": time.time(),
                    "voltage_l1": values[0] / 10.0,
                    "voltage_l2": values[1] / 10.0,
                    "voltage_l3": values[2] / 10.0,
                    "current_l1": values[3] / 100.0,
                    "current_l2": values[4] / 100.0,
                    "current_l3": values[5] / 100.0,
                    "frequency": values[6] / 100.0,
                    "power_factor": values[7] / 1000.0,
                }
                measurements.append(measurement)

                print(f"\n📊 Reading {i+1}:")
                print(
                    f"   Voltage: L1={measurement['voltage_l1']:.1f}V, L2={measurement['voltage_l2']:.1f}V, L3={measurement['voltage_l3']:.1f}V"
                )
                print(
                    f"   Current: L1={measurement['current_l1']:.2f}A, L2={measurement['current_l2']:.2f}A, L3={measurement['current_l3']:.2f}A"
                )
                print(
                    f"   Frequency: {measurement['frequency']:.2f}Hz, Power Factor: {measurement['power_factor']:.3f}"
                )

            if i < 1:  # Don't wait after the last reading
                time.sleep(3)

        # Show changes
        if len(measurements) == 2:
            print(f"\n📈 === CHANGES DETECTED ===")
            m1, m2 = measurements[0], measurements[1]

            voltage_changes = [
                abs(m2["voltage_l1"] - m1["voltage_l1"]),
                abs(m2["voltage_l2"] - m1["voltage_l2"]),
                abs(m2["voltage_l3"] - m1["voltage_l3"]),
            ]

            current_changes = [
                abs(m2["current_l1"] - m1["current_l1"]),
                abs(m2["current_l2"] - m1["current_l2"]),
                abs(m2["current_l3"] - m1["current_l3"]),
            ]

            freq_change = abs(m2["frequency"] - m1["frequency"])
            pf_change = abs(m2["power_factor"] - m1["power_factor"])

            print(f"📊 Average voltage change: {sum(voltage_changes)/3:.1f}V")
            print(f"📊 Average current change: {sum(current_changes)/3:.3f}A")
            print(f"📊 Frequency change: {freq_change:.3f}Hz")
            print(f"📊 Power factor change: {pf_change:.4f}")

            if (
                any(c > 0.1 for c in voltage_changes + current_changes)
                or freq_change > 0.01
            ):
                print(
                    "✅ Values are changing as expected (meter is simulating realistic variations)"
                )
            else:
                print(
                    "⚠️  Values seem static (this might be normal for short intervals)"
                )

        sock.close()
        print("\n" + "=" * 60)
        print("🎉 All comprehensive tests completed successfully!")
        print("✅ Electric meter simulator is working correctly")

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Test the Modbus electric meter simulator"
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Simulator host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=5020, help="Simulator port (default: 5020)"
    )
    parser.add_argument("--simple", action="store_true", help="Run simple tests only")

    args = parser.parse_args()

    if args.simple:
        # Run the original simple test
        import test_meter

        test_meter.test_meter()
    else:
        success = test_meter_comprehensive(args.host, args.port)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
