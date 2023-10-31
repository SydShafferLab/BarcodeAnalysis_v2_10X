# BarcodeAnalysis_v2_10X
## General work flow
To combine barcodes with 10X we insert transcribable lineage barcodes into cells and then perform 10X on those barcoded cells. 10X will capture the transcribed lineage barcode and attach it's cell barcode to it. Since these reads do not map to the genome, they will be marked as "unmapped" in the `possorted_genome_bam.bam` file. This wiki walks you through how to use cellranger and this code to extract lineage barcodes and link them to their respective Cell Barcodes (CB). 

## Setting up the python environment (you should only need to do this once)
All this code is run on the pmacs cluster as starcode is very memory intensive. NOTE: If you have already installed this file on the cluster and compiled starcode start at step 9.   

1. If you don’t already have it I recommend you download cyberduck (https://cyberduck.io) to easily interface with the cluster.   
2. Once cyberduck is installed, open it, hit open connection, in the top drop-down menu select "SFTP(SSH File Transfer Protocol)", for server type in "mercury.pmacs.upenn.edu", enter your PMACS username and password, and hit connect.  
3. Download all the files in this GitHub repository by hitting the green "Code" button above on this page, and select "Download ZIP".  
4. Drag and drop the downloaded file "BarcodeAnalysis_v2_10X-main" into your directory of choice.   
5. Change the file name from "BarcodeAnalysis-main" to simply "BarcodeAnalysis".   
6. To set up the virtual environment containing the necessary dependencies, open up terminal and type in `ssh <username>@consign.pmacs.upenn.edu` replacing `<username>` with your PMACS username, and hit enter. Then enter your PMACS password and hit enter.   
7. You should now be in a session on the terminal. Enter `bsub -Is bash` to start up an interactive session.   
8. Compile starcode by running: `make -C /path/to/starcode`.   
9. We will now make sure we are in the correct python version by entering the command `module load python/3.6.3`. If this worked you should be able to enter python `--version` and see the output `Python 3.6.3`.  
10. Enter cd /path/to/BarcodeAnalysis_v2_10X/. (tip: to get paths of folders I usually right click on them in cyberduck, select "copy URL", and select either choice, and keep everything after ".edu").   
11. Now set up your virtual environment by entering the line `python -m virtualenv bcEnv`.   
12. Next activate your virtual environment by entering `source /path/to/BarcodeAnalysis_v2_10X/bcEnv/bin/activate`.   
13. We can now install the necessary packages in this environment by running: `pip install -r /path/to/BarcodeAnalysis_v2_10X/requirements.txt`.  
14. Your virtual environment is now ready. If you ever want to leave the virtual environment simply enter `deactivate`. Every time you want to active the environment enter: `source /path/to/BarcodeAnalysis_v2_10X/bcEnv/bin/activate`.  
15. You also need to be able to run CellRanger on the cluster, you can access cellranger by either installing it as described [here](https://support.10xgenomics.com/single-cell-gene-expression/software/pipelines/latest/installation), or you can use the version of cellranger on the cluster. To use the version on the cluster, simply log in, activate a node by typing in bsub -Is bash, hitting enter, and then entering module load cellranger/5.0.1 (you can see if there are other versions by typing `module avail`). If you are downloading cell ranger make sure you add it you your path every time before running a cellranger command by entering this command `export PATH=/path/to/cellranger-3.1.0:$PATH` replacing with your path to the cellranger folder. If you are using the module on the cluster then just run `module load cellranger/5.0.1` every time before running `cellranger`. Note: I downloaded cell ranger so my example files will use `export PATH=/path/to/cellranger-3.1.0:$PATH`.  
    
## Run cellranger to map 10X reads to genome
Use `cellranger` to process your sequencing output. Here's a link to the [10X tutorial](https://support.10xgenomics.com/single-cell-gene-expression/software/pipelines/latest/using/tutorial_ov). 
    
## Step 1: Extract barcodes from .bam file
After running `cellranger` on the sequencing output, one of your output files will be `possorted_genome_bam.bam`. This file contains all the reads of your sample. There will be many reads that were not able to map to your genome. A good fraction of these reads should be your lineage barcode reads. To extract these reads, run `step1.sh`. An example of `step1.sh` is on the github. There are several things you should check in this script before running it.

1. Change the `BSUB` calls to match your desired error/output filenames.    
2. This script calls `samtools`. Currently, this script calls `samtools` as a module that is pre-installed in the cluster. 
3. Change the directory to your `/outs` directory from your `cellranger` output. 
4. On line 22, change the output filename as you desire. 
5. Submit this job to the cluster by inputting `cd path/to/BarcodeAnalysis_v2_10X` and `bsub < step1.sh`. 
    
Once you've successfully run `step1.sh` on all your 10X files, move all your `.txt` files to a new directory. You'll be calling this directory in Step 2.   

## Step 2: Cluster barcodes
1. Activate the python environment (you should do this everytime you run step2 code). Enter: `source /path/to/BarcodeAnalysis_v2_10X/bcEnv/bin/activate`.   
2. Inspect `step2.sh`. The only parts of this script that you should change are the `#BSUB` options. You'll notice that this script calls `ExtractBarcodes_10X.py`, and your variables will be called from `paths_and_variables.json`.    
3. Inspect `paths_and_variables.json`. These are the variables that you'll need to change.    
  1. `scripts_path`: Input `path/to/BarcodeAnalysis_v2_10X`
  2. `folder_path`: Input the path to the directory that holds all your `.txt` output from Step 1. 
  3. `target1` and `target2`: These are the sequences that flank the 20bp lineage barcode. If you are using barcode_v2 from the Shaffer Lab, you should not need to change these sequences.  
  4. `sc_mm`: This is the maximum levenschtein distances allowed for two barcode sequences to be considered the same. You may need to empirically determine the optimal `sc_mm` to get your expected number of unique barcodes. The highest value that the software allows for is 8. 
4. Submit this job to the cluster by inputting `cd path/to/BarcodeAnalysis_v2_10X` and `bsub < step2.sh`. 
    
After successfully running `step2.sh`, you should see the following output files:

1. `step1_output.txt`: This is a table that includes the Cell Barcode (CB), 20bp lineage barcode, whether the barcode was found using `target1` or `target2`, and the `*unmapped.txt` file that this CB comes from. 
2. `sc_input.txt`: This is a list of barcodes from `step1_output.txt` that are fed into `starcode` to cluster barcodes. 
3. `sc_output.txt`: This is the output file from `starcode`. 
4. `EB_output_modified.txt`: Using `sc_output.txt`, this script edits `step1_output.txt` with the modified barcodes. This will be the output you use to map each cell to a lineage barcode. 
5. `combo_counts.txt`: This table summarizes the lineage barcodes mapped to each CB. While I use this table as a sanity check, I do not use it for downstream analyses. 
    
    

