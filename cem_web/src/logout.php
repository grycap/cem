<?php

if (!isset($_SESSION)) {
    session_start();
}
// Unset all of the session variables.
$_SESSION = array();

session_write_close();

// Finally, destroy the session.
if (session_status() === PHP_SESSION_ACTIVE) {
    session_destroy();
}

header('Location: index.php');
?>
