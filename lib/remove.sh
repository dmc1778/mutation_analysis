#! /bin/bash

./removeComment <$1> $2

cp -r ~/vsprojects/mutation_analysis/$2 $1

rm -f ~/vsprojects/mutation_analysis/$2
