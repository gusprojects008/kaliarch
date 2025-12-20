# KaliArch

## Table of Contents
* [About](#-about)
* [How it works](#how-it-works)
* [Usage Modes](#usage-modes)
* [Recommendations](#recommendations)
* [Future Features](#future-features)
* [References](#references)

---

## 💡 About
> This simple script allows you to automatically install utilities via a *.txt* list, automatically apply customizable themes, dynamically add wallpapers based on user preferences, and automatically restore default settings if desired.

---

## How it works
- The script must be run in the repository directory.
- Allows you to install packages listed in a `.txt` file via the specified package manager.
- You can remove all packages and files installed by the script at any time. - The user can apply themes similar to Kali, for example, which can be customized.
- It is also possible to configure a dynamic wallpaper, which changes automatically according to the configured time and the chosen mode.
- Before any modification, the configuration files or directories are copied with the .old extension to ensure security.

⚠️ Important:
- It is always recommended to run as a normal user only; the script itself will prompt for the sudo password if necessary. Restart the machine after installing a specific theme.
- After applying the theme, it is recommended to review and, if necessary, customize the added configuration files.
- .old files allow you to restore the original configuration at any time.

---

## Usage Instructions

```bash
# Install the packages listed in a file
python3 kaliarch.py ​​install-utilities utilities.txt

# Uninstall the packages listed in a file
python3 kaliarch.py ​​uninstall-utilities utilities.txt

# Apply the Kali-like theme
python3 kaliarch.py ​​install-kalitheme

# Apply the Kali-like theme with dynamic wallpaper
python3 kaliarch.py ​​dynamic-background 5 randomize ~ kalitheme

# You can also use the default order instead of random
python3 kaliarch.py ​​dynamic-background 5 ordered ~ kalitheme

# Remove the Kali-like theme and restore backups
python3 kaliarch.py ​​uninstall-kalitheme
```
---

## Recommendations
- Run in virtual machines during or after installation. - Customize the themes' packages.json or script if needed, but be careful to follow the script and packages.json defaults.
- Customize `~/.config/i3/config` to your liking after applying the theme.
- Configure the terminal color, theme, or transparency if needed.
- Adjust Kitty fonts if needed.
- Set Zsh as the default shell.
