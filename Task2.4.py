import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM) #set the GPIO pin mode
GPIO.setup(12, GPIO.OUT) #setup the pin for PWM output

pi_pwm = GPIO.PWM(12, 50) #pin number and frequency in Hz
pi_pwm.start(0) #start the PWM signal as just a flat line at 0

try:
    while True:
        user_input = input("what is your desired duty cycle? (between 2 and 13)") #prompt the user for a servo angle
        try:
            angle = float(user_input)
            if 2 <= angle <= 13:
                print(angle)
                DC = angle #convert the inputted angle to the corresponding duty cycle
                print(DC)
                pi_pwm.ChangeDutyCycle(DC)
            else:
                print("that angle is not within the specified range, try again")
        except ValueError:
            print("I don't think thats an angle, try something else")
        sleep(0.1)
except KeyboardInterrupt:
    pi_pwm.stop()
    GPIO.output(12,False)
    print("program stopped")
