PyWPcheck
=========

Python script to check the update-status of one ore more WordPress sites through mysql.


This script uses [phpserialize](https://pypi.python.org/pypi/phpserialize) to decipher the serializes data in the mysql database of a Wordpress site.

It is not checking itself for updates but warns you either when the Wordpress installation did not check for some time or there are new versions available for core, plugins or themes.

The script needs read access to the wordpress database.
