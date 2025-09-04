"""Network utilities shared across modules."""

import os
import urllib.request
import urllib.parse
import socket
import ipaddress
from constants import USER_AGENT, MAX_DOWNLOAD_BYTES

def is_safe_url(url):
    """Check if URL is safe to download from."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        # Block localhost/loopback style hosts
        if hostname.lower() in ('localhost',):
            return False
        # Resolve host to IPs and ensure all are globally routable
        try:
            addrinfos = socket.getaddrinfo(hostname, None)
        except Exception:
            return False
        if not addrinfos:
            return False
        for ai in addrinfos:
            ip_str = ai[4][0]
            try:
                ip_obj = ipaddress.ip_address(ip_str)
            except ValueError:
                return False
            if not ip_obj.is_global:
                return False
        return True
    except Exception:
        return False

def download_file(url, target_path, expect_text=True, timeout=30, max_size=MAX_DOWNLOAD_BYTES):
    """Safely download a URL to a target path."""
    if not is_safe_url(url):
        raise RuntimeError(f"Unsafe URL blocked: {url}")
    os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)
    temp_path = target_path + ".tmp"
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass
    request = urllib.request.Request(url)
    request.add_header('User-Agent', USER_AGENT)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final_url = response.geturl()
        if not is_safe_url(final_url):
            raise RuntimeError(f"Unsafe redirect target blocked: {final_url}")
        content_length = response.headers.get('Content-Length')
        if content_length and int(content_length) > max_size:
            raise RuntimeError(f"File too large (>{max_size} bytes)")
        if expect_text:
            content_type = response.headers.get('Content-Type', '')
            ct_main = content_type.split(';', 1)[0].strip().lower() if content_type else ''
            if ct_main and not (ct_main.startswith('text/') or ct_main == 'application/octet-stream'):
                raise RuntimeError(f"Unexpected content type: {content_type}")
        downloaded = 0
        with open(temp_path, 'wb') as f:
            try:
                os.chmod(temp_path, 0o600)
            except Exception:
                pass
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                downloaded += len(chunk)
                if downloaded > max_size:
                    raise RuntimeError(f"File too large (>{max_size} bytes)")
                f.write(chunk)
    if os.path.getsize(temp_path) == 0:
        try:
            os.remove(temp_path)
        except Exception:
            pass
        raise RuntimeError("Downloaded file is empty")
    if os.path.islink(target_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass
        raise RuntimeError("Refusing to overwrite symlink at target path")
    os.replace(temp_path, target_path)
    return target_path
