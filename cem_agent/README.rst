Cluster Elasticity Manager - Agent (CEM-Agent)
==============================================

- It checks if users are executing commands in the node every time that receives a request from CEM-Server. 
- It kills all processes of unauthorized users (the list is provided by CEM Server on each communication).

Configuration variables in `cem.cfg`:
-------------------------------------
- `REST_AGENT_API_SECRET`: token used for the authentication with CEM-Server

Installation:
-------------------------------------

.. code-block:: bash

    cd cem_agent && python setup.py install 


Start/stop service:
-------------------------------------
.. code-block:: bash

    service cem-agent start/stop
    systemctl start/stop cem-agent

Enable/disable service:
-------------------------------------
.. code-block:: bash

    systemctl enable/disable cem-agent
    chkconfig cem-agent on/off


