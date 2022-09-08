# FEETECH STS series Serial Servo
#FEETECH #STS series #STS3032 #Serial Servo #Steper motor #Serial stepper motor

FT serial servo library using the commands of the "Hansrobot protocol interface" to provide hooks for HansRobot Elfin robot arm on Windows, Mac or Linux.

Same as stepper motor with 4096(0 - 4095) steps and the driver board integrated inside the motor, so that the program can read the goal position, current position and move status from the motor. 

This servo motor with 4 working mode, 
1. DC motor mode, 
2. PWM servo mode. 
3. Serial servo mode and 
4. Stepper serial servo mode (Infinite serial servo mode). 

I'm currently developing a python library for servo mode and infinite servo mode. Hope can publish later.

## Features:
1. DC motor mode
2. Serial servo mode
3. Stepper serial servo mode (Infinite serial servo mode)
4. Less time.delay command is used, smoother action
5. More flexibility, such as the user can change the speed at any point

## STS serial motor default setting:
Servo ID = 1
Baudrate = 1000000

## Usage : Take the app.py as an example
1. Set the servo ID for each motor with the "_write_servo_chg_setting.ipynb"
    e.g. ID = 2, 3...
2. Run the app.py

## Youtube:
https://youtu.be/9ao2Iik1vsE