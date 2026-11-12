# -*- coding: utf-8 -*-
"""
Generates the QAxRDP branding from QPainter drawings, so PNG and SVG files always match:
    docs/images/logo.svg, docs/images/logo.png (512 px), docs/images/banner.svg, docs/images/banner.png (1280x640)
    QAxRDP/images/logo.png (256 px, application icon)
    QAxRDP/designer/images/*.png (64 px, Qt Designer widget box icons)
Texts are converted to outlines (QPainterPath.addText), so the SVG files do not depend on installed fonts.
Usage: python tools/branding/makebranding.py   (needs a Qt binding with QtSvg; the Inter font is used if present)
"""
from os.path import abspath, dirname, join, isdir
from os import environ, makedirs
from sys import argv, path

environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = dirname(dirname(dirname(abspath(__file__))))  # type: str
if ROOT not in path:
    path.insert(0, ROOT)

from ManyQt.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QLinearGradient, QRadialGradient, QFont, \
    QImage, QPolygonF, QFontDatabase
from ManyQt.QtCore import Qt, QRectF, QPointF, QSize
from ManyQt.QtWidgets import QApplication
from ManyQt.QtSvg import QSvgGenerator

BLUE = QColor('#3B82F6')  # type: QColor
VIOLET = QColor('#6D28D9')  # type: QColor
CYAN = QColor('#67E8F9')  # type: QColor
NAVY = QColor('#0B1020')  # type: QColor
NAVY2 = QColor('#161C3D')  # type: QColor
WHITE = QColor('#FFFFFF')  # type: QColor
TEXT = QColor('#C9D1E0')  # type: QColor
GREEN = QColor('#43A047')  # type: QColor
FONT_FAMILY = 'Inter'  # type: str


def color(c, alpha):
    """
    :param c: QColor
    :param alpha: (float | int) 0..1
    :return: QColor
    """
    c = QColor(c)  # type: QColor
    c.setAlphaF(alpha)
    return c


def font(size, weight=QFont.Normal):
    """
    :param size: (float | int) pixel size.
    :param weight: int
    :return: QFont
    """
    f = QFont(FONT_FAMILY)  # type: QFont
    f.setPixelSize(int(size))
    f.setWeight(weight)
    return f


def textPath(text, f, x, y):
    """
    Outline of a text (baseline at y), so SVG output does not depend on fonts.
    :param text: str | unicode | QString
    :param f: QFont
    :param x: float | int
    :param y: float | int
    :return: QPainterPath
    """
    p = QPainterPath()  # type: QPainterPath
    p.addText(QPointF(x, y), f, text)
    return p


# ---------- Logo ----------
def drawLogo(p, rect):
    """
    Rounded tile with a monitor, a remote cursor and connection waves.
    :param p: QPainter
    :param rect: QRectF, square.
    :return:
    """
    p.save()
    p.translate(rect.topLeft())
    s = rect.width() / 512.0  # type: float
    p.scale(s, s)
    # Tile.
    tile = QPainterPath()  # type: QPainterPath
    tile.addRoundedRect(QRectF(16, 16, 480, 480), 112, 112)
    g = QLinearGradient(QPointF(16, 16), QPointF(496, 496))  # type: QLinearGradient
    g.setColorAt(0.0, BLUE)
    g.setColorAt(1.0, VIOLET)
    p.fillPath(tile, QBrush(g))
    sheen = QLinearGradient(QPointF(0, 16), QPointF(0, 300))  # type: QLinearGradient
    sheen.setColorAt(0.0, color(WHITE, 0.22))
    sheen.setColorAt(1.0, color(WHITE, 0.0))
    p.fillPath(tile, QBrush(sheen))
    # Monitor.
    p.setPen(Qt.NoPen)
    p.setBrush(WHITE)
    p.drawRoundedRect(QRectF(236, 340, 40, 50), 4, 4)
    p.drawRoundedRect(QRectF(170, 380, 172, 28), 14, 14)
    pen = QPen(WHITE, 26)  # type: QPen
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(color(NAVY, 0.30))
    p.drawRoundedRect(QRectF(92, 116, 328, 228), 30, 30)
    # Connection waves from the cursor tip.
    tip = QPointF(236, 196)  # type: QPointF
    wave = QPen(CYAN, 14)  # type: QPen
    wave.setCapStyle(Qt.RoundCap)
    p.setPen(wave)
    p.setBrush(Qt.NoBrush)
    for r in (30, 56):
        p.drawArc(QRectF(tip.x() - r, tip.y() - r, 2 * r, 2 * r), 105 * 16, 60 * 16)
    # Cursor.
    arrow = QPolygonF([QPointF(0, 0), QPointF(0, 104), QPointF(27, 80), QPointF(46, 120), QPointF(66, 111),
                       QPointF(47, 73), QPointF(84, 73)])  # type: QPolygonF
    arrow.translate(tip)
    shadow = QPolygonF(arrow)  # type: QPolygonF
    shadow.translate(6, 8)
    p.setPen(Qt.NoPen)
    p.setBrush(color(NAVY, 0.35))
    p.drawPolygon(shadow)
    outline = QPen(VIOLET.darker(130), 8)  # type: QPen
    outline.setJoinStyle(Qt.RoundJoin)
    p.setPen(outline)
    p.setBrush(WHITE)
    p.drawPolygon(arrow)
    p.restore()


# ---------- Banner ----------
def drawBanner(p, w, h):
    """
    1280x640 banner (GitHub social preview size).
    :param p: QPainter
    :param w: int
    :param h: int
    :return:
    """
    bg = QLinearGradient(QPointF(0, 0), QPointF(w, h))  # type: QLinearGradient
    bg.setColorAt(0.0, NAVY)
    bg.setColorAt(1.0, NAVY2)
    p.fillRect(QRectF(0, 0, w, h), QBrush(bg))
    # Dotted grid.
    p.setPen(Qt.NoPen)
    p.setBrush(color(WHITE, 0.05))
    for gx in range(20, w, 40):
        for gy in range(20, h, 40):
            p.drawEllipse(QPointF(gx, gy), 1.6, 1.6)
    # Glows behind the logo.
    for center, c, radius in ((QPointF(246, 310), BLUE, 330), (QPointF(356, 430), VIOLET, 300)):
        glow = QRadialGradient(center, radius)  # type: QRadialGradient
        glow.setColorAt(0.0, color(c, 0.38))
        glow.setColorAt(1.0, color(c, 0.0))
        p.fillRect(QRectF(0, 0, w, h), QBrush(glow))
    drawLogo(p, QRectF(96, 170, 300, 300))
    # Word mark: "QAx" white, "RDP" gradient.
    left = 456.0  # type: float
    title = font(132, QFont.Black)  # type: QFont
    qax = textPath('QAx', title, left - 4, 330)  # type: QPainterPath
    rdp = textPath('RDP', title, qax.boundingRect().right() + 6, 330)  # type: QPainterPath
    p.setBrush(WHITE)
    p.drawPath(qax)
    g = QLinearGradient(rdp.boundingRect().topLeft(), rdp.boundingRect().bottomRight())  # type: QLinearGradient
    g.setColorAt(0.0, QColor('#60A5FA'))
    g.setColorAt(1.0, QColor('#A78BFA'))
    p.setBrush(QBrush(g))
    p.drawPath(rdp)
    # Tag lines.
    p.setBrush(TEXT)
    p.drawPath(textPath('Microsoft Remote Desktop, embedded in Qt', font(34, QFont.Medium), left + 4, 404))
    # Accent line.
    line = QLinearGradient(QPointF(0, 0), QPointF(w, 0))  # type: QLinearGradient
    line.setColorAt(0.0, BLUE)
    line.setColorAt(1.0, VIOLET)
    p.fillRect(QRectF(0, h - 8, w, 8), QBrush(line))


# ---------- Designer icons ----------
def drawConnectionBarIcon(p, rect):
    """
    :param p: QPainter
    :param rect: QRectF
    :return:
    """
    p.save()
    p.translate(rect.topLeft())
    s = rect.width() / 64.0  # type: float
    p.scale(s, s)
    bar = QLinearGradient(QPointF(0, 18), QPointF(64, 46))  # type: QLinearGradient
    bar.setColorAt(0.0, BLUE)
    bar.setColorAt(1.0, VIOLET)
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(bar))
    p.drawRoundedRect(QRectF(2, 18, 60, 28), 7, 7)
    p.setBrush(WHITE)
    p.drawRoundedRect(QRectF(7, 25, 20, 14), 3, 3)
    p.drawRoundedRect(QRectF(30, 25, 13, 14), 3, 3)
    p.setBrush(GREEN)
    p.setPen(QPen(WHITE, 2))
    p.drawEllipse(QPointF(53, 32), 5, 5)
    p.restore()


def drawStatusDotIcon(p, rect):
    """
    :param p: QPainter
    :param rect: QRectF
    :return:
    """
    c = rect.center()  # type: QPointF
    r = rect.width() / 2.0  # type: float
    halo = QRadialGradient(c, r)  # type: QRadialGradient
    halo.setColorAt(0.45, color(GREEN, 0.45))
    halo.setColorAt(1.0, color(GREEN, 0.0))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(halo))
    p.drawEllipse(c, r, r)
    dot = QRadialGradient(QPointF(c.x() - r * 0.15, c.y() - r * 0.15), r * 0.55)  # type: QRadialGradient
    dot.setColorAt(0.0, GREEN.lighter(150))
    dot.setColorAt(1.0, GREEN)
    p.setBrush(QBrush(dot))
    p.drawEllipse(c, r * 0.45, r * 0.45)


# ---------- Output ----------
def render(draw, size, pngPaths=(), svgPath=None, title=''):
    """
    Renders a drawing into PNG files and optionally an SVG file.
    :param draw: callable(QPainter, float w, float h)
    :param size: QSize, logical size.
    :param pngPaths: list[tuple[str, int]] (path, width in px)
    :param svgPath: str | None
    :param title: str | unicode | QString
    :return:
    """
    for pngPath, width in pngPaths:
        scale = width / float(size.width())  # type: float
        img = QImage(int(round(size.width() * scale)), int(round(size.height() * scale)),
                     QImage.Format_ARGB32_Premultiplied)  # type: QImage
        img.fill(Qt.transparent)
        p = QPainter(img)  # type: QPainter
        p.setRenderHint(QPainter.Antialiasing, True)
        p.scale(scale, scale)
        draw(p, size.width(), size.height())
        p.end()
        img.save(pngPath)
        print('wrote', pngPath)
    if svgPath:
        gen = QSvgGenerator()  # type: QSvgGenerator
        gen.setFileName(svgPath)
        gen.setSize(size)
        gen.setViewBox(QRectF(0, 0, size.width(), size.height()))
        gen.setTitle(title)
        gen.setDescription('QAxRDP - generated by tools/branding/makebranding.py')
        p = QPainter(gen)  # type: QPainter
        p.setRenderHint(QPainter.Antialiasing, True)
        draw(p, size.width(), size.height())
        p.end()
        print('wrote', svgPath)


def ensureDir(d):
    """
    :param d: str | unicode | QString
    :return: str | unicode | QString
    """
    if not isdir(d):
        makedirs(d)
    return d


def main():
    """
    :return:
    """
    global FONT_FAMILY
    app = QApplication.instance() or QApplication(argv)  # type: QApplication
    if FONT_FAMILY not in QFontDatabase().families():
        FONT_FAMILY = app.font().family()  # type: str
        print('Inter not installed, using', FONT_FAMILY)
    docs = ensureDir(join(ROOT, 'docs', 'images'))  # type: str
    pkg = ensureDir(join(ROOT, 'QAxRDP', 'images'))  # type: str
    designer = ensureDir(join(ROOT, 'QAxRDP', 'designer', 'images'))  # type: str
    logo = lambda p, w, h: drawLogo(p, QRectF(0, 0, w, h))
    render(logo, QSize(512, 512), [(join(docs, 'logo.png'), 512), (join(pkg, 'logo.png'), 256),
                                   (join(designer, 'remotedesktopwidget.png'), 64)],
           join(docs, 'logo.svg'), 'QAxRDP logo')
    render(drawBanner, QSize(1280, 640), [(join(docs, 'banner.png'), 1280)], join(docs, 'banner.svg'),
           'QAxRDP banner')
    render(lambda p, w, h: drawConnectionBarIcon(p, QRectF(0, 0, w, h)), QSize(64, 64),
           [(join(designer, 'connectionbar.png'), 64)])
    render(lambda p, w, h: drawStatusDotIcon(p, QRectF(0, 0, w, h)), QSize(64, 64),
           [(join(designer, 'statusdot.png'), 64)])


if __name__ == '__main__':
    main()
