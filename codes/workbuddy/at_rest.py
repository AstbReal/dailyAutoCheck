# encoding=utf8
import base64
import hashlib
import hmac
import json
import os
import platform
import subprocess

SBOX = [
    0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5, 0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76,
    0xCA, 0x82, 0xC9, 0x7D, 0xFA, 0x59, 0x47, 0xF0, 0xAD, 0xD4, 0xA2, 0xAF, 0x9C, 0xA4, 0x72, 0xC0,
    0xB7, 0xFD, 0x93, 0x26, 0x36, 0x3F, 0xF7, 0xCC, 0x34, 0xA5, 0xE5, 0xF1, 0x71, 0xD8, 0x31, 0x15,
    0x04, 0xC7, 0x23, 0xC3, 0x18, 0x96, 0x05, 0x9A, 0x07, 0x12, 0x80, 0xE2, 0xEB, 0x27, 0xB2, 0x75,
    0x09, 0x83, 0x2C, 0x1A, 0x1B, 0x6E, 0x5A, 0xA0, 0x52, 0x3B, 0xD6, 0xB3, 0x29, 0xE3, 0x2F, 0x84,
    0x53, 0xD1, 0x00, 0xED, 0x20, 0xFC, 0xB1, 0x5B, 0x6A, 0xCB, 0xBE, 0x39, 0x4A, 0x4C, 0x58, 0xCF,
    0xD0, 0xEF, 0xAA, 0xFB, 0x43, 0x4D, 0x33, 0x85, 0x45, 0xF9, 0x02, 0x7F, 0x50, 0x3C, 0x9F, 0xA8,
    0x51, 0xA3, 0x40, 0x8F, 0x92, 0x9D, 0x38, 0xF5, 0xBC, 0xB6, 0xDA, 0x21, 0x10, 0xFF, 0xF3, 0xD2,
    0xCD, 0x0C, 0x13, 0xEC, 0x5F, 0x97, 0x44, 0x17, 0xC4, 0xA7, 0x7E, 0x3D, 0x64, 0x5D, 0x19, 0x73,
    0x60, 0x81, 0x4F, 0xDC, 0x22, 0x2A, 0x90, 0x88, 0x46, 0xEE, 0xB8, 0x14, 0xDE, 0x5E, 0x0B, 0xDB,
    0xE0, 0x32, 0x3A, 0x0A, 0x49, 0x06, 0x24, 0x5C, 0xC2, 0xD3, 0xAC, 0x62, 0x91, 0x95, 0xE4, 0x79,
    0xE7, 0xC8, 0x37, 0x6D, 0x8D, 0xD5, 0x4E, 0xA9, 0x6C, 0x56, 0xF4, 0xEA, 0x65, 0x7A, 0xAE, 0x08,
    0xBA, 0x78, 0x25, 0x2E, 0x1C, 0xA6, 0xB4, 0xC6, 0xE8, 0xDD, 0x74, 0x1F, 0x4B, 0xBD, 0x8B, 0x8A,
    0x70, 0x3E, 0xB5, 0x66, 0x48, 0x03, 0xF6, 0x0E, 0x61, 0x35, 0x57, 0xB9, 0x86, 0xC1, 0x1D, 0x9E,
    0xE1, 0xF8, 0x98, 0x11, 0x69, 0xD9, 0x8E, 0x94, 0x9B, 0x1E, 0x87, 0xE9, 0xCE, 0x55, 0x28, 0xDF,
    0x8C, 0xA1, 0x89, 0x0D, 0xBF, 0xE6, 0x42, 0x68, 0x41, 0x99, 0x2D, 0x0F, 0xB0, 0x54, 0xBB, 0x16,
]
RCON = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36]
AAD_PREFIX = b"WB-AAD\0"
FRAMING_NAME = {"file": "WBEF1", "field": "WBEV1"}
FRAMING_ID = {"file": 1, "field": 2}
GCM_REDUCTION = 0xE1000000000000000000000000000000
LOGGER_GET_JS = (
    "const b=process._linkedBinding('electron_browser_workbuddy_storage');"
    "const p=b.loggerGet();process.stdout.write(typeof p==='string'?p:JSON.stringify(p));"
)


def _xtime(value):
    value <<= 1
    return (value ^ 0x1B) & 0xFF if value & 0x100 else value


def _expand_key(key):
    nk = len(key) // 4
    nr = nk + 6
    words = [list(key[4 * i:4 * i + 4]) for i in range(nk)]
    for i in range(nk, 4 * (nr + 1)):
        temp = list(words[i - 1])
        if i % nk == 0:
            temp = temp[1:] + temp[:1]
            temp = [SBOX[b] for b in temp]
            temp[0] ^= RCON[i // nk - 1]
        elif nk > 6 and i % nk == 4:
            temp = [SBOX[b] for b in temp]
        words.append([words[i - nk][j] ^ temp[j] for j in range(4)])
    return words, nr


def _encrypt_block(words, nr, block):
    state = list(block)

    def add_round_key(round_index):
        for col in range(4):
            for row in range(4):
                state[row + 4 * col] ^= words[round_index * 4 + col][row]

    add_round_key(0)
    for round_index in range(1, nr + 1):
        state = [SBOX[b] for b in state]
        shifted = [0] * 16
        for row in range(4):
            for col in range(4):
                shifted[row + 4 * col] = state[row + 4 * ((col + row) % 4)]
        state = shifted
        if round_index != nr:
            mixed = []
            for col in range(4):
                a0, a1, a2, a3 = state[4 * col:4 * col + 4]
                mixed += [
                    _xtime(a0) ^ _xtime(a1) ^ a1 ^ a2 ^ a3,
                    a0 ^ _xtime(a1) ^ _xtime(a2) ^ a2 ^ a3,
                    a0 ^ a1 ^ _xtime(a2) ^ _xtime(a3) ^ a3,
                    _xtime(a0) ^ a0 ^ a1 ^ a2 ^ _xtime(a3),
                ]
            state = mixed
        add_round_key(round_index)
    return bytes(state)


def _gf_mul(x, y):
    result = 0
    value = y
    for i in range(128):
        if (x >> (127 - i)) & 1:
            result ^= value
        value = (value >> 1) ^ GCM_REDUCTION if value & 1 else value >> 1
    return result


def _ghash(hash_key, data):
    result = 0
    for i in range(0, len(data), 16):
        chunk = data[i:i + 16].ljust(16, b"\0")
        result = _gf_mul(result ^ int.from_bytes(chunk, "big"), hash_key)
    return result


def _pad16(data):
    remainder = len(data) % 16
    return data if remainder == 0 else data + b"\0" * (16 - remainder)


def aes_gcm_open(key, nonce, aad, ciphertext, tag):
    if len(nonce) != 12:
        raise ValueError(f"nonce 必须是 12 字节，实际 {len(nonce)}")
    words, nr = _expand_key(key)
    hash_key = int.from_bytes(_encrypt_block(words, nr, bytes(16)), "big")
    initial_counter = nonce + b"\x00\x00\x00\x01"
    lengths = (len(aad) * 8).to_bytes(8, "big") + (len(ciphertext) * 8).to_bytes(8, "big")
    auth = _ghash(hash_key, _pad16(aad) + _pad16(ciphertext) + lengths)
    expected_tag = (int.from_bytes(_encrypt_block(words, nr, initial_counter), "big") ^ auth).to_bytes(16, "big")
    if not hmac.compare_digest(expected_tag, tag):
        raise ValueError("信封校验失败：tag 不匹配（密钥或 AAD 不对）")
    plaintext = bytearray()
    increment = 1
    for i in range(0, len(ciphertext), 16):
        increment = (increment + 1) & 0xFFFFFFFF
        keystream = _encrypt_block(words, nr, nonce + increment.to_bytes(4, "big"))
        plaintext += bytes(a ^ b for a, b in zip(ciphertext[i:i + 16], keystream))
    return bytes(plaintext)


def _encode_u32(value):
    return value.to_bytes(4, "big")


def _encode_length_prefixed(text):
    raw = text.encode("utf-8")
    return _encode_u32(len(raw)) + raw


def build_aad(key_id, suite, framing="field"):
    return b"".join([
        AAD_PREFIX,
        b"\x01",
        _encode_length_prefixed(FRAMING_NAME[framing]),
        _encode_length_prefixed("sym-v1"),
        _encode_u32(suite),
        _encode_length_prefixed(key_id),
        bytes([FRAMING_ID[framing]]),
        b"\x00",
        b"\x00",
    ])


def derive_key(secret_b64):
    return hashlib.sha256(secret_b64.encode("utf-8")).digest()


def derive_key_id(key):
    return hashlib.sha256(key).hexdigest()[:16]


def is_field_wrapper(value):
    return isinstance(value, dict) and value.get("$wbEncrypted") == 1 and isinstance(value.get("envelope"), str)


def decrypt_field(value, key, framing="field"):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if not is_field_wrapper(value):
        raise ValueError(f"不认识的信封结构: {type(value).__name__}")
    envelope = json.loads(base64.b64decode(value["envelope"]).decode("utf-8"))
    expected = derive_key_id(key)
    if envelope["keyId"] != expected:
        raise ValueError(f"keyId 不匹配: 信封 {envelope['keyId']} / 本地密钥 {expected}")
    plaintext = aes_gcm_open(
        key,
        base64.b64decode(envelope["nonce"]),
        build_aad(envelope["keyId"], envelope["suite"], framing),
        base64.b64decode(envelope["ciphertext"]),
        base64.b64decode(envelope["authTag"]),
    )
    return plaintext.decode("utf-8")


def _powershell_exe_path():
    if platform.system() != "Windows":
        return ""
    script = "(Get-Process WorkBuddy -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Path)"
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, timeout=25,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip()


def _scanned_exe_paths():
    if platform.system() != "Windows":
        return
    drives = set()
    for base in (os.environ.get("LOCALAPPDATA"), os.environ.get("PROGRAMFILES"), os.getcwd()):
        if base:
            drive = os.path.splitdrive(base)[0]
            if drive:
                drives.add(drive + os.sep)
    for drive in sorted(drives):
        try:
            entries = list(os.scandir(drive))
        except OSError:
            continue
        for entry in entries:
            if not entry.is_dir():
                continue
            yield os.path.join(entry.path, "WorkBuddy", "WorkBuddy.exe")


def find_app_executable():
    override = os.environ.get("WORKBUDDY_EXE", "").strip()
    if override and os.path.exists(override):
        return override
    system = platform.system()
    candidates = []
    if system == "Windows":
        local = os.environ.get("LOCALAPPDATA", "")
        candidates = [
            os.path.join(local, "Programs", "WorkBuddy", "WorkBuddy.exe"),
            os.path.join(local, "WorkBuddy", "WorkBuddy.exe"),
            os.path.join(os.environ.get("PROGRAMFILES", ""), "WorkBuddy", "WorkBuddy.exe"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "WorkBuddy", "WorkBuddy.exe"),
        ]
    elif system == "Darwin":
        candidates = [
            "/Applications/WorkBuddy.app/Contents/MacOS/WorkBuddy",
            os.path.expanduser("~/Applications/WorkBuddy.app/Contents/MacOS/WorkBuddy"),
        ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    for path in list(_scanned_exe_paths()) + [_powershell_exe_path()]:
        if path and os.path.exists(path):
            return path
    raise SystemExit(
        "找不到 WorkBuddy 桌面端可执行文件，无法取出解密密钥。\n"
        "请设置环境变量 WORKBUDDY_EXE 指向它（例如 D:\\AI\\WorkBuddy\\WorkBuddy.exe）"
    )


def load_build_payload():
    executable = find_app_executable()
    env = dict(os.environ)
    env["ELECTRON_RUN_AS_NODE"] = "1"
    result = subprocess.run(
        [executable, "-e", LOGGER_GET_JS],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=60,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise SystemExit(f"从桌面端读取密钥失败（exit={result.returncode}）：{result.stderr.strip()[:300]}")
    try:
        return json.loads(result.stdout)
    except ValueError as exc:
        raise SystemExit(f"桌面端返回的密钥载荷无法解析（可能版本变了）: {exc}")


def load_key():
    payload = load_build_payload()
    secret = payload.get("atRestSecretKey")
    if not secret:
        raise SystemExit("桌面端没有返回 atRestSecretKey，请确认 WorkBuddy 已登录")
    return derive_key(secret)
