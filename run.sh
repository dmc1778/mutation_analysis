#! /bin/bash



# python3 analyze.py /home/nimashiri/postgres-REL_13_1/src/

project_name=postgre
mutantSourcesDir='/home/nimashiri/postgres-REL_13_1/src'
targetBuggyDir='/home/nimashiri/vsprojects/mutation_analysis/postgres/buggy'
targetCleanDir='/home/nimashiri/vsprojects/mutation_analysis/postgres/clean'

python3 mutatePostgre.py REDAWN $project_name $mutantSourcesDir $targetBuggyDir $targetCleanDir




python3 analyze.py /eecs/home/nshiri/nima/postgres-REL_12_5/src

project_name=postgre-12-5
mutantSourcesDir='/eecs/home/nshiri/nima/postgres-REL_12_5/src'
targetBuggyDir='/eecs/home/nshiri/nima/mutation_analysis/postgres/buggy'
targetCleanDir='/eecs/home/nshiri/nima/mutation_analysis/postgres/clean'

python3 mutatePostgre.py REDAWN $project_name $mutantSourcesDir $targetBuggyDir $targetCleanDir

