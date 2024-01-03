# Shusha

![Repo size](https://img.shields.io/github/repo-size/FourtyThree43/shusha)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![Repo language count](https://img.shields.io/github/languages/count/FourtyThree43/shusha?style=round-square)
![Repo top language](https://img.shields.io/github/languages/top/FourtyThree43/shusha?style=round-square)
![Commit activity](https://img.shields.io/github/commit-activity/m/FourtyThree43/shusha?style=round-square)
![Latest commit](https://img.shields.io/github/last-commit/FourtyThree43/shusha?style=round-square)

Shusha is a download manager that wraps around [aria2](https://aria2.github.io/), a lightweight multi-protocol and multi-source command-line download utility. Shusha-DM uses RPC (Remote Procedure Call) to communicate with aria2 and control the download tasks. Shusha-DM also provides a graphical user interface (GUI) based on Tkinter, a Python module for creating cross-platform GUI applications.

## Features

- Supports HTTP/HTTPS, FTP, SFTP, BitTorrent and Metalink protocols
- Allows multiple connections and segmented downloading
- Supports resume, pause, cancel and queue operations
- Displays download progress, speed, size and ETA
- Supports setting global and per-task options
- Supports adding, removing and saving sessions
- Provides a simple and user-friendly GUI with Tkinter widgets

## Installation

To install Shusha-DM, you need to have Python 3 and aria2 installed on your system. You can download Python 3 from [here](https://github.com/aria2/aria2) and aria2 from [here](https://linuxconfig.org/aria2-all-in-one-command-line-download-tool).

To run Shusha-DM, you need to start aria2 in daemon mode with RPC enabled. You can do this by running the following command:

```bash
aria2c --enable-rpc --rpc-listen-all=true --rpc-allow-origin-all
```

Then, you can run Shusha-DM by running the main.py file:

```bash
python main.py
```

## Usage

Shusha-DM has a simple and intuitive GUI that consists of three main parts:

- The menu bar, which provides access to various commands and options
- The task list, which shows the current download tasks and their status
- The task details, which shows the detailed information and options for the selected task

To add a new download task, you can use the File -> New Task menu or press Ctrl+N. A dialog window will pop up, where you can enter the URL, file name, save path and other options for the task. You can also drag and drop a URL or a torrent file to the task list to add a new task.

To start, pause, resume or cancel a task, you can use the buttons on the toolbar or the right-click menu on the task list. You can also use the keyboard shortcuts: F5 to start, F6 to pause, F7 to resume and F8 to cancel.

To change the global or per-task options, you can use the Options menu or the right-click menu on the task list. A dialog window will pop up, where you can modify the options such as max connections, download speed limit, proxy settings and so on.

To save or load a session, you can use the File -> Save Session or File -> Load Session menu. A session is a file that contains the information of the current download tasks. You can use it to resume the tasks later or transfer them to another machine.

To exit Shusha-DM, you can use the File -> Exit menu or press Alt+F4. You will be asked if you want to save the current session before exiting.

## Project Structure

* The Project Structure as per the Model-View-Controller (MVC) pattern of software architectural pattern:  

```
shusha
├── src
│   └── shusha
│       ├── __about__.py
│       ├── __init__.py
│       ├── frontend
│       │   ├── __init__.py
│       │   ├── model
│       │   │   ├── __init__.py
│       │   │   └── gui_model.py
│       │   ├── view
│       │   │   ├── __init__.py
│       │   │   └── main_view.py
│       │   └── controller
│       │       ├── __init__.py
│       │       └── gui_controller.py
│       ├── backend
│       │   ├── __init__.py
│       │   ├── model
│       │   │   ├── __init__.py
│       │   │   └── aria2c_connector.py
│       │   ├── middleware
│       │   │   ├── __init__.py
│       │   │   └── download_manager_middleware.py
│       │   └── controller
│       │       ├── __init__.py
│       │       └── download_manager_controller.py
│       ├── resources
│       │   ├── __init__.py
│       │   ├── aria2c
│       │   │   └── (aria2c-related resources)
│       │   └── assets
│       │       └── (icons, images, canvas, etc.)
│       └── main.py
├── tests
│   └── __init__.py
├── docs
│   └── index.html
├── LICENSE.txt
├── README.md
└── pyproject.toml

```

## License

`shusha` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.


# About Shusha

Shusha is more than just a download manager. It is also a tribute to the rich and diverse culture of East Africa, where the project originated. The name Shusha comes from the Swahili word "shusha", which means "download". Swahili is a language spoken by millions of people in eastern Africa, especially along the coast. It is influenced by Arabic, Indian, and European languages, making it truly multicultural.

The developers of Shusha-DM are based in Kenya, a country in East Africa famed for its scenic landscapes and vast wildlife preserves. Kenya is home to Mount Kenya, the second tallest peak in Africa, and Lake Victoria, the second largest freshwater lake in the world. Kenya is also known for its diverse ethnic groups, vibrant music, and delicious cuisine.

Shusha-DM aims to celebrate the beauty and diversity of East Africa by providing a fast, reliable, and user-friendly download manager that can handle any file from any source. Whether you want to download a song, a movie, a document, or a game, Shusha-DM can help you do it with ease and efficiency.

We hope you enjoy using Shusha-DM as much as we enjoyed creating it. If you have any feedback, suggestions, or questions, please feel free to contact us. We would love to hear from you!

Asante sana (Thank you very much)!

The Shusha-DM Team
