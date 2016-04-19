<?php


exec("ps auxwww|grep raspivid|grep -v grep", $output);
if(!$output) {
	$cmd = 'raspivid -o /var/www/html/video/video-' . time() . '.h264 -t 60000';
	$file = '/var/www/html/video/video-' . time() . '';
	$cmd = ' ( raspivid -t 30000 -w 640 -h 480 -fps 25 -b 1200000 -p 0,0,640,480 -o '.$file.'.h264 && MP4Box -add '.$file.'.h264 '.$file.'.mp4 && rm '.$file.'.h264 ) ';
	//$cmd .= ' > /tmp/raspvidoutput 2>&1 &';
	echo $cmd;
	set_time_limit(0);
	ini_set( 'display_errors', true );
	ini_set( 'error_reporting', E_ALL );
	exec( $cmd );
}