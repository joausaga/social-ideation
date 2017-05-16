./env/bin/supervisorctl stop all
./rabbitmq_server-3.6.5/sbin/rabbitmqctl stop
kill -9 $(cat /tmp/supervisord.pid)
