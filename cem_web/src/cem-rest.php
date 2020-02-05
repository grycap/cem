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

require_once 'http.php';
//require_once 'cred.php';

class CEMRest
{
    static public function connect($host, $port)
    {
        return new self($host, $port);
    }

    public function __construct($host = "localhost", $port = 10000)
    {
        $this->_host     = $host;
        $this->_port     = $port;
    }

    public function get_auth_data()
    {        
        $auth = array("user" => $_SESSION['user'], "password" => $_SESSION['password']);
        return $auth;
    }

    public function GetErrorMessage($output)
    {
        return $output;
    }

    public function BasicRESTCall($verb, $path, $extra_headers=array(), $params=array())
    {
        include 'config.php';
        $auth = $this->get_auth_data();
        //$headers = array("Authorization:" . $auth);
        $headers = array();
        $headers = array_merge($headers, $extra_headers);

        if ($im_use_ssl) {
            $protocol = 'https';
        } else {
            $protocol = 'http';
        }
        
        try {
            $res = Http::connect($this->_host, $this->_port, $protocol)
            ->setHeaders($headers)
            ->exec($verb, $path, $params);
                
            $status = $res->getStatus();
            $output = $res->getOutput();
        } catch (Exception $e) {
            $status = 600;
            $output = "Exception: " . $e->getMessage();
        }

        $res = $output;
        if ($status != 200) {
            $res = 'Error: Code: ' . strval($status) . '. ' . $this->GetErrorMessage($output);
        }

        return new Http_response($status, $res);
    }

    public function RemoveResources( $vmID )
    {
        $data = $this->get_auth_data();
        $data['vmID'] = $vmID;
        $headers = array('Content-Type: application/json' );
        $res = $this->BasicRESTCall("POST", '/remove_resources', $headers, json_encode($data) );
        return $res->getOutput();
    }

    public function StartResources( $vmID )
    {
        $data = $this->get_auth_data();
        $data['vmID'] = $vmID;
        $headers = array('Content-Type: application/json' );
        $res = $this->BasicRESTCall("POST", '/restart_resources', $headers, json_encode($data) );
        return $res->getOutput();
    }

    public function StopResources( $vmID )
    {
        $data = $this->get_auth_data();
        $data['vmID'] = $vmID;
        $headers = array('Content-Type: application/json' );
        $res = $this->BasicRESTCall("POST", '/stop_resources', $headers, json_encode($data) );
        return $res->getOutput();
    }

    public function AddResources( )
    {
        $data = $this->get_auth_data();
        $headers = array('Content-Type: application/json' );
        $res = $this->BasicRESTCall("POST", '/add_resources', $headers, json_encode($data) );
        return $res->getOutput();
    }


    public function RemoveAssignation( $alloc_vmID, $alloc_username, $alloc_id )
    {
        $data = $this->get_auth_data();
        $data['vmID'] = $alloc_vmID;
        $data['username'] = $alloc_username;
        $data['alloc_id'] = $alloc_id;
        $headers = array('Content-Type: application/json' );
        $res = $this->BasicRESTCall("POST", '/remove_assignation', $headers, json_encode($data) );
        return $res->getOutput();
    }

    public function DemandResources()
    {
        $data = json_encode($this->get_auth_data());
        $headers = array('Content-Type: application/json' );
        $res = $this->BasicRESTCall("POST", '/demand_resources', $headers, $data);
        return $res->getOutput();
    }

    public function AskingDeallocate()
    {
        $data = json_encode($this->get_auth_data());
        $headers = array('Content-Type: application/json' );
        $res = $this->BasicRESTCall("POST", '/asking_deallocate', $headers, $data);
        return $res->getOutput();
    }

}
?>
