"""Naemon Vault Plugin - Vim Blowfish2 Encrypted Vault

This plugin provides secure password/secret storage using Vim's blowfish2
encryption format.

Plugin Identification:
---------------------
Identifies vault configurations with type = "naemon_vault".

Purpose:
--------
Provides encrypted storage for sensitive monitoring configuration data:
    - Passwords (SNMP community strings, NSClient++ passwords, etc.)
    - API keys
    - Authentication tokens
    - Any sensitive monitoring credentials

The vault file is encrypted using Vim's blowfish2 encryption, allowing
secrets to be edited securely using: vim -x vault_file

Encryption Details:
------------------
- Algorithm: Blowfish in CFB (Cipher Feedback) mode
- Key Derivation: SHA256 with 1000 iterations (password + salt)
- File Format: VimCrypt~03! header + salt + IV + ciphertext
- Endianness: Little-endian (Vim-compatible)

Why Vim Encryption?
-------------------
- Easy editing: vim -x vault_file
- Widely available (Vim is ubiquitous)
- Reasonably secure for monitoring secrets
- No additional tools required

Security Considerations:
------------------------
1. Password Strength: Use strong passwords for vault encryption
2. File Permissions: Restrict vault file access (chmod 600)
3. Key Management: Store vault password securely (environment variable)
4. Rotation: Regularly rotate vault passwords
5. Backups: Keep encrypted backups of vault file

Vault File Format:
-----------------
Plain text format (when decrypted):
    # Comments start with #
    key=value
    $KEY$=value
    prefix:KEY=value

Multiple key formats are supported:
    MYSQL_PASSWORD=secret123
    $MYSQL_PASSWORD$=secret123  # Also accessible as MYSQL_PASSWORD
    host:SNMP_COMMUNITY=public  # Also accessible as SNMP_COMMUNITY

Configuration Example:
---------------------
Cookbook configuration:
    [vault_naemon_prod]
    type = naemon_vault
    file = /etc/coshsh/vault_prod.enc
    key = ${VAULT_PASSWORD}

Environment:
    export VAULT_PASSWORD="your-strong-password"

Usage in Datasources:
--------------------
In monitoring configuration, reference secrets using @VAULT[key]:
    # In CSV file or datasource:
    host_name,name,type,SNMPCOMMUNITY
    switch01,os,network,@VAULT[SNMP_COMMUNITY]

    dbserver,mysql,database,@VAULT[MYSQL_PASSWORD]

Coshsh will automatically substitute the vault value.

Creating a Vault File:
---------------------
1. Create plain text file:
    $ cat > vault_prod.txt <<EOF
    # Production vault
    SNMP_COMMUNITY=public
    MYSQL_ROOT_PASSWORD=MySuperSecret123
    WINDOWS_NSC_PASSWORD=WinSecret456
    EOF

2. Encrypt with Vim:
    $ vim -x vault_prod.txt
    # Enter encryption password when prompted
    # Save and quit: :wq

3. Rename to .enc:
    $ mv vault_prod.txt vault_prod.enc

4. Configure in cookbook:
    [vault_prod]
    type = naemon_vault
    file = /path/to/vault_prod.enc
    key = ${VAULT_PASSWORD}

Technical Details:
-----------------
The decrypt_vim_blowfish2 function implements Vim's VimCrypt~03!
encryption format:

1. File Structure:
    - Header: "VimCrypt~03!" (12 bytes)
    - Salt: 8 bytes (for key derivation)
    - IV: 8 bytes (initialization vector)
    - Ciphertext: Remaining bytes

2. Key Derivation:
    - Start with password
    - Iterate 1000 times: pw = SHA256(pw + salt)
    - Final key: SHA256(pw + salt).digest()

3. Decryption:
    - Blowfish in CFB mode (implemented manually)
    - Little-endian byte swapping for Vim compatibility
    - XOR keystream with ciphertext

Classes:
--------
- NaemonVault: Vault implementation using Vim blowfish2 encryption

Dependencies:
-------------
- pycryptodomex: Cryptographic operations (Blowfish, SHA256)
"""

from __future__ import annotations

import os
import re
import struct
from typing import Optional, Dict, Any

from Cryptodome.Cipher import Blowfish
from Cryptodome.Hash import SHA256

import coshsh
from coshsh.vault import Vault, VaultNotAvailable, VaultCorrupt
from coshsh.util import compare_attr


def __vault_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify Naemon vault configurations.

    Called by the plugin factory system to determine if a vault
    configuration should use the NaemonVault class.

    Args:
        params: Vault configuration dictionary

    Returns:
        NaemonVault class if type="naemon_vault"
        None if no match

    Example:
        params = {'type': 'naemon_vault', 'file': '/path/vault.enc'}
        Returns: NaemonVault class

        params = {'type': 'other_vault'}
        Returns: None
    """
    if params is None:
        params = {}

    if coshsh.util.compare_attr("type", params, "naemon_vault"):
        return NaemonVault
    return None


class NaemonVault(Vault):
    """Vault using Vim blowfish2 encryption.

    Provides secure storage for monitoring secrets using Vim's VimCrypt~03!
    encryption format. Secrets can be edited using: vim -x vault_file

    Attributes:
        file: Path to encrypted vault file
        password: Decryption password
        _data: Dictionary of decrypted key-value pairs

    Configuration:
        [vault_prod]
        type = naemon_vault
        file = /etc/coshsh/vault_prod.enc
        key = ${VAULT_PASSWORD}

    Example:
        vault = NaemonVault(
            file='/path/to/vault.enc',
            key='password123'
        )
        secrets = vault.read()
        mysql_pass = secrets['MYSQL_PASSWORD']
    """

    def __init__(self, **params: Any) -> None:
        """Initialize Naemon vault.

        Args:
            **params: Vault configuration parameters
                file: Path to encrypted vault file
                key: Decryption password
        """
        super().__init__(**params)
        self.file: Optional[str] = params.get('file')
        self.password: Optional[str] = params.get('key')
        self._data: Dict[str, str] = {}

    def derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password and salt.

        Uses Vim's key derivation algorithm:
        - Iterate 1000 times: pw = SHA256(pw + salt)
        - Return final SHA256(pw + salt).digest()

        This provides reasonable protection against brute-force attacks
        while remaining compatible with Vim encryption.

        Args:
            password: User password
            salt: Random 8-byte salt from encrypted file

        Returns:
            32-byte encryption key

        Note:
            1000 iterations is relatively weak by modern standards
            (PBKDF2 typically uses 100,000+), but matches Vim's
            implementation for compatibility.
        """
        pw = password
        for _ in range(1000):
            pw = SHA256.new(pw.encode('utf-8') + salt).hexdigest()
        return SHA256.new(pw.encode('utf-8') + salt).digest()

    def decrypt_vim_blowfish2(self, file_path: str, password: str) -> str:
        """Decrypt a Vim blowfish2 encrypted file.

        Implements the VimCrypt~03! decryption algorithm, which uses
        Blowfish in CFB mode with Vim-specific endianness handling.

        Args:
            file_path: Path to encrypted file
            password: Decryption password

        Returns:
            Decrypted file contents as string

        Raises:
            VaultNotAvailable: If file doesn't exist or can't be read
            VaultCorrupt: If file is not a valid VimCrypt~03! file
                         or password is incorrect

        File Structure:
            Bytes 0-11: Header "VimCrypt~03!"
            Bytes 12-19: Salt (8 bytes)
            Bytes 20-27: IV (8 bytes)
            Bytes 28+: Ciphertext

        Algorithm:
            1. Derive key from password + salt (1000 SHA256 iterations)
            2. Initialize Blowfish cipher with derived key
            3. Decrypt using CFB mode (manually implemented)
            4. Handle Vim's little-endian byte swapping
            5. XOR keystream with ciphertext blocks
        """
        # Validate file exists
        if not os.path.isfile(file_path):
            raise VaultNotAvailable(
                f"file does not exist or is not a regular file: {file_path}"
            )

        # Read encrypted file
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
        except IOError as e:
            raise VaultNotAvailable(
                f"could not open file {file_path}: {str(e)}"
            ) from e

        # Validate VimCrypt~03! header
        if not data.startswith(b'VimCrypt~03!'):
            raise VaultCorrupt("not a Vim blowfish2 encrypted file")

        # Extract components
        salt = data[12:20]  # 8 bytes
        iv = data[20:28]    # 8 bytes
        ciphertext = data[28:]

        # Derive encryption key
        key = self.derive_key(password, salt)

        # Initialize Blowfish cipher (ECB mode for manual CFB)
        bf = Blowfish.new(key, Blowfish.MODE_ECB)

        def cipher_block(data: bytes) -> bytes:
            """Encrypt a single block with Vim-compatible endianness.

            Vim uses little-endian Blowfish, but Python's Blowfish
            uses big-endian. This function handles the conversion.

            Args:
                data: 8-byte block to encrypt

            Returns:
                8-byte encrypted block
            """
            # Swap from big-endian to little-endian
            swapped_input = struct.pack("<2L", *struct.unpack(">2L", data))

            # Encrypt block
            encrypted = bf.encrypt(swapped_input)

            # Swap back from little-endian to big-endian
            return struct.pack("<2L", *struct.unpack(">2L", encrypted))

        # Decrypt using CFB mode
        plaintext_parts = []
        block0 = iv  # Initial block is IV

        for i in range(0, len(ciphertext), 8):
            block1 = ciphertext[i:i+8]

            # Generate keystream from previous block
            keystream = cipher_block(block0)

            # XOR keystream with ciphertext to get plaintext
            chunk = bytes(a ^ b for a, b in zip(keystream, block1))
            plaintext_parts.append(chunk)

            # Current ciphertext block becomes next feedback
            block0 = block1

        plaintext = b''.join(plaintext_parts)

        # Decode to UTF-8
        try:
            return plaintext.decode('utf-8')
        except UnicodeDecodeError:
            raise VaultNotAvailable(
                "failed to decode decrypted content. "
                "likely incorrect password or corrupted file."
            )

    def read(self, **kwargs: Any) -> Dict[str, str]:
        """Read and decrypt vault file.

        Decrypts the vault file and parses key=value pairs into a dictionary.
        Supports multiple key formats for flexible access.

        Returns:
            Dictionary of key-value pairs

        Raises:
            ValueError: If password or file path not provided
            VaultNotAvailable: If file can't be read or password is wrong
            VaultCorrupt: If file format is invalid

        Key Formats Supported:
            1. Simple: KEY=value → accessible as KEY
            2. Dollar: $KEY$=value → accessible as KEY
            3. Prefixed: prefix:KEY=value → accessible as KEY

        Example Vault File:
            # Database passwords
            MYSQL_PASSWORD=secret123
            $POSTGRES_PASSWORD$=secret456

            # SNMP communities
            core:SNMP_COMMUNITY=public
            edge:SNMP_COMMUNITY=private

        Access in config:
            @VAULT[MYSQL_PASSWORD] → "secret123"
            @VAULT[POSTGRES_PASSWORD] → "secret456"
            @VAULT[SNMP_COMMUNITY] → "private" (edge value wins)
        """
        # Validate required parameters
        if not self.password:
            raise ValueError("no password provided for vault decryption")
        if not self.file:
            raise ValueError("no file path provided for vault")

        # Decrypt file
        contents = self.decrypt_vim_blowfish2(self.file, self.password)

        # Parse key=value pairs
        for line in contents.splitlines():
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Parse key=value
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Store with original key
                self._data[key] = value

                # Handle $KEY$ format → also store as KEY
                if "$" in key:
                    normalized_key = re.sub(r'^\$(.*)\$$', r'\1', key)
                    self._data[normalized_key] = value

                # Handle prefix:KEY format → also store as KEY
                if ":" in key:
                    suffix_key = key.split(":", 1)[1]
                    self._data[suffix_key] = value

        return self._data
