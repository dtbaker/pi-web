<?php


if((int)$_POST['status'] && !empty($_POST['image']) && !empty($_POST['crop'])){

	file_put_contents('CMT/running-flag.txt', (int)$_POST['status']);

	// start tracking!
	// fire up our python procses in the background with our chosen dimensions and wait :)


	exec("ps auxwww|grep start.py|grep -v grep", $output);
	if(!$output){

		// script not running yet! start it.
		$image_width = $_POST['image']['width'];
		$image_height = $_POST['image']['height'];
		$tracking_width = 240;
		$tracking_height = 180;
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
		$cmd .= ' --quiet ';
//		$cmd .= ' --output-dir /var/www/html/CMT/output ';
		$cmd .= ') ';
		$cmd .= '> /tmp/follow 2>&1 &';
		echo $cmd;
		ini_set('display_errors',true);
		ini_set('error_reporting',E_ALL);
		exec($cmd);

	}

}else{
	unlink('CMT/running-flag.txt');
}
