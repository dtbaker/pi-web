<?php

$image = 'still.jpg';

//take still image with PiCamera and store it in '/var/www/img' directory
//edit the raspistill command here to taste but make sure not to remove the double quotes!
shell_exec("raspistill -w 640 -h 480 -q 80 -t 1000 -o /var/www/html/images/".$image);

echo '/images/'.$image.'?time='.time();