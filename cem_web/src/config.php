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


//$im_use_rest=false;
//$im_port=8899;
$db="/var/www/www-data/cem.db";
$db_users_table="users";
$db_allocation_table="allocations";
$db_resources_table="resources";
$cem_host="XXX";
$cem_port="10000";

$DEFAULT_DB_vmID="-1";
$DEFAULT_DB_alloc_id="-1";

$users_states = [
    "0" => "-",
    "1" => "NOTHING_RESERVED",
    "2" => "WAITING_RESOURCES",
    "3" => "RESOURCES_ASSIGNED",
    "4" => "ACTIVE"
];

$resources_states = [
    "0" => "-",
    "1" => "PENDING",
    "2" => "CONFIGURING",
    "3" => "CONFIGURED",
    "4" => "UNCONFIGURED",
    "5" => "STOPPED",
    "6" => "FAILED"
];

$utilization_states = [
    "0" => "-",
    "1" => "IDLE",
    "2" => "USED",
    "3" => "FULL"
];

include_once('db.php');
?>
