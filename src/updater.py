"""
Auto-update module for the DailyReporter app.
Checks GitHub Releases for newer versions, downloads updates, and applies them.
"""

import os
import sys
import json
import subprocess
import urllib.request
import urllib.error
import threading

GITHUB_REPO = "gitano-at-work/AutomatorDailyProgress"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def get_current_version():
    """Read the current version from version.txt."""
    version_paths = [
        os.path.join(os.path.dirname(__file__), 'version.txt'),
        os.path.join(os.path.dirname(sys.executable), 'src', 'version.txt'),
        os.path.join(os.path.dirname(sys.executable), 'version.txt'),
    ]
    
    for path in version_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return f.read().strip()
            except Exception:
                continue
    
    return "0.0.0"


def _parse_version(version_str):
    """Parse a version string like '2026.02.10' or 'v2026.02.10' into a comparable tuple."""
    v = version_str.strip().lstrip('v')
    try:
        return tuple(int(x) for x in v.split('.'))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def check_for_update(current_version):
    """
    Check GitHub Releases for a newer version.
    
    Returns:
        tuple: (new_version, download_url) if update available
        None: if up-to-date or check failed
    """
    try:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={
                'User-Agent': 'DailyReporter-AutoUpdater',
                'Accept': 'application/vnd.github.v3+json'
            }
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        tag_name = data.get('tag_name', '')
        new_version = tag_name.lstrip('v')
        
        # Compare versions
        current_tuple = _parse_version(current_version)
        new_tuple = _parse_version(new_version)
        
        if new_tuple > current_tuple:
            # Find the first .exe asset in the release
            assets = data.get('assets', [])
            download_url = None
            
            for asset in assets:
                if asset.get('name', '').lower().endswith('.exe'):
                    download_url = asset.get('browser_download_url')
                    break
            
            if download_url:
                return (new_version, download_url)
        
        return None
        
    except (urllib.error.URLError, urllib.error.HTTPError, 
            json.JSONDecodeError, OSError, Exception):
        # Silently fail — never block the user
        return None


def download_update(download_url, progress_callback=None):
    """
    Download the update exe to a temp file next to the current exe.
    
    Args:
        download_url: URL of the exe to download
        progress_callback: function(percent: int) called with progress updates
    
    Returns:
        str: path to the downloaded file, or None on failure
    """
    try:
        # Determine where the current exe is
        if getattr(sys, 'frozen', False):
            current_dir = os.path.dirname(sys.executable)
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
        
        dest_path = os.path.join(current_dir, '_update.exe')
        
        req = urllib.request.Request(
            download_url,
            headers={'User-Agent': 'DailyReporter-AutoUpdater'}
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            chunk_size = 64 * 1024  # 64KB chunks
            
            with open(dest_path, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        percent = int(downloaded / total_size * 100)
                        progress_callback(percent)
        
        if progress_callback:
            progress_callback(100)
        
        return dest_path
        
    except Exception:
        # Clean up partial download
        try:
            if os.path.exists(dest_path):
                os.remove(dest_path)
        except Exception:
            pass
        return None


def apply_update(new_exe_path, root_window):
    """
    Launch the updater batch script to swap the exe and restart.
    
    Args:
        new_exe_path: path to the downloaded update exe
        root_window: the tkinter root window (to close the app)
    """
    if getattr(sys, 'frozen', False):
        current_exe = sys.executable
    else:
        # In dev mode, don't actually replace anything
        return False
    
    # Find updater.bat — it should be next to the exe
    exe_dir = os.path.dirname(current_exe)
    updater_bat = os.path.join(exe_dir, 'updater.bat')
    
    if not os.path.exists(updater_bat):
        return False
    
    try:
        # Launch the batch script in a new console, detached from this process
        subprocess.Popen(
            ['cmd', '/c', updater_bat, current_exe, new_exe_path],
            creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.DETACHED_PROCESS,
            close_fds=True
        )
        
        # Close the app so the batch script can replace the exe
        root_window.after(500, root_window.destroy)
        return True
        
    except Exception:
        return False
