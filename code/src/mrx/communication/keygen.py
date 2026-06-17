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

def get_or_generate_cert(keydir: Path, force_regen: bool =False, dnsname="localhost"):
    print(f"generating or loading certificate for hostname: {dnsname}, stored in {keydir}")
    if force_regen or not os.path.exists(keydir/f"{dnsname}.crt") or not os.path.exists(keydir/f"{dnsname}.key"):
        os.makedirs(keydir, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w+b", delete_on_close=False) as tf:
            tf.write(f"[dn]\nCN={dnsname}\n[req]\ndistinguished_name = dn\n[EXT]\nsubjectAltName=DNS:{dnsname}\nkeyUsage=digitalSignature\nextendedKeyUsage=serverAuth".encode())
            print(tf.name)
            tf.close()

            cmd = f"openssl req -x509 -out {keydir/f"{dnsname}.crt"} -keyout {keydir/f"{dnsname}.key"} " + \
                                    "-newkey rsa:2048 -nodes -sha256 " +\
                                    f'-subj \"/CN={dnsname}\" -extensions EXT -config {tf.name}'
            r = subprocess.run(cmd, cwd=".", shell=True).returncode
            if r != 0:
                raise Exception(f"subprocess failed.")
            tf.close()
            os.remove(tf.name)
    return get_cert(keydir / f"{dnsname}.crt")


def get_cert(cert_path: Path):
    with open(cert_path, "r") as f:
        return f.read()