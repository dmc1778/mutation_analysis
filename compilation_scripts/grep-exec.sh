#! /bin/bash

cd /home/nimashiri/

chmod -R 755 diffutils-3.6

cd /home/nimashiri/diffutils-3.6/
./configure
make check
rm -rf /home/nimashiri/diffutils-3.6/
