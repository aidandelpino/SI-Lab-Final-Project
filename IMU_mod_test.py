import qwiic_icm20948
import time

imu = qwiic_icm20948.QwiicIcm20948()

if imu.connected == False:
    print("IMU not connected. Check wiring.")
else:
    imu.begin()
    while True:
        if imu.dataReady():
            imu.getAgmt()
            print("Accel: X={:.2f}, Y={:.2f}, Z={:.2f}".format(imu.axRaw, imu.ayRaw, imu.azRaw))
            print("Gyro: X={:.2f}, Y={:.2f}, Z={:.2f}".format(imu.gxRaw, imu.gyRaw, imu.gzRaw))
            print("Mag: X={:.2f}, Y={:.2f}, Z={:.2f}".format(imu.mxRaw, imu.myRaw, imu.mzRaw))
            print("Temp: {:.2f} C\n".format(imu.temp))
        time.sleep(0.5)
