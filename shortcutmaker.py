import base64
import ctypes
import hashlib
import html
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import (
    QBuffer,
    QByteArray,
    QEasingCurve,
    QFileInfo,
    QIODevice,
    QPointF,
    QPropertyAnimation,
    QRectF,
    Qt,
    QTimer,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QIcon,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PyQt6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QFileDialog,
    QFileIconProvider,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

INVALID_NAME_CHARS = '\\/:*?"<>|'
ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)

COL_W = 392       
GAP = 18          
PAD = 26           
SHADOW = 16       
RADIUS = 22      
CREATE_TEXT = "Create Shortcut"

ICON_FONT = "Segoe MDL2 Assets"
G_MIN = "\uE921"
G_CLOSE = "\uE8BB"
G_LINK = "\uE71B"
G_ADD = "\uE710"
G_DELETE = "\uE74D"
G_SEARCH = "\uE721"
G_DESKTOP = "\uE7F4"
G_PICTURE = "\uE8B9"
G_FOLDER = "\uED25"
G_CHECK = "\uE73E"
G_ERROR = "\uE783"
G_WARN = "\uE7BA"

PS_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
try {
    $ws = New-Object -ComObject WScript.Shell
    $dirs = @()
    if ($env:SM_START -eq '1')   { $dirs += [Environment]::GetFolderPath('Programs') }
    if ($env:SM_DESKTOP -eq '1') { $dirs += [Environment]::GetFolderPath('Desktop') }
    foreach ($d in $dirs) {
        $lnk = Join-Path $d ($env:SM_NAME + '.lnk')
        $s = $ws.CreateShortcut($lnk)
        $s.TargetPath = $env:SM_TARGET
        $s.WorkingDirectory = $env:SM_WORKDIR
        if ($env:SM_ICON) { $s.IconLocation = $env:SM_ICON }
        $s.Save()
        Write-Output $lnk
    }
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
"""

STYLE = """
QToolTip {
    background: #1b1f3a; color: #eef0ff;
    border: 1px solid rgba(255,255,255,0.15); padding: 6px; border-radius: 6px;
}

QFrame#card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
}
QFrame#sep { background: rgba(255,255,255,0.07); border: none; }

QFrame#drop {
    background: rgba(255,255,255,0.04);
    border: 2px dashed rgba(255,255,255,0.18);
    border-radius: 20px;
}
QFrame#drop[state="hover"] {
    background: rgba(124,92,255,0.09);
    border: 2px dashed rgba(124,92,255,0.85);
}
QFrame#drop[state="drag"] {
    background: rgba(34,211,238,0.11);
    border: 2px solid #22d3ee;
}
QFrame#drop[state="filled"] {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.12);
}
QLabel#plus {
    background: rgba(124,92,255,0.18); color: #b9a8ff; border-radius: 32px;
}
QLabel#dzTitle { color: #ffffff; font-size: 16px; font-weight: 700; }
QLabel#dzSub   { color: #8a90b5; font-size: 12px; }
QLabel#fileIcon {
    background: rgba(255,255,255,0.07); color: #b9a8ff; border-radius: 18px;
}
QLabel#fileName { color: #ffffff; font-size: 16px; font-weight: 700; }
QLabel#filePath { color: #8a90b5; font-size: 11px; }
QLabel#badge {
    background: rgba(124,92,255,0.25); color: #d3c8ff;
    border-radius: 8px; padding: 2px 10px; font-size: 11px; font-weight: 700;
}
QLabel#dzHint { color: #7d83a8; font-size: 11px; }

QLabel#title    { color: #ffffff; font-size: 17px; font-weight: 700; }
QLabel#subtitle { color: #8a90b5; font-size: 11px; }
QLabel#cap      { color: #c9cdf2; font-size: 12px; font-weight: 600; }
QLabel#hint     { color: #7d83a8; font-size: 11px; }
QLabel#rowTitle { color: #eef0ff; font-size: 13px; font-weight: 600; }
QLabel#rowSub   { color: #8a90b5; font-size: 11px; }
QLabel#logo {
    color: white; border-radius: 13px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7c5cff, stop:1 #22d3ee);
}
QLabel#thumb    { background: rgba(255,255,255,0.07); color: #b9a8ff; border-radius: 12px; }
QLabel#optIcon  { background: rgba(124,92,255,0.16); color: #b9a8ff; border-radius: 12px; }

QLineEdit {
    background: rgba(0,0,0,0.28);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 11px; padding: 10px 12px;
    color: #eef0ff; font-size: 13px;
    selection-background-color: #7c5cff;
    placeholder-text-color: #6b7194;
}
QLineEdit:focus { border: 1px solid #7c5cff; background: rgba(0,0,0,0.36); }

QPushButton#ghost {
    background: rgba(255,255,255,0.07); color: #dfe2ff;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 11px; padding: 9px 16px; font-size: 12px;
}
QPushButton#ghost:hover   { background: rgba(255,255,255,0.14); }
QPushButton#ghost:pressed { background: rgba(255,255,255,0.04); }

QPushButton#ghostDanger {
    background: rgba(255,255,255,0.07); color: #ff8b94;
    border: 1px solid rgba(255,255,255,0.08); border-radius: 11px;
}
QPushButton#ghostDanger:hover { background: rgba(229,72,77,0.28); }

QPushButton#primary {
    color: white; border: none; border-radius: 15px;
    font-size: 15px; font-weight: 700;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c5cff, stop:1 #22a6f2);
}
QPushButton#primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9078ff, stop:1 #3bbcf8);
}
QPushButton#primary:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6647e6, stop:1 #1a90d6);
}
QPushButton#primary:disabled { background: rgba(255,255,255,0.10); color: rgba(255,255,255,0.45); }

QPushButton#winBtn, QPushButton#closeBtn {
    background: transparent; color: #b6bbe0; border: none; border-radius: 9px;
}
QPushButton#winBtn:hover   { background: rgba(255,255,255,0.12); color: white; }
QPushButton#closeBtn:hover { background: #e5484d; color: white; }

QFrame#mock {
    background: rgba(8,10,22,0.75);
    border: 1px solid rgba(255,255,255,0.08); border-radius: 14px;
}
QFrame#mockBar { background: rgba(255,255,255,0.07); border-radius: 10px; }
QFrame#mockRow {
    background: rgba(124,92,255,0.20);
    border: 1px solid rgba(124,92,255,0.45); border-radius: 10px;
}
QLabel#mockGlyph { color: #8a90b5; }
QLabel#mockIcon  { color: #eef0ff; }
QLabel#mockQuery { color: #eef0ff; font-size: 12px; }
QLabel#mockName  { color: #ffffff; font-size: 13px; font-weight: 600; }

QFrame#toast {
    background: rgba(22,25,46,0.97);
    border: 1px solid rgba(255,255,255,0.14); border-radius: 14px;
}
QFrame#toast[kind="ok"]    { border: 1px solid rgba(52,211,153,0.65); }
QFrame#toast[kind="error"] { border: 1px solid rgba(248,113,113,0.70); }
QFrame#toast[kind="warn"]  { border: 1px solid rgba(251,191,36,0.65); }
QLabel#toastText { color: #eef0ff; font-size: 12px; }
"""

def icons_dir() -> Path:
    base = Path(os.environ.get("APPDATA") or Path.home())
    path = base / "ShortcutMaker" / "icons"
    path.mkdir(parents=True, exist_ok=True)
    return path


def start_menu_programs_dir() -> Path:
    base = Path(os.environ.get("APPDATA") or Path.home())
    return base / "Microsoft" / "Windows" / "Start Menu" / "Programs"


def image_to_ico(src: str, dst: Path) -> None:
    img = QImage(src)
    if img.isNull():
        raise ValueError("This image can't be read.")

    entries = []
    for size in ICON_SIZES:
        scaled = img.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        canvas = QImage(size, size, QImage.Format.Format_ARGB32)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        painter.drawImage((size - scaled.width()) // 2, (size - scaled.height()) // 2, scaled)
        painter.end()

        data = QByteArray()
        buf = QBuffer(data)
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        canvas.save(buf, "PNG")
        buf.close()
        entries.append((size, bytes(data)))

    header = struct.pack("<HHH", 0, 1, len(entries))
    offset = 6 + 16 * len(entries)
    directory = b""
    images = b""
    for size, png in entries:
        dim = 0 if size >= 256 else size
        directory += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset)
        images += png
        offset += len(png)

    dst.write_bytes(header + directory + images)


def prepare_icon(target: str, name: str, custom_icon: str) -> str:
    if custom_icon:
        tag = hashlib.md5(target.lower().encode("utf-8")).hexdigest()[:6]
        dst = icons_dir() / f"{name}_{tag}.ico"
        if Path(custom_icon).suffix.lower() == ".ico":
            shutil.copyfile(custom_icon, dst)
        else:
            image_to_ico(custom_icon, dst)
        return f"{dst},0"

    if Path(target).suffix.lower() == ".exe":
        return f"{target},0" 

    return "" 


def create_shortcuts(target: str, name: str, icon_location: str, start_menu: bool, desktop: bool) -> list:
    if sys.platform != "win32":
        raise RuntimeError("This app only works on Windows.")

    env = os.environ.copy()
    env.update(
        {
            "SM_TARGET": target,
            "SM_WORKDIR": str(Path(target).parent),
            "SM_NAME": name,
            "SM_ICON": icon_location,
            "SM_START": "1" if start_menu else "0",
            "SM_DESKTOP": "1" if desktop else "0",
        }
    )
    encoded = base64.b64encode(PS_SCRIPT.encode("utf-16-le")).decode("ascii")
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-EncodedCommand",
            encoded,
        ],
        env=env,
        capture_output=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode != 0:
        err = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(err or "Failed to create the shortcut.")

    out = result.stdout.decode("utf-8-sig", errors="replace")
    return [line.strip() for line in out.splitlines() if line.strip()]

def icon_font(px: int) -> QFont:
    f = QFont(ICON_FONT)
    f.setPixelSize(px)
    return f


def repolish(w: QWidget) -> None:
    w.style().unpolish(w)
    w.style().polish(w)
    w.update()


def make_label(text: str = "", name: str = "", wrap: bool = False) -> QLabel:
    lab = QLabel(text)
    if name:
        lab.setObjectName(name)
    lab.setWordWrap(wrap)
    return lab


def make_glyph(glyph: str, px: int, size: int, name: str) -> QLabel:
    lab = QLabel(glyph)
    lab.setObjectName(name)
    lab.setFont(icon_font(px))
    lab.setFixedSize(size, size)
    lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lab


def make_sep() -> QFrame:
    sep = QFrame()
    sep.setObjectName("sep")
    sep.setFixedHeight(1)
    return sep


def make_app_icon() -> QIcon:
    pm = QPixmap(256, 256)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    grad = QLinearGradient(0, 0, 256, 256)
    grad.setColorAt(0, QColor("#7c5cff"))
    grad.setColorAt(1, QColor("#22d3ee"))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(grad))
    p.drawRoundedRect(QRectF(12, 12, 232, 232), 60, 60)
    p.setPen(QColor("white"))
    p.setFont(icon_font(128))
    p.drawText(QRectF(0, 0, 256, 256), Qt.AlignmentFlag.AlignCenter, G_LINK)
    p.end()
    return QIcon(pm)


class ElidedLabel(QLabel):

    def __init__(self, name: str = "") -> None:
        super().__init__()
        if name:
            self.setObjectName(name)
        self._full = ""
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

    def set_full_text(self, text: str) -> None:
        self._full = text
        self.setToolTip(text)
        self._update()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update()

    def _update(self) -> None:
        shown = self.fontMetrics().elidedText(
            self._full, Qt.TextElideMode.ElideMiddle, max(10, self.width() - 4)
        )
        QLabel.setText(self, shown)


class Card(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("card")


class ToggleSwitch(QAbstractButton):

    def __init__(self, checked: bool = False) -> None:
        super().__init__()
        self._knob = 1.0 if checked else 0.0
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(50, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._anim = QPropertyAnimation(self, b"knob", self)
        self._anim.setDuration(170)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.toggled.connect(self._on_toggled)

    def _get_knob(self) -> float:
        return self._knob

    def _set_knob(self, value: float) -> None:
        self._knob = value
        self.update()

    knob = pyqtProperty(float, _get_knob, _set_knob)

    def _on_toggled(self, on: bool) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._knob)
        self._anim.setEndValue(1.0 if on else 0.0)
        self._anim.start()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect())
        off = QColor("#3a3f63")
        on = QColor("#7c5cff")
        t = self._knob
        track = QColor(
            int(off.red() + (on.red() - off.red()) * t),
            int(off.green() + (on.green() - off.green()) * t),
            int(off.blue() + (on.blue() - off.blue()) * t),
        )
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        d = r.height() - 6
        x = 3 + t * (r.width() - d - 6)
        p.setBrush(QColor("white"))
        p.drawEllipse(QRectF(x, 3, d, d))


class TitleBar(QWidget):

    def __init__(self, window: QWidget) -> None:
        super().__init__()
        self._win = window
        self.setFixedHeight(54)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        logo = make_glyph(G_LINK, 20, 42, "logo")
        lay.addWidget(logo)

        texts = QVBoxLayout()
        texts.setSpacing(1)
        texts.addWidget(make_label("Shortcut Maker", "title"))
        texts.addWidget(make_label("Add any file to the Start Menu and Desktop", "subtitle"))
        lay.addLayout(texts)
        lay.addStretch(1)

        btn_min = QPushButton(G_MIN)
        btn_min.setObjectName("winBtn")
        btn_min.setFont(icon_font(10))
        btn_min.setFixedSize(38, 32)
        btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_min.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_min.clicked.connect(self._win.showMinimized)

        btn_close = QPushButton(G_CLOSE)
        btn_close.setObjectName("closeBtn")
        btn_close.setFont(icon_font(10))
        btn_close.setFixedSize(38, 32)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_close.clicked.connect(self._win.close)

        lay.addWidget(btn_min)
        lay.addWidget(btn_close)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self._win.windowHandle()
            if handle is not None:
                handle.startSystemMove()
        super().mousePressEvent(event)


class DropZone(QFrame):

    clicked = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("drop")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hover = False
        self._drag = False
        self._filled = False

        self.stack = QStackedLayout(self)
        self.stack.setContentsMargins(0, 0, 0, 0)
        self.stack.addWidget(self._build_empty())
        self.stack.addWidget(self._build_filled())
        self._refresh()

    def _build_empty(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(10)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)

        plus = make_glyph(G_ADD, 24, 64, "plus")
        title = make_label("Drop a file here", "dzTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = make_label("exe, py, bat, or any other file\nor click to browse", "dzSub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        v.addStretch(1)
        v.addWidget(plus, 0, Qt.AlignmentFlag.AlignCenter)
        v.addSpacing(4)
        v.addWidget(title)
        v.addWidget(sub)
        v.addStretch(1)
        return w

    def _build_filled(self) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(22, 20, 22, 20)
        h.setSpacing(16)

        self.f_icon = make_glyph(G_LINK, 26, 76, "fileIcon")
        h.addWidget(self.f_icon)

        col = QVBoxLayout()
        col.setSpacing(6)
        col.addStretch(1)
        self.f_name = ElidedLabel("fileName")
        self.f_path = ElidedLabel("filePath")
        self.f_path.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.f_path.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        col.addWidget(self.f_name)
        col.addWidget(self.f_path)

        meta = QHBoxLayout()
        meta.setSpacing(8)
        self.f_badge = make_label("EXE", "badge")
        meta.addWidget(self.f_badge)
        meta.addWidget(make_label("Click to change the file", "dzHint"))
        meta.addStretch(1)
        col.addSpacing(2)
        col.addLayout(meta)
        col.addStretch(1)
        h.addLayout(col, 1)
        return w

    def set_file(self, path: str) -> None:
        p = Path(path)
        self.f_name.set_full_text(p.name)
        self.f_path.set_full_text(str(p))
        self.f_badge.setText((p.suffix.lstrip(".").upper() or "FILE")[:6])
        self._filled = True
        self.stack.setCurrentIndex(1)
        self._refresh()

    def set_pixmap(self, pm: QPixmap) -> None:
        if pm.isNull():
            self.f_icon.setText(G_LINK)
        else:
            self.f_icon.setPixmap(pm)

    def set_drag(self, on: bool) -> None:
        self._drag = on
        self._refresh()

    def _refresh(self) -> None:
        if self._drag:
            state = "drag"
        elif self._hover:
            state = "hover"
        elif self._filled:
            state = "filled"
        else:
            state = "idle"
        self.setProperty("state", state)
        repolish(self)

    def enterEvent(self, event) -> None:
        self._hover = True
        self._refresh()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self._refresh()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class Toast(QFrame):

    COLORS = {"ok": "#34d399", "error": "#f87171", "warn": "#fbbf24"}
    GLYPHS = {"ok": G_CHECK, "error": G_ERROR, "warn": G_WARN}

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("toast")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 12, 20, 12)
        lay.setSpacing(14)

        self.icon = QLabel()
        self.icon.setFont(icon_font(20))
        self.icon.setFixedWidth(26)
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text = make_label("", "toastText", wrap=True)
        lay.addWidget(self.icon)
        lay.addWidget(self.text, 1)

        self.effect = QGraphicsOpacityEffect(self)
        self.effect.setOpacity(0.0)
        self.setGraphicsEffect(self.effect)
        self.anim = QPropertyAnimation(self.effect, b"opacity", self)
        self.anim.finished.connect(self._on_finished)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._fade_out)
        self.hide()

    def show_message(self, title: str, sub: str = "", kind: str = "ok", ms: int = 4600) -> None:
        self.setProperty("kind", kind)
        repolish(self)
        color = self.COLORS.get(kind, "#34d399")
        self.icon.setStyleSheet(f"color: {color};")
        self.icon.setText(self.GLYPHS.get(kind, G_CHECK))
        body = f"<b>{html.escape(title)}</b>"
        if sub:
            body += f"<br><span style='color:#9aa0c3'>{html.escape(sub)}</span>"
        self.text.setText(body)

        parent = self.parentWidget()
        self.setFixedWidth(min(520, parent.width() - 2 * (SHADOW + 30)))
        self.adjustSize()
        self.move((parent.width() - self.width()) // 2, SHADOW + 66)
        self.raise_()
        self.show()

        self.anim.stop()
        self.anim.setDuration(200)
        self.anim.setStartValue(self.effect.opacity())
        self.anim.setEndValue(1.0)
        self.anim.start()
        self.timer.start(ms)

    def _fade_out(self) -> None:
        self.anim.stop()
        self.anim.setDuration(350)
        self.anim.setStartValue(self.effect.opacity())
        self.anim.setEndValue(0.0)
        self.anim.start()

    def _on_finished(self) -> None:
        if self.effect.opacity() <= 0.01:
            self.hide()

class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Shortcut Maker")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAcceptDrops(True)
        self.setStyleSheet(STYLE)

        self.target = ""
        self.custom_icon = ""
        self._bg = None

        body_w = COL_W * 2 + GAP

        outer = QVBoxLayout(self)
        outer.setContentsMargins(SHADOW + PAD, SHADOW + 12, SHADOW + PAD, SHADOW + PAD)
        outer.setSpacing(14)
        outer.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        bar = TitleBar(self)
        bar.setFixedWidth(body_w)
        outer.addWidget(bar)

        columns = QHBoxLayout()
        columns.setSpacing(GAP)
        columns.addWidget(self._build_right_column())
        columns.addWidget(self._build_left_column())
        outer.addLayout(columns)

        self.toast = Toast(self)
        self.refresh_visuals()

    def _column(self) -> tuple:
        col = QWidget()
        col.setFixedWidth(COL_W)
        lay = QVBoxLayout(col)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)
        return col, lay

    def _build_right_column(self) -> QWidget:
        col, lay = self._column()

        self.drop = DropZone()
        self.drop.setMinimumHeight(230)
        self.drop.clicked.connect(self.choose_target)
        lay.addWidget(self.drop, 1)

        card = Card()
        v = QVBoxLayout(card)
        v.setContentsMargins(18, 16, 18, 16)
        v.setSpacing(10)

        v.addWidget(make_label("Shortcut name", "cap"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. My App")
        self.name_edit.setAcceptDrops(False)
        self.name_edit.textChanged.connect(self.refresh_visuals)
        v.addWidget(self.name_edit)
        v.addWidget(make_label("Without .exe - this is the name shown in Windows search", "hint", wrap=True))
        v.addSpacing(2)
        v.addWidget(make_sep())
        v.addSpacing(2)

        row = QHBoxLayout()
        row.setSpacing(12)
        self.icon_thumb = make_glyph(G_PICTURE, 18, 44, "thumb")
        row.addWidget(self.icon_thumb)

        texts = QVBoxLayout()
        texts.setSpacing(2)
        texts.addWidget(make_label("Custom icon (optional)", "rowTitle"))
        self.icon_status = ElidedLabel("rowSub")
        texts.addWidget(self.icon_status)
        row.addLayout(texts, 1)

        btn_icon = QPushButton("Choose image")
        btn_icon.setObjectName("ghost")
        btn_icon.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_icon.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_icon.setToolTip(
            "The image is converted to an icon and saved in\n%APPDATA%\\ShortcutMaker\\icons - do not delete it"
        )
        btn_icon.clicked.connect(self.choose_icon)
        row.addWidget(btn_icon)

        self.btn_clear = QPushButton(G_DELETE)
        self.btn_clear.setObjectName("ghostDanger")
        self.btn_clear.setFont(icon_font(14))
        self.btn_clear.setFixedSize(38, 38)
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_clear.setToolTip("Remove custom icon")
        self.btn_clear.clicked.connect(self.clear_icon)
        self.btn_clear.hide()
        row.addWidget(self.btn_clear)
        v.addLayout(row)

        lay.addWidget(card)
        return col

    def _build_left_column(self) -> QWidget:
        col, lay = self._column()

        opts = Card()
        v = QVBoxLayout(opts)
        v.setContentsMargins(18, 14, 18, 14)
        v.setSpacing(12)
        self.tg_start = ToggleSwitch(True)
        self.tg_desktop = ToggleSwitch(False)
        v.addWidget(self._option_row(G_SEARCH, "Start Menu", "Also shows up in Windows search", self.tg_start))
        v.addWidget(make_sep())
        v.addWidget(self._option_row(G_DESKTOP, "Desktop", "Also create a shortcut on the Desktop", self.tg_desktop))
        lay.addWidget(opts)

        prev = Card()
        pv = QVBoxLayout(prev)
        pv.setContentsMargins(18, 14, 18, 16)
        pv.setSpacing(10)
        pv.addWidget(make_label("Preview in Windows search", "cap"))

        mock = QFrame()
        mock.setObjectName("mock")
        mock.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        mv = QVBoxLayout(mock)
        mv.setContentsMargins(10, 10, 10, 10)
        mv.setSpacing(8)

        bar = QFrame()
        bar.setObjectName("mockBar")
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(10, 7, 10, 7)
        bl.setSpacing(8)
        bl.addWidget(make_glyph(G_SEARCH, 12, 16, "mockGlyph"))
        self.mock_query = make_label("", "mockQuery")
        bl.addWidget(self.mock_query, 1)
        mv.addWidget(bar)

        row = QFrame()
        row.setObjectName("mockRow")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(10, 8, 10, 8)
        rl.setSpacing(10)
        self.mock_icon = make_glyph(G_LINK, 16, 32, "mockIcon")
        rl.addWidget(self.mock_icon)
        tv = QVBoxLayout()
        tv.setSpacing(0)
        self.mock_name = ElidedLabel("mockName")
        tv.addWidget(self.mock_name)
        tv.addWidget(make_label("App", "rowSub"))
        rl.addLayout(tv, 1)
        mv.addWidget(row)

        pv.addWidget(mock)
        lay.addWidget(prev)

        lay.addStretch(1)

        self.btn_create = QPushButton(CREATE_TEXT)
        self.btn_create.setObjectName("primary")
        self.btn_create.setMinimumHeight(54)
        self.btn_create.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_create.clicked.connect(self.on_create)
        lay.addWidget(self.btn_create)

        btn_open = QPushButton("Open Start Menu folder")
        btn_open.setObjectName("ghost")
        btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_open.clicked.connect(self.open_start_folder)
        lay.addWidget(btn_open)
        return col

    def _option_row(self, glyph: str, title: str, sub: str, toggle: ToggleSwitch) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(12)
        h.addWidget(make_glyph(glyph, 16, 40, "optIcon"))
        col = QVBoxLayout()
        col.setSpacing(1)
        col.addWidget(make_label(title, "rowTitle"))
        col.addWidget(make_label(sub, "rowSub"))
        h.addLayout(col, 1)
        h.addWidget(toggle)
        return w

    def _render_bg(self) -> QPixmap:
        dpr = self.devicePixelRatioF()
        w, h = self.width(), self.height()
        pm = QPixmap(max(1, int(w * dpr)), max(1, int(h * dpr)))
        pm.setDevicePixelRatio(dpr)
        pm.fill(Qt.GlobalColor.transparent)

        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        full = QRectF(0, 0, w, h)

        p.setPen(Qt.PenStyle.NoPen)
        for i in range(SHADOW):
            r = full.adjusted(i, i + 3, -i, -i + 3)
            p.setBrush(QColor(0, 0, 0, 5))
            p.drawRoundedRect(r, RADIUS + (SHADOW - i), RADIUS + (SHADOW - i))

        box = full.adjusted(SHADOW, SHADOW, -SHADOW, -SHADOW)
        path = QPainterPath()
        path.addRoundedRect(box, RADIUS, RADIUS)

        base = QLinearGradient(box.topLeft(), box.bottomRight())
        base.setColorAt(0.0, QColor("#191c3a"))
        base.setColorAt(1.0, QColor("#0a0c19"))
        p.fillPath(path, QBrush(base))

        p.setClipPath(path)
        glow1 = QRadialGradient(QPointF(box.right() - 40, box.top() + 10), 420)
        glow1.setColorAt(0.0, QColor(124, 92, 255, 100))
        glow1.setColorAt(1.0, QColor(124, 92, 255, 0))
        p.fillRect(box, QBrush(glow1))

        glow2 = QRadialGradient(QPointF(box.left() + 30, box.bottom() - 10), 380)
        glow2.setColorAt(0.0, QColor(34, 211, 238, 60))
        glow2.setColorAt(1.0, QColor(34, 211, 238, 0))
        p.fillRect(box, QBrush(glow2))
        p.setClipping(False)

        p.setPen(QPen(QColor(255, 255, 255, 28), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)
        p.end()
        return pm

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._bg = self._render_bg()

    def paintEvent(self, _event) -> None:
        if self._bg is None:
            self._bg = self._render_bg()
        p = QPainter(self)
        p.drawPixmap(0, 0, self._bg)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            self.drop.set_drag(True)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:
        self.drop.set_drag(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:
        self.drop.set_drag(False)
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self.set_target(url.toLocalFile())
                break

    def choose_target(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select file",
            "",
            "Common files (*.exe *.bat *.cmd *.py *.pyw *.jar *.ps1 *.vbs *.js *.msi *.ahk);;"
            "Programs (*.exe);;All files (*.*)",
        )
        if path:
            self.set_target(path)

    def set_target(self, path: str) -> None:
        path = os.path.normpath(path)
        if not os.path.isfile(path):
            self.toast.show_message("That is not a file", "Folders are not supported. Pick a file.", "warn")
            return
        self.target = path
        self.drop.set_file(path)
        self.name_edit.setText(Path(path).stem)
        self.update_icon_status()
        self.refresh_visuals()

    def choose_icon(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select icon image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.gif *.ico);;All files (*.*)",
        )
        if not path:
            return
        if QImage(path).isNull():
            self.toast.show_message("Couldn't read this image", "Try another one (png or jpg works best).", "error")
            return
        self.custom_icon = os.path.normpath(path)
        self.update_icon_status()
        self.refresh_visuals()

    def clear_icon(self) -> None:
        self.custom_icon = ""
        self.update_icon_status()
        self.refresh_visuals()

    def update_icon_status(self) -> None:
        if self.custom_icon:
            self.icon_status.set_full_text(Path(self.custom_icon).name)
            pm = self.make_pixmap(self.custom_icon, 36)
            if pm.isNull():
                self.icon_thumb.setText(G_PICTURE)
            else:
                self.icon_thumb.setPixmap(pm)
            self.btn_clear.show()
            return

        self.icon_thumb.setText(G_PICTURE)
        self.btn_clear.hide()
        if not self.target:
            text = "Default: the file's own icon"
        elif Path(self.target).suffix.lower() == ".exe":
            text = "Default: the exe's own icon"
        else:
            ext = Path(self.target).suffix.lower() or "file"
            text = f"Default: file-type icon ({ext})"
        self.icon_status.set_full_text(text)

    def make_pixmap(self, source: str, size: int) -> QPixmap:
        dpr = self.devicePixelRatioF()
        px = int(size * dpr)
        if Path(source).suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif", ".ico"):
            pm = QPixmap(source)
        else:
            pm = QFileIconProvider().icon(QFileInfo(source)).pixmap(px, px)
        if pm.isNull():
            return pm
        pm = pm.scaled(
            px, px, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        pm.setDevicePixelRatio(dpr)
        return pm

    def current_pixmap(self, size: int) -> QPixmap:
        if self.custom_icon:
            return self.make_pixmap(self.custom_icon, size)
        if self.target and os.path.exists(self.target):
            return self.make_pixmap(self.target, size)
        return QPixmap()

    def refresh_visuals(self) -> None:
        self.drop.set_pixmap(self.current_pixmap(52))

        pm = self.current_pixmap(28)
        if pm.isNull():
            self.mock_icon.setText(G_LINK)
        else:
            self.mock_icon.setPixmap(pm)

        name = self.name_edit.text().strip()
        self.mock_name.set_full_text(name or "Shortcut name")
        query = name[:3].lower()
        if query:
            self.mock_query.setStyleSheet("color: #eef0ff;")
            self.mock_query.setText(query)
        else:
            self.mock_query.setStyleSheet("color: #6b7194;")
            self.mock_query.setText("Type here to search")

    def open_start_folder(self) -> None:
        folder = start_menu_programs_dir()
        if folder.exists() and hasattr(os, "startfile"):
            os.startfile(str(folder))  # type: ignore[attr-defined]
        else:
            self.toast.show_message("Folder not found", "This only works on Windows.", "warn")

    def on_create(self) -> None:
        target = self.target
        name = self.name_edit.text().strip().rstrip(". ")
        want_start = self.tg_start.isChecked()
        want_desktop = self.tg_desktop.isChecked()

        if not target or not os.path.isfile(target):
            self.toast.show_message("Choose a file first", "Drop a file in the box or click it to browse.", "warn")
            return
        if not name:
            self.toast.show_message("Name is empty", "Type a name for the shortcut.", "warn")
            return
        if any(c in INVALID_NAME_CHARS for c in name):
            self.toast.show_message("Invalid name", f"These characters are not allowed:  {INVALID_NAME_CHARS}", "warn")
            return
        if not (want_start or want_desktop):
            self.toast.show_message("No destination selected", "Turn on Start Menu, Desktop, or both.", "warn")
            return

        self.btn_create.setEnabled(False)
        self.btn_create.setText("Working…")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        QApplication.processEvents()
        try:
            icon_location = prepare_icon(target, name, self.custom_icon)
            create_shortcuts(target, name, icon_location, want_start, want_desktop)
        except Exception as exc:  # noqa: BLE001
            QApplication.restoreOverrideCursor()
            self.btn_create.setEnabled(True)
            self.btn_create.setText(CREATE_TEXT)
            self.toast.show_message("Couldn't create the shortcut", str(exc)[:220], "error", ms=7000)
            return
        QApplication.restoreOverrideCursor()

        self.btn_create.setEnabled(True)
        self.btn_create.setText("✓  Created!")
        QTimer.singleShot(1800, lambda: self.btn_create.setText(CREATE_TEXT))

        places = []
        if want_start:
            places.append("Start Menu")
        if want_desktop:
            places.append("Desktop")
        sub = " and ".join(places)
        if want_start:
            sub += " - it may take a few seconds to appear in search"
        self.toast.show_message("Shortcut created", sub, "ok")


def main() -> None:
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ShortcutMaker.App")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass

    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

    font = QFont()
    font.setFamilies(["Segoe UI", "Tahoma"])
    font.setPointSize(10)
    app.setFont(font)
    app.setWindowIcon(make_app_icon())

    win = MainWindow()
    win.show()

    screen = app.primaryScreen()
    if screen is not None:
        geo = screen.availableGeometry()
        win.move(geo.center() - win.rect().center())

    sys.exit(app.exec())


if __name__ == "__main__":
    main()