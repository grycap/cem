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
    $info_users = get_users();
    $custom_assignations_info = array();
    for($i = 0; $i < count($info_users) ; $i++) 
    {
        $vmID = $info_users[$i]['vmID_assigned'];
        $alloc_id = $info_users[$i]['current_alloc_id'];
        $username = $info_users[$i]['name'];
        $state = $users_states[ strval( $info_users[$i]['state'] ) ] ;

        if ( $vmID != $DEFAULT_DB_vmID and $alloc_id != $DEFAULT_DB_alloc_id)
        {
            $node_info = get_node_info($vmID);
            array_push ( $custom_assignations_info, array( "vmID" => $vmID, "username" => $username, "nodename" => $node_info['nodename'], "state" => $state , "alloc_id" => $alloc_id) );
        }
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
					function confirm_delete(username, nodename, vmID, alloc_id) {
						swal({
							title: "Sure that you want to unassing the resource  " + nodename+ " for user " + username +"?",
							text: "",
							icon: "warning",
							buttons: true,
							dangerMode: true
							})
							.then((willStop) => {
								if (willStop) 
								{
									swal("Request sended", { icon: "success" });
									sleep(1000).then(() => {
										window.location.href = 'do.php?op=remove_assignation&vmID=' + vmID +'&username='+ username + '&alloc_id=' + alloc_id;
									});
								}
						});
					}

				</script>
						<!-- Main -->
				<section id="main" class="container">
                    
					<header>
						<h2>Current assignations</h2> 
					</header>
                    

					<section class="box">
						<div class="col">           
                            <div class="table-wrapper">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Resource name</th>
                                            <th>User</th>
                                            <th>User state</th>
                                            <!-- <th>Allocation ID</th> -->
											
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <?php
                                            for($i = 0; $i < count($custom_assignations_info) ; $i++) 
                                            {
                                                echo "<td>" . $custom_assignations_info[$i]['nodename'] . "</td>";
                                                echo "<td>" . $custom_assignations_info[$i]['username'] . "</td>";
                                                echo "<td>" . $custom_assignations_info[$i]['state'] . "</td>";
                                                #echo "<td>" . $custom_assignations_info[$i]['alloc_id'] . "</td>";
												echo "<td>" . '<a class="button special icon fa-trash" onclick="javascript:confirm_delete( \''  . $custom_assignations_info[$i]['username'] .  '\' , \'' . $custom_assignations_info[$i]['nodename'] .  '\' , \'' . $custom_assignations_info[$i]['vmID'] .  '\' , \'' . $custom_assignations_info[$i]['alloc_id'] . '\' )" href=#>Unassign</a>'. "</td>" ;
												
                                            echo "</tr>";
                                            }
                                        unset($resource);
                                        ?>

                                    <tbody>
                                </table>
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
			
		</body>
	</html>
<?php
}
?>