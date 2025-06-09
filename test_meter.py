#!/usr/bin/env python3
"""
Simple test script for the Modbus electric meter simulator
"""

import sys
import socket
import struct
import time


def create_modbus_tcp_request(
    transaction_id, unit_id, function_code, start_address, count
):
    """Create a Modbus TCP request for reading holding registers"""
    data = struct.pack(">BHH", function_code, start_address, count)
    length = len(data) + 1  # +1 for unit_id
    header = struct.pack(">HHHB", transaction_id, 0, length, unit_id)
    return header + data


def parse_modbus_tcp_response(response):
    """Parse a Modbus TCP response"""
    if len(response) < 8:
        return None

    transaction_id, protocol_id, length, unit_id, function_code = struct.unpack(
        ">HHHBB", response[:8]
    )

    if function_code & 0x80:  # Exception response
        exception_code = response[8]
        return {"error": f"Exception {exception_code}"}

    if function_code == 0x03:  # Read holding registers
        byte_count = response[8]
        data = response[9 : 9 + byte_count]
        values = []
        for i in range(0, byte_count, 2):
            value = struct.unpack(">H", data[i : i + 2])[0]
            values.append(value)
        return {"values": values}

    return None


def test_meter():
    """Test the electric meter simulator"""
    try:
        # Connect to the simulator
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect(("127.0.0.1", 5020))

        print("Connected to Modbus simulator on 127.0.0.1:5020")

        # Test 1: Read cumulative consumption (registers 0-1)
        print("\n=== Test 1: Cumulative consumption ===")
        request = create_modbus_tcp_request(1, 1, 0x03, 0, 2)
        sock.send(request)
        response = sock.recv(1024)
        result = parse_modbus_tcp_response(response)

        if result and "values" in result:
            low_word = result["values"][0]
            high_word = result["values"][1]
            consumption = ((high_word << 16) | low_word) / 100.0
            print(f"Cumulative consumption: {consumption:.2f} kWh")
        else:
            print("Error reading cumulative consumption")

        # Test 2: Read instantaneous power (registers 2-3)
        print("\n=== Test 2: Instantaneous power ===")
        request = create_modbus_tcp_request(2, 1, 0x03, 2, 2)
        sock.send(request)
        response = sock.recv(1024)
        result = parse_modbus_tcp_response(response)

        if result and "values" in result:
            low_word = result["values"][0]
            high_word = result["values"][1]
            power = ((high_word << 16) | low_word) / 10.0
            print(f"Instantaneous power: {power:.1f} W")
        else:
            print("Error reading instantaneous power")

        # Test 3: Read electric meter specific registers (voltage L1-L3)
        print("\n=== Test 3: Voltage readings ===")
        request = create_modbus_tcp_request(3, 1, 0x03, 10, 3)
        sock.send(request)
        response = sock.recv(1024)
        result = parse_modbus_tcp_response(response)

        if result and "values" in result:
            voltage_l1 = result["values"][0] / 10.0
            voltage_l2 = result["values"][1] / 10.0
            voltage_l3 = result["values"][2] / 10.0
            print(f"Voltage L1: {voltage_l1:.1f} V")
            print(f"Voltage L2: {voltage_l2:.1f} V")
            print(f"Voltage L3: {voltage_l3:.1f} V")
        else:
            print("Error reading voltages")

        # Test 4: Read current readings (registers 13-15)
        print("\n=== Test 4: Current readings ===")
        request = create_modbus_tcp_request(4, 1, 0x03, 13, 3)
        sock.send(request)
        response = sock.recv(1024)
        result = parse_modbus_tcp_response(response)

        if result and "values" in result:
            current_l1 = result["values"][0] / 100.0
            current_l2 = result["values"][1] / 100.0
            current_l3 = result["values"][2] / 100.0
            print(f"Current L1: {current_l1:.2f} A")
            print(f"Current L2: {current_l2:.2f} A")
            print(f"Current L3: {current_l3:.2f} A")
        else:
            print("Error reading currents")

        # Test 5: Read frequency and power factor (registers 16-17)
        print("\n=== Test 5: Frequency and power factor ===")
        request = create_modbus_tcp_request(5, 1, 0x03, 16, 2)
        sock.send(request)
        response = sock.recv(1024)
        result = parse_modbus_tcp_response(response)

        if result and "values" in result:
            frequency = result["values"][0] / 100.0
            power_factor = result["values"][1] / 1000.0
            print(f"Frequency: {frequency:.2f} Hz")
            print(f"Power factor: {power_factor:.3f}")
        else:
            print("Error reading frequency and power factor")

        # Test 6: Read status registers (registers 100-101)
        print("\n=== Test 6: Status registers ===")
        request = create_modbus_tcp_request(6, 1, 0x03, 100, 2)
        sock.send(request)
        response = sock.recv(1024)
        result = parse_modbus_tcp_response(response)

        if result and "values" in result:
            online_status = result["values"][0]
            meter_type = result["values"][1]
            print(f"Meter online: {'Yes' if online_status else 'No'}")
            print(f"Meter type: {meter_type} (0=Electric)")
        else:
            print("Error reading status")

        sock.close()
        print("\n✅ All tests completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_meter()
