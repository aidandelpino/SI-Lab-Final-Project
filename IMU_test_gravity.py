#!/usr/bin/env python3
import qwiic_icm20948
import time
import math
import numpy as np

# ---- Complementary filter parameters ----
ALPHA = 0.98  # Gyro weight (vs. accelerometer)
DT = 0.01     # Loop time (seconds)

def normalize(v):
    norm = np.linalg.norm(v)
    return v / norm if norm != 0 else v

# Convert gyro degrees/s to radians/s
def deg2rad(d):
    return d * math.pi / 180.0

# Rotation matrices from roll, pitch, yaw (XYZ order)
def euler_to_R(roll, pitch, yaw):
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    R = np.array([
        [cy*cp, cy*sp*sr - sy*cr, cy*sp*cr + sy*sr],
        [sy*cp, sy*sp*sr + cy*cr, sy*sp*cr - cy*sr],
        [-sp,   cp*sr,            cp*cr]
    ])
    return R

# ---- Initialize IMU ----
imu = qwiic_icm20948.QwiicIcm20948()
if not imu.connected:
    print("IMU not detected. Check wiring and address.")
    exit(1)

imu.begin()
print("ICM-20948 ready.\n")

# ---- Orientation initialization ----
roll, pitch, yaw = 0.0, 0.0, 0.0

t_last = time.time()

try:
    while True:
        if imu.dataReady():
            imu.getAgmt()
            
            # Raw sensor data
            ax, ay, az = imu.axRaw, imu.ayRaw, imu.azRaw
            gx, gy, gz = deg2rad(imu.gxRaw), deg2rad(imu.gyRaw), deg2rad(imu.gzRaw)

            # Time delta
            t_now = time.time()
            dt = t_now - t_last
            t_last = t_now

            # --- Gyro integration (predict orientation) ---
            roll_gyro  += gx * dt if 'roll_gyro' in locals() else gx * dt
            pitch_gyro += gy * dt if 'pitch_gyro' in locals() else gy * dt
            yaw_gyro   += gz * dt if 'yaw_gyro' in locals() else gz * dt

            # --- Accelerometer-based angles ---
            acc_vector = normalize(np.array([ax, ay, az]))
            pitch_acc = math.atan2(-acc_vector[0], math.sqrt(acc_vector[1]**2 + acc_vector[2]**2))
            roll_acc  = math.atan2(acc_vector[1], acc_vector[2])

            # --- Complementary filter ---
            roll  = ALPHA * (roll + gx * dt)   + (1 - ALPHA) * roll_acc
            pitch = ALPHA * (pitch + gy * dt)  + (1 - ALPHA) * pitch_acc
            yaw   = yaw + gz * dt  # Yaw unobservable w/o mag, but still integrate gyro

            # --- Remove gravity ---
            R = euler_to_R(roll, pitch, yaw)
            acc_world = R @ np.array([ax, ay, az])
            lin_acc = acc_world - np.array([0, 0, 9.81])  # subtract gravity

            print(f"Linear Acc (m/s²): X={lin_acc[0]:6.2f}, Y={lin_acc[1]:6.2f}, Z={lin_acc[2]:6.2f}")
            print(f"Gyro (deg/s): X={imu.gxRaw:6.2f}, Y={imu.gyRaw:6.2f}, Z={imu.gzRaw:6.2f}")
            print(f"Orientation (deg): Roll={math.degrees(roll):6.1f}, Pitch={math.degrees(pitch):6.1f}, Yaw={math.degrees(yaw):6.1f}\n")

        time.sleep(DT)

except KeyboardInterrupt:
    print("Stopping.")
