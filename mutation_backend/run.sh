#!/bin/bash

baseDir="/home/nimashiri/vsprojects/mutation_analysis/mutation_backend"
mutatedDir="/home/nimashiri/vsprojects/mutation_analysis/temp/"

cd "/home/nimashiri/vsprojects/mutation_analysis/mutation_backend"


for inputVal in "$baseDir"/*
do
  if [[ $inputVal =~ \.c$ ]];
  then
	if [[ $1 = 'REDAWN' ]];
	then
		echo $inputVal
		echo $mutatedDir$2
		txl -o "$mutatedDir$2" $inputVal ./CtoCprime.Txl
	  
	elif [[ $1 = 'REDAWZ' ]];
	then
	 	txl -o "$mutatedDir$2" $inputVal ./REDAWZ.Txl
	  
	elif [[ $1 = 'REC2A' ]];
	then
	  txl -o "$mutatedDir$2" $inputVal ./REC2A.Txl
	  
	elif [[ $1 = 'RMFS' ]];
	then
	  txl -o "$mutatedDir$2" $inputVal ./RMFS.Txl
	  
	elif [[ $1 = 'REC2M' ]];
	then
	  txl -o "$mutatedDir$2" $inputVal ./REC2M.Txl
	  
	elif [[ $1 = 'REM2A' ]];
	then
	  txl -o "$mutatedDir$2" $inputVal ./REM2A.Txl
	fi 
  fi
done




