import os
import paramiko
import tempfile
from scp import SCPClient

def ssh_execute(server, command):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=server["ip"],
            port=int(server["port"]),
            username=server["username"],
            password=server["password"],
            timeout=5
        )
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        client.close()
        return output, error
    except Exception as e:
        return "", str(e)

def get_sftp(server):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=server["ip"],
        port=int(server["port"]),
        username=server["username"],
        password=server["password"],
        timeout=5
    )
    return client, client.open_sftp()

def scp_backup(server, remote_path, local_backup_dir="backups"):
    os.makedirs(local_backup_dir, exist_ok=True)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=server["ip"],
        port=int(server["port"]),
        username=server["username"],
        password=server["password"]
    )
    with SCPClient(ssh.get_transport()) as scp:
        scp.get(remote_path, local_backup_dir, recursive=True)
    ssh.close()
