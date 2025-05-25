import subprocess
import os
import sys
import time
import shlex
import argparse

OPERATIONS = ["UPLOAD", "DOWNLOAD"]
VOLUMES_MB = [10, 50, 100] 
CLIENT_WORKER_LOAD_COUNTS = [1, 5, 50]

CLIENT_UPLOAD_FILES_DIR = "test_files_client"
PYTHON_EXE = sys.executable
STRESS_CLIENT_SCRIPT = "stress_test_client.py"


def run_single_stress_test(
    test_id_global,
    server_ip_arg,
    server_port_arg,
    operation_arg,
    volume_mb_for_table_arg,
    num_client_load_workers_arg,
    client_stress_concurrency_type_arg,
    actual_server_worker_count_arg,
    actual_server_type_name_arg,
    output_csv_file_path_arg
):

    volume_as_float_str = f"{float(volume_mb_for_table_arg)}" # e.g., "10.0"

    volume_param_for_stress_client_call = volume_as_float_str 

    server_config_info_str_for_stress_client_call = f"{actual_server_worker_count_arg}_{actual_server_type_name_arg}"

    command_to_execute = [
        PYTHON_EXE,
        STRESS_CLIENT_SCRIPT,
        str(test_id_global),
        server_ip_arg,
        str(server_port_arg),
        operation_arg,
        volume_param_for_stress_client_call, 
        str(num_client_load_workers_arg),
        client_stress_concurrency_type_arg,
        server_config_info_str_for_stress_client_call
    ]

    print(f"\n[Automator] Test Global ID: {test_id_global}")
    print(f"  Target Server Config: {actual_server_type_name_arg} with {actual_server_worker_count_arg} workers")
    print(f"  Client Stress Config: {num_client_load_workers_arg} workers using {client_stress_concurrency_type_arg}")
    print(f"  Test Operation: {operation_arg}, Context Volume for table: {volume_mb_for_table_arg}MB")
    print(f"  Executing: {shlex.join(command_to_execute)}")

    if operation_arg == "UPLOAD":
        filename_for_check = f"file_{volume_as_float_str}MB.dat" 
        expected_local_file = os.path.join(CLIENT_UPLOAD_FILES_DIR, filename_for_check)
        
        if not os.path.exists(expected_local_file):
            error_message_detail = f"UPLOAD_FILE_NOT_FOUND:{expected_local_file}" 
            print(f"  [Automator] ERROR: {error_message_detail}. Please ensure create_dummy_files.py created this exact filename.")
            csv_line_on_error = f"{test_id_global},{operation_arg},{volume_mb_for_table_arg}MB,{num_client_load_workers_arg},{actual_server_worker_count_arg},0,0,0,{num_client_load_workers_arg},{error_message_detail}\n"
            with open(output_csv_file_path_arg, "a") as f_out:
                f_out.write(csv_line_on_error)
            return

    try:
        process_result = subprocess.run(command_to_execute, capture_output=True, text=True, timeout=1800, check=False)

        final_csv_line = ""
        if process_result.stdout:
            stress_client_raw_output = process_result.stdout.strip()
            print(f"  [Automator] STDOUT from {STRESS_CLIENT_SCRIPT}:\n    {stress_client_raw_output}")
            
            output_parts = stress_client_raw_output.split(',')
            if len(output_parts) >= 9:
                avg_time = output_parts[5]
                avg_throughput = output_parts[6]
                succeeded_workers = output_parts[7]
                failed_workers = output_parts[8]

                csv_data_for_table = [
                    str(test_id_global),
                    operation_arg,
                    f"{volume_mb_for_table_arg}MB", 
                    str(num_client_load_workers_arg),
                    str(actual_server_worker_count_arg),
                    avg_time,
                    avg_throughput,
                    succeeded_workers,
                    failed_workers
                ]
                final_csv_line = ",".join(csv_data_for_table) + "\n"
            else:
                final_csv_line = f"{test_id_global},{operation_arg},{volume_mb_for_table_arg}MB,{num_client_load_workers_arg},{actual_server_worker_count_arg},ERROR,0,0,{num_client_load_workers_arg},MALFORMED_STRESS_CLIENT_OUTPUT\n"
                print(f"  [Automator] ERROR: Malformed output from {STRESS_CLIENT_SCRIPT}")
        else:
            final_csv_line = f"{test_id_global},{operation_arg},{volume_mb_for_table_arg}MB,{num_client_load_workers_arg},{actual_server_worker_count_arg},ERROR,0,0,{num_client_load_workers_arg},NO_STDOUT_FROM_STRESS_CLIENT\n"
            print(f"  [Automator] ERROR: No STDOUT from {STRESS_CLIENT_SCRIPT}.")

        with open(output_csv_file_path_arg, "a") as f_out:
            f_out.write(final_csv_line)

        if process_result.stderr:
            print(f"  [Automator] STDERR from {STRESS_CLIENT_SCRIPT}:\n    {process_result.stderr.strip()}")
        
        if process_result.returncode != 0:
            print(f"  [Automator] WARNING: {STRESS_CLIENT_SCRIPT} exited with code {process_result.returncode}")

    except subprocess.TimeoutExpired:
        timeout_error_detail = "TIMEOUT_EXPIRED_30MIN"
        print(f"  [Automator] ERROR: {timeout_error_detail}")
        csv_line_on_error = f"{test_id_global},{operation_arg},{volume_mb_for_table_arg}MB,{num_client_load_workers_arg},{actual_server_worker_count_arg},0,0,0,{num_client_load_workers_arg},{timeout_error_detail}\n"
        with open(output_csv_file_path_arg, "a") as f_out:
            f_out.write(csv_line_on_error)
    except Exception as e_main:
        execution_failure_detail = f"AUTOMATOR_EXEC_FAIL:{type(e_main).__name__}"
        print(f"  [Automator] ERROR: Failed to execute/process {STRESS_CLIENT_SCRIPT}: {e_main}")
        csv_line_on_error = f"{test_id_global},{operation_arg},{volume_mb_for_table_arg}MB,{num_client_load_workers_arg},{actual_server_worker_count_arg},0,0,0,{num_client_load_workers_arg},{execution_failure_detail}\n"
        with open(output_csv_file_path_arg, "a") as f_out:
            f_out.write(csv_line_on_error)


def main_automator():
    parser = argparse.ArgumentParser(description="Automated runner for stress_test_client.py")
    parser.add_argument("server_ip", help="Target Server IP address")
    parser.add_argument("server_port", type=int, help="Target Server port number")
    parser.add_argument("current_server_workers", type=int, choices=[1, 5, 50], help="Number of workers the currently running server is configured with (1, 5, or 50)")
    parser.add_argument("current_server_type", choices=["mthread_pool", "mproc_pool"], help="Type of the currently running server ('mthread_pool' or 'mproc_pool')")
    parser.add_argument("client_stress_type", choices=["thread", "process"], help="Concurrency type for stress_test_client.py's own workers ('thread' or 'process')")
    parser.add_argument("output_csv", help="Path to the CSV file to append results to")
    parser.add_argument("--offset", type=int, default=0, help="Starting number for Test ID (Nomor column offset, default 0)")

    args = parser.parse_args()

    if not os.path.exists(STRESS_CLIENT_SCRIPT):
        print(f"CRITICAL ERROR: The stress client script '{STRESS_CLIENT_SCRIPT}' was not found. Exiting.")
        sys.exit(1)

    if not os.path.exists(CLIENT_UPLOAD_FILES_DIR) and "UPLOAD" in OPERATIONS :
        print(f"WARNING: Client upload files directory '{CLIENT_UPLOAD_FILES_DIR}' not found. UPLOAD tests may fail if files are missing. Ensure create_dummy_files.py (float-naming version) has been run in the correct directory.")

    if not os.path.exists(args.output_csv) or os.path.getsize(args.output_csv) == 0:
        with open(args.output_csv, "w") as f_header:
            f_header.write("Nomor,Operasi,Volume,JumlahClientWorkerPool,JumlahServerWorkerPool,WaktuTotalPerClient(s),ThroughputPerClient(Bps),JumlahClientSukses,JumlahClientGagal\n")
        print(f"Initialized CSV results file: {args.output_csv}")
    else:
        print(f"Appending results to existing CSV file: {args.output_csv}")
    
    print(f"--- Starting Batch of Automated Client Runs ---")
    print(f"  Targeting Server: {args.server_ip}:{args.server_port}")
    print(f"  Assumed Server Config: Workers={args.current_server_workers}, Type='{args.current_server_type}'")
    print(f"  Client Stress Type for these runs: '{args.client_stress_type}' pool in {STRESS_CLIENT_SCRIPT}")
    print(f"  Test ID (Nomor) Offset: {args.offset}")
    
    test_run_count_this_batch = 0
    
    for operation_loop_var in OPERATIONS:
        for volume_mb_loop_var in VOLUMES_MB:
            for num_client_load_workers_loop_var in CLIENT_WORKER_LOAD_COUNTS:
                test_run_count_this_batch += 1
                effective_global_test_id = args.offset + test_run_count_this_batch
                
                run_single_stress_test(
                    effective_global_test_id,
                    args.server_ip,
                    args.server_port,
                    operation_loop_var,
                    volume_mb_loop_var,
                    num_client_load_workers_loop_var,
                    args.client_stress_type, 
                    args.current_server_workers,
                    args.current_server_type,   
                    args.output_csv             
                )
                time.sleep(5) 

    total_tests_in_this_batch_config = len(OPERATIONS) * len(VOLUMES_MB) * len(CLIENT_WORKER_LOAD_COUNTS)
    print(f"\n--- Batch of {test_run_count_this_batch} (expected {total_tests_in_this_batch_config}) Client Runs Complete ---")
    print(f"Results for this batch appended to: {args.output_csv}")

if __name__ == "__main__":
    main_automator()
