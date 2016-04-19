<?php

// change in center-cam and relevant binaries as well.
$tracking_width = 240;
$tracking_height = 180;
$tracking_width = 320;
$tracking_height = 240;
//		$tracking_width = 640;
//		$tracking_height = 480;


if((int)$_POST['status'] && !empty($_POST['image']) && !empty($_POST['crop'])){


	file_put_contents('running-flag.txt', (int)$_POST['status']);


	switch($_POST['trackingmethod']){
		case 'cmt':


			// start tracking!
			// fire up our python procses in the background with our chosen dimensions and wait :)

			exec("ps auxwww|grep start.py|grep -v grep", $output);
			if(!$output){

				// script not running yet! start it.
				$image_width = $_POST['image']['width'];
				$image_height = $_POST['image']['height'];
				$div = $tracking_width/$image_width;
				$div_check = $tracking_height/$image_height;
				if($div != $div_check){
					die('Failed to get crop dimensions');
				}
				$crop = $_POST['crop'];
				$tlX = floor($crop['cropX'] * $div);
				$tlY = floor($crop['cropY'] * $div);
				$blX = floor($crop['cropW'] * $div);
				$blY = floor($crop['cropH'] * $div);
				$bbox = $tlX.','.$tlY.','.$blX.','.$blY;

				// 125,25,207,200

				$cmd = '';
				$cmd .= '( cd /var/www/html/CMT/ && ';
				$cmd .= '/usr/bin/python /var/www/html/CMT/start.py --width '.$tracking_width.' --height '.$tracking_height.' --bbox '.$bbox.'';
				if(isset($_POST['minspeed']) && (int)$_POST['minspeed'] > 0){
					$cmd .= ' --minspeed '.(int)$_POST['minspeed'];
				}
				if(isset($_POST['maxspeed']) && (int)$_POST['maxspeed'] < 30){
					$cmd .= ' --maxspeed '.(int)$_POST['maxspeed'];
				}
				$cmd .= ' --frameimage ../images/still.jpg';
				//$cmd .= ' --quiet ';
//		$cmd .= ' --output-dir /var/www/html/CMT/output ';
				$cmd .= ') ';
				$cmd .= '> /tmp/follow 2>&1 &';
				echo $cmd;
				ini_set('display_errors',true);
				ini_set('error_reporting',E_ALL);
				exec($cmd);

			}
			break;
		case 'cppmt-tes':

			// start tracking!
			// fire up our python procses in the background with our chosen dimensions and wait :)

			exec("ps auxwww|grep cmt|grep -v grep", $output);
			if(!$output){

				// script not running yet! start it.
				$image_width = $_POST['image']['width'];
				$image_height = $_POST['image']['height'];
				$div = $tracking_width/$image_width;
				$div_check = $tracking_height/$image_height;
				if($div != $div_check){
					die('Failed to get crop dimensions');
				}
				$crop = $_POST['crop'];
				$tlX = floor($crop['cropX'] * $div);
				$tlY = floor($crop['cropY'] * $div);
				$blX = floor($crop['cropW'] * $div);
				$blY = floor($crop['cropH'] * $div);
				$bbox = $tlX.','.$tlY.','.$blX.','.$blY;

				// 125,25,207,200

				$cmd = '';
				$cmd .= '/var/www/html/CppMT-tesYolan/build/cmt ';
				$cmd .= ' --bbox '.$bbox.'';
				//$cmd .= ' --width '.$tracking_width.' --height '.$tracking_height.' ';
				if(isset($_POST['minspeed']) && (int)$_POST['minspeed'] > 0){
					//$cmd .= ' --minspeed '.(int)$_POST['minspeed'];
				}
				if(isset($_POST['maxspeed']) && (int)$_POST['maxspeed'] < 30){
					//$cmd .= ' --maxspeed '.(int)$_POST['maxspeed'];
				}
				$cmd .= ' --frameimage ../images/still.jpg';
				$cmd .= ' --quiet ';
				$cmd .= ' --output-file /var/www/html/CppMT-tesYolan/build/log.txt ';
				$cmd .= '';
				$cmd .= '> /tmp/follow 2>&1 &';
				echo $cmd;
				ini_set('display_errors',true);
				ini_set('error_reporting',E_ALL);
				exec($cmd);

			}
			break;
		case 'dlibcpp':

			// start tracking!
			// fire up our python procses in the background with our chosen dimensions and wait :)

			exec("ps auxwww|grep dlib-track|grep -v grep", $output);
			if(!$output){

				$path = '/var/www/html/dlib-track/build/';
				$binary = 'test3';
				$still = '/var/www/html/images/still.jpg';

				// script not running yet! start it.
				$image_width = $_POST['image']['width'];
				$image_height = $_POST['image']['height'];
				$div = $tracking_width/$image_width;
				$div_check = $tracking_height/$image_height;
				if($div != $div_check){
					die('Failed to get crop dimensions');
				}
				$crop = $_POST['crop'];
				$tlX = floor($crop['cropX'] * $div);
				$tlY = floor($crop['cropY'] * $div);
				$blX = floor(($crop['cropX'] + $crop['cropW']) * $div);
				$blY = floor(($crop['cropY'] + $crop['cropH']) * $div);
				$bbox = $tlX.' '.$tlY.' '.$blX.' '.$blY;

				// 125,25,207,200

				$cmd = '';
				$cmd .= $path.$binary;
				$cmd .= ' '. $tlX.' '.$tlY.' '.$blX.' '.$blY;
				$cmd .= ' '.$tracking_width.' '.$tracking_height.' ';
				$cmd .= ' '.$still;
				if(isset($_POST['minspeed']) && (int)$_POST['minspeed'] > 0){
					//$cmd .= ' --minspeed '.(int)$_POST['minspeed'];
				}
				if(isset($_POST['maxspeed']) && (int)$_POST['maxspeed'] < 30){
					//$cmd .= ' --maxspeed '.(int)$_POST['maxspeed'];
				}
				$cmd .= '> /tmp/follow 2>&1 &';
				echo $cmd;
				ini_set('display_errors',true);
				ini_set('error_reporting',E_ALL);
				exec($cmd);

			}
			break;
	}

}else{
	unlink('running-flag.txt');
}
