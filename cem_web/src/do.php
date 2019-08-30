<?php

if (!isset($_SESSION)) {
    session_start();
} 

require_once 'config.php'; 
require_once 'user.php';
if (!check_session_user()) 
{
    header('Location: index.php?error=Invalid User');
} 
else 
{
    $op = "";
    if (isset($_POST['op'])) 
    {
        $op = $_POST['op'];
    } elseif (isset($_GET['op'])) 
    {
        $op = $_GET['op'];
    }

    if (strlen($op) > 0) 
    {
        if ($op == "demand_resources") 
        {
            include_once 'resources.php';
            demand_resources ( $_SESSION['user'], $_SESSION['password'] );
            header('Location: main.php');
            
        }
        elseif ( $op == "remove_resources" and $_SESSION['role'] == 'teacher')
        {
            include_once 'resources.php';
            remove_resources ( $_SESSION['user'], $_SESSION['password'], $_GET['vmID'] );
            header('Location: info-resources.php');
        }
        elseif ( $op == "restart_resources" and $_SESSION['role'] == 'teacher')
        {
            include_once 'resources.php';
            restart_resources ( $_SESSION['user'], $_SESSION['password'], $_GET['vmID'] );
            header('Location: info-resources.php');
        }
        elseif ( $op == "stop_resources" and $_SESSION['role'] == 'teacher')
        {
            include_once 'resources.php';
            stop_resources ( $_SESSION['user'], $_SESSION['password'], $_GET['vmID'] );
            header('Location: info-resources.php');
        }
        elseif ( $op == "add_resources" and $_SESSION['role'] == 'teacher')
        {
            include_once 'resources.php';
            add_resources ( $_SESSION['user'], $_SESSION['password'] );
            header('Location: info-resources.php');
        }
        elseif ( $op == "remove_assignation" and $_SESSION['role'] == 'teacher')
        {
            include_once 'resources.php';
            remove_assignation ( $_SESSION['user'], $_SESSION['password'], $_GET['vmID'], $_GET['username'], $_GET['alloc_id'] );
            header('Location: info-assignations.php');
        }
        elseif ( $op == "ask_deallocate")
        {
            include_once 'resources.php';
            ask_deallocate ( $_SESSION['user'], $_SESSION['password'] );
            header('Location: main.php');
        }
        else 
        {
            header('Location: login.php?error=Invalid operation');
        }
            
            
    } 
    else 
    {
        header('Location: index.php?error=Invalid operation');
    }
}
?>