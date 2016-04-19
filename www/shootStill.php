<?php


$context = new ZMQContext();

//$requester = new ZMQSocket($context, ZMQ::SOCKET_REQ);
//$requester->connect("tcp://localhost:5555");
//$requester->send("reset");
//$reply = $requester->recv();


$image = 'still.jpg';

//take still image with PiCamera and store it in '/var/www/img' directory
//edit the raspistill command here to taste but make sure not to remove the double quotes!
shell_exec("raspistill -w 640 -h 480 -q 80 -t 1000 -o /var/www/html/images/".$image);
//shell_exec("raspistill -w 240 -h 180 -q 80 -t 1000 -o /var/www/html/images/".$image);

echo '/images/'.$image.'?time='.time();