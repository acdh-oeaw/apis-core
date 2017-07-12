Installation
============

Prerequisites
-------------

APIS webapp needs Python 3.5+ and several python packages that can be easily installed by using pip.

Create a new virtualenv and activate it:

.. code-block:: console

   virtualenv -p pyton3.5 your_virtualenv_name
   source your_virtualenv_name/bin/activate

Git and submodules
------------------

We use the system in several different projects. To allow for high configurability while keeping it simple we decided
to split the system in several git submodules:

* apis-core: the main application code
* apis-PROJECTNAME-settings (for the main system used in apis project we omit the PROJECTNAME in the repo names): The settings folder of the various projects. These contain not only the app settings (e.g.
  db user, db password etc.) but also the settings for the autocompletes and the RDF parsers.
* apis-PROJECTNAME-webpage: The webpage app of the respective project. Seperating these base templates and javascripts
  from the rest of the app allows us to give every project its very own look.

If you want to get a basic running system that you can work from, you can clone apis-apis and initialize the submodules::

    git clone --recursive https://github.com/acdh-oeaw/apis.git

After that you need to set two symlinks::

    cd apisapp/apis
    ln -s ../../apis-settings settings
    cd ..
    ln -s ../apis-webpage webpage

Now you have the correct folder structure in place and are good to go on with installing

Installation
------------

Change to the directory you have downloaded APIS to and install the needed Python packages::

    cd apisapp
    pip install -r requirements.txt

Next you need to create a file called copy the ``APIS_directory/apisapp/apis/settings/dummysettings.py`` file to another name.
We suggest ``server.py``::

    cp APIS_directory/apisapp/apis/settings/dummysettings.py APIS_directory/apisapp/apis/settings/server.py

Edit ``server.py`` to your needs. E.g. if you intend to use Mysql it should look something like::

    import os
    from .base import *

    SECRET_KEY = 'asdaaserffsdfi'
    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = True

    DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'databsename',
        'USER': 'dtabaseuser',
        'PASSWORD': 'databasepassword',
        'HOST': 'localhost',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',
        }
    }

Dont forget to set ``DEBUG = False`` once you are in production.

Once the database connection is set run:

.. code-block:: console

    python manage.py migrate --settings=apis.settings.server

For convenience we suggest you alter ``manage.py`` to::

    if __name__ == "__main__":
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apis.settings.server")

        from django.core.management import execute_from_command_line

        execute_from_command_line(sys.argv)

Once that is done you dont have to incluse ``--settings=apis.settings.server`` in your commands anymore.

Next we migrate the APIS internal tables:

.. code-block:: console

    python manage.py makemigrations metainfo entities relations vocabularies highlighter labels webpage
    python manage.py migrate

and create a superuser:

.. code-block:: console

    python manage.py createsuperuser

answer the questions and you should be good to go:

.. code-block:: console

    python manage.py runserver

should bring up a development server window with your new apis instance.


Serving APIS via Apache WSGI
----------------------------

If you plan to use APIS in production you should deploy it via a proper webserver. We use Apache_ and ``mod_wsgi`` to
do so. Our apche virtualhost config looks something like:

.. code-block:: aconf

   <VirtualHost *:80>
      ServerName server_name
      ServerAlias server_alias #alias names if needed
      DocumentRoot /var/www/html #document root of your installation
      WSGIDaemonProcess apis.eos.arz.oeaw.ac.at user=#1025 group=#1025 python-path=/var/www/html/
      WSGIProcessGroup apis.eos.arz.oeaw.ac.at user=#1025 group=#1025 python-path=/var/www/html/
      WSGIScriptAlias / /var/www/html/apisapp/apis/wsgi.py
      <Directory /var/www/html>
        Require all granted
        AllowOverride All
        Options All granted
      </Directory>
      Alias /static /var/www/html/apisapp/static_dir #static directories to server via Apache
      Alias /downloads /var/www/html/apisapp/downloads
   </VirtualHost>

If the database is connected and the virtualhost is configured you are good to go:

.. code-block:: bash

    service apache2 reload


.. _Apache: https://httpd.apache.org/