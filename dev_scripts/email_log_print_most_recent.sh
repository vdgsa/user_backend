docker exec -it vdgsa_django bash -c 'cat email_logs/$(ls -1 email_logs | tail -n 1)'
