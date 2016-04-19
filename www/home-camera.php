<?php


$context = new ZMQContext();

//  Socket to talk to server
$requester = new ZMQSocket($context, ZMQ::SOCKET_REQ);
$requester->connect("tcp://localhost:5555");

$requester->send("reset");
$reply = $requester->recv();

echo 'done';