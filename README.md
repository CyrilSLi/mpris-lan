# mpris-lan

Control MPRIS-compatible media players over the network using a web interface.

Visit [layout_demo.html](static/layout_demo.html) to see a static demo of the interface layout.

## Features

- Play/pause, next, previous
- Fast forward and rewind (10 seconds per click)
- Draggable progress bar
- Change loop and shuffle modes on supported players (X icon when off)
- Remove player (trash icon)
- Polling pauses when the web interface is not visible to save resources, also controllable via a toggle button

## Installation & Usage

[playerctl](https://github.com/altdesktop/playerctl), available in most package managers, must be installed and available in the PATH.

### From package

```
pip install dist/mpris_lan-1.0.0.tar.gz
mpris-lan
```

### Manual

```
pip install -r requirements.txt
python src/app.py
```

The web interface is available at the computer's local IP address (and [localhost](http://localhost:58468)), port 58468.

## Todo

- Perform the same action on multiple players using checkboxes
- Adjustable polling interval