<h1 align="center">
  <a href="https://github.com/iAmNikola/WackyPyWebM">
    <img src="docs/images/banner.png" alt="Banner" width="100%">
  </a>
</h1>

<div align="center">
  <a href="https://github.com/iAmNikola/WackyPyWebM/issues/new?assignees=&labels=bug&template=01_BUG_REPORT.md&title=bug%3A+">Report a Bug</a>
  ·
  <a href="https://github.com/iAmNikola/WackyPyWebM/issues/new?assignees=&labels=enhancement&template=02_FEATURE_REQUEST.md&title=feat%3A+">Request a Feature</a>
  .
  <a href="https://github.com/iAmNikola/WackyPyWebM/issues/new?assignees=&labels=question&template=04_SUPPORT_QUESTION.md&title=support%3A+">Ask a Question</a>
</div>

<div align="center">
  <br />

[![Project license](https://img.shields.io/github/license/iAmNikola/WackyPyWebM.svg?style=flat-square)](LICENSE)
[![Pull Requests welcome](https://img.shields.io/badge/PRs-welcome-ff69b4.svg?style=flat-square)](https://github.com/iAmNikola/WackyPyWebM/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22)
[![code with love by iAmNikola](https://img.shields.io/badge/%3C%2F%3E%20with%20%E2%99%A5%20by-iAmNikola-ff1414.svg?style=flat-square)](https://github.com/iAmNikola)

</div>

<details open="open">
<summary>Table of Contents</summary>

- [About](#about)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
  - [Terminal UI](#terminal-ui)
  - [Console commands](#console-commands)
- [Modes](#modes)
- [Support](#support)
- [Project assistance](#project-assistance)
- [Contributing](#contributing)
- [Authors \& contributors](#authors--contributors)
- [License](#license)
- [Acknowledgements](#acknowledgements)

</details>

---

## About

WackyPyWebM is a tool that allows you to create **WebM** videos with changing aspect ratios.

This is a **Python** implementation of [OIRNOIR's WackyWebM](https://github.com/OIRNOIR/WackyWebM) in hopes of making the tool more accessible.

## Getting Started

### Prerequisites

- [FFmpeg](https://ffmpeg.org/download.html)
- [Python](https://www.python.org/downloads/)

### Installation

If you don't want to use console commands skip this part and go to [Usage](#usage).

Install required python packages by running this command:
```bash
pip install -r requirements_no_term.txt
``` 
You can also install `requirements.txt` instead if you plan on running Terminal UI in the future

> Note: Using a virtual environment is highly recommended.

## Usage

You can use this tool in two different ways.

1. [Terminal UI](#terminal-ui)
2. [Console commands](#console-commands)

### Terminal UI

You can run Terminal UI by running one of the `run` scripts. If you are on Windows double-click `run.bat`. Otherwise, type `bash run.sh` or `sh run.sh` in the terminal.

### Console commands

If you want full control, console commands are the way to go about using WackyPyWebM.

- Create a webm with the `bounce` effect applied to it.
  ```bash
  python wackypywebm.py path/to/video.mp4
  ```

- Create a webm with the `shrink` effect applied to it.
  ```bash
  python wackypywebm.py path/to/video.mp4 shrink
  ```

- Create a webm with the `shutter` and `audiobounce` effects applied to it.
  ```bash
  python wackypywebm.py path/to/video.mp4 shutter+audiobounce
  ```

- Create a webm with the `rotate` effect applied to it, rotating 50 degrees per second.
  ```bash
  python wackypywebm.py path/to/video.mp4 rotate --angle 50
  ```

- Create a webm with the `bounce` effect applied to it, bouncing with a speed of 3, outputting the video to a custom path and using 8 threads in the process.
  ```bash
  python wackypywebm.py path/to/video.mp4 --tempo 3 --output path/to/output/video.webm --threads 8
  ```

- Create a webm with the `keyframes` effect applied to it, using the keyframes from the provided file.
  ```bash
  python wackypywebm.py path/to/video.mp4 keyframes --keyframes path/to/keyframes.txt
  ```

> Note: Run python wackypywebm.py --help for a full list of options.

## Modes

- `bounce` (Default): The video's height periodically increases and decreases.
- `shutter`: The video's width periodically increases and decreases.
- `sporadic`: The video glitches and wobbles randomly.
- `shrink`: The video shrinks vertically from full height to just one pixel over its entire duration.
- `audiobounce`: The video's height changes relative to the current audio level compared to the highest within the video.
- `audioshutter`: The video's width changes relative to the current audio level compared to the highest within the video.
- `keyframes`: The video's height and width change based on a number of keyframes outlined in the file given as an argument. The format for said file is Described [Here](docs/keyframes.md).

## Support

Reach out by opening a support question at [GitHub issues](https://github.com/iAmNikola/WackyPyWebM/issues/new?assignees=&labels=question&template=04_SUPPORT_QUESTION.md&title=support%3A+)

## Project assistance

If you want to say **thank you** or/and support active development of WackyPyWebM **star** [the project](https://github.com/iAmNikola/WackyPyWebM).

## Contributing

First off, thanks for taking the time to contribute! Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make will benefit everybody else and are **greatly appreciated**.


Please read [our contribution guidelines](docs/CONTRIBUTING.md), and thank you for being involved!

## Authors & contributors

The original setup of this repository is by [Nikola Damjanović](https://github.com/iAmNikola).

For a full list of all authors and contributors, see [the contributors page](https://github.com/iAmNikola/WackyPyWebM/contributors).

## License

This project is licensed under the **GPL-3.0 license**.

See [LICENSE](LICENSE) for more information.

## Acknowledgements

[OIRNOIR's WackyWebM](https://github.com/OIRNOIR/WackyWebM) - The original tool on which this one is based on, with personal touches and improvements.
