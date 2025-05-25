import os

def create_file_if_not_exists(filepath, size_mb):
    size_bytes = int(size_mb * 1024 * 1024)
    if not os.path.exists(filepath) or os.path.getsize(filepath) != size_bytes:
        print(f"Creating {filepath} of {size_mb}MB...")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(os.urandom(size_bytes))
        print(f"Created {filepath}.")
    else:
        print(f"{filepath} already exists with correct size.")

if __name__ == "__main__":
    test_files_dir = "test_files_client"
    create_file_if_not_exists(os.path.join(test_files_dir, "file_10MB.dat"), 10)
    create_file_if_not_exists(os.path.join(test_files_dir, "file_50MB.dat"), 50)
    create_file_if_not_exists(os.path.join(test_files_dir, "file_100MB.dat"), 100)

    server_files_dir = "files"
    create_file_if_not_exists(os.path.join(server_files_dir, "server_file_10MB.dat"), 10)
    create_file_if_not_exists(os.path.join(server_files_dir, "server_file_50MB.dat"), 50)
    create_file_if_not_exists(os.path.join(server_files_dir, "server_file_100MB.dat"), 100)
    
    if not os.path.exists(os.path.join(server_files_dir, "sample.txt")):
        with open(os.path.join(server_files_dir, "sample.txt"), "w") as f:
            f.write("This is a sample file for LIST and basic GET testing.")
        print(f"Created {os.path.join(server_files_dir, 'sample.txt')}.")
    else:
        print(f"{os.path.join(server_files_dir, 'sample.txt')} already exists.")
        
    print("\nDummy file creation/check complete.")
    print(f"Client upload files are in: ./{test_files_dir}")
    print(f"Server download files should be in: ./files (relative to where server is run)")
