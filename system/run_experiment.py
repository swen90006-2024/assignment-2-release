# Code is written based on https://jzamudio.com/sql-grammar-based-fuzzer/

import subprocess
import random
import csv
import argparse
import os
import glob

import matplotlib.pyplot as plt

from grammar_fuzzer import MyGrammarFuzzer
from mutation_fuzzer import MyMutationFuzzer

# Common supporting functions
def plot(x, y):
    plt.plot(x, y, linestyle='-')
    plt.xlabel('# Input')
    plt.ylabel('% Coverage')
    plt.title('Branch coverage over time')
    plt.savefig('plot.pdf')
    print("Saved plot.pdf")

def remove_file_if_exists(file_path):
    print("File to be deleted :" + str(file_path))
    if os.path.isfile(file_path):  # Check if the file exists
        try:
            os.remove(file_path)  # Attempt to remove the file
            pass
        except PermissionError:
            pass
        except Exception as e:
            pass
    else:
        pass

# Main experiment class that support all type of fuzzers
class Experiment:
    def __init__(self, fuzzer_type, db_file, corpus_path = None, feedback_enabled = False, clean_database = False):
        if fuzzer_type == "grammar_based":
            self.fuzzer = MyGrammarFuzzer()
        elif fuzzer_type == "mutation_based":
            random.seed()
            # initialize the seed corpus
            seeds = []

            # Pattern to match files with "seed" as the extension
            pattern = os.path.join(corpus_path, '*.dat')

            # Get a list of all files matching the pattern
            seed_files = glob.glob(pattern)

            # Loop through each file and read its contents
            for file_path in seed_files:
                with open(file_path, 'r') as file:
                    content = file.read()
                    seeds.append(content)
                    
            # Ensure the seed corpus is not empty
            if len(seeds) == 0:
                print(f'[ERROR] Mutation fuzzing requires a non-empty seed corpus')
                exit()
                    
            self.fuzzer = MyMutationFuzzer(seeds)
        else:
            print(f"[ERROR] The specified fuzzer type '{fuzzer_type}' is not support")
            exit()
            
        if db_file == None:
            db_file = "empty.db"

        self.db_file = db_file
        self.sqlite3 = self.find_sqlite3_executable()
        self.feedback_enabled = feedback_enabled
        self.clean_database = clean_database

    def find_sqlite3_executable(self):
        # Try to find sqlite3 in the current working directory or the script's directory
        script_directory = os.path.dirname(os.path.abspath(__file__))
        script_sqlite3_path = os.path.join(script_directory, "sqlite3")

        if os.path.exists(script_sqlite3_path):
            return script_sqlite3_path

        # If sqlite3 is not found in the script's directory or CWD, you can add additional paths or customize this logic.
        raise FileNotFoundError("sqlite3 executable not found. Please set the path manually.")

    def remove_file_if_exists(self, file_path):
        if os.path.isfile(file_path):  # Check if the file exists
            try:
                os.remove(file_path)  # Attempt to remove the file
                print(f"File '{file_path}' has been removed.")
            except PermissionError:
                print(f"Permission denied to remove file '{file_path}'.")
            except Exception as e:
                print(f"An error occurred while removing file '{file_path}': {e}")
        else:
            print(f"File '{file_path}' does not exist.")

    def run(self, sqlcmd):
        if self.clean_database:
            remove_file_if_exists(self.db_file)

        # Replace NULL bytes to prevent ValueError exceptions
        sqlcmd = sqlcmd.replace('\x00', '_')
        command = f'echo "{sqlcmd}" | {self.sqlite3} {self.db_file}'
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, error = process.communicate()


    def get_coverage(self):
        coverage_report_file = "coverage_report.csv"
        gcovr_command = f"gcovr --csv --txt-metric branch --exclude-unreachable-branches -o {coverage_report_file}"
        subprocess.run(gcovr_command, shell=True, check=True)

        with open(coverage_report_file, 'r') as f:
            branch_cov_percent = None
            reader = csv.DictReader(f, delimiter=',')
            for row in reader:
                assert 'filename' in row
                assert 'branch_percent' in row
                if row['filename'] == 'sqlite3.c':
                    branch_cov_percent = float(row['branch_percent'])
                    break
            assert branch_cov_percent is not None
        return branch_cov_percent

    def clean(self):
        print("Cleaning up project directory for a new measurement...")
        # Delete old empty.db, PDFs, coverage reports
        subprocess.run("make clean", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # Build sqlite and .gcno if not exists.
        subprocess.run("make", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("Done.")

    def generate_and_run(self):
        new_input = self.fuzzer.fuzz()
        self.run(new_input)
        return new_input
    
    def generate_and_run_k_plot_coverage(self, k, plot_every_x):
        self.clean()

        cov = []
        old_cov = 0
        for i in range(k):
            print("Generate and run input ", i)
            new_input = self.generate_and_run()
            if plot_every_x != -1 and i%plot_every_x==0:
                new_cov = self.get_coverage()
                if self.feedback_enabled:
                    if (new_cov > old_cov):
                        print("[UPDATE] New code has been covered. Add the generated input as a new seed.")
                        self.fuzzer.add_seed(new_input)
                old_cov = new_cov
                print("Current coverage: " + str(old_cov))
            cov.append(old_cov)

        # Do one final coverage measurment (or the only one, if plot_every_x == -1).
        cov.append(self.get_coverage())

        plot(x=list(range(len(cov))), y=cov)

def main():
    parser = argparse.ArgumentParser(description='SQL fuzzer and coverage plotter')
    parser.add_argument('--runs', type=int, help='How many inputs should be generated and run?')
    parser.add_argument('--plot-every-x', default=-1, type=int, help='Coverage will be measured after plot_every_x. (default:-1, i.e. there is only one coverage measurement at the end)')
    parser.add_argument('--corpus', type=str, help='Path to the seed corpus (optional)')
    parser.add_argument('--db_file', type=str, help='Name of the database file (optional)')
    parser.add_argument('--fuzzer_type', type=str, help='Type of fuzzer')
    parser.add_argument('--feedback_enabled', action="store_true", help='Enable coverage feedback (optinal)')
    parser.add_argument('--clean_database', action="store_true", help='Clean the database after each run (optional)')
    args = parser.parse_args()
    runs = args.runs
    plot_every_x = args.plot_every_x
    corpus = args.corpus
    db_file = args.db_file
    fuzzer_type=args.fuzzer_type
    feedback_enabled=args.feedback_enabled
    clean_database=args.clean_database
    
    if feedback_enabled:
        plot_every_x = 1

    experiment = Experiment(fuzzer_type, db_file, corpus, feedback_enabled, clean_database)
    experiment.generate_and_run_k_plot_coverage(runs, plot_every_x)

if __name__ == "__main__":
    main()
