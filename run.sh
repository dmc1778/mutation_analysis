#! /bin/bash



# python3 analyze.py /home/nimashiri/postgres-REL_13_1/src/

project_name=postgre
mutantSourcesDir=/home/nimashiri/postgres-REL_13_1/src
targetBuggyDir=/home/nimashiri/vsprojects/mutation_analysis/postgres/buggy
targetCleanDir=/home/nimashiri/vsprojects/mutation_analysis/postgres/clean

python3 mutatePostgre.py $postgre $mutantSourcesDir $targetBuggyDir $targetCleanDir
