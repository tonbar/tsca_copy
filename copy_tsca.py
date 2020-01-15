import os
from datetime import datetime
import shutil
import tkinter as tk
from tkinter import ttk
import logging
import sys

# Global variables
from config import archive_directory_cluster
from config import results_directory_cluster
from config import results_directory_l_drive
from config import ntc_names
from config import ntc_directories
from config import ntc_files
from config import sample_directories
from config import sample_files

# Temp variables
#run_id = "191220_NB551415_0052_AHVVJVAFXY"


def error_conditions(root, e):
    from box import MyInformationWindow
    i = MyInformationWindow(root, label_text=e)


def parse_variables(run_id):
    variables = {}
    # Load variables files for all samples on the run
    for s in next(os.walk(os.path.join(results_directory_cluster, run_id, "IlluminaTruSightCancer")))[1]:
        current_variables = {}
        with open(os.path.join(results_directory_cluster, run_id, "IlluminaTruSightCancer", s,
                               f"{s}.variables")) as vf:
            for line in vf:
                split_line = line.rstrip().split("=")
                try:
                    current_variables[split_line[0]] = split_line[1]
                except IndexError:
                    pass
        variables[s] = current_variables
    return variables


def copy_sample(source_directory, target_directory, run_id, s):
    if sample_files:
        for f in sample_files:
            # Copy files from cluster to L: drive
            shutil.copy2(os.path.join(source_directory, f"{run_id}_{s}_{f}"), target_directory)
    if sample_directories:
        for d in sample_directories:
            if not os.path.exists(os.path.join(target_directory, d)):
                os.makedirs(os.path.join(target_directory, d))
            # Copy directory files
            for f in os.listdir((os.path.join(source_directory, d))):
                shutil.copy2(os.path.join(source_directory, d, f),
                             os.path.join(source_directory, d))
    return f"Sample {s} copy successful"


def copy_ntc(archive_directory, target_directory):
    if ntc_files:
        for f in ntc_files:
            shutil.copy2(os.path.join(archive_directory, f),
                         os.path.join(target_directory))
        for d in ntc_directories:
            # Make directory
            if not os.path.exists(os.path.join(target_directory, d)):
                os.makedirs(os.path.join(target_directory, d))
            # Copy directory files
            for f in os.listdir((os.path.join(archive_directory, d))):
                shutil.copy2(os.path.join(archive_directory, d, f),
                             os.path.join(target_directory, d))
    return "NTC copy successful"


def rename_dir(root, old, new):
    # Print informative error if can't find the original directory
    if not os.path.exists(old):
        err = f"Unable to find directory to rename. Please try again."
        logging.exception(NotADirectoryError(err))
        error_conditions(root, err)
        sys.exit(1)
    # Delete existing destination directories
    if os.path.exists(new):
        try:
            shutil.rmtree(new)
        except PermissionError and OSError:
            err = f"Could not delete an existing directory. Please delete all newly created data manually and " \
                  f"try again."
            logging.exception(PermissionError(err))
            error_conditions(root, err)
            sys.exit(1)
    try:
        os.rename(old, new)
    except:
        err = f"Problem with renaming newly created directories. Please try again."
        logging.exception(Exception(err))
        error_conditions(root, err)
        sys.exit(1)
    return f"Rename {new} successful"


def main():
    # Log to file
    # Delete previous log file if exists
    if os.path.exists(os.path.join(os.getcwd(), "tsca_copy.log")):
        os.remove(os.path.join(os.getcwd(), "tsca_copy.log"))
    # Create logger
    logger = logging.getLogger()
    file_handler = logging.FileHandler(os.path.join(os.getcwd(), "tsca_copy.log"))
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)

    # Start pop-up
    root = tk.Tk()
    root.wm_title("TSCa file copy")
    root.label = ttk.Label(text="Software is working. Please wait.")
    root.label.grid(column=0,  row=0)
    root.eval('tk::PlaceWindow %s center' % root.winfo_pathname(root.winfo_id()))
    from box import MyEntryWindow
    w = MyEntryWindow(root)
    try:
        run_id = w.run_id
    except AttributeError:
        err = f"Run id entry was not entered correctly. Please start again."
        logging.exception(AttributeError(err))
        error_conditions(root, err)
        sys.exit(1)

    # Obtain current year
    yr = datetime.now().year

    # Check existence of results directory on L: and if not there, create it
    if not os.path.exists(os.path.join(results_directory_l_drive, f"{yr} Runs")):
        os.makedirs(os.path.join(results_directory_l_drive, f"{yr} Runs"))

    # Obtain worksheet id
    # Load variables files
    try:
        all_variables = parse_variables(run_id)
    except StopIteration:
        err = f"Run id was entered incorrectly as {run_id}"
        logging.exception(err)
        error_conditions(root, err)
        sys.exit(1)

    # Extract worksheet id from variables files
    worksheets = []
    for s, d in all_variables.items():
        worksheets.append(d.get('worklistId'))
    worksheet_ids = list(set(worksheets))

    if len(worksheet_ids) != 1:
        err = f"Unable to identify the worksheet id for run {run_id}. Program Exiting."
        logging.exception(Exception(err))
        error_conditions(root, err)
        sys.exit(1)

    # Remove " from worksheet id for downstream use
    worksheet_id = worksheet_ids[0].split('"')[1]

    # Make directory named after worksheet on L:
    if not os.path.exists(os.path.join(results_directory_l_drive, f"{yr} Runs", worksheet_id)):
        os.makedirs(os.path.join(results_directory_l_drive, f"{yr} Runs", worksheet_id))

    # Check all required data present on source drives
    

    # Copy data from cluster to L: drive
    try:
        for sample in next(os.walk(os.path.join(results_directory_cluster, run_id, "IlluminaTruSightCancer")))[1]:
            # Name directories
            archive_directory = os.path.join(archive_directory_cluster, run_id)
            source_directory = os.path.join(results_directory_cluster, run_id, "IlluminaTruSightCancer", sample)
            target_directory = os.path.join(results_directory_l_drive, f"{yr} Runs", worksheet_id, sample)
            # Make directory named after sample on L: drive
            if not os.path.exists(target_directory):
                os.makedirs(os.path.join(target_directory))
            if sample not in ntc_names:
                logger.info(copy_sample(source_directory, target_directory, run_id, sample))
            else:
                logger.info(copy_ntc(archive_directory, target_directory))
    except:
        err = AttributeError(f"Invalid run ID. Please check and try again.")
        logging.exception(err)
        error_conditions(root, err)
        sys.exit(1)

    # Rename sample directories on L: drive with order. Do not rename NTC.
    for sample, d in all_variables.items():
        # Find the number for order
        retrieved_order = d.get('order')
        if len(retrieved_order) != 2:
            order = f"0{retrieved_order}"
        else:
            order = retrieved_order
        directory_new_name = f"{order} {sample}"

        # Rename all samples except NTC
        if sample not in ntc_names:
            old_path = os.path.join(results_directory_l_drive, f"{yr} Runs", worksheet_id, sample)
            new_path = os.path.join(results_directory_l_drive, f"{yr} Runs", worksheet_id, directory_new_name)
            logger.info(rename_dir(root, old_path, new_path))

    # Check expected number of entries in log file
    expected_num_log_entries = ((len(all_variables.keys()) - len(ntc_names)) * 2) + len(ntc_names)
    print(expected_num_log_entries)
    with open(os.path.join(os.getcwd(), "tsca_copy.log"), 'r') as lf:
        num_log_entries = sum(1 for _ in lf)
    print(num_log_entries)
    if num_log_entries == expected_num_log_entries:
        from box import MyInformationWindow
        i = MyInformationWindow(root, label_text="Software has completed successfully")
    else:
        from box import MyInformationWindow
        i = MyInformationWindow(root, label_text="Software has failed. Please troubleshoot and try again.")


if __name__ == '__main__':
    main()
