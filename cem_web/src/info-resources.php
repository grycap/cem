<?php

if(!isset($_SESSION)) session_start();

include_once('user.php'); // To use check_session_user()
if (!check_session_user() or $_SESSION['role'] != 'teacher') 
{
    header('Location: login.php?error=Invalid User');
} 
else 
{

    include('resources.php');  
    include('config.php');  
	$info_nodes = get_all_nodes_info();

	$general_monitoring_data = get_resources_general_monitoring();
	$dataNodeState_points = array();
	$dataUtilizationNodeState_points = array();

	for($i = 0; $i < count($general_monitoring_data[0]) ; $i++) 
	{
		array_push($dataNodeState_points, array("label" => $resources_states[$i], "y" => $general_monitoring_data[0][$i] ) );
	}
	
	for($i = 0; $i < count($general_monitoring_data[1]) ; $i++) 	
	{
		array_push($dataUtilizationNodeState_points, array("label" => $utilization_states[$i], "y" => $general_monitoring_data[1][$i] ) );
	}

    
?> 

	<!DOCTYPE HTML>
	<meta http-equiv="refresh" content="60">
	<html>
		<head>
			<title>Generic - Alpha by HTML5 UP</title>
			<meta charset="utf-8" />
			<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no" />
			<link rel="stylesheet" href="assets/css/main.css" />


			<script type="text/javascript" charset="utf-8">
				function operate( url ) {
					window.location.href = url;					
				}
			</script>
	
		</head>
		<body class="is-preload">
			<div id="page-wrapper">
				
				<?php include 'header.php'?> 
								
				<script type="text/javascript" charset="utf-8">
					function sleep (time) {
  							return new Promise((resolve) => setTimeout(resolve, time));
					}

					function confirm_delete(nodename, vmID) {
						swal({
							title: "Sure that you want to delete " + nodename+ "?",
							text: "",
							icon: "warning",
							buttons: true,
							dangerMode: true,
							})
							.then((willDelete) => {
								if (willDelete) 
								{
									swal("Request sended", { icon: "success" });
									sleep(1000).then(() => {
										window.location.href = 'do.php?op=remove_resources&vmID=' + vmID;
									});
								}
						});
					}
					function confirm_start(nodename, vmID) {
						swal({
							title: "Sure that you want to restart " + nodename+ "?",
							text: "",
							icon: "warning",
							buttons: true,
							dangerMode: true,
							})
							.then((willStart) => {
								if (willStart) 
								{
									swal("Request sended", { icon: "success" });
									sleep(1000).then(() => {
										window.location.href = 'do.php?op=restart_resources&vmID=' + vmID;
									});
								}
						});
					}
					function confirm_stop(nodename, vmID) {
						swal({
							title: "Sure that you want to suspend " + nodename+ "?",
							text: "",
							icon: "warning",
							buttons: true,
							dangerMode: true,
							})
							.then((willStop) => {
								if (willStop) 
								{
									swal("Request sended", { icon: "success" });
									sleep(1000).then(() => {
										window.location.href = 'do.php?op=stop_resources&vmID=' + vmID;
									});
								}
						});
					}
					function confirm_add(nodename, vmID) {

						swal({
							title: "Sure that you want to add 1 VMs ?",
							text: "",
							icon: "warning",
							buttons: true,
							dangerMode: true,
							})
							.then((willAdd) => {
								if (willAdd) 
								{
									swal("Request sended", { icon: "success" });
									sleep(1000).then(() => {
										window.location.href = 'do.php?op=add_resources';
									});
								}
							});
					}

				</script>

				<script>
				window.onload = function() {
				
				var chart = new CanvasJS.Chart("node_state", {
					animationEnabled: true,
					title:{
						text: "Current node state overview"
					},
					axisY: {
						title: "Number of nodes",
						prefix: "",
						suffix:  ""
					},
					data: [{
						type: "column",
						yValueFormatString: "#,### Units",
						//indexLabel: "{y}",
						//indexLabelPlacement: "inside",
						//indexLabelFontWeight: "bolder",
						//indexLabelFontColor: "white",
						dataPoints: <?php echo json_encode($dataNodeState_points, JSON_NUMERIC_CHECK); ?>
					}]
				});
				chart.render();
				
				var chart2 = new CanvasJS.Chart("node_utilization_state", {
					animationEnabled: true,
					title:{
						text: "Current node utilization state overview"
					},
					axisY: {
						title: "Number of nodes",
						prefix: "",
						suffix:  ""
					},
					data: [{
						type: "column",
						yValueFormatString: "#,### Units",
						//indexLabel: "{y}",
						//indexLabelPlacement: "inside",
						//indexLabelFontWeight: "bolder",
						//indexLabelFontColor: "white",
						dataPoints: <?php echo json_encode($dataUtilizationNodeState_points, JSON_NUMERIC_CHECK); ?>
					}]
				});
				chart2.render();

				}
				</script>
						<!-- Main -->
				<section id="main" class="container">
                    
					<header>
						<h2>Resources</h2> 
					</header>
                    
					<div id="node_state" style="height: 370px; width: 100%;"></div>
					<div id="node_utilization_state" style="height: 370px; width: 100%;"></div>
					

					<section class="box">
						<div class="col">           
                            <div class="table-wrapper">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Node name</th>
                                            <th>RDP URL</th>
                                            <th>IP</th>
                                            <th>State</th>
                                            <th>Utilization state</th>
											
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <?php
                                            for($i = 0; $i < count($info_nodes) ; $i++) 
                                            {
                                                echo "<td>" . $info_nodes[$i]['nodename'] . "</td>";
                                                echo "<td>" . $info_nodes[$i]['assigned_rdp_url'] . "</td>";
                                                echo "<td>" . $info_nodes[$i]['ip'] . "</td>";
                                                echo "<td>" . $resources_states[ strval( $info_nodes[$i]['state'] ) ] . "</td>";
												echo "<td>" . $utilization_states[ strval( $info_nodes[$i]['utilization_state'] ) ] . "</td>";
												
												$is_used = FALSE;
												if ( $utilization_states[ strval( $info_nodes[$i]['utilization_state'] ) ] == 'USED' or $utilization_states[ strval( $info_nodes[$i]['utilization_state'] ) ] == 'FULL' )
												{
													$is_used = TRUE;
												}

												if ($resources_states[ strval( $info_nodes[$i]['state'] ) ] == "STOPPED")
												{
													echo "<td>" . '<a class="button special icon fa-play" onclick="javascript:confirm_start( \''  . $info_nodes[$i]['nodename'] .  '\' , \'' . $info_nodes[$i]['vmID'] . '\' )" href=#>Restart</a>'. "</td>" ;
												}
												elseif  ($resources_states[ strval( $info_nodes[$i]['state'] ) ] == "CONFIGURED" and ! $is_used)
												{
													echo "<td>" . '<a class="button special icon fa-stop" onclick="javascript:confirm_stop( \''  . $info_nodes[$i]['nodename'] .  '\' , \'' . $info_nodes[$i]['vmID'] . '\' )" href=#>Suspend</a>'. "</td>" ;
												}
												
												if ($resources_states[ strval( $info_nodes[$i]['state'] ) ] != "PENDING" and ! $is_used)
												{
													echo "<td>" . '<a class="button special icon fa-trash" onclick="javascript:confirm_delete( \''  . $info_nodes[$i]['nodename'] .  '\' , \'' . $info_nodes[$i]['vmID'] . '\' )" href=#>Delete</a>' . "</td>" ;
												}											
											echo "</tr>";
											
                                            }
                                        ?>

                                    <tbody>
								</table>
								<a class="button special icon fa-plus" onclick="javascript:confirm_add()" href=#>Add new resource</a>
                            </div>
                        </div>
        
				
						
					</section>

				</section>
				
			</div>
			<!-- Scripts -->
				<script src="assets/js/jquery.min.js"></script>
				<script src="assets/js/jquery.dropotron.min.js"></script>
				<script src="assets/js/jquery.scrollex.min.js"></script>
				<script src="assets/js/browser.min.js"></script>
				<script src="assets/js/breakpoints.min.js"></script>
				<script src="assets/js/util.js"></script>
				<script src="assets/js/main.js"></script>
				<script src="assets/js/sweetalert.min.js"></script>
				<script src="https://canvasjs.com/assets/script/canvasjs.min.js"></script>
			
		</body>
	</html>
<?php
}
?>
