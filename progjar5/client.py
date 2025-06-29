import socket
import os

SERVER_ADDRESS = ('127.0.0.1', 8889)

def list_files():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(SERVER_ADDRESS)
    
    request = b"GET / HTTP/1.1\r\n\r\n"
    sock.send(request)
  
    response = sock.recv(4096)

    print("--- LIST FILES RESPONSE ---")
    print(response.decode(errors='ignore'))
    sock.close()

def upload_file(filename):
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found.")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(SERVER_ADDRESS)

    with open(filename, 'rb') as f:
        file_content = f.read()

    boundary = "boundary123"
    
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(filename)}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + file_content + f"\r\n--{boundary}--\r\n".encode()

    headers = (
        f"POST /upload HTTP/1.1\r\n"
        f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
        f"Content-Length: {len(body)}\r\n\r\n"
    )

    request = headers.encode() + body
    sock.sendall(request)

    response = sock.recv(4096).decode(errors='ignore')
    print(f"--- UPLOAD '{filename}' RESPONSE ---")
    print(response)
    sock.close()

def delete_file(filename):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(SERVER_ADDRESS)
    
    request = f"DELETE /{filename} HTTP/1.1\r\n\r\n".encode()
    sock.send(request)
    
    response = sock.recv(4096).decode(errors='ignore')
    print(f"--- DELETE '{filename}' RESPONSE ---")
    print(response)
    sock.close()

if __name__ == "__main__":
    print("1. Listing files on server...")
    list_files()
    
    dummy_filename = "upload_test.txt"
    with open(dummy_filename, "w") as f:
        f.write("This is a test file.")
    
    print("\n2. Uploading 'upload_test.txt'...")
    upload_file(dummy_filename)
    
    print("\n3. Listing files again to see the uploaded file...")
    list_files()
    
    print(f"\n4. Deleting '{dummy_filename}'...")
    delete_file(dummy_filename)
    
    print("\n5. Listing files a final time to confirm deletion...")
    list_files()
