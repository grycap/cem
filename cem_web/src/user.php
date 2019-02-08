<?php
/*
 IM - Infrastructure Manager
 Copyright (C) 2011 - GRyCAP - Universitat Politecnica de Valencia

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

include_once('crypt.php');

function check_session_user() {
    include('config.php');

    if (isset($_SESSION['user']) && isset($_SESSION['password'])) {
	    $password = $_SESSION['password'];
        $username = $_SESSION['user'];
	
	    $res = false;
    	$db = new IMDB();
    	$res = $db->get_items_from_table($db_users_table, array("name" => "'" . $db->escapeString($username) . "'"));
        $db->close();
	    if (count($res) > 0) {
	   		$res = check_password($password, $res[0]["password"]);
	    }
        return $res;
    //} elseif (isset($_SESSION['user']) && isset($_SESSION['user_token'])) {
    //   return check_user_token();
    } else {
        return false;
    }
}

function get_users() {
    include('config.php');

    $db = new IMDB();
    $res = $db->get_items_from_table($db_users_table);
    $db->close();
    return $res;
}

function get_user ($username) {
    include('config.php');

    $db = new IMDB();
    $res = $db->get_items_from_table($db_users_table, array("name" => "'" . $db->escapeString($username) . "'"));
    $db->close();
    if (count($res) > 0)
        return $res[0];
    else
        return NULL;
}



