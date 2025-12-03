# GPIO setup
import RPi.GPIO as GPIO
import qwiic_icm20948
import time
import pygame
import numpy as np
from ahrs.filters import Madgwick
from ahrs.common.orientation import q2euler

GPIO.setmode(GPIO.BCM)

a1 = 23
a2 = 22
b1 = 17
b2 = 27
pins = [a1, a2, b1, b2]

for pin in pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)

GPIO.setup(24, GPIO.IN)

imu = qwiic_icm20948.QwiicIcm20948()
imu.begin()


madgwick = Madgwick()  # default beta, sample rate
q = np.array([1.0, 0.0, 0.0, 0.0])   # initial quaternion

try:
    while True:

        x_data_raw, y_data_raw, z_data_raw = [], [], []
        x_rot_data_raw, y_rot_data_raw, z_rot_data_raw = [], [], []

        
        roll_list, pitch_list, yaw_list = [], [], []

        count = 0

        try:
            while True:
                if GPIO.input(24) == 1:

                    if imu.dataReady():
                        count += 1
                        if count == 1:
                            print('recording...')
                        print(count)

                        imu.getAgmt()

                        # Raw accel
                        ax = imu.axRaw
                        ay = imu.ayRaw
                        az = imu.azRaw

                        # Raw gyro
                        gx = imu.gxRaw
                        gy = imu.gyRaw
                        gz = imu.gzRaw

                        x_data_raw.append(ax)
                        y_data_raw.append(ay)
                        z_data_raw.append(az)

                        x_rot_data_raw.append(gx)
                        y_rot_data_raw.append(gy)
                        z_rot_data_raw.append(gz)


                        # Convert accel to g units
                        ax_g = ax / 16384.0
                        ay_g = ay / 16384.0
                        az_g = az / 16384.0

                        # Convert gyro to rad/s (ICM20948 ⇒ LSB sensitivity depends on range)
                        # Assuming ±250 dps → 131 LSB/deg/s
                        gx_r = (gx / 131.0) * np.pi/180.0
                        gy_r = (gy / 131.0) * np.pi/180.0
                        gz_r = (gz / 131.0) * np.pi/180.0

                        gyro_vec = np.array([gx_r, gy_r, gz_r])
                        accel_vec = np.array([ax_g, ay_g, az_g])

                        # Update quaternion
                        q = madgwick.updateIMU(q, gyro_vec, accel_vec)

                        # Convert to Euler degrees
                        roll, pitch, yaw = np.degrees(q2euler(q))
                        roll_list.append(roll)
                        pitch_list.append(pitch)
                        yaw_list.append(yaw)

                        # ---------------------------

                        if GPIO.input(24) == 0:
                            break

                        time.sleep(0.01)

                else:
                    time.sleep(0.01)
                    if count != 0:
                        break

        except KeyboardInterrupt:
            print("\nRecording stopped.")



        x_data = x_data_raw
        y_data = y_data_raw
        z_data = z_data_raw

        x_rot_data = x_rot_data_raw
        y_rot_data = y_rot_data_raw
        z_rot_data = z_rot_data_raw

        def psuedorandom():
            avg_last_data = (x_data[-1] + y_data[-1] + z_data[-1]
                             + x_rot_data[-1] + y_rot_data[-1] + z_rot_data[-1]) / 6
            frac = abs(avg_last_data) % 1
            direction = int(frac * 10) % 2
            rotations = int(abs(frac * 10) % 1 * 10) + 2
            runtime = int(abs(frac * 100) % 10) + 3
            if runtime > 7:
                runtime -= 5
            return [direction, rotations, runtime]

        result = psuedorandom()

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
            print("Averages:", averages)
            return averages.index(max(averages))

        dominant_motion = determine_motion()

        def dimension():
            return [
                "environmental", "emotional", "physical", "financial",
                "spiritual", "intellectual", "social", "occupational"
            ][dominant_motion]

        print(result)
        print(dimension())


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
                
            if dimension == "environmental":
                    arrow = 26
                    audio = "Environmental.mp3"
            elif dimension == "emotional":
                    arrow = 70
                    audio = "Emotional.mp3"
            elif dimension == "physical":
                    arrow = 114
                    audio = "Physical.mp3"
            elif dimension == "financial":
                    arrow = 158
                    audio = "Financial.mp3"
            elif dimension == "spiritual":
                    arrow = 202
                    audio = "Spiritual.mp3"
            elif dimension == "intellectual":
                    arrow = 246
                    audio = "Intellectual.mp3"
            elif dimension == "social":
                    arrow = 290
                    audio = "Social.mp3"
            elif dimension == "occupational":
                    arrow = 334
                    audio = "Occupational.mp3"
                    
            if direction == 0:  # Clockwise
                matrix = FSCW 
                reverse = FSACW
                arrow_point = arrow/360
            else:  # Counterclockwise
                matrix = FSACW 
                reverse = FSCW
                arrow_point = (360-arrow)/360


            pygame.mixer.init()
            pygame.mixer.music.load("si_music.mp3")
            pygame.mixer.music.play()



            for i in range(int((rotations + arrow_point)*50*4)):
                turn = matrix[i % 4]
                for pin, val in zip(pins, turn):
                    GPIO.output(pin, val)
                time.sleep(runtime / 500)

            pygame.mixer.music.stop()

            pygame.mixer.music.load(audio)

            pygame.mixer.music.play()

            time.sleep(7)

            for i in range(int(50*4*arrow_point)):
                turn = reverse[i % 4]
                for pin, val in zip(pins, turn):
                    GPIO.output(pin, val)
                time.sleep(runtime / 500)

        spin(result[0], result[1], dimension(), result[2])

except KeyboardInterrupt:
    GPIO.cleanup()
