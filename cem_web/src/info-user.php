<?php

if(!isset($_SESSION)) session_start();

include_once('user.php'); // To use check_session_user()
if (!check_session_user() or $_SESSION['role'] != 'teacher') 
{
    header('Location: login.php?error=Invalid User');
} 
else 
{

    if (! isset($_GET['username'])) 
    {
        header('Location: login.php?error=Invalid User');
    }
    else
    {

        include('resources.php');  
        include('config.php');  
        $all_allocations = get_all_allocations_by_user ( $_GET['username'] );

?> 

	<!DOCTYPE HTML>
	<meta http-equiv="refresh" content="60">
	<html>
		<head>
			<title>Generic - Alpha by HTML5 UP</title>
			<meta charset="utf-8" />
			<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no" />
			<link rel="stylesheet" href="assets/css/main.css" />
	
		</head>
		<body class="is-preload">
			<div id="page-wrapper">
				
				<?php include 'header.php'?> 
                
						<!-- Main -->
				<section id="main" class="container">
                    
					<header>
						<h2>Information about <?php echo $_GET['username']; ?> </h2> 
					</header>
                    

					<section class="box">
						<div class="col">           
                            <div class="table-wrapper">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Allocation ID</th>
                                            <th>Resource</th>
                                            <th>Start ( RFC 2822 )</th>
                                            <th>End ( RFC 2822 )</th>											
                                        </tr>
                                    </thead>
                                    <tbody>
										<?php
											
                                            for($i = 0; $i < count($all_allocations) ; $i++) 
                                            {
											echo "<tr>";
                                                echo "<td>" . $all_allocations[$i]['alloc_id'] . "</td>";
                                                echo "<td>" . $all_allocations[$i]['resources_vmID'] . "</td>";
                                                echo "<td>" . date( 'r', $all_allocations[$i]['timestamp_start']) . "</td>";
                                                if (! $all_allocations[$i]['timestamp_finish'] == '')
                                                {
                                                    echo "<td>" . date( 'r', $all_allocations[$i]['timestamp_finish'])  . "</td>";
                                                }
                                                
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
}
?>