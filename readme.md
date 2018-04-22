Isometric Demo - for Pygame SDL2
================================

This project is my attempt to create a reasonably fast method of displaying isometric tiles in Python. 
Unfortunately it does not yet make use of vanilla Pygame SDL2, I've had to add a little special sauce
to get the demo to it's current state.

Assuming you manage to grab and install my branch of Pygame SDL2 though, you
should be able to run this code and see something like this:

![current_build screen shot](https://i.imgur.com/Bzcfomq.png)

Dependencies
------------

You will also need the following python libraries:

- my latest branch of pygame_sdl2: 
- pytmx

You can grab pytmx with pip:

`pip install pytmx`

and grab my latest branch of pygame_sdl2 here:

[https://github.com/MyreMylar/pygame_sdl2/tree/hack_branch_latest](https://github.com/MyreMylar/pygame_sdl2/tree/hack_branch_latest)

Controls
--------

Move the player around by clicking the left mouse button on the window.

Scroll the screen using the arrow keys.

Freezing the script/creating an executable
------------------------------------------

I wanted this script to be potentially distributable because there is nothing more annoying than 
finishing a game and finding you can't give it to people. 

Assuming you have that special sauce version of Pygame SDL2 I mentioned earlier you should be able to build
an exectuable with PyInstaller. By following these steps, first:

`pip install pyinstaller`

Then in the script directory create a .spec file for PyInstaller that looks something like this:

```# -*- mode: python -*-

block_cipher = None


a = Analysis(['isometric_demo.py'],
             pathex=['C:\\path_to_your_script_here\\],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['pygame'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

a.datas += Tree('data', prefix='data')

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

options = [ ('v', None, 'OPTION')]
exe = EXE(pyz,
          a.scripts,
          options,
          exclude_binaries=True,
          name='isometric_demo',
          debug=True,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='isometric_demo')
```

You may want to turn off the debug & console flags, and the verbose option. And perhaps compress it all into one file.
I'll leave that as an exercise. Make sure you don't accidentally remove the `excludes=['pygame']` line though, that's important.

Save your .spec file and then run:

`pyinstaller your_spec_file_name.spec`

And your compiled exe file should be sitting in a new 'dist' subdirectory. 

Wrap up
-------
So far it's only tested to run and freeze on windows, but perhaps, by the next time I update this readme that will no longer be the case.

Contact me at [dan@myrespace](mailto:dan@myrespace) if you have any questions.
