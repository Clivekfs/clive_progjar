import os

def create_file_if_not_exists(filepath, size_mb_float):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    size_bytes = int(size_mb_float * 1024 * 1024)
    if not os.path.exists(filepath) or os.path.getsize(filepath) != size_bytes:
        print(f"Creating {filepath} of {size_mb_float}MB...")
        with open(filepath, 'wb') as f:
            f.write(os.urandom(size_bytes))
        print(f"Created {filepath}.")
    else:
        print(f"{filepath} already exists with correct size.")

if __name__ == "__main__":

    VOLUMES_TO_CREATE = [10.0, 50.0, 100.0]

    client_upload_dir = "test_files_client"
    for vol in VOLUMES_TO_CREATE:
        create_file_if_not_exists(os.path.join(client_upload_dir, f"file_{vol}MB.dat"), vol)

    server_files_dir = "files"
    for vol in VOLUMES_TO_CREATE:
        create_file_if_not_exists(os.path.join(server_files_dir, f"server_file_{vol}MB.dat"), vol)

    sample_server_file = os.path.join(server_files_dir, "sample.txt")
    if not os.path.exists(sample_server_file):
        os.makedirs(os.path.dirname(sample_server_file), exist_ok=True)
        with open(sample_server_file, "w") as f:
            f.write("This is a sample file for LIST and basic GET testing.")
        print(f"Created {sample_server_file}.")
    else:
        print(f"{sample_server_file} already exists.")

    print("\nDummy file creation/check complete.")
    print(f"Client upload files should be in: ./{client_upload_dir} (relative to script execution)")
    print(f"Server download files should be in: ./{server_files_dir} (relative to where server is run)")
