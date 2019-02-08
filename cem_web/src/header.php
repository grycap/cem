
<header id="header" >
    <div class="logo"> <img src="images/marca_UPV_principal_blanco300.png" alt="" /> </div>
    <nav id="nav">

    <?php

    if (isset($_SESSION['user']) and isset($_SESSION['password']) and isset($_SESSION['role']) ) {
    ?>  
        <ul>
            <li><a href="main.php">Home</a></li>
            <!-- <li><a href="main.php">TESTS</a></li> -->
    <?php
        if ( $_SESSION['role'] == 'teacher')
        {
    ?>        
            <li>
                <a href="#">Admin options</a>
                <ul>
                    <li><a href="info-resources.php">Current resources</a></li>
                    <li><a href="info-assignations.php">Current assignations</a></li>
                    <li><a href="info-users.php">Users current state </a></li>
                </ul>
            </li>
    <?php
        }
        else
        {
    ?>
            <li><a href="main.php">Student options</a></li>
    <?php    
        }
    ?>        
            <li><a href="logout.php" class="button">Logout</a></li>
        </ul> 

    <?php
    } else {
    ?>

        <ul>
            <li><a href="index.php">Home</a></li>
            <li>
                <a href="#" class="icon fa-angle-down">Layouts</a>
                <ul>
                    <li><a href="generic.html">Generic</a></li>
                    <li><a href="contact.html">Contact</a></li>
                    <li><a href="elements.html">Elements</a></li>
                    <li>
                        <a href="#">Submenu</a>
                        <ul>
                            <li><a href="#">Option One</a></li>
                            <li><a href="#">Option Two</a></li>
                            <li><a href="#">Option Three</a></li>
                            <li><a href="#">Option Four</a></li>
                        </ul>
                    </li>
                </ul>
            </li>
            <li><a href="login.php" class="button">Sign Up</a></li>
        </ul>



    <?php 
        }
    ?>

    </nav>
</header>




