# Poster-Script

A lightweight Python script set for generating and placing poster elements (text, images) into templates.

This repository contains a small toolchain to help programmatically compose poster graphics from assets and a positions configuration. It is aimed at simple, repeatable poster generation or batching tasks where you want to place text and images into fixed positions on a canvas.

## What this project contains

- `poster_generator.py` - Primary script that composes posters. It reads assets, positions, and text input and renders images.
- `poster_placer.py` - Helper utilities for calculating placement coordinates and applying transformations.
- `poster_text.txt` - Example or source text used when rendering textual content onto posters.
- `positions.json` - JSON file that defines named positions, sizes, and alignment information for where elements should go on the poster.
- `assets/` - Directory containing image assets (icons, logos, background images) used by the generator.
- `README.md` - This file.

## Requirements

- Python 3.8+
- Pillow (PIL) for image composition: pip install Pillow

Optional (depending on the scripts):
- reportlab (for advanced text layout) — pip install reportlab

Create a virtual environment and install dependencies:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install --upgrade pip; pip install Pillow
```

## Quick start

1. Populate the `assets/` directory with background images, logos, and any other artwork you want to use.
2. Edit `positions.json` to set coordinates, widths/heights, and alignment rules for the elements you want to place. Use existing entries as examples.
3. Add or edit `poster_text.txt` with the text that should appear on the poster (or modify the scripts to read from another source).
4. Run the generator:

```powershell
python poster_generator.py
```

By default the script will create output images in the current directory or in a configurable `output/` folder if the script supports it.

## Configuration notes

- `positions.json` structure should contain objects with keys like `name`, `x`, `y`, `width`, `height`, and `align`. Coordinates are pixel-based relative to the top-left of the canvas unless otherwise noted in the file.
- `poster_text.txt` can be plain text. If you need multi-line layout, ensure your generator script performs line wrapping or uses a library that supports rich text layout.

## Customization

- Fonts: To change fonts, either add a TTF file to `assets/` and point the generator to it, or install system fonts and update the script to use the desired font path/name.
- Colors and styles: Modify the script's drawing/color constants or expose them via a small config file.
- Batch generation: If you want to generate multiple posters, adapt `poster_generator.py` to iterate over a CSV, JSON array, or a directory of input files.

## Troubleshooting

- If you see errors about Pillow imports, ensure the virtual environment is active and `Pillow` is installed.
- If images are not positioned as expected, check pixel coordinates in `positions.json` and ensure the canvas size used by the script matches your background image size.

## Small tips and next steps

- Add a `requirements.txt` to lock dependencies.
- Add CLI flags to `poster_generator.py` for input file, output folder, and verbosity.
- Add a simple unit test that loads `positions.json` and validates coordinate values are inside canvas bounds.

## License

This project does not currently include a license file. Add one (for example, MIT) if you intend to share or publish the code.

---

If you'd like, I can also:
- open and inspect `poster_generator.py` to add CLI options (input/output, font, canvas size), or
- add a `requirements.txt` and a sample `output/` directory and a basic unit test to validate positions.
Tell me which you'd prefer and I'll implement it.
