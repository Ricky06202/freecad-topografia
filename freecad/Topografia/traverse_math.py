"""Conversión de rumbo/azimut y distancia a coordenadas topográficas planas.

Azimut desde Norte en sentido horario. Rumbo cuadrantal N/S <ángulo> E/O.
No aplica declinación magnética, convergencia de meridianos o conversión CRS.
"""
import math
import re


def _angle_parts(text):
    raw = str(text).strip().replace(",", ".")
    if not raw or not re.fullmatch(r"""[\d.\s:°º'"′″]+""", raw):
        raise ValueError("Ángulo inválido; usa grados o grados:minutos:segundos")
    numbers = re.findall(r"\d+(?:\.\d+)?", raw)
    if not 1 <= len(numbers) <= 3:
        raise ValueError("Introduce grados, minutos y segundos (máximo 3 partes)")
    values = [float(part) for part in numbers]
    if any(not math.isfinite(n) for n in values):
        raise ValueError("Ángulo no finito")
    if any(n >= 60 for n in values[1:]):
        raise ValueError("Minutos y segundos deben ser menores que 60")
    return values[0] + (values[1] / 60 if len(values) > 1 else 0) + (
        values[2] / 3600 if len(values) > 2 else 0
    )


def direction_to_azimuth(text, mode):
    """Devuelve grados desde Norte. RUMBO admite N45E, S 30° 15' O."""
    mode = str(mode).strip().upper()
    raw = str(text).strip().upper()
    if mode in ("AZIMUT", "AZIMUTH"):
        az = _angle_parts(raw)
        if not 0 <= az <= 360:
            raise ValueError("Azimut debe estar entre 0 y 360°")
        return az % 360
    if mode != "RUMBO":
        raise ValueError("Elige Rumbo o Azimut")
    match = re.fullmatch(r"([NS])\s*(.*?)\s*([EWO])", raw)
    if not match:
        raise ValueError("Rumbo esperado: N 45 E, S 20 O, N 12:30 W")
    ns, raw_angle, ew = match.groups()
    angle = _angle_parts(raw_angle)
    if not 0 <= angle <= 90:
        raise ValueError("Rumbo cuadrantal debe estar entre 0 y 90°")
    east = ew == "E"
    if ns == "N":
        return (angle if east else 360 - angle) % 360
    return 180 - angle if east else 180 + angle


def point_from_tramo(east, north, elevation, direction, mode, distance, delta_z=0):
    """Calcula (E,N,Z) desde un punto de salida y un tramo horizontal."""
    try:
        x, y, z, length, dz = (float(v) for v in (
            east, north, elevation, distance, delta_z
        ))
    except (ValueError, TypeError):
        raise ValueError("Coordenadas, distancia y desnivel deben ser números")
    if not all(math.isfinite(v) for v in (x, y, z, length, dz)):
        raise ValueError("Valores no finitos")
    if length <= 0:
        raise ValueError("La distancia horizontal debe ser mayor que cero")
    az = direction_to_azimuth(direction, mode)
    radians = math.radians(az)
    return (
        x + length * math.sin(radians),
        y + length * math.cos(radians),
        z + dz,
    )
