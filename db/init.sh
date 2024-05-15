path_db_bin=`pg_config --bindir`
path_db_config=`psql -U postgres --no-align --quiet --tuples-only --command='SHOW config_file'`
path_pg_hba=`psql -U postgres --no-align --quiet --tuples-only --command='SHOW hba_file'`
path_db_data=`psql -U postgres --no-align --quiet --tuples-only --command='SHOW data_directory'`

#config setup
sed -i "s/^#*\(log_replication_commands *= *\).*/\1on/" $path_db_config
sed -i "s/^#*\(archive_mode *= *\).*/\1on/" $path_db_config
sed -i "s|^#*\(archive_command *= *\).*|\1'cp %p /tmp/archive/%f'|" $path_db_config
sed -i "s/^#*\(max_wal_senders *= *\).*/\110/" $path_db_config
sed -i "s/^#*\(wal_level *= *\).*/\1replica/" $path_db_config
sed -i "s/^#*\(wal_log_hints *= *\).*/\1on/" $path_db_config
sed -i "s/^#*\(logging_collector *= *\).*/\1on/" $path_db_config
sed -i -e"s/^#log_filename = 'postgresql-\%Y-\%m-\%d_\%H\%M\%S.log'.*$/log_filename = 'postgresql.log'/" $path_db_config
sed -i "s/#log_line_prefix = '%m \[%p\] '/log_line_prefix = '%m [%p] %q%u@%d '/g" $path_db_config

#database setup
mkdir -p /tmp/archive
psql -c "CREATE USER $DB_REPL_USER WITH REPLICATION LOGIN PASSWORD '$DB_REPL_PASSWORD';"
psql -c "CREATE DATABASE $DB_DATABASE;"
psql -d $DB_DATABASE -a -f /init.sql
psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_DATABASE TO $DB_USER;"
psql -d $DB_DATABASE -c "ALTER TABLE Emails OWNER TO $DB_USER;"
psql -d $DB_DATABASE -c "ALTER TABLE Phones OWNER TO $DB_USER;"
psql -d db_bot -c "GRANT EXECUTE ON FUNCTION pg_current_logfile() TO $DB_USER;"
psql -d db_bot -c "GRANT EXECUTE ON FUNCTION pg_read_file(text) TO $DB_USER;"
echo "host replication $DB_REPL_USER 0.0.0.0/0 trust" >> $path_pg_hba
echo "host all $DB_USER bot trust" >> $path_pg_hba
/$path_db_bin/pg_ctl restart -D $path_db_data
