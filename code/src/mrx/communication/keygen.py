import subprocess
from pathlib import Path
import shutil
import tempfile
import os
import textwrap

def generate_key(keydir: Path, keyname: str):
    ids: list[str] = []
    if shutil.which("ssh-keygen") is None:
        raise Exception("ssh-keygen not found")

    keydir.mkdir(parents=True, mode=777, exist_ok=True)
    subprocess.run(f"ssh-keygen -f {keydir/keyname} -N \"\" -q -t ed25519 -C \"\"")
    res = subprocess.run(f"ssh-keygen -f {keydir/keyname} -e", stdout=subprocess.PIPE).stdout
    return res.decode()

def get_or_generate_cert(keydir: Path, force_regen: bool =False, host="localhost"):
    if force_regen or not os.path.exists(keydir/f"{host}.crt") or not os.path.exists(keydir/f"{host}.key"):
        os.makedirs(keydir, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w+b", delete_on_close=False) as tf:
            if host == "localhost":
                tf.write(b"[dn]\nCN=localhost\n[req]\ndistinguished_name = dn\n[EXT]\nsubjectAltName=DNS:localhost\nkeyUsage=digitalSignature\nextendedKeyUsage=serverAuth")
            else:
                tf.write(textwrap.dedent(f"""\
                    [dn]
                    CN={host}
                    [req]
                    distinguished_name = dn
                    [EXT]
                    subjectAltName=@alt_names
                    keyUsage=digitalSignature
                    extendedKeyUsage=serverAuth
                    [alt_names]
                    DNS.1 = localhost
                    IP.1 = 127.0.0.1
                    IP.2 = {host}""").encode())
            print(tf.name)
            tf.close()

            cmd = f"openssl req -x509 -out {keydir/f"{host}.crt"} -keyout {keydir/f"{host}.key"} " + \
                                    "-newkey rsa:2048 -nodes -sha256 " +\
                                    f'-subj \"/CN={host}\" -extensions EXT -config {tf.name}'
            r = subprocess.run(cmd, cwd=".", shell=True).returncode
            if r != 0:
                raise Exception(f"subprocess failed.")
            tf.close()
            os.remove(tf.name)
    return get_cert(keydir / f"{host}.crt")

def get_cert(cert_path: Path):
    with open(cert_path, "r") as f:
        return f.read()