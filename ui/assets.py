"""
Vector and Dynamic Asset Generator for Second Brain AI Companion.
Generates cute mascot avatars and icons dynamically with QPainter & QPixmap.
"""

from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QBrush, QPen, QRadialGradient,
    QLinearGradient, QPainterPath, QFont
)
from PyQt6.QtCore import Qt, QRectF, QPointF

def create_cute_mascot_pixmap(size: int = 128, mood: str = "happy", glow: bool = True) -> QPixmap:
    """Generates a high-res cute kawaii brain/bot mascot pixmap."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    center = size / 2.0
    radius = size * 0.42

    # Outer soft neon glow
    if glow:
        glow_grad = QRadialGradient(center, center, size * 0.48)
        glow_grad.setColorAt(0.0, QColor(139, 92, 246, 120))  # Purple/Violet
        glow_grad.setColorAt(0.7, QColor(59, 130, 246, 60))   # Blue
        glow_grad.setColorAt(1.0, QColor(16, 185, 129, 0))    # Transparent
        painter.setBrush(QBrush(glow_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(size * 0.02, size * 0.02, size * 0.96, size * 0.96))

    # Main mascot body gradient (Cute Glassy Sphere)
    body_grad = QLinearGradient(center - radius, center - radius, center + radius, center + radius)
    body_grad.setColorAt(0.0, QColor(167, 139, 250))  # Violet 400
    body_grad.setColorAt(0.5, QColor(99, 102, 241))   # Indigo 500
    body_grad.setColorAt(1.0, QColor(59, 130, 246))   # Blue 500

    body_rect = QRectF(center - radius, center - radius, radius * 2, radius * 2)
    painter.setBrush(QBrush(body_grad))
    painter.setPen(QPen(QColor(255, 255, 255, 80), max(1.5, size * 0.02)))
    painter.drawEllipse(body_rect)

    # Brain lobes / Chibi hair curve highlight on top
    highlight_path = QPainterPath()
    highlight_path.moveTo(center - radius * 0.6, center - radius * 0.3)
    highlight_path.cubicTo(
        center - radius * 0.3, center - radius * 0.9,
        center + radius * 0.3, center - radius * 0.9,
        center + radius * 0.6, center - radius * 0.3
    )
    highlight_pen = QPen(QColor(255, 255, 255, 160), max(2.0, size * 0.04))
    highlight_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(highlight_pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPath(highlight_path)

    # Eyes
    eye_y = center - radius * 0.05
    eye_dx = radius * 0.35
    eye_w = radius * 0.22
    eye_h = radius * 0.26

    # Left eye
    painter.setBrush(QBrush(QColor(15, 23, 42)))  # Deep slate
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(QRectF(center - eye_dx - eye_w/2, eye_y - eye_h/2, eye_w, eye_h))
    # Right eye
    painter.drawEllipse(QRectF(center + eye_dx - eye_w/2, eye_y - eye_h/2, eye_w, eye_h))

    # Eye sparkles (Cute anime reflections)
    sparkle_r1 = eye_w * 0.38
    sparkle_r2 = eye_w * 0.2
    painter.setBrush(QBrush(QColor(255, 255, 255)))
    painter.drawEllipse(QRectF(center - eye_dx - eye_w/4, eye_y - eye_h/3, sparkle_r1, sparkle_r1))
    painter.drawEllipse(QRectF(center + eye_dx - eye_w/4, eye_y - eye_h/3, sparkle_r1, sparkle_r1))

    painter.drawEllipse(QRectF(center - eye_dx + eye_w/8, eye_y + eye_h/6, sparkle_r2, sparkle_r2))
    painter.drawEllipse(QRectF(center + eye_dx + eye_w/8, eye_y + eye_h/6, sparkle_r2, sparkle_r2))

    # Cute rosy blush cheeks
    blush_y = eye_y + eye_h * 0.7
    blush_dx = radius * 0.52
    blush_w = radius * 0.25
    blush_h = radius * 0.14
    painter.setBrush(QBrush(QColor(244, 114, 182, 180)))  # Pink-400
    painter.drawEllipse(QRectF(center - blush_dx - blush_w/2, blush_y, blush_w, blush_h))
    painter.drawEllipse(QRectF(center + blush_dx - blush_w/2, blush_y, blush_w, blush_h))

    # Cute smile mouth
    mouth_path = QPainterPath()
    mouth_y = center + radius * 0.25
    mouth_path.moveTo(center - radius * 0.16, mouth_y)
    mouth_path.quadTo(center, mouth_y + radius * 0.18, center + radius * 0.16, mouth_y)
    mouth_pen = QPen(QColor(15, 23, 42), max(2.0, size * 0.035))
    mouth_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(mouth_pen)
    painter.drawPath(mouth_path)

    # Antenna / Sparkle on head
    spark_pen = QPen(QColor(251, 191, 36), max(2.0, size * 0.03))  # Amber/Gold
    spark_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(spark_pen)
    top_y = center - radius * 0.95
    painter.drawLine(QPointF(center, top_y - size*0.06), QPointF(center, top_y + size*0.02))
    painter.drawLine(QPointF(center - size*0.04, top_y - size*0.02), QPointF(center + size*0.04, top_y - size*0.02))

    painter.end()
    return pixmap
