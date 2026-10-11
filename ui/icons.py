"""Inline SVG icons (stroke style). No emoji anywhere in the UI."""

_P = {
    "star": '<path d="M12 3.2l2.7 5.6 6.1.8-4.5 4.2 1.1 6.1L12 17l-5.4 2.9 1.1-6.1L3.2 9.6l6.1-.8z"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "truck": '<path d="M3 6h11v10H3zM14 9h4l3 3v4h-7z"/><circle cx="7" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/>',
    "shield": '<path d="M12 3l7 3v6c0 4.5-3 7.8-7 9-4-1.2-7-4.5-7-9V6z"/><path d="M8.8 12.2l2.2 2.2 4.2-4.4"/>',
    "lock": '<rect x="5" y="10.5" width="14" height="9.5" rx="2"/><path d="M8 10.5V8a4 4 0 018 0v2.5"/>',
    "spark": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5L18 18M18 6l-2.5 2.5M8.5 15.5L6 18"/>',
    "mountain": '<path d="M3 19l6.5-11 3.5 5.5 2-3L21 19z"/>',
    "gem": '<path d="M6 4h12l3 5-9 11L3 9z"/><path d="M3 9h18M9 4l-2 5 5 11 5-11-2-5"/>',
    "box": '<path d="M3.5 7.5L12 3l8.5 4.5v9L12 21l-8.5-4.5z"/><path d="M3.5 7.5L12 12l8.5-4.5M12 12v9"/>',
    "refund": '<path d="M4 12a8 8 0 108-8H7"/><path d="M7 1v6H1" transform="translate(2 -1)"/>',
    "pin": '<path d="M12 21s6-5.6 6-10.5A6 6 0 006 10.5C6 15.4 12 21 12 21z"/><circle cx="12" cy="10.5" r="2.2"/>',
}


def icon(name: str, size: int = 20, stroke: float = 1.7, cls: str = "") -> str:
    return (f'<svg class="ic {cls}" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_P[name]}</svg>')


def stars(avg: float, count: int | None = None, size: int = 15) -> str:
    """Star rating as inline SVG (filled proportionally)."""
    out = []
    for i in range(1, 6):
        fill = max(0.0, min(1.0, avg - (i - 1)))
        gid = f"g{i}{int(avg * 10)}"
        out.append(f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" aria-hidden="true"><defs><linearGradient id="{gid}">'
                   f'<stop offset="{fill * 100:.0f}%" stop-color="#b8892b"/><stop offset="{fill * 100:.0f}%" stop-color="#e2ddd2"/></linearGradient></defs>'
                   f'<path fill="url(#{gid})" d="{_P["star"].split(chr(34))[1]}"/></svg>')
    label = f'<span class="rtxt">{avg:.1f}' + (f' <span class="muted">({count})</span>' if count is not None else "") + "</span>"
    return f'<span class="stars" aria-label="{avg:.1f} out of 5">{"".join(out)}{label}</span>'
