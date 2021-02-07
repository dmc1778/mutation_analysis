#! /bin/bash

cd /home/nimashiri/

chmod -R 755 coreutils-8.32

cd /home/nimashiri/coreutils-8.32/
./configure
make check
rm -rf /home/nimashiri/coreutils-8.32/src/
