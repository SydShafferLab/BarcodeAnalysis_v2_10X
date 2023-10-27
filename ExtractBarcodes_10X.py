import argparse
import jstyleson
import os
import subprocess
from time import sleep
from collections import Counter

def process_file(folder_path, target1, target2):
    print("Running pre-starcode prep...")

    #This is input into starcode. It includes just the unmodified barcodes. 
    scinput_path = f"{folder_path}/sc_input.txt" 

    #This output file contains the CB, the unmodified barcode, whether this sequence was found using target1 or target2 (see below) and which sample the CB belongs to.
    #This output will be fed to modify_barcode function
    step1_output_path = f"{folder_path}/step1_output.txt" 

    output_table = []
    bp_output_table = []

    # Loop through all files in the specified folder
    for filename in os.listdir(folder_path):
        # Check if the file ends with "unmapped.txt"
        if filename.endswith("unmapped.txt"):
            with open(os.path.join(folder_path, filename), 'r') as file:
                for line in file:
                    # Split the line into cell barcode and sequence
                    cell_barcode, sequence = line.strip().split()

                    # Check for target1
                    if target1 in sequence:
                        index = sequence.index(target1)
                        if index >= 20:
                            preceding_20bp = sequence[index-20:index]
                            output_table.append((cell_barcode, preceding_20bp, "Target1", filename))
                            bp_output_table.append(preceding_20bp)

                    # Check for target2
                    if target2 in sequence:
                        index = sequence.index(target2)
                        if index + 16 + 20 <= len(sequence):
                            succeeding_20bp = sequence[index+16:index+16+20]
                            output_table.append((cell_barcode, succeeding_20bp, "Target2", filename))
                            bp_output_table.append(succeeding_20bp)

    # Write the output_table to the specified output file
    with open(step1_output_path, 'w') as outfile:
        for item in output_table:
            outfile.write("\t".join(item) + "\n")

    # Write the bp_output_table to the specified 20bp output file
    with open(scinput_path, 'w') as bp_outfile:
        for bp in bp_output_table:
            bp_outfile.write(bp + "\n")

    print("Pre-starcode prep complete!")


def run_starcode(folder_path, sc_mm, starcode_path):
    print("Running starcode...")

    sc_input_path = f"{folder_path}/sc_input.txt"
    sc_output_path = f"{folder_path}/sc_output.txt"

    starcodeCommand = [starcode_path + '/starcode', '-d', str(sc_mm), '-t', '20', '-i', sc_input_path, '-o', sc_output_path, '--seq-id']
    subprocess.call(starcodeCommand)
    sleep(1)

    while os.path.isfile(sc_output_path) == False:
        sleep(20)

    print("Starcode complete!")


def modify_barcode(folder_path):
    print("Running post-starcode cleanup...")

    step1_output_path = f"{folder_path}/step1_output.txt"
    sc_output_path = f"{folder_path}/sc_output.txt"
    
    # Read the contents of EB_output.txt into a list
    with open(step1_output_path, "r") as file:
        input_lines = [line.strip().split('\t') for line in file.readlines()]

    # Create a dictionary from sc_output.txt where the key is the lineage_barcode from the first column
    # and the value is the list of indices from the third column.
    replace_dict = {}
    with open(sc_output_path, "r") as file:
        for line in file.readlines():
            parts = line.strip().split('\t')
            lineage_barcode, _, indices = parts  # unpack the three columns
            for index in map(int, indices.split(',')):
                replace_dict[index] = lineage_barcode

    # Replace the values in EB_output.txt based on the dictionary
    for index, lineage_barcode in replace_dict.items():
        if 1 <= index <= len(input_lines):  # Check if index is valid
            input_lines[index - 1][1] = lineage_barcode

    # Write the modified contents back to a file within the folder
    with open(f"{folder_path}/EB_output_modified.txt", "w") as file:
        for line in input_lines:
            file.write('\t'.join(line) + '\n')

    # Generate combo_counts.txt based on sc_input_modified.txt
    combo_counts = Counter(['\t'.join(line) for line in input_lines])

    with open(f"{folder_path}/combo_counts.txt", "w") as file:
        for combo, count in combo_counts.items():
            parts = combo.split('\t')
            file.write(parts[0] + '\t' + parts[1] + '\t' + str(count) + '\n')

    print("Post-starcode cleanup complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process all files in a folder ending with "unmapped.txt" to find target sequences.')
    parser.add_argument('config_file', type=str, help='Path to the JSON configuration file')
    args = parser.parse_args()

    # Read the configuration file
    with open(args.config_file, 'r') as f:
        config = jstyleson.load(f)

    # Extract values from the configuration
    scripts_path = config['scripts_path']
    folder_path = config['folder_path']
    target1 = config['target1']
    target2 = config['target2']
    sc_mm = config['sc_mm']

    # Add starcode to PATH
    starcode_path = scripts_path + '/starcode/'
    os.environ["PATH"] += starcode_path

    print("Running ExtractBarcodes...")

    process_file(folder_path, target1, target2)
    run_starcode(folder_path, sc_mm, starcode_path)
    modify_barcode(folder_path)

    print("ExtractBarcodes complete!")