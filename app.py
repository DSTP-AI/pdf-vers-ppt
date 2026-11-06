"""PDF vers PPT - interface graphique (Mac / Windows).

Glissez un ou plusieurs PDF dans la fenêtre (ou sur l'icône de l'app sous Mac,
ou sur le .exe sous Windows). Chaque page devient une diapositive image en
qualité maximale (600 dpi, PNG sans perte). Le .pptx est enregistré à côté du PDF.
"""
import os
import subprocess
import sys

from PySide6.QtCore import QEvent, QPointF, QRectF, Qt, QThread, QTimer, Signal
from PySide6.QtGui import (QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath,
                           QPen, QPixmap, QRadialGradient)
from PySide6.QtWidgets import (QApplication, QFileDialog, QGraphicsDropShadowEffect,
                               QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget)

from converter import convert

APP_NAME = "PDF vers PPT"


def resource(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", name)


def is_pdf(path):
    return path.lower().endswith(".pdf") and os.path.isfile(path)


def reveal(path):
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", "-R", path])
        elif os.name == "nt":
            subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
        else:
            subprocess.Popen(["xdg-open", os.path.dirname(path)])
    except Exception:  # noqa: BLE001
        pass


class Worker(QThread):
    progress = Signal(int, int, str)        # page, total, nom
    file_done = Signal(str, str)            # pdf, pptx
    file_error = Signal(str, str)           # pdf, message

    def __init__(self, files):
        super().__init__()
        self.files = files

    def run(self):
        for src in self.files:
            name = os.path.basename(src)
            try:
                out = convert(src, progress=lambda i, n, name=name: self.progress.emit(i, n, name))
                self.file_done.emit(src, out)
            except Exception as e:  # noqa: BLE001
                self.file_error.emit(src, str(e))


class DropCard(QWidget):
    """Carte en verre dépoli : zone où déposer les PDF."""
    clicked = Signal()

    def __init__(self):
        super().__init__()
        self.hover = False
        self.setMinimumSize(420, 300)
        self.setCursor(Qt.PointingHandCursor)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(60)
        shadow.setOffset(0, 18)
        shadow.setColor(QColor(120, 40, 0, 70))
        self.setGraphicsEffect(shadow)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 36, 32, 30)
        lay.setSpacing(10)
        self.icon = QLabel(alignment=Qt.AlignCenter)
        pm = QPixmap(resource("icon.png"))
        if not pm.isNull():
            self.icon.setPixmap(pm.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.title = QLabel("Déposez vos PDF ici", alignment=Qt.AlignCenter)
        self.title.setObjectName("title")
        self.sub = QLabel("ou cliquez pour choisir un fichier", alignment=Qt.AlignCenter)
        self.sub.setObjectName("sub")
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)
        self.bar.hide()
        self.status = QLabel("", alignment=Qt.AlignCenter)
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        self.btn = QPushButton("Afficher le PowerPoint")
        self.btn.setObjectName("reveal")
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.hide()
        lay.addStretch(1)
        lay.addWidget(self.icon)
        lay.addSpacing(6)
        lay.addWidget(self.title)
        lay.addWidget(self.sub)
        lay.addSpacing(8)
        lay.addWidget(self.bar)
        lay.addWidget(self.status)
        lay.addWidget(self.btn, alignment=Qt.AlignCenter)
        lay.addStretch(1)

    def set_hover(self, on):
        self.hover = on
        self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and not self.btn.underMouse():
            self.clicked.emit()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(r, 30, 30)
        # verre : blanc translucide + reflet en haut
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        a = 150 if self.hover else 105
        g.setColorAt(0, QColor(255, 255, 255, a + 60))
        g.setColorAt(0.5, QColor(255, 255, 255, a))
        g.setColorAt(1, QColor(255, 255, 255, a - 25))
        p.fillPath(path, g)
        # liseré lumineux
        rim = QLinearGradient(r.topLeft(), r.bottomRight())
        rim.setColorAt(0, QColor(255, 255, 255, 230))
        rim.setColorAt(0.5, QColor(255, 255, 255, 90))
        rim.setColorAt(1, QColor(255, 255, 255, 170))
        p.setPen(QPen(rim, 1.6))
        p.drawPath(path)
        if self.hover:
            inner = QPainterPath()
            inner.addRoundedRect(r.adjusted(14, 14, -14, -14), 22, 22)
            pen = QPen(QColor(232, 86, 30, 200), 2, Qt.DashLine)
            pen.setDashPattern([6, 5])
            p.setPen(pen)
            p.drawPath(inner)


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon(resource("icon.png")))
        self.resize(560, 460)
        self.setMinimumSize(480, 400)
        self.setAcceptDrops(True)
        self.queue, self.done, self.errors = [], [], []
        self.worker = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(34, 34, 34, 22)
        self.card = DropCard()
        self.card.clicked.connect(self.choose)
        self.card.btn.clicked.connect(self.reveal_last)
        lay.addWidget(self.card, 1)
        foot = QLabel("Qualité maximale · 600 dpi · images sans perte · enregistré à côté du PDF",
                      alignment=Qt.AlignCenter)
        foot.setObjectName("foot")
        lay.addSpacing(12)
        lay.addWidget(foot)

        self.setStyleSheet("""
            QLabel { background: transparent; color: #2b1a10; }
            QLabel#title { font-size: 24px; font-weight: 700; color: #2b1408; }
            QLabel#sub { font-size: 14px; color: rgba(60,30,10,0.65); }
            QLabel#status { font-size: 13px; color: #3a2010; }
            QLabel#foot { font-size: 11px; color: rgba(255,255,255,0.92); }
            QProgressBar { background: rgba(255,255,255,0.55); border: none; border-radius: 4px; }
            QProgressBar::chunk { border-radius: 4px;
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #ff9a3c, stop:1 #e4481a); }
            QPushButton#reveal { background: rgba(255,255,255,0.75); color: #c2410c;
                border: 1px solid rgba(255,255,255,0.95); border-radius: 14px;
                padding: 7px 18px; font-size: 13px; font-weight: 600; }
            QPushButton#reveal:hover { background: rgba(255,255,255,0.95); }
        """)

    # --- fond "liquide" : dégradé orange avec bulles de lumière
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect())
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, QColor("#ffb062"))
        g.setColorAt(0.55, QColor("#f2702b"))
        g.setColorAt(1, QColor("#d8431c"))
        p.fillRect(r, g)
        for cx, cy, rad, col in ((0.15, 0.12, 0.55, QColor(255, 236, 200, 150)),
                                 (0.95, 0.85, 0.60, QColor(255, 90, 120, 90)),
                                 (0.85, 0.10, 0.40, QColor(255, 255, 255, 70))):
            rg = QRadialGradient(QPointF(r.width() * cx, r.height() * cy), max(r.width(), r.height()) * rad)
            rg.setColorAt(0, col)
            c2 = QColor(col); c2.setAlpha(0)
            rg.setColorAt(1, c2)
            p.fillRect(r, rg)

    # --- glisser-déposer
    def dragEnterEvent(self, e):
        if any(is_pdf(u.toLocalFile()) for u in e.mimeData().urls()):
            e.acceptProposedAction()
            self.card.set_hover(True)

    def dragLeaveEvent(self, _):
        self.card.set_hover(False)

    def dropEvent(self, e):
        self.card.set_hover(False)
        self.add_files([u.toLocalFile() for u in e.mimeData().urls()])

    def choose(self):
        if self.worker:
            return
        paths, _ = QFileDialog.getOpenFileNames(self, "Choisir des PDF", os.path.expanduser("~"),
                                                "PDF (*.pdf *.PDF)")
        self.add_files(paths)

    def add_files(self, paths):
        pdfs = [p for p in paths if is_pdf(p)]
        if not pdfs:
            return
        self.queue.extend(pdfs)
        if not self.worker:
            self.done, self.errors = [], []
            self.start()

    def start(self):
        files, self.queue = self.queue, []
        self.card.btn.hide()
        self.card.bar.show()
        self.card.bar.setValue(0)
        self.card.title.setText("Conversion en cours…")
        self.card.sub.setText(f"{len(files)} fichier(s)" if len(files) > 1 else os.path.basename(files[0]))
        self.worker = Worker(files)
        self.worker.progress.connect(self.on_progress)
        self.worker.file_done.connect(lambda s, o: self.done.append(o))
        self.worker.file_error.connect(lambda s, m: self.errors.append(f"{os.path.basename(s)} : {m}"))
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_progress(self, i, n, name):
        self.card.bar.setMaximum(n)
        self.card.bar.setValue(i)
        self.card.status.setText(f"{name} — page {i} sur {n}")

    def on_finished(self):
        self.worker = None
        if self.queue:
            self.start()
            return
        self.card.bar.hide()
        if self.done:
            self.card.title.setText("C'est prêt ✓")
            names = ", ".join(os.path.basename(p) for p in self.done[:3])
            more = f" (+{len(self.done) - 3})" if len(self.done) > 3 else ""
            self.card.sub.setText(f"{names}{more}")
            self.card.status.setText("Enregistré à côté du PDF. Déposez d'autres PDF pour continuer.")
            self.card.btn.show()
        else:
            self.card.title.setText("Déposez vos PDF ici")
            self.card.sub.setText("ou cliquez pour choisir un fichier")
            self.card.status.setText("")
        if self.errors:
            self.card.status.setText("Erreur : " + " / ".join(self.errors))

    def reveal_last(self):
        if self.done:
            reveal(self.done[-1])


class App(QApplication):
    """Reçoit aussi les PDF déposés sur l'icône de l'app (Dock / Finder sous Mac)."""

    def __init__(self, argv):
        super().__init__(argv)
        self.window = None
        self.pending = []

    def event(self, e):
        if e.type() == QEvent.FileOpen:
            path = e.file()
            if self.window:
                self.window.add_files([path])
            else:
                self.pending.append(path)
            return True
        return super().event(e)


def main():
    # Mode ligne de commande : app fichier.pdf [...] --cli
    args = [a for a in sys.argv[1:] if not a.startswith("-psn")]
    if "--cli" in args:
        for a in args:
            if is_pdf(a):
                print(convert(a))
        return
    app = App(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setFont(QFont("SF Pro Text" if sys.platform == "darwin" else "Segoe UI", 13))
    app.setWindowIcon(QIcon(resource("icon.png")))
    win = Window()
    app.window = win
    win.show()
    # PDF glissés sur le .exe (Windows) ou sur l'icône (Mac)
    files = [a for a in args if is_pdf(a)] + app.pending
    if files:
        QTimer.singleShot(200, lambda: win.add_files(files))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
