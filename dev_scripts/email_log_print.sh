if test "$#" -ne 1; then
    echo "usage: $0 log_filename"
    exit 1
fi

docker exec -it vdgsa_django bash -c "cat email_logs/$1"
