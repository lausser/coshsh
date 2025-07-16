import os
import re
from Cryptodome.Cipher import Blowfish
from Cryptodome.Hash import SHA256
import struct
import coshsh
from coshsh.vault import Vault, VaultNotAvailable, VaultCorrupt
from coshsh.util import compare_attr

def __vault_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "naemon_vault"):
        return NaemonVault

class NaemonVault(Vault):

    def __init__(self, **params):
        super().__init__(**params)
        self.file = params.get('file')
        self.password = params.get('key')
        self.data = {}

    def derive_key(self, password, salt):
        pw = password
        for _ in range(1000):
            hasher = SHA256.new()
            hasher.update(pw.encode('utf-8') + salt)
            pw = hasher.hexdigest()
        hasher = SHA256.new()
        hasher.update(pw.encode('utf-8') + salt)
        return hasher.digest()

    def decrypt_vim_blowfish2(self, file_path, password):
        if not os.path.isfile(file_path):
            raise VaultNotAvailable(f"file does not exist or is not a regular file: {file_path}")
    
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
        except IOError as e:
            raise VaultNotAvailable(f"could not open file {file_path}: {str(e)}") from e
        if not data.startswith(b'VimCrypt~03!'):
            raise VaultCorrupt("not a Vim blowfish2 encrypted file")
        salt = data[12:20]
        iv = data[20:28]
        ciphertext = data[28:]
        key = self.derive_key(password, salt)
        bf = Blowfish.new(key, Blowfish.MODE_ECB)
        def cipher_block(data):
            swapped_input = struct.pack("<2L", *struct.unpack(">2L", data))
            encrypted = bf.encrypt(swapped_input)
            swapped_output = struct.pack("<2L", *struct.unpack(">2L", encrypted))
            return swapped_output
        plaintext = bytearray()
        block0 = iv
        i = 0
        while i < len(ciphertext):
            block1 = ciphertext[i:i+8]
            keystream = cipher_block(block0)
            chunk = bytes(a ^ b for a, b in zip(keystream, block1))
            plaintext.extend(chunk)
            block0 = block1
            i += 8
        try:
            return plaintext.decode('utf-8')
        except UnicodeDecodeError:
            raise VaultNotAvailable("failed to decode decrypted content. likely incorrect password or corrupted file.")

    def read(self, **kwargs):
        if not self.password:
            raise ValueError("no password provided for vault decryption")
        if not self.file:
            raise ValueError("no file path provided for vault")

        contents = self.decrypt_vim_blowfish2(self.file, self.password)

        # Parse into dict
        for line in contents.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                self._data[key] = value
                if "$" in key:
                    key = re.sub(r'^\$(.*)\$$', r'\1', key)
                    self._data[key] = value
                if ":" in key:
                    self._data[key.split(":", 1)[1]] = value

        return self._data

