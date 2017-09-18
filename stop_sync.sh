./env/bin/supervisorctl stop all
./rabbitmq_server-3.6.10/sbin/rabbitmqctl stop
kill -9 $(cat /tmp/supervisord.pid)
