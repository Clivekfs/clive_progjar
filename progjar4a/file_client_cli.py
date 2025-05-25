import os
import socket
import json
import base64
import logging

server_address=('0.0.0.0',50000)

def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    logging.warning(f"connecting to {server_address}")
    try:

        if not command_str.endswith("\r\n\r\n"):
            command_str += "\r\n\r\n"

        sock.sendall(command_str.encode())

        data_received = ""
        while True:
            data = sock.recv(4096)  # Jangan kecil! Bisa terpotong base64-nya
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break

        hasil = json.loads(data_received.strip())
        return hasil

    except Exception as e:
        logging.warning(f"error during data receiving: {e}")
        return False

def remote_list():
    command_str=f"LIST\r\n\r\n"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        print("daftar file : ")
        for nmfile in hasil['data']:
            print(f"- {nmfile}")
        return True
    else:
        print("Gagal")
        return False

def remote_get(filename=""):
    command_str=f"GET {filename}\r\n\r\n"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        #proses file dalam bentuk base64 ke bentuk bytes
        namafile= hasil['data_namafile']
        isifile = base64.b64decode(hasil['data_file'])
        fp = open(namafile,'wb+')
        fp.write(isifile)
        fp.close()
        return True
    else:
        print("Gagal")
        return False

def remote_upload(local_filepath=""):
    print(f"Client: Attempting UPLOAD for '{local_filepath}'")
    if not local_filepath:
        print("Client: Path file lokal kosong.")
        return False
    if not os.path.exists(local_filepath):
        print(f"Client: File lokal '{local_filepath}' tidak ditemukan.")
        return False
    try:
        server_filename = os.path.basename(local_filepath)
        with open(local_filepath, 'rb') as fp:
            file_content_bytes = fp.read()
        encoded_content_str = base64.b64encode(file_content_bytes).decode()
        command_str = f"UPLOAD {server_filename} {encoded_content_str}\r\n\r\n"
        hasil = send_command(command_str)
        if hasil and hasil.get('status') == 'OK':
            print(f"Client: Upload '{server_filename}' berhasil: {hasil.get('data')}")
            return True
        else:
            error_msg = hasil.get('data', 'Unknown error') if hasil else "No response"
            print(f"Client: Gagal upload '{server_filename}': {error_msg}")
            return False
    except Exception as e:
        print(f"Client: Error UPLOAD '{local_filepath}': {str(e)}")
        return False


def remote_delete(filename=""):
    if not filename:
        print("Client: Nama file untuk DELETE tidak boleh kosong.")
        return False
    command_str = f"DELETE {filename}\r\n\r\n"
    hasil = send_command(command_str)
    if hasil and hasil.get('status') == 'OK':
        print(f"Client: Hapus file '{filename}' berhasil: {hasil.get('data')}")
        return True
    else:
        error_msg = hasil.get('data', 'Unknown error') if hasil else "No response or critical error"
        print(f"Client: Gagal menghapus file '{filename}': {error_msg}")
        return False


if __name__ == '__main__':
    server_address = ('172.16.16.101', 50000)
    while True:
        try:
            user_input = input("Enter command > ").strip()
            if not user_input:
                continue

            parts = user_input.split()
            command = parts[0].upper()

            if command == "LIST":
                remote_list()
            elif command == "GET":
                if len(parts) > 1:
                    remote_get(parts[1])
                else:
                    print("Usage: GET <server_filename>")
            elif command == "UPLOAD":
                if len(parts) > 1:
                    local_file_to_upload = parts[1]
                    remote_upload(local_file_to_upload)
                else:
                    print("Usage: UPLOAD <local_filepath>")
            elif command == "DELETE":
                if len(parts) > 1:
                    remote_delete(parts[1])
                else:
                    print("Usage: DELETE <server_filename>")
            else:
                print(f"Unknown command: {command}.")
        except Exception as e:
            print(f"An error occurred: {e}")
