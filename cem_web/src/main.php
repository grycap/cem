<?php
/*
<?php
echo "<h2>Your Input:</h2>";
echo "user: " . $_POST['uname'];
echo "<br>";
echo $_POST['psw'];
echo "<br>";
echo $_POST['remember'];   
*/

if(!isset($_SESSION)) session_start();
if (isset($_POST['password']))
    $_SESSION['password'] = $_POST['password'];
if (isset($_POST['username']))
    $_SESSION['user'] = $_POST['username'];

//include_once('format.php');

include_once('user.php'); // To use check_session_user()
if (!check_session_user()) 
{
    header('Location: login.php?error=Invalid User');
} 
else 
{
	include('resources.php');
	$username = $_SESSION['user'];
	$password = $_SESSION['password'];
	$aux = get_user($username);
	$role = 'student';
	if ( ! is_null($aux) )
	{
		$role = $aux['role'];
	}	
	$_SESSION['role'] = $role;


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
		<script type="text/javascript" charset="utf-8">
				function sleep (time) {
						return new Promise((resolve) => setTimeout(resolve, time));
				}

				function confirm_deallocate() {
					swal({
						title: "Sure that you do not want your resources?" ,
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
									window.location.href = 'do.php?op=ask_deallocate&';
								});
							}
					});
				}
			</script>

		<body class="is-preload">
			<div id="page-wrapper">
				
				<?php include 'header.php'?> 

				<!-- Main -->
				<section id="main" class="container">
					<header>
						<h2>NOMBRE ASIGNATURA</h2> 
					</header>

					<section class="box">
						<div class="col">
						
						<p>Hola <strong><?php echo $_SESSION['user'] ?></strong>, ¿qué tal? </p>

<?php 

	if ( is_user_in_state($username, $password, "NOTHING_RESERVED") == true) 
	{		
?>
		<p>No tienes ningún recursos informático asignado, ¿quieres tener acceso a un escritorio remoto?</p>
	
		<a class="button" href="#" text-align="center" onclick="javascript:operate('do.php?op=demand_resources')">Solicitar escritorio remoto</a>

<?php 
	}
	elseif ( is_user_in_state($username, $password, "WAITING_RESOURCES") == true) 
	{

?>			
			<p>Se está procesando su petición de recursos, espere por favor, los recursos informáticos estarán disponibles en breve</p>
<?php
	}
	elseif ( is_user_in_state($username, $password, "UNKNOWN") == true) 
	{
?>
				<p>Recurso no disponible.</p>
<?php
	
	} 
	elseif ( (is_user_in_state($username, $password, "RESOURCES_ASSIGNED")==true) or ( is_user_in_state($username, $password, "ACTIVE") == true ) )
	{	
		$host = get_user_assigned_resource_info($username,$password)['assigned_rdp_url'];
?>
		<p> Los recursos asignados son: </p>
		<div class="table-wrapper">
			<table>
				<thead>
					<tr>
						<th>HOST del escritorio remoto</th>
						<th>Usuario</th>
						<th>Contraseña</th>
					</tr>
				</thead>
				<tbody>
					<tr>
						<td><?php echo $host ?></td>
						<td><?php echo $username ?></td>
						<td><?php echo $password ?></td>
						<td><a class="button special icon fa-close" onclick="javascript:confirm_deallocate()" href=#>Cancelar recursos</a> </td>
					</tr>
				<tbody>
			</table>
			<p> * <i>Recuerde que debe estar conectado a la VPN de la UPV para poder acceder al recurso informático.</i> </p>
		</div>
		

	</div>	
	
<?php	
	}


?>					
						
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