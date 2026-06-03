import subprocess
from pathlib import Path
import shutil
import tempfile
import os

def generate_key(keydir: Path, keyname: str):
    ids: list[str] = []
    if shutil.which("ssh-keygen") is None:
        raise Exception("ssh-keygen not found")

    keydir.mkdir(parents=True, mode=777, exist_ok=True)
    subprocess.run(f"ssh-keygen -f {keydir/keyname} -N \"\" -q -t ed25519 -C \"\"")
    res = subprocess.run(f"ssh-keygen -f {keydir/keyname} -e", stdout=subprocess.PIPE).stdout
    return res.decode()

def get_or_generate_cert(keydir: Path, force_regen: bool =False):
    if force_regen or not os.path.exists(keydir/"localhost.crt") or not os.path.exists(keydir/"localhost.key"):
        os.makedirs(keydir, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w+b", delete_on_close=False) as tf:
            tf.write(b"[dn]\nCN=localhost\n[req]\ndistinguished_name = dn\n[EXT]\nsubjectAltName=DNS:localhost\nkeyUsage=digitalSignature\nextendedKeyUsage=serverAuth")
            print(tf.name)
            tf.close()
            
            r = subprocess.run(f"openssl req -x509 -out {keydir/"localhost.crt"} -keyout {keydir/"localhost.key"} \
                                    -newkey rsa:2048 -nodes -sha256 \
                                    -subj \"/CN=localhost\" -extensions EXT -config {tf.name}").returncode
            if r != 0:
                raise Exception("subprocess failed")
            os.remove(tf.name)
    return get_cert(keydir / "localhost.crt")

def get_cert(cert_path: Path):
    with open(cert_path, "r") as f:
        return f.read()