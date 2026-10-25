from collections import deque
import time
import serial
import numpy as np

# Force matplotlib to use a standalone pop-up window backend
import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

# 1. Serial port setup (Adjust 'COM4' to match your Arduino)
ser = serial.Serial('COM4', 9600, timeout=1)
time.sleep(2)  # Allow Arduino to reset and clear serial buffer

# 2. Sliding window buffer (keeps last 100 points)
WINDOW_SIZE = 100
x_vals = deque(maxlen=WINDOW_SIZE)
y_vals = deque(maxlen=WINDOW_SIZE)

# 3. Setup standalone live plot
plt.close('all')  # Close any lingering graph windows
plt.ion()
fig, ax = plt.subplots(figsize=(7, 6))
ax.set_xlim(-20000, 20000)
ax.set_ylim(-20000, 20000)
ax.grid(True)
(line,) = ax.plot([], [], 'ro-', label='Motion Path')

status_text = ax.text(
    0.05,
    0.95,
    '',
    transform=ax.transAxes,
    fontsize=11,
    verticalalignment='top',
    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.6),
)


def detect_circular_motion(x, y):
    if len(x) < 30:
        return False

    x_arr = np.array(x)
    y_arr = np.array(y)

    cx, cy = np.mean(x_arr), np.mean(y_arr)
    radii = np.sqrt((x_arr - cx) ** 2 + (y_arr - cy) ** 2)
    mean_radius = np.mean(radii)

    if mean_radius > 1000 and (np.std(radii) / mean_radius) < 0.35:
        return True
    return False


print("Starting smooth live motion tracking in external window...")

frame_counter = 0

try:
    while True:
        # Check if the plot window was closed by the user
        if not plt.fignum_exists(fig.number):
            print('\nPlot window closed by user. Exiting...')
            break

        if ser.in_waiting > 0:
            raw_data = ser.readline()
            data = raw_data.decode('utf-8', errors='ignore').strip()

            if data:
                values = data.split(',')
                if len(values) >= 3:
                    try:
                        ax_val = int(values[0])
                        ay_val = int(values[1])

                        x_vals.append(ax_val)
                        y_vals.append(ay_val)

                        frame_counter += 1

                        # Throttle drawing: only update canvas every 3 packets to prevent lag
                        if frame_counter % 3 == 0:
                            line.set_data(list(x_vals), list(y_vals))

                            if detect_circular_motion(x_vals, y_vals):
                                status_text.set_text(
                                    'Gesture Detected: Circular Motion!'
                                )
                                line.set_color('green')
                            else:
                                status_text.set_text('Tracking motion...')
                                line.set_color('red')

                            # plt.pause processes GUI events and keeps the window responsive
                            plt.pause(0.001)

                    except ValueError:
                        continue
        else:
            # Short sleep to prevent 100% CPU usage when no serial data is ready
            time.sleep(0.005)

except KeyboardInterrupt:
    print('\nExiting program...')
finally:
    ser.close()
    plt.ioff()
    plt.close('all')