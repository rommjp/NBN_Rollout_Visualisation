<?php
/************************
Author: Rommel Poggenberg
Subject: FIT5147
Server side script receiving three filter values 
	1)'state' - State selection from user
	2)'tech' - Access Technology to visualise (HFC, FTTP, FTTN, FTTC, FTTB)
	3)'schedule' - Rollout schedule
Used to query a mongo database to retrieve the data in form of documents.
Data is encoded to JSON and sent client side to display in the web app in highcharts graph.
************************/


$state = isset($_GET['state'])? $_GET['state']: "";
$tech = isset($_GET['tech'])? $_GET['tech']: "";
$schedule = isset($_GET['schedule'])? $_GET['schedule']: "";
$filter='';


$filter = ['technology_type' => $tech, 'state' => $state];


$options = [
	'projection' => ['_id' => 0, 'results' => 1]
];

$manager = new MongoDB\Driver\Manager("mongodb://localhost:27017");
$query = new MongoDB\Driver\Query($filter, $options);
$cursor = $manager->executeQuery('nbn.map', $query);

$map_data = array();

foreach ($cursor as $map_info) {
	$map_data = json_decode(json_encode($map_info), True);
}


$filter = ['schedule' => $schedule];
$options = [
	'projection' => ['_id' => 0, 'results' => 1]
];

$manager = new MongoDB\Driver\Manager("mongodb://localhost:27017");
$query = new MongoDB\Driver\Query($filter, $options);
$cursor = $manager->executeQuery('nbn.chart', $query);

$chart_data = array();

foreach ($cursor as $chart_info) {
	$chart_data = json_decode(json_encode($chart_info), True);
}

echo json_encode(array('map'=> $map_data['results'],'chart'=>$chart_data['results']));

?>