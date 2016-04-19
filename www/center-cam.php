<?php

// this file just sends the current object permissions through the pipe to our running robot.py script
// this is a test to see if the camera will center on the object.

$context = new ZMQContext();

//  Socket to talk to server
echo "Connecting to robot server…\n";
$requester = new ZMQSocket($context, ZMQ::SOCKET_REQ);
$requester->connect("tcp://localhost:5555");


$tracking_width = 320;
$tracking_height = 240;

$image_width = $_POST['image']['width'];
$image_height = $_POST['image']['height'];
$div = $tracking_width/$image_width;
$div_check = $tracking_height/$image_height;
if($div != $div_check){
	die('Failed to get crop dimensions');
}
$crop = $_POST['crop'];
$left = floor($crop['cropX'] * $div);
$top = floor($crop['cropY'] * $div);
$right = floor(($crop['cropX'] + $crop['cropW']) * $div);
$bottom = floor(($crop['cropY'] + $crop['cropH']) * $div);
$bbox = "$left:$top|$right:$top|$right:$bottom|$left:$bottom";

echo "sending $bbox <br>\n\n";
$requester->send($bbox);
$reply = $requester->recv();
echo "Done: $reply";
// socket.send(b"" + str(tl[0]) + ":" + str(tl[1]) + "|" + str(br[0]) + ":" + str(tl[1]) + "|" + str(br[0]) + ":" + str(br[1]) + "|" + str(tl[0]) + ":" + str(br[1]))
