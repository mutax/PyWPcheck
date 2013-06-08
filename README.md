PyWPcheck
=========

Python script to check the update-status of one ore more WordPress sites through mysql.


This script uses [phpserialize](https://pypi.python.org/pypi/phpserialize) to decipher the serializes data in the mysql database of a Wordpress site.

It is not checking itself for updates but warns you either when the Wordpress installation did not check for some time or there are new versions available for core, plugins or themes. And no, it does not check if you actually have the plugins or themes activated.

The script needs read access to the wordpress database.


WHY?
----

There are two reasons for this script. One was that I needed something small to have a playground for a nice project layout, the second was that I still need to get better at python and the third was that I was missing a tool for myself to check teh various wordpress installations I operate without configuring all of them. Also I have the intention to never again write _new_ software in php. For reasons.


Warnings:
---------

I have no idea if the code works as expected, I tested against three local installations and it seemed to do the job.
The first release took about one day of work, so don't expect much - although this is way too much time wasted, to be honest.
Deserializing php objects into python is not the craziest thing, but having 3 different object combinations to parse is. 


more crazyness:
---------------

I had the plan to add a notification system so nagios/icinga can get the check results of the script or similar. 

You could already execute the script as cgi if you make sure the config path is outside the document root and check via nagios daily if the string ERROR occurs. (htaccess should be put in front)


Future ideas:
-------------

If I have too muich time an automated email to the admin configured in the database could be an idea as well as setting the timeout for the cron check per site in the settings.

