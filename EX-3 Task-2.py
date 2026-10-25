from collections import deque
import serial
import time
import numpy as np

# Configured for your COM5 port[cite: 10]
SERIAL_PORT = 'COM5'
BAUD_RATE = 9600

# Authorized list including your physical card and simulated cards[cite: 6]
authorized_cards = ["0006493766", "CARD1", "04AABBCCDD", "CARD2", "7890123456"]


def detect_circular_motion(ser, max_listen_window=5.0):
    print("\n" + "=" * 55)
    print("3. PROMPTING USER: PERFORM A PROPER CIRCULAR MOTION")
    print(f"4. ANALYZING RADIAL TRAJECTORY (Listening for {int(max_listen_window)}s)...")
    print("=" * 55)

    # Flush stale data from buffer so old movements don't carry over
    ser.reset_input_buffer()

    # Store a larger rolling window of points to capture full loops
    WINDOW_SIZE = 40
    x_window = deque(maxlen=WINDOW_SIZE)
    y_window = deque(maxlen=WINDOW_SIZE)

    start_time = time.time()

    while time.time() - start_time < max_listen_window:
        if ser.in_waiting > 0:
            raw_data = ser.readline().decode('utf-8', errors='ignore').strip()
            if raw_data.startswith("MPU:"):
                try:
                    values = raw_data[4:].split(',')
                    if len(values) >= 2:
                        x_window.append(int(values[0]))
                        y_window.append(int(values[1]))

                        # Evaluate when we have enough points for trajectory analysis
                        if len(x_window) >= 30:
                            x_arr = np.array(x_window)
                            y_arr = np.array(y_window)

                            # Calculate center and polar radii (matching your lab report algorithm)
                            cx, cy = np.mean(x_arr), np.mean(y_arr)
                            radii = np.sqrt((x_arr - cx) ** 2 + (y_arr - cy) ** 2)
                            mean_radius = np.mean(radii)
                            radius_spread = np.std(radii)

                            # Check condition: Meaningful radius size and low relative spread (stable circle)
                            if mean_radius > 1500 and (radius_spread / mean_radius) < 0.40:
                                print(
                                    f"--> Proper Circular Motion Verified! (Mean Radius: {mean_radius:.0f} LSB, Spread Ratio: {(radius_spread / mean_radius):.2f})")
                                ser.reset_input_buffer()
                                return True
                except ValueError:
                    pass
        time.sleep(0.01)

    print("--> Gesture Timeout: No proper circular trajectory detected.")
    ser.reset_input_buffer()
    return False


def main():
    print(f"Connecting to Arduino on {SERIAL_PORT}...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    time.sleep(2)  # Wait for Arduino reset

    print("Smart Access Control System Active!")

    try:
        while True:
            print("\n" + "-" * 55)
            # Step 1 & 2: Scans RFID tag automatically via USB HID reader / input prompt[cite: 6]
            card_uid = input("1. Scan RFID Card on Reader: ").strip().upper()

            print(f"-> Scanned UID: {card_uid}")

            # Step 2: Check if UID is authorized[cite: 6]
            if card_uid in authorized_cards:
                print("-> RFID Status: AUTHORIZED [PASS]")

                # Step 3 & 4: Prompt and analyze proper circular motion trajectory
                if detect_circular_motion(ser):
                    print("\n[RESULT] ACCESS GRANTED!")
                    print("5. Control: Servo Unlocked (180°) | Green LED ON (Pin 4) | Red LED OFF (Pin 3)")
                    ser.write(b'A')
                else:
                    print("\n[RESULT] ACCESS DENIED (Invalid Motion or Shake)!")
                    print("5. Control: Servo Locked (90°) | Red LED ON (Pin 3) | Green LED OFF (Pin 4)")
                    ser.write(b'D')
            else:
                print("-> RFID Status: UNAUTHORIZED CARD [FAIL]")
                print("\n[RESULT] ACCESS DENIED!")
                print("5. Control: Servo Locked (90°) | Red LED ON (Pin 3) | Green LED OFF (Pin 4)")
                ser.write(b'D')

            # Clear buffer before waiting for the next input line
            ser.reset_input_buffer()
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nExiting system...")
    finally:
        ser.close()
        print("Serial connection closed.")


if __name__ == "__main__":
    main()