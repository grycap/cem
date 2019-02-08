<?php


function demand_resources ( $username, $password ) 
{
    include('config.php');
    
    if ( is_user_in_state( $username , $password, "NOTHING_RESERVED" ) ) 
    {
        include_once 'cem-rest.php';
        $cem = CEMRest::connect($cem_host, $cem_port);
        $response = $cem->DemandResources();
        return true;
    }
    
    return false;
    
}

function remove_resources ( $username, $password, $vmID ) 
{
    include('config.php');
    
    include_once 'cem-rest.php';
    $cem = CEMRest::connect($cem_host, $cem_port);
    $response = $cem->RemoveResources($vmID);
    return true;
    
}
function restart_resources ( $username, $password, $vmID ) 
{
    include('config.php');
    
    include_once 'cem-rest.php';
    $cem = CEMRest::connect($cem_host, $cem_port);
    $response = $cem->StartResources($vmID);
    return true;
    
}
function stop_resources ( $username, $password, $vmID ) 
{
    include('config.php');
    
    include_once 'cem-rest.php';
    $cem = CEMRest::connect($cem_host, $cem_port);
    $response = $cem->StopResources($vmID);
    return true;
    
}

function add_resources ( $username, $password ) 
{
    include('config.php');
    
    include_once 'cem-rest.php';
    $cem = CEMRest::connect($cem_host, $cem_port);
    $response = $cem->AddResources();
    return true;
    
}


function remove_assignation ( $username, $password, $alloc_vmID, $alloc_username, $alloc_id ) 
{
    include('config.php');
    
    include_once 'cem-rest.php';
    $cem = CEMRest::connect($cem_host, $cem_port);
    $response = $cem->RemoveAssignation($alloc_vmID, $alloc_username, $alloc_id);
    return true;
    
    
}

function get_all_nodes_info () 
{
    include('config.php');
    $node_info_array = array();
    $db = new IMDB();
    $node_info_array = $db->get_items_from_table($db_resources_table);
    $db->close(); 
    return $node_info_array;
}


function get_node_info ( $vmID ) 
{
    include('config.php');
    $node_info_array = array();
    $db = new IMDB();
    $node_info_array = $db->get_items_from_table($db_resources_table, array( "vmID" => "'" . $db->escapeString($vmID) . "'"));
    $db->close(); 
    return $node_info_array[0];
}


function get_user_info ( $username , $password )
{
    include('config.php');
    $users_info = array();
    $db = new IMDB();
    $users_info = $db->get_items_from_table($db_users_table, array( "name" => "'" . $db->escapeString($username) . "'"));
    $db->close(); 
    return $users_info[0];
}

function get_all_allocations_by_user ( $username  )
{
    include('config.php');
    $users_info = array();
    $db = new IMDB();
    $users_info = $db->get_items_from_table($db_allocation_table, array( "username" => "'" . $db->escapeString($username) . "'"), $order = 'timestamp_start DESC');
    $db->close(); 
    return $users_info;
}


function get_user_assigned_resource_info ( $username , $password )
{
    include('config.php');
    $result = NULL; 
    $users_info = get_user_info( $username , $password );
    $vmID = $users_info['vmID_assigned'];
    if ($vmID != $DEFAULT_DB_vmID)
    {
        $result=get_node_info($vmID);
    } 
    return $result;
}


function is_user_in_state( $username , $password, $state_string )
{
    include('config.php');
    $user_info = get_user_info ($username , $password ) ;
    $in_target_state = false;
    if ( $users_states[ strval($user_info["state"]) ] ==  $state_string  )
    {
        $in_target_state = true;
    }
    return $in_target_state;
}



?>