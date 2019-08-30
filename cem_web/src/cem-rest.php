<?php
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

    

    /*

    public function BasicRESTCall($verb, $path, $extra_headers=array(), $params=array())
    {
        include 'config.php';
        $auth = $this->get_auth_data();
        $headers = array("Authorization:" . $auth);
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

    public function GetInfrastructureList()
    {
        $headers = array('Accept: text/*');
        $res = $this->BasicRESTCall("GET", '/infrastructures', $headers);

        if ($res->getStatus() != 200) {
            return $res->getOutput();
        } else {
            $inf_urls = explode("\n", $res->getOutput());
            $inf_ids = array();
            foreach ($inf_urls as $inf_url) {
                $inf_id = trim(basename(parse_url($inf_url, PHP_URL_PATH)));
                if (strlen($inf_id) > 0) {
                    $inf_ids[] = $inf_id;
                }
            }
            return $inf_ids;
        }
    }

    public function GetInfrastructureInfo($id)
    {
        $headers = array('Accept: text/*');
        $res = $this->BasicRESTCall("GET", '/infrastructures/'.$id, $headers);

        if ($res->getStatus() != 200) {
            return 'Error: Code: ' . strval($res->getStatus()) . '. ' . GetErrorMessage($output);
        } else {
            $vm_urls = explode("\n", $res->getOutput());
            $vm_ids = array();
            foreach ($vm_urls as $vm_url) {
                $vm_id = trim(basename(parse_url($vm_url, PHP_URL_PATH)));
                if (strlen($vm_id) > 0) {
                    $vm_ids[] = $vm_id;
                }
            }
            return $vm_ids;
        }
    }

    public function GetInfrastructureState($id)
    {
        $headers = array('Accept: application/json');
        $res = $this->BasicRESTCall("GET", '/infrastructures/'.$id.'/state', $headers);

        if ($res->getStatus() != 200) {
            return $res->getOutput();
        } else {
            return json_decode($res->getOutput(), true)["state"];
        }
    }

    public function DestroyInfrastructure($id)
    {
        $headers = array('Accept: text/*');
        $res = $this->BasicRESTCall("DELETE", '/infrastructures/'.$id, $headers);
        
        if ($res->getStatus() != 200) {
            return $res->getOutput();
        } else {
            return "";
        }
    }

    public function GetVMInfo($inf_id, $vm_id)
    {
        $headers = array('Accept: text/*');
        $res = $this->BasicRESTCall("GET", '/infrastructures/' . $inf_id . '/vms/' . $vm_id, $headers);
        return $res->getOutput();
    }

    public function GetInfrastructureContMsg($id)
    {
        $headers = array('Accept: text/*');
        $res = $this->BasicRESTCall("GET", '/infrastructures/'.$id.'/contmsg', $headers);
        return $res->getOutput();
    }

    public function GetVMProperty($inf_id, $vm_id, $property)
    {
        $headers = array('Accept: text/*');
        $res = $this->BasicRESTCall("GET", '/infrastructures/' . $inf_id . '/vms/' . $vm_id . "/" . $property, $headers);
        return $res->getOutput();
    }

    public function GetVMContMsg($inf_id, $vm_id)
    {
        $headers = array('Accept: text/*');
        $res = $this->BasicRESTCall("GET", '/infrastructures/' . $inf_id . '/vms/' . $vm_id . "/contmsg", $headers);
        return $res->getOutput();
    }

    public function GetContentType($content)
    {
        if (strpos($content, "tosca_definitions_version") !== false) {
            return 'text/yaml';
        } elseif (substr(trim($content), 0, 1) == "[") {
            return 'application/json';
        } else {
            return 'text/plain';
        }
    }

    public function CreateInfrastructure($radl, $async)
    {
        $headers = array('Accept: text/*', 'Content-Length: ' . strlen($radl), 'Content-Type: ' . $this->GetContentType($radl));
        if ($async) {
            $res = $this->BasicRESTCall("POST", '/infrastructures?async=yes', $headers, $radl);
        } else {
            $res = $this->BasicRESTCall("POST", '/infrastructures', $headers, $radl);
        }
        return $res->getOutput();
    }

    public function StartVM($inf_id, $vm_id)
    {
        $headers = array('Accept: text/*');
        $res = $this->BasicRESTCall("PUT", '/infrastructures/' . $inf_id . '/vms/' . $vm_id . "/start", $headers);
        return $res->getOutput();
    }

    public function StopVM($inf_id, $vm_id)
    {
        $headers = array('Accept: text/*');
        $res = $this->BasicRESTCall("PUT", '/infrastructures/' . $inf_id . '/vms/' . $vm_id . "/stop", $headers);
        return $res->getOutput();
    }

    public function AddResource($inf_id, $radl)
    {
        $headers = array('Accept: text/*', 'Content-Length: ' . strlen($radl), 'Content-Type: ' . $this->GetContentType($radl));
        $res = $this->BasicRESTCall("POST", '/infrastructures/' . $inf_id, $headers, $radl);
        return $res->getOutput();
    }

    public function RemoveResource($inf_id, $vm_id)
    {
        $headers = array('Accept: text/*');
        $res = $this->BasicRESTCall("DELETE", '/infrastructures/' . $inf_id . '/vms/' . $vm_id, $headers);
        return $res->getOutput();
    }

    public function Reconfigure($inf_id, $radl)
    {
        $headers = array('Accept: text/*', 'Content-Type: text/plain', 'Content-Length: ' . strlen($radl));
        $res = $this->BasicRESTCall("PUT", '/infrastructures/' . $inf_id . '/reconfigure', $headers, $radl);
        return $res->getOutput();
    }

    public function GetOutputs($inf_id)
    {
        $headers = array('Accept: application/json');
        $res = $this->BasicRESTCall("GET", '/infrastructures/' . $inf_id . '/outputs', $headers);
        return json_decode($res->getOutput(), true)["outputs"];
    }
    */
}
?>
