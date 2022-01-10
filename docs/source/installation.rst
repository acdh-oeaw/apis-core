Installation with Docker
========================

This is the recommended way to install APIS on local machines as well as on server infrastructure.

Docker Image
------------
APIS docker images can be pulled from `docker hub <https://hub.docker.com/repository/docker/sennierer/apis>`_. Images are tagged
from v0.9.1 onwards. Latest image is tagged with :latest.
The images are automatically built and tagged and should be up-to-date with altest versions of code.

Docker Compose
--------------

The following docker-compose file can be used as a starting point for deploying an APIS instance:

.. code-block:: yaml

    version: '2'


    services:
            web:
                image: sennierer/apis:latest
                environment:
                    - APIS_PROJECT=apis_test #as used in the apis-settings repo
                    - APIS_DB_NAME=testdb 
                    - APIS_DB_USER=testuser
                    - APIS_DB_PASSWORD=testpwd
                    - APIS_DB_HOST=database
                    - APIS_DB_PORT=3306
                    - APIS_AUTO_CREATE_DB=1
                    - DJANGO_SUPERUSER_PASSWORD=adminpass123 #change that to admin password
                    - DJANGO_SUPERUSER_USERNAME=admin #change that to admin username
                    - DJANGO_SUPERUSER_EMAIL=my_user@domain.com #change that to email
                    # and more e.g. APIS_DB_PORT >> apis-webpage-base/apis/settings/base.py
                container_name: apis_core_apis_test #use apis_core_$APIS_PROJECT, e.g. apis_core_mpr
                command: sh /start-apis/start-apis/start.sh 
                volumes:           
                        - config-volume:/config-apis    
                        - staticfiles-volume:/apis/apis-webpage-base/staticfiles
                networks:
                - backend
                depends_on:
                - database
            
            database:
                image: mysql:5.7
                command: --default-authentication-plugin=mysql_native_password
                restart: always
                environment:
                        - MYSQL_ROOT_PASSWORD=rootpwd
                        - MYSQL_DATABASE=testdb
                        - MYSQL_USER=testuser
                        - MYSQL_PASSWORD=testpwd
                networks:
                        - backend
            nginx:
                image: nginx:latest
                container_name: ngx_apis_apis_test #use ngx_apis_$PROJECT_NAME, e.g, ngx_apis_mpr
                environment:
                    - APIS_PROJECT=apis_test
                    - APIS_SERVER_NAME=localhost #as used in the apis-settings repo >> needs to be present in both images
                volumes:
                    - config-volume:/config-apis    
                    - staticfiles-volume:/staticfiles  
                ports:
                        - "8080:81"
                depends_on:
                        - web
                networks:
                    - backend
                command: /bin/bash -c "envsubst '$${APIS_PROJECT},$${APIS_SERVER_NAME}' < /config-apis/start-apis/nginx/nginx.template > /etc/nginx/conf.d/default.conf && exec nginx -g 'daemon off;'"
    networks:
    backend:
        driver: bridge

    volumes:
    config-volume:
            driver: local
    staticfiles-volume:
            driver: local

After ``docker-compose up`` you should now have a default APIS installation accessible under http://localhost:8080.


Installation without Docker
===========================

Prerequisites
-------------

APIS webapp needs Python 3.6+ and several python packages that can be easily installed by using `pip <https://pip.pypa.io/en/stable/>`_, 
`pipenv <https://github.com/pypa/pipenv>`_, or `poetry <https://python-poetry.org/>`_.

Create a new virtualenv and activate it:

.. code-block:: console

   virtualenv -p pyton3 your_virtualenv_name
   source your_virtualenv_name/bin/activate

To activate the virtualenv on Windows, go to the directory your_virtualenv_name/Scripts and run activate.bat from the command line.


Installation on a linux box
----------------------------

Change to the directory you have downloaded APIS to and install the needed Python packages:

.. code-block:: console

    cd apis-core
    pip install -r requirements.txt

Next you need to create a file called copy the ``APIS_directory/apis-core/apis/settings/settings_test_ci.py`` file to another name.
We suggest ``server.py``::

    cp APIS_directory/apis-core/apis/settings/settings_test_ci.py APIS_directory/apis-core/apis/settings/server.py

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

Once that is done you dont have to include ``--settings=apis.settings.server`` in your commands anymore.

Next we migrate the APIS internal tables:

.. code-block:: console

    python manage.py migrate

and create a superuser:

.. code-block:: console

    python manage.py createsuperuser

answer the questions and hit enter.
Now you can already proceed running the development server:

.. code-block:: console

    python manage.py runserver

should bring up a development server window with your new apis instance.


Installation on Windows
-----------------------

Change to the directory you have downloaded APIS to and install the needed Python packages
In the command prompt that pops up after the activation of the virtualenv, change directory to where you have downloaded apis (eg. to apis-core) and install the modules in requirements.txt

.. code-block:: console

    pip install -r requirements.txt

If you encounter problems while installing the packages in the requirements.txt file, remove the ones that cause the problem (from the requirements.txt file), and download the .whl file of the problematic module from the following site: http://www.lfd.uci.edu/~gohlke/pythonlibs/ (choosing the correct version: your python version must be equal to the number after cp in the name of the .whl file, and your operating system 32-bit/64-bit with the end of the file name.)

Install the missing module by running the following command in the prompt from where your .whl file resides:

.. code-block:: console

    pip install name_of_the_whl_file

Install numpy+mkl, download the wheel file from the link above and install with the command:

.. code-block:: console

    pip install name_of_the_whl_file

Download and install SQLite (www.sqlite.org).

Next copy the dummpysettings.py file and rename it to server.py with the following command:
copy apisapp\apis\settings\dummysettings.py apisapp\apis\settings\server.py
Now edit ``server.py`` to your needs.

If you installed sqlite, it should look like below::

    import os
    from .base import *

    SECRET_KEY = 'd3j@zlckxkw73c3*ud2-11$)d6i)^my(60*o1psh*&-u35#ayi'
    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = True

    DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.sqlite3',
           'NAME': os.path.join('path\\to\\your\\sqlite\\installation', 'db.sqlite3'),
       }
    }

If you intend to use Mysql it should look something like::

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

Once the database connection is set, run:

.. code-block:: console

    python manage.py migrate --settings=apis.settings.server

For convenience we suggest you alter ``manage.py`` to::

    if __name__ == "__main__":
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apis.settings.server")

        from django.core.management import execute_from_command_line

        execute_from_command_line(sys.argv)

Once that is done you dont have to include ``--settings=apis.settings.server`` in your commands anymore.

Next we migrate the APIS internal tables:

.. code-block:: console

    python manage.py makemigrations metainfo entities relations vocabularies highlighter labels webpage
    python manage.py migrate

and create a superuser:

.. code-block:: console

    python manage.py createsuperuser

answer the questions and change to the static directory to download javascript libraries:

If you havent installed NPM and bower yet, install NodeJS, and bower with npm. Bower depends on Node.js and NPM, download the installation package from the Node.js site and click through it. You can now install Bower with npm. You might need to restart Windows to get all the path variables setup.
Open the Git Bash or Command Prompt and install bower with the following command.

.. code-block:: console

    npm install -g bower

If you have already installed bower you can proceed with installing the javascript libraries directly. In the command line or git bash go to the directory apis-webpage\static\webpage\libraries and run:

.. code-block:: console

    bower install

Finally the below command brings up a development server window with your new apis instance.

.. code-block:: console

    python manage.py runserver


Serving APIS via Apache WSGI
----------------------------

If you plan to use APIS in production you should deploy it via a proper webserver. We use Apache_ and ``mod_wsgi`` to
do so. Our apche virtualhost config looks something like:

.. code-block:: aconf

   <VirtualHost *:80>
      ServerName server_name
      ServerAlias server_alias #alias names if needed
      DocumentRoot /var/www/html #document root of your installation
      WSGIDaemonProcess YOUR_URL user=#1025 group=#1025 python-path=/var/www/html/
      WSGIProcessGroup YOUR_URL user=#1025 group=#1025 python-path=/var/www/html/
      WSGIScriptAlias / /var/www/html/apis-core/apis/wsgi.py
      <Directory /var/www/html>
        Require all granted
        AllowOverride All
        Options All granted
      </Directory>
      Alias /static /var/www/html/apis-core/static_dir #static directories to server via Apache
      Alias /downloads /var/www/html/apis-core/downloads
   </VirtualHost>

If the database is connected and the virtualhost is configured you are good to go:

.. code-block:: bash

    service apache2 reload


.. _Apache: https://httpd.apache.org/