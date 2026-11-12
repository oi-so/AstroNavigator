[app]
title = AstroNavigator
project_dir = .
input_file = src/astronavigator/__main__.py
exec_directory = dist
project_file = 
icon = /Users/oiso/programs/AstroNavigator/.venv/lib/python3.12/site-packages/PySide6/scripts/deploy_lib/pyside_icon.icns

[python]
python_path = /Users/oiso/programs/AstroNavigator/.venv/bin/python3
packages = Nuitka==4.3.5

[qt]
qml_files = 
excluded_qml_plugins = 
modules = Core,DBus,Gui,Positioning,Widgets
plugins = accessiblebridge,egldeviceintegrations,generic,iconengines,imageformats,platforminputcontexts,platforms,platforms/darwin,platformthemes,position

[android]
wheel_pyside = 
wheel_shiboken = 
plugins = 

[nuitka]
macos.permissions = NSLocationUsageDescription:LocationAccess
mode = standalone
extra_args = --quiet --noinclude-qt-translations

[buildozer]
mode = debug
recipe_dir = 
jars_dir = 
ndk_path = 
sdk_path = 
local_libs = 
arch = 

