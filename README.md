<!-- # Copyright (c) 2023 Nikita Beloglazov -->
<!-- License: Mozilla Public License 2.0 -->

# ✨ YTCON
[![License: Mozilla Public License 2.0](https://img.shields.io/badge/License:_MPL_2.0-blueviolet?logo=googledocs&logoColor=white&style=for-the-badge)](https://mozilla.org/en-US/MPL/2.0)
[![linting: pylint](https://img.shields.io/badge/Linting:_pylint-success?logo=azurefunctions&logoColor=white&style=for-the-badge)](https://pylint.pycqa.org/en/latest/)
[![based on yt-dlp](https://img.shields.io/badge/Based_on:_yt--dlp-ff0000?logoColor=white&style=for-the-badge&logo=youtube)](https://github.com/yt-dlp/yt-dlp)
[![maintainer: NikitaBeloglazov](https://img.shields.io/badge/Maintainer:_.%E2%80%A2%C2%B0%E2%97%8F%E2%9D%A4%EF%B8%8F%20NikitaBeloglazov%20Software%20Foundation%20%E2%9D%A4%EF%B8%8F%E2%97%8F%C2%B0%E2%80%A2.-informational?logoColor=white&style=for-the-badge&logo=github)](https://github.com/NikitaBeloglazov)
#### TUI for the yt-dlp utility, with support for many settings, some fixes, and multithreading
#### 🚧 Currently in the BETA stage of development
#### ⚠️ Please note, project is not dead, i'm still working in dev branches. Stable releases will come out when they are stable. Sometimes I write about progress here > https://t.me/nb_code

# 📘 Features:
* yt-dlp features
* Self-update feature
* Multiple downloads at the same time
* Clipboard auto-paste
* "Special mode"
* Shows the resolution of downloading videos, even in generic extractor
* Beautiful, colorful and comfortable human UI

#### TODO:
* Desktop notifications support
* RPM packaging

and more.. 

# 🚀 Install
### YTCON is avalible on PyPI 🎆 - https://pypi.org/project/ytcon/

## ▶️ Install it like a pip package in pipx (Recommended)
* `pipx install ytcon`
* `pipx ensurepath`

If pipx is not installed, install it with a system package manager - `python3-pipx`

### Manual install
* `git clone https://github.com/NikitaBeloglazov/ytcon && cd ytcon`
* `pip3 install -r requirements.txt`
* `cd src/ytcon && python3 yt.py`

# 💿 Support

__•‎ 🟩 Linux - FULL SUPPORT__

__•‎ 🟩 Android - FULL SUPPORT in Termux with some tweaks__

__•‎ 🟩 MacOS - Works__ on macOS HighSierra 10.13

__•‎ 🟩 BSD Systems - Works__ on __FreeBSD / GhostBSD__ and OpenBSD / FuguIta

__•‎ 🟥 Windows - Don't works, because Urwid don't support it.__
Related Issues: [-1-](https://github.com/urwid/urwid/issues/240) and [-2-](https://github.com/NikitaBeloglazov/ytcon/issues/new). Maybe it will be fixed soon. Use WSL or Cygwin unstead.

# 🖼️ Screenshots
### Main screen
![Main screen image](https://github.com/NikitaBeloglazov/ytcon/raw/main/screenshots/main_screenshot.jpg)
### Settings screen
![Settings screen image](https://github.com/NikitaBeloglazov/ytcon/raw/main/screenshots/settings_screenshot.jpg)

# ⚙️ Settings save file
The save file is located at `~/.config/ytcon`

# 💬 Testing / Debug / Troubleshooting
* See `/tmp/debug.log` and `/tmp/info.log`. They are cleared every new launch of the utility.
* Try this same link with regular yt-dlp (`yt-dlp [link]`)
  
# Contribution / Issues
* 🥼 __Pull requests are welcome!__
* 🌈 Feel free to write Issues! The developer can answer you in the following languages: Ukrainian, English, Russian.
* Don't forget to attach version (`pip3 show ytcon`) and error text :)
* ⏩ To speed up the process write to [maintainer](https://github.com/NikitaBeloglazov)

<!-- # Changelog          -->
<!-- * 0.0.0 ALPHA:       -->
<!--   * WORKING: WORKING -->
<!--   * WORKING: WORKING -->
