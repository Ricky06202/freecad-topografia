"""Selección rectangular de puntos proyectados a pantalla.

No decide el orden del polígono: un recuadro selecciona un CONJUNTO.
El recorrido se define después, antes de crear la parcela.
"""


def rectangle_indices(projected, first, last, margin_px=0):
    """Índices de puntos dentro de una ventana rectangular en píxeles.

    projected admite (x, y) o None; first y last son esquinas opuestas.
    El margen amplía un poco la zona de captura para puntos grandes.
    """
    if margin_px < 0:
        raise ValueError("Margen de selección no puede ser negativo")
    x1, y1 = first
    x2, y2 = last
    xmin, xmax = sorted((float(x1), float(x2)))
    ymin, ymax = sorted((float(y1), float(y2)))
    result = []
    for index, xy in enumerate(projected):
        if xy is None:
            continue
        x, y = xy
        if (xmin - margin_px <= x <= xmax + margin_px and
                ymin - margin_px <= y <= ymax + margin_px):
            result.append(index)
    return result


def reorder_indices(indices, ordered):
    """Valida que un usuario reorganice todos y solo los vértices elegidos."""
    indices = list(indices)
    ordered = list(ordered)
    if (len(indices) != len(set(indices)) or
            len(ordered) != len(set(ordered)) or
            len(indices) != len(ordered) or
            set(indices) != set(ordered)):
        raise ValueError("El orden debe incluir los puntos seleccionados una sola vez")
    return ordered


def closest_point_index(projected, pos, radius_px=16):
    """Vértice más cercano al clic (centro proyectado, con tolerancia)."""
    if radius_px <= 0:
        raise ValueError("Radio de captura inválido")
    px, py = float(pos[0]), float(pos[1])
    closest = None
    best_sq = float(radius_px) ** 2
    for i, xy in enumerate(projected):
        if xy is None:
            continue
        dx = float(xy[0]) - px
        dy = float(xy[1]) - py
        distance_sq = dx * dx + dy * dy
        if distance_sq <= best_sq:
            closest, best_sq = i, distance_sq
    return closest
