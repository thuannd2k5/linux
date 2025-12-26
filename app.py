from flask import Flask, render_template, request, redirect, url_for, send_file
import os
import tempfile

from services.server_service import load_servers, save_servers
from services.ssh_service import ssh_execute, get_sftp, scp_backup
from services.log_service import write_log, load_logs
from services.bookmark_service import load_bookmarks, add_bookmark, save_bookmarks

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/servers")
def servers():
    server_list = load_servers()
    return render_template("servers.html", servers=server_list)

@app.route("/add-server", methods=["POST"])
def add_server():
    servers = load_servers()

    new_server = {
        "ip": request.form["ip"],
        "port": request.form["port"],
        "username": request.form["username"],
        "password": request.form["password"]
    }

    servers.append(new_server)
    save_servers(servers)

    return redirect(url_for("servers"))



@app.route("/sftp/<int:server_id>")
def sftp_browser(server_id):
    servers = load_servers()
    server = servers[server_id]

    client, sftp = get_sftp(server)

    path = request.args.get("path", ".")
    raw_files = sftp.listdir_attr(path)

    files = []
    for f in raw_files:
        files.append({
            "name": f.filename,
            "is_dir": f.st_mode & 0o40000 != 0
        })

    sftp.close()
    client.close()

    return render_template(
        "sftp.html",
        server=server,
        files=files,
        path=path,
        server_id=server_id
    )


@app.route("/ssh-test/<int:server_id>")
def ssh_test(server_id):
    servers = load_servers()

    if server_id >= len(servers):
        return "Server not found"

    server = servers[server_id]
    output, error = ssh_execute(server, "ls")

    write_log(
        action="SSH Command",
        server_ip=server["ip"],
        detail="ls"
    )

    return render_template(
        "ssh_test.html",
        server=server,
        output=output,
        error=error
    )

@app.route("/download/<int:server_id>")
def download_file(server_id):
    servers = load_servers()
    server = servers[server_id]
    path = request.args.get("path")

    client, sftp = get_sftp(server)

    # Lấy tên file gốc
    filename = os.path.basename(path)

    # Tạo file tạm có hậu tố đúng
    temp = tempfile.NamedTemporaryFile(delete=False)
    sftp.get(path, temp.name)

    sftp.close()
    client.close()

    write_log(
        action="Download",
        server_ip=server["ip"],
        detail=path
    )

    return send_file(
        temp.name,
        as_attachment=True,
        download_name=filename   # DÒNG QUAN TRỌNG
    )



@app.route("/upload/<int:server_id>", methods=["POST"])
def upload_file(server_id):
    servers = load_servers()
    server = servers[server_id]

    remote_path = request.form.get("path", ".")
    uploaded_file = request.files.get("file")

    if uploaded_file is None:
        return "No file selected"

    client, sftp = get_sftp(server)

    # Đường dẫn file trên Ubuntu
    remote_file_path = remote_path + "/" + uploaded_file.filename

    # Lưu file tạm trên Windows
    temp_path = os.path.join("temp_" + uploaded_file.filename)
    uploaded_file.save(temp_path)

    # Upload qua SFTP
    sftp.put(temp_path, remote_file_path)

    # Dọn dẹp
    sftp.close()
    client.close()
    os.remove(temp_path)

    write_log(
        action="Upload",
        server_ip=server["ip"],
        detail=remote_file_path
    )

    return redirect(url_for("sftp_browser", server_id=server_id, path=remote_path))

@app.route("/scp-backup/<int:server_id>")
def scp_backup_route(server_id):
    servers = load_servers()
    server = servers[server_id]

    # Backup từ SFTP Documents
    remote_path = "Documents"

    scp_backup(server, remote_path)

    write_log(
        action="SCP Backup",
        server_ip=server["ip"],
        detail=remote_path
    )

    return f"Backup completed for server {server['ip']}"

@app.route("/logs")
def view_logs():
    logs = load_logs()
    logs.reverse()  # log mới lên trên
    return render_template("logs.html", logs=logs)


@app.route("/search/<int:server_id>", methods=["GET", "POST"])
def search_file(server_id):
    servers = load_servers()
    server = servers[server_id]

    results = []
    keyword = ""
    path = request.args.get("path", ".")

    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip()
        if keyword:
            command = f'find {path} -name "*{keyword}*"'
            output, error = ssh_execute(server, command)
            if output:
                results = output.splitlines()
            else:
                results = []

            # log (nếu đã làm giai đoạn 7)
            write_log("Search", server["ip"], f'{path} | "{keyword}"')

    return render_template(
        "search.html",
        server=server,
        server_id=server_id,
        path=path,
        results=results,
        keyword=keyword
    )

@app.route("/bookmark/<int:server_id>")
def bookmark(server_id):
    servers = load_servers()
    server = servers[server_id]
    path = request.args.get("path", ".")

    add_bookmark(server["ip"], path)
    write_log("Bookmark", server["ip"], path)

    return redirect(url_for("sftp_browser", server_id=server_id, path=path))

@app.route("/bookmarks")
def view_bookmarks():
    bookmarks = load_bookmarks()
    return render_template("bookmarks.html", bookmarks=bookmarks)

@app.route("/delete/<int:server_id>")
def delete_file(server_id):
    servers = load_servers()
    server = servers[server_id]

    path = request.args.get("path")
    current_path = request.args.get("current", ".")

    if not path:
        return "Invalid file path"

    client, sftp = get_sftp(server)

    try:
        # kiểm tra xem có phải file không
        file_attr = sftp.stat(path)

        # nếu là thư mục thì không cho xóa
        if file_attr.st_mode & 0o40000:
            return "Cannot delete folder"

        # xóa file
        sftp.remove(path)

        # ghi log
        write_log("Delete File", server["ip"], path)

    except Exception as e:
        sftp.close()
        client.close()
        return f"Delete failed: {e}"

    sftp.close()
    client.close()

    return redirect(url_for("sftp_browser", server_id=server_id, path=current_path))

@app.route("/bookmark-delete/<int:index>")
def delete_bookmark(index):
    bookmarks = load_bookmarks()

    if index < 0 or index >= len(bookmarks):
        return "Invalid bookmark"

    removed = bookmarks.pop(index)
    save_bookmarks(bookmarks)

    # ghi log nếu bạn đã có log
    write_log("Delete Bookmark", removed["server"], removed["path"])

    return redirect(url_for("view_bookmarks"))


if __name__ == "__main__":
    app.run(debug=True)


