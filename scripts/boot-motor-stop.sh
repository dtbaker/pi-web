#!/bin/bash
DEVICE=/dev/ttyAMA0
stty -F $DEVICE 19200
byte() {
  printf "\\x$(printf "%x" $1)"
}

stty raw -F $DEVICE

{
  byte 0xD0 #both stop
  byte 0
  byte 0
} > $DEVICE

echo "Done";
