"""
Modern Dark Glassmorphism Design System & Stylesheet for Second Brain AI Companion.
"""

DARK_GLASS_STYLE = """
/* Global Window */
QWidget#MainContainer {
    background: rgba(18, 20, 29, 0.94);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
}

/* Header */
QWidget#HeaderBar {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(30, 34, 48, 0.95),
        stop:1 rgba(24, 27, 39, 0.95));
    border-top-left-radius: 16px;
    border-top-right-radius: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

QLabel#HeaderTitle {
    color: #F8FAFC;
    font-weight: 700;
    font-size: 13.5px;
    letter-spacing: 0.3px;
}

QLabel#HeaderSubtitle {
    color: #94A3B8;
    font-size: 11px;
}

/* Window Control Buttons */
QPushButton.HeaderBtn {
    background: transparent;
    color: #94A3B8;
    border: none;
    border-radius: 8px;
    padding: 4px;
    font-size: 12px;
}

QPushButton.HeaderBtn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: #F8FAFC;
}

QPushButton.HeaderBtn#CloseBtn:hover {
    background: rgba(239, 68, 68, 0.25);
    color: #F87171;
}

/* Quick Action Pills */
QPushButton.ActionPill {
    background: rgba(30, 41, 59, 0.7);
    color: #CBD5E1;
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 12px;
    padding: 5px 10px;
    font-size: 11.5px;
    font-weight: 500;
}

QPushButton.ActionPill:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(99, 102, 241, 0.4),
        stop:1 rgba(139, 92, 246, 0.4));
    color: #FFFFFF;
    border-color: rgba(167, 139, 250, 0.5);
}

/* Message Scroll Area */
QScrollArea#ChatScrollArea {
    background: transparent;
    border: none;
}

QWidget#ChatContentWidget {
    background: transparent;
}

/* ScrollBar */
QScrollBar:vertical {
    border: none;
    background: rgba(15, 23, 42, 0.3);
    width: 6px;
    border-radius: 3px;
    margin: 4px 1px 4px 1px;
}

QScrollBar::handle:vertical {
    background: rgba(148, 163, 184, 0.25);
    border-radius: 3px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(148, 163, 184, 0.5);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
    height: 0px;
}

/* Input Area */
QWidget#InputContainer {
    background: rgba(24, 28, 42, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    margin: 4px 10px 10px 10px;
}

QTextEdit#PromptInput {
    background: transparent;
    border: none;
    color: #F1F5F9;
    font-size: 13px;
    padding: 6px 8px;
    line-height: 1.4;
}

QPushButton#SendBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #6366F1,
        stop:1 #8B5CF6);
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 6px 12px;
    font-weight: 600;
    font-size: 12.5px;
}

QPushButton#SendBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #4F46E5,
        stop:1 #7C3AED);
}

QPushButton#SendBtn:disabled {
    background: rgba(71, 85, 105, 0.5);
    color: #94A3B8;
}

/* Tool execution status badge */
QWidget.ToolBadge {
    background: rgba(15, 23, 42, 0.85);
    border-left: 3px solid #8B5CF6;
    border-radius: 6px;
    padding: 6px 10px;
    margin: 2px 0px;
}

QLabel.ToolBadgeText {
    color: #C084FC;
    font-size: 11.5px;
    font-family: monospace;
}

/* Resize Grip */
QSizeGrip {
    image: none;
    width: 14px;
    height: 14px;
    background: transparent;
}

/* Thinking & Tool Process Accordion */
QFrame#ThinkingAccordion {
    background: rgba(20, 24, 38, 0.85);
    border: 1px solid rgba(139, 92, 246, 0.25);
    border-radius: 10px;
    margin: 4px 0px;
}

QFrame#ThinkingAccordion:hover {
    border-color: rgba(167, 139, 250, 0.45);
}

QWidget#ThinkingHeader {
    background: rgba(30, 37, 56, 0.6);
    border-top-left-radius: 9px;
    border-top-right-radius: 9px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

QLabel#ThinkingTitle {
    color: #C4B5FD;
    font-size: 11.5px;
    font-weight: 600;
}

QLabel#ThinkingBadge {
    color: #94A3B8;
    font-size: 10.5px;
    background: rgba(15, 23, 42, 0.6);
    border-radius: 4px;
    padding: 2px 6px;
}

QPushButton#ThinkingToggleBtn {
    background: transparent;
    border: none;
    color: #A78BFA;
    font-size: 11px;
    font-weight: 700;
    padding: 2px;
}

QPushButton#ThinkingToggleBtn:hover {
    color: #DDD6FE;
}

QFrame#ThinkingStepCard {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-left: 3px solid #8B5CF6;
    border-radius: 6px;
    margin: 2px 0px;
    padding: 4px 6px;
}

QTextEdit.CodeBox {
    background: #0B0F19;
    color: #38BDF8;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 4px;
    font-family: 'JetBrains Mono', 'Fira Code', 'DejaVu Sans Mono', monospace;
    font-size: 11px;
    padding: 4px;
}
"""

