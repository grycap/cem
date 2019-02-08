<!DOCTYPE HTML>
<!--
	Alpha by HTML5 UP
	html5up.net | @ajlkn
	Free for personal and commercial use under the CCA 3.0 license (html5up.net/license)
-->
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
			<form action="main.php" method="POST">
				<br></br> 			
				<div class="container">
				  <div class="col-4 col-12-narrower">
						<label for="username"><b>Username</b></label>
						<input type="text" placeholder="Enter Username" name="username" required>
						<label for="password"><b>Password</b></label>
						<input type="password" placeholder="Enter Password" name="password" required>
						
						<?php
							if (isset($_GET['error'])) {
    					?>
							<font color="red">Username or password are incorrect. </font> 
						<?php
							}else {
						?>
							<br></br>
						<?php
							}
						?>
						<ul class="actions">
							<li><input type="submit" value="Login" /></li>
							<!-- <li><input type="reset" value="Reset" class="alt" /></li> -->
						</ul>
					</div>
				</div>
			  </form>
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