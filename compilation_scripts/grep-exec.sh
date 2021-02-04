#! /bin/bash

cd /home/nimashiri/

chmod -R 755 grep-3.6

cd /home/nimashiri/grep-3.6/
./configure
make check
rm -rf /home/nimashiri/grep-3.6/
