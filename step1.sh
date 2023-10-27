#!/bin/bash
#BSUB -J unmapped_T3
#BSUB -o unmapped_T3.%J.out
#BSUB -e unmapped_T3.%J.error
#BSUB -q normal
#BSUB -n 1
#BSUB -M 30000

module load samtools/1.11

cd /project/shafferslab/Raymond/RWSN066/T3/outs

samtools view -b -f 4 possorted_genome_bam.bam > unmapped.bam

samtools view unmapped.bam | awk '{
    for (i = 12; i <= NF; i++) {
        if ($i ~ /^CB:Z:/) {
            cb = substr($i, 6);  # Extracts the cell barcode value after "CB:Z:"
        }
    }
    print cb "\t" $10;  # Print cell barcode and read sequence
}' > T3_unmapped.txt