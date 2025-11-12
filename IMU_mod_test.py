import qwiic_icm20948
import time

imu = qwiic_icm20948.QwiicIcm20948()

imu.begin()


try:
    while True:
        if imu.dataReady():
            imu.getAgmt()  # updates .ax, .ay, .az, .gx, .gy, .gz

            # acceleration (g)
            x_data.append(imu.ax)
            y_data.append(imu.ay)
            z_data.append(imu.az)

            # gyroscope (deg/s)
            x_rot_data.append(imu.gx)
            y_rot_data.append(imu.gy)
            z_rot_data.append(imu.gz)

            print(f"Accel: ({imu.ax:.2f}, {imu.ay:.2f}, {imu.az:.2f})  "
                  f"Gyro: ({imu.gx:.2f}, {imu.gy:.2f}, {imu.gz:.2f})")

            time.sleep(0.1)  # adjust for desired sampling rate

except KeyboardInterrupt:
    print("\nRecording stopped.")
