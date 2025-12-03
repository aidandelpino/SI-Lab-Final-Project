#!/usr/bin/env python3
# imu_with_gravity_removal.py
import time
import math
import RPi.GPIO as GPIO
import qwiic_icm20948
import pygame
import numpy as np
from ahrs.filters import Madgwick

GPIO.setmode(GPIO.BCM)

# --- GPIO / stepper pins ---
a1 = 23
a2 = 22
b1 = 17
b2 = 27
pins = [a1, a2, b1, b2]

for pin in pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)

GPIO.setup(24, GPIO.IN)  # input to start/stop recording

# --- IMU ---
imu = qwiic_icm20948.QwiicIcm20948()
if not imu.begin():
    raise RuntimeError("Failed to initialize IMU. Check connection and I2C.")

# --- Madgwick filter ---
madgwick = Madgwick()            # default beta; tune if needed
q = np.array([1.0, 0.0, 0.0, 0.0])  # quaternion w,x,y,z initial

# Conversion assumptions (adjust if your library already returns scaled values)
LSB_PER_G = 16384.0   # accelerometer LSB per g at +/-2g (ICM typical)
LSB_PER_DPS = 131.0   # gyro LSB per deg/s at +/-250 dps (ICM typical)
G_TO_MS2 = 9.80665

def raw_acc_to_ms2(ax_raw, ay_raw, az_raw):
    """Convert accel raw LSB -> m/s^2 (assumes ±2g range)."""
    ax_g = ax_raw / LSB_PER_G
    ay_g = ay_raw / LSB_PER_G
    az_g = az_raw / LSB_PER_G
    return ax_g * G_TO_MS2, ay_g * G_TO_MS2, az_g * G_TO_MS2

def raw_gyro_to_rads(gx_raw, gy_raw, gz_raw):
    """Convert gyro raw LSB -> rad/s (assumes ±250 dps)."""
    gx_dps = gx_raw / LSB_PER_DPS
    gy_dps = gy_raw / LSB_PER_DPS
    gz_dps = gz_raw / LSB_PER_DPS
    return math.radians(gx_dps), math.radians(gy_dps), math.radians(gz_dps)

def gravity_from_quaternion(q):
    """Compute gravity unit vector (body frame) from quaternion.
       q = [w, x, y, z]
       returns (gx, gy, gz) as unit vector (in g units)
    """
    q0, q1, q2, q3 = q
    gx = 2.0 * (q1 * q3 - q0 * q2)
    gy = 2.0 * (q0 * q1 + q2 * q3)
    gz = q0*q0 - q1*q1 - q2*q2 + q3*q3
    return np.array([gx, gy, gz])

# --- Stepper control matrices (unchanged) ---
FSCW = [
    [1,0,0,1],
    [1,0,1,0],
    [0,1,1,0],
    [0,1,0,1]
]

FSACW = [
    [0,1,0,1],
    [0,1,1,0],
    [1,0,1,0],
    [1,0,0,1]
]

def spin(direction, rotations, dimension, runtime):
    # select arrow and audio per dimension
    if dimension == "environmental":
        arrow = 26; audio = "Environmental.mp3"
    elif dimension == "emotional":
        arrow = 70; audio = "Emotional.mp3"
    elif dimension == "physical":
        arrow = 114; audio = "Physical.mp3"
    elif dimension == "financial":
        arrow = 158; audio = "Financial.mp3"
    elif dimension == "spiritual":
        arrow = 202; audio = "Spiritual.mp3"
    elif dimension == "intellectual":
        arrow = 246; audio = "Intellectual.mp3"
    elif dimension == "social":
        arrow = 290; audio = "Social.mp3"
    elif dimension == "occupational":
        arrow = 334; audio = "Occupational.mp3"
    else:
        arrow = 0; audio = "si_music.mp3"

    if direction == 0:
        matrix = FSCW
        reverse = FSACW
        arrow_point = arrow / 360.0
    else:
        matrix = FSACW
        reverse = FSCW
        arrow_point = (360 - arrow) / 360.0

    pygame.mixer.init()
    pygame.mixer.music.load("si_music.mp3")
    pygame.mixer.music.play()

    for i in range(int((rotations + arrow_point) * 50 * 4)):
        turn = matrix[i % 4]
        for pin, val in zip(pins, turn):
            GPIO.output(pin, val)
        time.sleep(runtime / 500.0)

    pygame.mixer.music.stop()
    pygame.mixer.music.load(audio)
    pygame.mixer.music.play()

    time.sleep(7)

    for i in range(int(50 * 4 * arrow_point)):
        turn = reverse[i % 4]
        for pin, val in zip(pins, turn):
            GPIO.output(pin, val)
        time.sleep(runtime / 500.0)

# Main loop
try:
    while True:
        # lists for raw & fused linear accel & gyro
        x_data_raw, y_data_raw, z_data_raw = [], [], []
        x_rot_data_raw, y_rot_data_raw, z_rot_data_raw = [], [], []

        # *** These will contain gravity-removed linear accel in m/s^2 ***
        lin_x, lin_y, lin_z = [], [], []

        count = 0
        last_t = time.time()

        try:
            while True:
                # wait for input pin high to record
                if GPIO.input(24) == 1:
                    if imu.dataReady():
                        count += 1
                        if count == 1:
                            print('recording...')
                        print(count)

                        imu.getAgmt()  # read fresh IMU values

                        # Read raw values from the library object.
                        # You used .axRaw previously; keep those names:
                        ax_raw = getattr(imu, "axRaw", None)
                        ay_raw = getattr(imu, "ayRaw", None)
                        az_raw = getattr(imu, "azRaw", None)

                        gx_raw = getattr(imu, "gxRaw", None)
                        gy_raw = getattr(imu, "gyRaw", None)
                        gz_raw = getattr(imu, "gzRaw", None)

                        # Some qwiic libraries expose .ax/.gx scaled already.
                        # If any of the raw fields are None, try alternative attribute names:
                        if ax_raw is None:
                            ax_raw = getattr(imu, "ax", 0.0)
                        if ay_raw is None:
                            ay_raw = getattr(imu, "ay", 0.0)
                        if az_raw is None:
                            az_raw = getattr(imu, "az", 0.0)
                        if gx_raw is None:
                            gx_raw = getattr(imu, "gx", 0.0)
                        if gy_raw is None:
                            gy_raw = getattr(imu, "gy", 0.0)
                        if gz_raw is None:
                            gz_raw = getattr(imu, "gz", 0.0)

                        # Append raw lists (for reference / debugging)
                        x_data_raw.append(ax_raw)
                        y_data_raw.append(ay_raw)
                        z_data_raw.append(az_raw)
                        x_rot_data_raw.append(gx_raw)
                        y_rot_data_raw.append(gy_raw)
                        z_rot_data_raw.append(gz_raw)

                        # --- Convert to physical units ---
                        # accel -> m/s^2, gyro -> rad/s (for filter)
                        ax_ms2, ay_ms2, az_ms2 = raw_acc_to_ms2(ax_raw, ay_raw, az_raw)
                        gx_rads, gy_rads, gz_rads = raw_gyro_to_rads(gx_raw, gy_raw, gz_raw)

                        # For Madgwick.updateIMU we need accel as a unit vector (g units)
                        # So use accel normalized to g (i.e., divide m/s^2 by 9.80665)
                        ax_g_unit = ax_ms2 / G_TO_MS2
                        ay_g_unit = ay_ms2 / G_TO_MS2
                        az_g_unit = az_ms2 / G_TO_MS2

                        # Update Madgwick sample period dynamically
                        now = time.time()
                        dt = now - last_t if (now - last_t) > 0 else 1e-3
                        last_t = now
                        madgwick.sample_period = dt

                        # Update quaternion using gyro (rad/s) and accel unit vector (not scaled)
                        # Note: the ahrs.Madgwick.updateIMU expects (q, gyr, acc) or (q, gyr, acc, mag)
                        try:
                            q = madgwick.updateIMU(q, np.array([gx_rads, gy_rads, gz_rads]), 
                                                   np.array([ax_g_unit, ay_g_unit, az_g_unit]))
                        except TypeError:
                            # some versions use different signature order: try alternative
                            q = madgwick.updateIMU(np.array([gx_rads, gy_rads, gz_rads]),
                                                   np.array([ax_g_unit, ay_g_unit, az_g_unit]), q)

                        # Compute gravity unit vector from quaternion (in g units)
                        g_body_unit = gravity_from_quaternion(q)  # units: 1*g

                        # Convert gravity to m/s^2 and subtract from measured accel (m/s^2)
                        gravity_ms2 = g_body_unit * G_TO_MS2
                        linear_acc_ms2 = np.array([ax_ms2, ay_ms2, az_ms2]) - gravity_ms2

                        # Append linear acceleration lists
                        lin_x.append(float(linear_acc_ms2[0]))
                        lin_y.append(float(linear_acc_ms2[1]))
                        lin_z.append(float(linear_acc_ms2[2]))

                        # If input goes low mid-recording, break out
                        if GPIO.input(24) == 0:
                            break

                        # respect sampling delay
                        time.sleep(0.01)  # ~100 Hz target

                else:
                    # idle waiting for record start
                    time.sleep(0.01)
                    # if we have recorded and button released, break to processing stage
                    if count != 0:
                        break

        except KeyboardInterrupt:
            print("\nRecording stopped.")

        # === Now use gravity-removed acceleration (lin_x, lin_y, lin_z)
        # If no data (edge case) put a zero to avoid division by zero later
        if not lin_x:
            lin_x.append(0.0)
        if not lin_y:
            lin_y.append(0.0)
        if not lin_z:
            lin_z.append(0.0)
        if not x_rot_data_raw:
            x_rot_data_raw.append(0.0)
            y_rot_data_raw.append(0.0)
            z_rot_data_raw.append(0.0)

        # Use linear accel for subsequent analysis:
        x_data = lin_x
        y_data = lin_y
        z_data = lin_z

        # Convert raw gyro LSB -> deg/s for your existing code's use (so values are human-friendly)
        x_rot_data = [gx_r / LSB_PER_DPS for gx_r in x_rot_data_raw]
        y_rot_data = [gy_r / LSB_PER_DPS for gy_r in y_rot_data_raw]
        z_rot_data = [gz_r / LSB_PER_DPS for gz_r in z_rot_data_raw]

        # --- existing psuedorandom function (unchanged except it uses the new x_data etc) ---
        def psuedorandom():
            avg_last_data = (x_data[-1] + y_data[-1] + z_data[-1] + x_rot_data[-1] + y_rot_data[-1] + z_rot_data[-1]) / 6
            frac = abs(avg_last_data) % 1
            dir = int(frac * 10)
            direction = dir % 2
            dir_frac = abs(frac * 10) % 1
            rots = int(dir_frac * 10)
            rotations = rots + 2
            rot_frac = abs(dir_frac * 10) % 1
            rt = int(rot_frac * 10)
            runtime = rt + 3
            if runtime > 7:
                runtime = runtime - 5
            return [direction, rotations, runtime]

        result = psuedorandom()

        # Make sure the dominant motion gives its dimension (the same logic but uses linear accel)
        y_neg_data = [y for y in y_data if y < 0]
        y_pos_data = [y for y in y_data if y > 0]
        z_pos_data = [z for z in z_data if z > 0]
        z_neg_data = [z for z in z_data if z < 0]

        def determine_motion():
            x_avg = sum(abs(x) for x in x_data) / len(x_data)
            y_neg_avg = sum(abs(y) for y in y_neg_data) / len(y_neg_data) if y_neg_data else 0
            y_pos_avg = sum(abs(y) for y in y_pos_data) / len(y_pos_data) if y_pos_data else 0
            z_neg_avg = sum(abs(z) for z in z_neg_data) / len(z_neg_data) if z_neg_data else 0
            z_pos_avg = sum(abs(z) for z in z_pos_data) / len(z_pos_data) if z_pos_data else 0
            xr_avg = sum(abs(xr) for xr in x_rot_data) / len(x_rot_data)
            yr_avg = sum(abs(yr) for yr in y_rot_data) / len(y_rot_data)
            zr_avg = sum(abs(zr) for zr in z_rot_data) / len(z_rot_data)

            averages = [x_avg, y_neg_avg, y_pos_avg, z_neg_avg, z_pos_avg, xr_avg, yr_avg, zr_avg]

            max_avg = max(averages)
            print("Averages:", averages)
            return averages.index(max_avg)

        dominant_motion = determine_motion()

        def dimension():
            if dominant_motion == 0:
                return 'environmental'
            elif dominant_motion == 1:
                return "emotional"
            elif dominant_motion == 2:
                return "physical"
            elif dominant_motion == 3:
                return "financial"
            elif dominant_motion == 4:
                return 'spiritual'
            elif dominant_motion == 5:
                return 'intellectual'
            elif dominant_motion == 6:
                return 'social'
            elif dominant_motion == 7:
                return 'occupational'

        print(result)
        print(dimension())

        # call spin as before (unchanged)
        spin(result[0], result[1], dimension(), result[2])

except KeyboardInterrupt:
    print("Cleaning up GPIO...")
    GPIO.cleanup()
