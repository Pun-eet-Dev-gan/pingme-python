# how to deploy.

1. apt-get install apache2
2. apt-get install apache2-dev
3. apt-get install python3-dev
4. pip install mod_wsgi
5. mod_wsgi-express module-config
    > a. LoadModule wsgi_module "/home/yongwoo/.conda/envs/pingme/lib/python3.6/site-packages/mod_wsgi/server/mod_wsgi-py36.cpython-36m-x86_64-linux-gnu.so"
      b. WSGIPythonHome "/home/yongwoo/.conda/envs/pingme"
6. sudo chown root /etc/apache2
7. sudo chmod -R 777 /etc/apache2
8. sudo echo LoadModule wsgi_module /home/yongwoo/.conda/envs/pingme/lib/python3.6/site-packages/mod_wsgi/server/mod_wsgi-py36.cpython-36m-x86_64-linux-gnu.so > /etc/apache2/mods-available/mod_wsgi.load


# DB to model
1. flask-sqlacodegen "mysql://yongwoo:dldyddn1@127.0.0.1/pingme" --flask > models.py
