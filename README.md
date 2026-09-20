<div align="center">

# 🔗 Shortcut Maker

**Give any `.exe` (or script) a real Start Menu shortcut — so it shows up in Windows search like a normal installed app.**

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52?logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D4?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue)

<!-- Put a screenshot at docs/screenshot.png and it will show up here -->
<img src="docs/" alt="Shortcut Maker screenshot" width="820">

</div>

---

## Why?

Portable apps and standalone `.exe` files usually don't come with a Start Menu shortcut, so you can't launch them by pressing <kbd>Win</kbd> and typing their name.

**Shortcut Maker** fixes that in a few clicks: pick a file, and it creates a proper `.lnk` shortcut in your Start Menu (and optionally on your Desktop) — with the right name and icon.

## Features

- 🔍 **Shows up in Windows search** — creates the shortcut in your per-user Start Menu `Programs` folder
- 🖥️ **Optional Desktop shortcut** — one toggle, works even if your Desktop is redirected to OneDrive
- 🏷️ **Clean names** — the shortcut is named after the file *without* the `.exe` extension (you can rename it)
- 🎨 **Keeps the original icon** — `.exe` shortcuts use the exe's own icon
- 📄 **Works with other file types** — `.py`, `.pyw`, `.bat`, `.cmd`, `.jar`, `.ps1`, `.vbs`, `.msi`, … anything you can open
- 🖼️ **Custom icon (optional)** — pick any image (`png`, `jpg`, `webp`, `bmp`, `gif`, `ico`); it's converted to a multi-size `.ico` automatically. Great for scripts that would otherwise show the generic Python logo
- 👀 **Live preview** — see how the shortcut will look in Windows search before creating it
- 🖱️ **Drag & drop** — drop a file anywhere on the window
- ✨ **Modern dark UI** — frameless window, animated toggles, toast notifications

## Download (no Python needed)

The easiest way to use Shortcut Maker is the ready-made `.exe`:

1. Go to the [**Releases**](../../releases/latest) page.
2. Download **`ShortcutMaker.exe`** from the latest release.
3. Double-click it — that's it. No installation, no Python, nothing else required.

> ⚠️ **Windows SmartScreen / antivirus warning:** the exe isn't code-signed, so Windows may show *"Windows protected your PC"*. Click **More info → Run anyway**. Some antivirus programs also flag apps built with PyInstaller by mistake (false positive). If you'd rather not trust a binary, [run from source](#run-from-source) or [build the exe yourself](#build-a-standalone-exe) — the whole app is a single readable Python file.

## Run from source

**Requirements**

- Windows 10 or 11
- Python 3.9+
- [PyQt6](https://pypi.org/project/PyQt6/)

> No `pywin32` needed — shortcuts are created through Windows' built-in PowerShell / `WScript.Shell`.

**Install & run**

```bash
git clone https://github.com/<your-username>/shortcut-maker.git
cd shortcut-maker
pip install PyQt6
python shortcut_maker.py
```

## Usage

1. **Drop a file** onto the window (or click the box to browse).
2. Check the **shortcut name** — it's pre-filled from the file name.
3. *(Optional)* Click **Choose image** to set a custom icon.
4. Turn on **Start Menu** and/or **Desktop**.
5. Click **Create Shortcut**.

Then press <kbd>Win</kbd>, type the name, and your app is there. The first time, Windows may need a few seconds to index the new shortcut.

## Build a standalone `.exe`

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name ShortcutMaker shortcut_maker.py
```

The result is in `dist/ShortcutMaker.exe`.

> Tip: add `--icon app.ico` to give the exe its own icon.

**Publishing a release (for maintainers):** on GitHub go to **Releases → Draft a new release**, create a tag such as `v1.0.0`, drag `dist/ShortcutMaker.exe` into the assets box, and click **Publish release**. Users can then download it from the [Releases](../../releases/latest) page.

## How it works

| Piece | What it does |
|---|---|
| Start Menu shortcut | Saved to `%APPDATA%\Microsoft\Windows\Start Menu\Programs` (current user only, no admin rights needed) |
| Desktop shortcut | Saved to the real Desktop folder resolved by Windows |
| `.lnk` creation | A small PowerShell script using `WScript.Shell`; paths are passed via environment variables, so Unicode / spaces / quotes in paths are safe |
| Icons for `.exe` | `IconLocation = <exe>,0` (the exe's own icon) |
| Icons for other files | Left to Windows (file-type icon), unless you choose a custom image |
| Custom icons | Converted to a multi-size PNG-based `.ico` and stored in `%APPDATA%\ShortcutMaker\icons` |

## Notes & FAQ

**The shortcut icon disappeared.**
If you used a custom image, don't delete `%APPDATA%\ShortcutMaker\icons` — the shortcut points to the `.ico` stored there.

**Can I remove a shortcut?**
Yes — use **Open Start Menu folder** in the app and delete the `.lnk` file (or delete it from the Desktop).

**A shortcut with the same name already exists.**
It is overwritten.

**Shortcut for all users?**
Not yet. Shortcuts are created for the current user only, which avoids needing administrator rights.

## Roadmap

- [ ] Shortcuts for all users (admin)
- [ ] Command-line arguments field
- [ ] "Run as administrator" option
- [ ] Manage / delete created shortcuts inside the app

## Contributing

Issues and pull requests are welcome. If you find a bug, please include your Windows version and the type of file you were creating a shortcut for.

## License

Released under the [MIT License](LICENSE).
