import os
import socket
import json
import base64
import logging
import time as time_module 
import argparse
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(processName)s - %(threadName)s - %(message)s')

TARGET_SERVER_ADDRESS = ('0.0.0.0', 50000) 

def send_request_to_server(command_str=""):
    response_json = None
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(300)
        sock.connect(TARGET_SERVER_ADDRESS)
        
        if not command_str.endswith("\r\n\r\n"):
            command_str += "\r\n\r\n"
        
        sock.sendall(command_str.encode())

        data_received_buffer = bytearray() 
        while True:
            data_chunk = sock.recv(65536) 
            if not data_chunk:
                break 
            data_received_buffer.extend(data_chunk)
            if b"\r\n\r\n" in data_received_buffer:
                break
        
        decoded_buffer_str = data_received_buffer.decode()
        if decoded_buffer_str.strip():
            actual_response_data = decoded_buffer_str.split("\r\n\r\n")[0]
            response_json = json.loads(actual_response_data)
        else:
            response_json = {'status': 'ERROR', 'data': 'No response from server'}

    except socket.timeout:
        logging.error(f"Worker ({os.getpid()}-{multiprocessing.current_process().name}-{threading.get_ident()}): Socket timeout with {TARGET_SERVER_ADDRESS}")
        response_json = {'status': 'ERROR', 'data': 'Socket timeout'}
    except ConnectionRefusedError:
        logging.error(f"Worker ({os.getpid()}): Connection refused by {TARGET_SERVER_ADDRESS}")
        response_json = {'status': 'ERROR', 'data': 'Connection refused'}
    except json.JSONDecodeError as jde:
        logging.error(f"Worker ({os.getpid()}): Failed to decode JSON response. Error: {jde}. Response buffer: '{data_received_buffer[:500]}...'")
        response_json = {'status': 'ERROR', 'data': 'Invalid JSON response'}
    except Exception as e:
        logging.error(f"Worker ({os.getpid()}): Generic error in send_request_to_server: {type(e).__name__} - {e}")
        response_json = {'status': 'ERROR', 'data': f'Client-side send/recv error: {str(e)}'}
    finally:
        if sock:
            sock.close()
    return response_json

def perform_operation_task(worker_id, operation_type, local_file_path_for_upload, server_filename_for_op, file_size_bytes_expected):
    start_time = time_module.time()
    error_message = None
    actual_processed_bytes = 0

    try:
        if operation_type == "UPLOAD":
            if not os.path.exists(local_file_path_for_upload):
                raise FileNotFoundError(f"Local file for upload not found: {local_file_path_for_upload}")
            
            with open(local_file_path_for_upload, 'rb') as fp:
                file_content_bytes = fp.read()
            
            actual_processed_bytes = len(file_content_bytes)
            if actual_processed_bytes != file_size_bytes_expected:
                 logging.warning(f"Worker {worker_id}: UPLOAD file size mismatch. Expected {file_size_bytes_expected}, got {actual_processed_bytes}")
            
            encoded_content_str = base64.b64encode(file_content_bytes).decode()
            command_str = f"UPLOAD {server_filename_for_op} {encoded_content_str}"
            logging.debug(f"Worker {worker_id}: UPLOAD command for {server_filename_for_op} (data len: {len(encoded_content_str)})")


        elif operation_type == "DOWNLOAD":
            command_str = f"GET {server_filename_for_op}"
            actual_processed_bytes = file_size_bytes_expected
        
        elif operation_type == "LIST":
            command_str = f"LIST"
        else:
            raise ValueError(f"Unknown operation: {operation_type}")

        response = send_request_to_server(command_str)

        if not response:
             raise Exception("No response from server")
        
        if response.get('status') != 'OK':
            error_detail = response.get('data', 'Unknown server error')
            raise Exception(f"Server returned ERROR for {operation_type} {server_filename_for_op}: {error_detail}")

        if operation_type == "DOWNLOAD" and response.get('status') == 'OK':
            downloaded_content_b64 = response.get('data_file', '')
            if not downloaded_content_b64:
                raise Exception("Downloaded file data is empty in response.")
            downloaded_bytes = base64.b64decode(downloaded_content_b64)
            actual_processed_bytes = len(downloaded_bytes)
            logging.debug(f"Worker {worker_id}: Successfully downloaded {actual_processed_bytes} bytes for {server_filename_for_op}.")


        elif operation_type == "LIST" and response.get('status') == 'OK':
            actual_processed_bytes = len(json.dumps(response).encode())

        success = True
    
    except FileNotFoundError as fnf_ex:
        success = False
        error_message = str(fnf_ex)
    except Exception as e:
        success = False
        error_message = f"{type(e).__name__}: {str(e)}"


    end_time = time_module.time()
    time_taken_sec = end_time - start_time
    
    throughput_Bps = 0
    if success and time_taken_sec > 0 and actual_processed_bytes > 0:
        throughput_Bps = actual_processed_bytes / time_taken_sec
    
    return worker_id, success, time_taken_sec, throughput_Bps, actual_processed_bytes, error_message

def run_stress_test(test_num, server_ip, server_port, operation, file_volume_mb, num_client_workers, client_pool_type, server_pool_size_info):
    global TARGET_SERVER_ADDRESS
    TARGET_SERVER_ADDRESS = (server_ip, int(server_port))

    file_size_bytes_expected = 0
    local_file_for_upload = ""
    server_file_for_op = "" 

    volume_name_str = f"{file_volume_mb}MB"
    if operation in ["UPLOAD", "DOWNLOAD"]:
        file_size_bytes_expected = int(file_volume_mb * 1024 * 1024)
        local_file_for_upload = os.path.join("test_files_client", f"file_{volume_name_str}.dat")
        server_file_for_op = f"server_file_{volume_name_str}.dat" 
    elif operation == "LIST":
        file_size_bytes_expected = 0
    else:
        logging.error(f"Invalid operation for stress test: {operation}")
        print(f"{test_num},{operation},{file_volume_mb},{num_client_workers},{server_pool_size_info},0,0,0,{num_client_workers},N/A,N/A,Invalid_Operation")
        return

    if operation == "UPLOAD":
        if not os.path.exists(local_file_for_upload):
            logging.error(f"Required UPLOAD file {local_file_for_upload} does not exist. Run create_dummy_files.py.")
            print(f"{test_num},{operation},{file_volume_mb},{num_client_workers},{server_pool_size_info},0,0,0,{num_client_workers},N/A,N/A,Missing_Upload_File")
            return

    tasks_args = []
    for i in range(num_client_workers):
        worker_id = i + 1
        current_server_target_filename = server_file_for_op
        if operation == "UPLOAD":
            current_server_target_filename = f"stress_upload_vol{file_volume_mb}MB_w{worker_id}.dat"
        
        tasks_args.append((worker_id, operation, local_file_for_upload, current_server_target_filename, file_size_bytes_expected))

    all_worker_results = []
    test_start_wall_time = time_module.time()

    if client_pool_type == "thread":
        executor_class = ThreadPoolExecutor
    elif client_pool_type == "process":
        executor_class = ProcessPoolExecutor
    else:
        logging.error(f"Invalid client pool type: {client_pool_type}")
        print(f"{test_num},{operation},{file_volume_mb},{num_client_workers},{server_pool_size_info},0,0,0,{num_client_workers},N/A,N/A,Invalid_Client_Pool_Type")
        return

    with executor_class(max_workers=num_client_workers if num_client_workers > 0 else None) as executor:
        future_to_args = {executor.submit(perform_operation_task, *args): args for args in tasks_args}
        
        for future in as_completed(future_to_args):
            try:
                result = future.result()
                all_worker_results.append(result)
            except Exception as exc:
                logging.error(f"Task generated an exception: {exc} for args {future_to_args[future]}")
                worker_id_from_args = future_to_args[future][0]
                all_worker_results.append((worker_id_from_args, False, 0,0,0, str(exc)))


    test_end_wall_time = time_module.time()
    total_wall_time_for_test = test_end_wall_time - test_start_wall_time
    
    successful_client_ops = sum(1 for r in all_worker_results if r[1]) 
    failed_client_ops = num_client_workers - successful_client_ops
    
    avg_time_per_client_op = 0
    avg_throughput_per_client_op_Bps = 0

    if successful_client_ops > 0:
        total_time_successful = sum(r[2] for r in all_worker_results if r[1])
        total_throughput_successful = sum(r[3] for r in all_worker_results if r[1])
        
        avg_time_per_client_op = total_time_successful / successful_client_ops
        avg_throughput_per_client_op_Bps = total_throughput_successful / successful_client_ops
      
    print(f"{test_num},{operation},{file_volume_mb}MB,{num_client_workers} {client_pool_type},{server_pool_size_info},{avg_time_per_client_op:.4f},{avg_throughput_per_client_op_Bps:.2f},{successful_client_ops},{failed_client_ops},{total_wall_time_for_test:.4f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="File Server Stress Test Client")
    parser.add_argument("test_num", type=int, help="Test number for identification in results")
    parser.add_argument("server_ip", help="Server IP address")
    parser.add_argument("server_port", type=int, help="Server port number")
    parser.add_argument("operation", choices=["UPLOAD", "DOWNLOAD", "LIST"], help="Operation to perform")
    parser.add_argument("file_volume_mb", type=float, help="File volume in MB (for UPLOAD/DOWNLOAD). Use 0 for LIST.")
    parser.add_argument("num_client_workers", type=int, help="Number of concurrent client workers (0 for sequential in main thread if executor handles it, or 1 for single worker)")
    parser.add_argument("client_pool_type", choices=["thread", "process"], help="Client worker pool type")
    parser.add_argument("server_pool_size_info", type=str, help="Informational string about server pool size (e.g., '5_threads')")

    args = parser.parse_args()

    if args.num_client_workers < 0:
        print("Number of client workers cannot be negative.")
        sys.exit(1)
    if args.operation != "LIST" and args.file_volume_mb <= 0:
        print("File volume must be positive for UPLOAD/DOWNLOAD.")
        sys.exit(1)
        
    if args.client_pool_type == "process":
        multiprocessing.freeze_support()

    run_stress_test(
        args.test_num,
        args.server_ip,
        args.server_port,
        args.operation,
        args.file_volume_mb,
        args.num_client_workers,
        args.client_pool_type,
        args.server_pool_size_info
    )
