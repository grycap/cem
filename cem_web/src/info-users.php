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
					function show_assignations ( username, html_data ) {
						
						
					}

				</script>
						<!-- Main -->
				<section id="main" class="container">
                    
					<header>
						<h2>Users</h2> 
					</header>
                    

					<section class="box">
						<div class="col">           
                            <div class="table-wrapper">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>User</th>
                                            <th>User state</th>
                                            <th>Since ( RFC 2822 )</th>
                                            <!-- <th>Allocation ID</th> -->
											
                                        </tr>
                                    </thead>
                                    <tbody>
										<?php
											
                                            for($i = 0; $i < count($info_users) ; $i++) 
                                            {
											echo "<tr>";
                                                echo "<td>" . $info_users[$i]['name'] . "</td>";
                                                echo "<td>" . $users_states[ strval( $info_users[$i]['state'] ) ] . "</td>";
                                                echo "<td>" . date( 'r', $info_users[$i]['timestamp_update_state'])  . "</td>";
												echo '<td> <a class="button special icon fa-search" href="info-user.php?username=' . $info_users[$i]['name'] . '">Show assignations</a></td>' ;
                                            echo "</tr>";
                                            }
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
			
		</body>
	</html>
<?php
}
?>