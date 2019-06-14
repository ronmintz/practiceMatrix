#!/bin/bash

set -x
port=8091
log_file=matrix.log.gz
state_store=/scratch/ron/MatrixCodeLevels/CodeLevel2/GitHubStore/gh_store2017ESX/gh.sqlite
state_store_module=ghstore.store
start_time=1501541900
round_time=3600
num_agent_procs=1
num_rounds=2
export PYTHONPATH=/scratch/ron/MatrixCodeLevels/CodeLevel2
matrix controller -p $port -l $log_file -s $state_store -m $state_store_module -n $num_agent_procs -r $num_rounds -t $start_time -q $round_time
