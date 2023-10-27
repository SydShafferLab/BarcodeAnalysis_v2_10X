#!/bin/bash
#BSUB -J EB_10X
#BSUB -o EB_10X.%J.out
#BSUB -e EB_10X.%J.error
#BSUB -q normal
#BSUB -n 6
#BSUB -M 10000
#BSUB -R "span[hosts=1] rusage [mem=10000]"

python ./scripts/ExtractBarcodes_10X.py paths_and_variables.json