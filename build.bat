@ECHO OFF
@REM Make a Windows executable file from the python project.
@REM Create a venv, install the requirements, then create exe.
@REM The exe will be in the dist folder.
@REM
@REM Usage: build.bat
@REM
@REM Author: PE1OBW

if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller==6.10.0

pyinstaller --onefile baseband_config\main.py --add-data "libusb0.dll;." -n baseband_config_cli
pyinstaller --onefile baseband_gui\main.py --add-data "libusb0.dll;." -n baseband_config
