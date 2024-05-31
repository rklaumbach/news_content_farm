#!/bin/bash

# Prevent the display from turning off
xset s off -dpms
xset s noblank

# Run the target script with passed arguments
python3 gen_video.py "$@"

# Restore the display settings
xset s on +dpms
xset s blank
