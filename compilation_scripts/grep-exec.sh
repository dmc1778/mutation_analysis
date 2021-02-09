#! /bin/bash

cd /home/nimashiri/

chmod -R 755 postgres-REL_13_1

cd /home/nimashiri/postgres-REL_13_1/
./configure
make check
rm -rf /home/nimashiri/postgres-REL_13_1/
