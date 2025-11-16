#!/usr/bin/env python3
# python 3.13

import sys
import os
import subprocess
import typing
import json
import shutil
import logging
import argparse
from pathlib import Path

class ColoredFormatter(logging.Formatter):
    GREY = "\x1b[38;20m"
    CYAN = "\x1b[36;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"
    
    FORMATS = {
        logging.DEBUG: GREY + "%(message)s" + RESET,
        logging.INFO: CYAN + "[*] %(message)s" + RESET,
        logging.WARNING: YELLOW + "[!] %(message)s" + RESET,
        logging.ERROR: RED + "[ERROR] %(message)s" + RESET,
        logging.CRITICAL: BOLD_RED + "[CRITICAL] %(message)s" + RESET,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(ColoredFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])

SCRIPT_DIR = Path(__file__).resolve().parent
THEMES_DIR = SCRIPT_DIR / "themes"
PACKAGES_JSON = THEMES_DIR / "packages.json"
KALITHEME_PACKAGES_TXT = SCRIPT_DIR / "kalitheme-packages.txt"
SUPPORTED_WALLPAPERS = ["kalitheme"]
KALITHEME_WALLPAPERS_DIR = THEMES_DIR / "kalitheme" / "wallpapers"

def PrivilegiesVerify() -> bool:
    return os.geteuid() == 0

def _run_subprocess(command: list[str], check: bool = True) -> subprocess.CompletedProcess:
    logging.info(f"Running command: {' '.join(command)}")
    try:
        return subprocess.run(command, check=check, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to run command: {' '.join(command)}")
        logging.error(f"Error output:\n{e.stderr}")
        raise e
    except FileNotFoundError:
        logging.error(f"Command '{command[0]}' not found. Check if it is installed and in the PATH.")
        sys.exit(1)

def build_command(base_command: list[str]) -> list[str]:
    if not PrivilegiesVerify():
        return ["sudo"] + base_command
    return base_command

def read_utilities_list(utilities_list_path: Path) -> list[str]:
    logging.info(f"Reading utilities list from '{utilities_list_path}'")
    try:
        with open(utilities_list_path, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        logging.error(f"Utilities file '{utilities_list_path}' not found.")
        sys.exit(1)

def needed_packages_check(packages_list: list) -> list:
    return [pkg for pkg in packages_list if subprocess.run(["pacman", "-Q", pkg], capture_output=True).returncode != 0]

def installed_packages_check(packages_list: list) -> list:
    return [pkg for pkg in packages_list if subprocess.run(["pacman", "-Q", pkg], capture_output=True).returncode == 0]

def InstallUtilities(utilities_list_path: Path):
    utilities = read_utilities_list(utilities_list_path)
    if not utilities:
        logging.warning("The utilities list is empty. No action will be taken.")
        return

    packages_to_install = needed_packages_check(utilities)
    
    if not packages_to_install:
        logging.info("All utilities are already installed. No action needed.")
        return

    logging.info(f"Installing utilities... (Packages to install: {', '.join(packages_to_install)})")
    command = build_command(["pacman", "-S", "--noconfirm"] + packages_to_install)
    
    try:
        _run_subprocess(command)
        logging.info(f"Utilities {', '.join(packages_to_install)} were successfully installed.")
    except subprocess.CalledProcessError:
        logging.error("Failed to install the utilities.")
        sys.exit(1)

def UninstallUtilities(utilities_list_path: Path):
    utilities = read_utilities_list(utilities_list_path)
    if not utilities:
        logging.warning("The utilities list is empty. No action will be taken.")
        return

    packages_to_uninstall = installed_packages_check(utilities)
    
    if not packages_to_uninstall:
        logging.info("No utilities are installed. No action needed.")
        return

    logging.info(f"Uninstalling utilities... (Packages to uninstall: {', '.join(packages_to_uninstall)})")
    command = build_command(["pacman", "-Rns", "--noconfirm"] + packages_to_uninstall)

    try:
        _run_subprocess(command)
        logging.info(f"Utilities {', '.join(packages_to_uninstall)} were successfully uninstalled.")
    except subprocess.CalledProcessError:
        logging.error("Failed to uninstall the utilities.")
        sys.exit(1)

def expand_path(path: Path) -> Path:
    return Path(os.path.expanduser(os.path.expandvars(str(path)))).resolve()

def is_system_path(path: Path) -> bool:
    system_paths = ['/etc', '/usr', '/root', '/var', '/boot']
    return any(part in path.absolute().parts for part in system_paths)

def safe_copy(src: Path, dst: Path):
    try:
        src = expand_path(src)
        dst = expand_path(dst)
        
        dst.parent.mkdir(parents=True, exist_ok=True)

        if is_system_path(dst) or not os.access(dst.parent, os.W_OK):
            logging.info(f"Using sudo to copy {src} -> {dst}")
            cmd = build_command(["cp", "-r", "--preserve=mode,timestamps", str(src), str(dst)])
            _run_subprocess(cmd)
        else:
            logging.info(f"Copying {src} -> {dst}")
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
        return True
    except Exception as e:
        logging.error(f"Failed to copy: {src} -> {dst} ({e})")
        return False

def file_backup(path: Path):
    expanded_path = expand_path(path)
    backup_path = expanded_path.with_suffix(expanded_path.suffix + ".old")

    if expanded_path.exists():
        logging.info(f"Creating backup of {expanded_path} to {backup_path}")
        safe_copy(expanded_path, backup_path)

def config_apply(src: typing.Union[str, list], dst: typing.Union[str, list]):
    if isinstance(src, list) and isinstance(dst, list):
        if len(src) != len(dst):
            logging.error("Error: source and destination lists have different lengths.")
            return
        for s, d in zip(src, dst):
            safe_copy(THEMES_DIR / s, Path(d))
    else:
        safe_copy(THEMES_DIR / str(src), Path(str(dst)))

def restore_from_backup(path: Path):
    expanded_path = expand_path(path)
    backup_path = expanded_path.with_suffix(expanded_path.suffix + ".old")

    if backup_path.exists():
        logging.info(f"Restoring {backup_path} to {expanded_path}")
        try:
            safe_copy(backup_path, expanded_path)
            logging.info(f"Backup from {backup_path} restored successfully.")
        except Exception as e:
            logging.error(f"Restore failed: {e}")
    else:
        logging.warning(f"No backup found for: {expanded_path}")

def load_json_packages(json_path: Path) -> dict:
    try:
        with open(json_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as error:
        logging.critical(f"Failed to load {json_path}: {error}")
        sys.exit(1)

def InstallKalitheme():
    logging.info("Installing Kalitheme...")
    json_data = load_json_packages(PACKAGES_JSON)
    system_packages = json_data.get("System packages", {}).get("kalitheme", {})
    packages_configs = json_data.get("Packages config", {}).get("kalitheme", {})

    packages_to_install = needed_packages_check(list(system_packages.keys()))

    if packages_to_install:
        logging.info(f"Packages to be installed: {', '.join(packages_to_install)}")
        KALITHEME_PACKAGES_TXT.write_text("\n".join(packages_to_install), encoding="utf-8")
        InstallUtilities(KALITHEME_PACKAGES_TXT)
    else:
        logging.info("All required packages are already installed.")

    logging.info("[STARTING BACKUP PROCESS]")
    for pkg_cfg in system_packages.values():
        paths = [pkg_cfg] if isinstance(pkg_cfg, str) else pkg_cfg
        for path in paths:
            if path.strip():
                file_backup(Path(path.strip()))

    logging.info("[APPLYING SETTINGS]")
    for pkg, src_config in packages_configs.items():
        dst_config = system_packages.get(pkg)
        if dst_config:
            logging.info(f"Applying settings for {pkg}: {src_config} -> {dst_config}")
            config_apply(src_config, dst_config)
    
    logging.info("KaliTheme installed successfully! 🎉")

def UninstallKalitheme():
    logging.info("Uninstalling Kalitheme...")
    json_data = load_json_packages(PACKAGES_JSON)
    system_packages = json_data.get("System packages", {}).get("kalitheme", {})

    logging.info("[STARTING RESTORE PROCESS]")
    for pkg_cfg in system_packages.values():
        paths = [pkg_cfg] if isinstance(pkg_cfg, str) else pkg_cfg
        for path in paths:
            if path.strip():
                restore_from_backup(Path(path.strip()))

    CRITICAL_KEYWORDS = ("bash", "i3", "python")
    packages_to_check = [pkg for pkg in system_packages if not any(keyword in pkg for keyword in CRITICAL_KEYWORDS)]
    packages_to_uninstall = installed_packages_check(packages_to_check)
    
    if packages_to_uninstall:
        logging.info(f"Packages to be uninstalled: {', '.join(packages_to_uninstall)}")
        KALITHEME_PACKAGES_TXT.write_text("\n".join(packages_to_uninstall), encoding="utf-8")
        UninstallUtilities(KALITHEME_PACKAGES_TXT)
    else:
        logging.info("No packages to uninstall.")

    logging.info("KaliTheme uninstalled successfully!")

def dynamic_background(sec: int, mode: str, wallpapers_path_str: str, wallpapers_type: str):
    if "feh" in needed_packages_check(["feh"]):
        logging.warning("feh not found. Installing...")
        try:
            _run_subprocess(build_command(["pacman", "-S", "--noconfirm", "feh"]))
        except subprocess.CalledProcessError:
            logging.error("Could not install feh. Aborting.")
            sys.exit(1)
    
    wallpapers_path = expand_path(Path(wallpapers_path_str)) / wallpapers_type / "wallpapers"
    
    if wallpapers_type not in SUPPORTED_WALLPAPERS:
        logging.error(f"Wallpaper type not supported. Supported: {SUPPORTED_WALLPAPERS}")
        sys.exit(1)

    logging.info(f"Copying wallpapers from '{KALITHEME_WALLPAPERS_DIR}' to '{wallpapers_path}'")
    shutil.rmtree(wallpapers_path, ignore_errors=True)
    shutil.copytree(KALITHEME_WALLPAPERS_DIR, wallpapers_path)

    subprocess.run(["pkill", "-f", ".dynamic_background.sh"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    script_path = expand_path(Path("~/.dynamic_background.sh"))
    script_content = f"""#!/bin/bash
# Auto-generated by AutoKALI
while true; do
  mapfile -t W < <(find "{wallpapers_path}" -maxdepth 1 -type f)
  if [ ${{#W[@]}} -eq 0 ]; then
    sleep {sec}
    continue
  fi
"""
    if mode == "randomize":
        script_content += f'  feh --no-fehbg --bg-scale --randomize "${{W[@]}}"\n'
    elif mode == "ordered":
        script_content += f'  for img in "${{W[@]}}"; do\n    feh --no-fehbg --bg-scale "$img"\n    sleep {sec}\n  done\n'
    else:
        logging.error("Invalid mode! Use 'randomize' or 'ordered'.")
        sys.exit(1)
        
    script_content += f"  sleep {sec}\ndone &\n"
    
    script_path.write_text(script_content, encoding="utf-8")
    script_path.chmod(0o755)
    logging.info(f"Dynamic wallpaper script created at {script_path}")
    
    i3_config_path = expand_path(Path("~/.config/i3/config"))
    if i3_config_path.exists():
        answer = input(f"[*] Do you want to add '{script_path}' to i3 startup? (y/n): ").strip().lower()
        if answer == 'y':
            exec_line = f"exec --no-startup-id {script_path} # by AutoKALI\n"
            content = i3_config_path.read_text(encoding="utf-8")
            if exec_line not in content:
                with open(i3_config_path, "a", encoding="utf-8") as f:
                    f.write("\n" + exec_line)
                logging.info(f"Execution line added to {i3_config_path}")
    
    try:
        subprocess.Popen([str(script_path)])
        logging.info(f"Dynamic wallpaper started from {script_path}.")
    except Exception as e:
        logging.error(f"Error executing {script_path}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="AutoKALI: A tool to automate the installation and configuration of themes and utilities.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    p_install = subparsers.add_parser("install-utilities", help="Install utilities from a list.")
    p_install.add_argument("utilities_list", type=Path, help="Path to the .txt file with the list of utilities.")
    p_install.set_defaults(func=lambda args: InstallUtilities(args.utilities_list))

    p_uninstall = subparsers.add_parser("uninstall-utilities", help="Uninstall utilities from a list.")
    p_uninstall.add_argument("utilities_list", type=Path, help="Path to the .txt file with the list of utilities.")
    p_uninstall.set_defaults(func=lambda args: UninstallUtilities(args.utilities_list))

    p_install_theme = subparsers.add_parser("install-kalitheme", help="Apply the Kali theme.")
    p_install_theme.set_defaults(func=lambda args: InstallKalitheme())
    
    p_uninstall_theme = subparsers.add_parser("uninstall-kalitheme", help="Remove the Kali theme and restore backups.")
    p_uninstall_theme.set_defaults(func=lambda args: UninstallKalitheme())

    p_dynamic_bg = subparsers.add_parser("dynamic-background", help="Set up a dynamic wallpaper.")
    p_dynamic_bg.add_argument("sec", type=int, help="Seconds between wallpaper changes.")
    p_dynamic_bg.add_argument("mode", choices=["randomize", "ordered"], help="Switching mode (random or ordered).")
    p_dynamic_bg.add_argument("wallpapers_path", type=str, help="Directory to save the wallpapers.")
    p_dynamic_bg.add_argument("wallpapers_type", choices=SUPPORTED_WALLPAPERS, help="Type of wallpaper pack.")
    p_dynamic_bg.set_defaults(func=lambda args: dynamic_background(args.sec, args.mode, args.wallpapers_path, args.wallpapers_type))

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    setup_logging()
    try:
        main()
    except Exception as e:
        logging.critical(f"An unhandled error occurred: {e}", exc_info=True)
        sys.exit(1)
