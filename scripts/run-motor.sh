#!/bin/bash
DEVICE=/dev/ttyAMA0
stty -F $DEVICE 19200
byte() {
  printf "\\x$(printf "%x" $1)"
}

stty raw -F $DEVICE

{
  #byte 0xC2 # m1 forward
  byte 0xDA # both alt
  #byte 0xD6 # both back
  #byte 0xD9 # both forward
  byte 10 #m1 speed
  byte 10 #m2 speed
} > $DEVICE

sleep 2;

{
  byte 0xD0 #both stop
  byte 0
  byte 0
} > $DEVICE
