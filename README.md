# MB Color Harmony Creator (Krita Plugin)

A Krita Python docker plugin that paints a 12-hue harmony wheel directly on the active layer.

## Features

- Harmony presets:
  - Complementary
  - Split Complementary
  - Triad
  - Analogous
  - Double Complementary
  - Rectangular Tetrad
  - Square Tetrad
  - Polychromatic
- Harmony rotation (clockwise / counter-clockwise)
- Position selector (Full + 9 anchors)
- Color Space selector (RYB, RGB/HSV, CMY)
- Hue Mapping selector (Mathematical / Artistic LUT)
- Color Model selector (HSV / HSL)
- 12 hue sectors with custom ring styling and center hole

## Project Structure

- `MBColorHarmonyWheel.desktop` — Krita plugin metadata
- `mb_color_harmony_wheel/__init__.py` — docker registration
- `mb_color_harmony_wheel/mb_color_harmony_wheel.py` — main plugin logic
- `mb_color_harmony_wheel/Manual.html` / `manual.html` — plugin help pages

## Installation

### 1) Locate Krita resources folder

In Krita:

`Settings > Manage Resources... > Open Resource Folder`

Then open (or create) the `pykrita` folder.

### 2) Copy plugin files

Copy this project so that inside `pykrita` you have:

- `MBColorHarmonyWheel.desktop`
- `mb_color_harmony_wheel/` (folder with Python files)

### 3) Enable plugin

In Krita:

`Settings > Configure Krita... > Python Plugin Manager`

Enable **MB Color Harmony Wheel** and restart Krita.

### 4) Open the docker

`Settings > Dockers > MB Color Harmony Wheel`

## Usage

1. Select a paintable layer.
2. Choose a harmony, color options, and wheel position.
3. Click **Paint**.
4. Use **↺** / **↻** to rotate harmony selection.

## Notes

- The plugin paints into the active node/layer.
- If the plugin does not appear after install, verify both `.desktop` and package folder are inside `pykrita`, then restart Krita.

## Credits

The color wheel and harmony system used in this plugin are based on the color theory explained by **Marc Brunet** in his video:
[Color Harmony for Artists](https://www.youtube.com/watch?v=Ejp74Picub0)

## License

No license file is currently included.
