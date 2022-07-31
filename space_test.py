'''
Code for testing Arducam motor camera + Neo Pixel + Pi zero in space environment 
Using script.

Usage: camera_demo.py output_prefix
Where
    output_prefix is output file prefix or file name

The script will take a picture with no LEDs then R,G,B seperatly each picture is saved to output_prefix

'''

import sys
import time
import serial
import os
import board
import neopixel
from datetime import datetime
import logging
import threading
from ctypes import *
import traceback
from gpiozero import CPUTemperature
from gpiozero import LoadAverage
from camera_handler import CameraHandler
import pathlib
from timeit import default_timer as timer
import time
import RPi.GPIO as GPIO
import tarfile

pixels = neopixel.NeoPixel(board.D21, 5,brightness =1)
this_file_directory = str(pathlib.Path(__file__).parent.resolve())
GPIO.setmode(GPIO.BCM)
LED_ENABLE_PIN = 23
GPIO.setup(LED_ENABLE_PIN,GPIO.OUT)

# takes a picture from Arducam camera
def take_pic(output_prefix,focus ,r, g, b):
    # Figure out what image number is this
    with open(this_file_directory + "/number_of_images_taken.txt", "r+") as f:
        number_of_images_taken = int(f.read())
        f.seek(0)
        f.write(str(number_of_images_taken+1))
        f.truncate()

    # Generate Image file name
    print("About to take an image (#%d). Focus:%d, Red:%d, Green:%d, Blue:%d" %(number_of_images_taken,focus,r,g,b))
    image_file_name = "{0}_SN{5:05d}_F{1:04d}_R{2:03d}_G{3:03d}_B{4:03d}.jpg".format(output_prefix,focus,r,g,b,number_of_images_taken)
    
    # Turn on LEDs
    LED_start = timer()
    GPIO.output(LED_ENABLE_PIN, True)# Turn on Neo pixel enable line
    time.sleep(0.5)        # Wait for stabilization
    pixels.fill((r, g, b)) # Neo pixel
    pixels.show()          # Neo pixel
    time.sleep(0.5)        # Wait for stabilization
    
    # Take the picture
    camera = CameraHandler()
    camera.change_focus(focus)
    camera.take_pic_scp2(image_file_name)
    
    # Turn off LEDs
    pixels.fill((0, 0 , 0))
    pixels.show()
    GPIO.output(LED_ENABLE_PIN, False)# Turn on Neo pixel enable line
    LED_end = timer()
    
    # Report the aftermath
    LED_on_sec = LED_end-LED_start
    print("LEDs were on for %.3f sec"%(LED_on_sec))
    
    # Append data to LED table
    with open(this_file_directory + "/activity_log.txt", "a") as f:
        #f.write("SN,Focus,R,G,B,LED_on_sec\n")
        f.write("{0:05d},{1:04d},{2:03d},{3:03d},{4:04d},{5:.3f}\n".format(number_of_images_taken,focus,r,g,b,LED_on_sec))
    
    return image_file_name

# Save all images together
def tar_images(output_prefix, list_of_files):
    output_filename = output_prefix + "_all.tar"
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(this_file_directory + "/activity_log.txt")
        for file_path in list_of_files:
            tar.add(file_path)
            
    return(output_filename)


# get telemetry data
def get_telemetry():
    cpu_temp = CPUTemperature()
    cpu_temp = int(cpu_temp.temperature)
    cpu_load = int(LoadAverage(minutes=1).load_average*100)
    in_bytes = cpu_temp.to_bytes(1,'big')
    ser.write(in_bytes)
    in_bytes = cpu_load.to_bytes(1,'big')
    ser.write(in_bytes)
    with open ('uptime.txt','r') as the_file:
        uptime = int(the_file.read())
    in_bytes = uptime.to_bytes(3,'big')
    ser.write(in_bytes)
    print("Sent telemetry. CPU temp: %d, cpu load: %d, uptime: %d" % (cpu_temp,cpu_load, uptime))

if __name__ == "__main__":
    try:
        # Inputs
        r = 100
        g = 100
        b = 100
        focus1 = 1000
        focus2 = 100
        
        if len(sys.argv) > 1:
            output_prefix = sys.argv[1]
        else:
            output_prefix = 'image_'
                    
        # Take pictures
        image_names = []
        image_names.append(take_pic(output_prefix, focus1 ,0, 0, 0)) # No light (Black)
        image_names.append(take_pic(output_prefix, focus1 ,r, 0, 0)) # R
        image_names.append(take_pic(output_prefix, focus1 ,0, g, 0)) # G
        image_names.append(take_pic(output_prefix, focus1 ,0, 0, b)) # B
        image_names.append(take_pic(output_prefix, focus1 ,r, g, b)) # W (focus1)
        image_names.append(take_pic(output_prefix, focus2 ,r, g, b)) # W (focus2)
        
        # TAR all images together
        tar_file_name = tar_images(output_prefix,image_names)
        print("All files are in TAR %s" % tar_file_name)

    except Exception:
        print(traceback.format_exc())
