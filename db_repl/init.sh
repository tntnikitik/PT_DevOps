sleep 20

path_db_bin=`pg_config --bindir`
path_db_data=`psql -U postgres --no-align --quiet --tuples-only --command='SHOW data_directory'`
/$path_db_bin/pg_ctl stop -D $path_db_data
rm -rf /var/lib/postgresql/data/*
pg_basebackup -R -h db -U $DB_REPL_USER -D /var/lib/postgresql/data -P
/$path_db_bin/pg_ctl start -D $path_db_data
