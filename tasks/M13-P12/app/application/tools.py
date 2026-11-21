"""Herramienta propia del asistente: consulta de incidencias ficticias.

- Solo lectura: los datos son inmutables (MappingProxyType) y se devuelve una copia
  con los campos permitidos.
- Valida los argumentos antes de leer nada.
"""

import re
from types import MappingProxyType

TICKET_ID_PATTERN = re.compile(r"^SOP-\d{5}$")
ALLOWED_FIELDS = ("ticket_id", "status", "subject", "priority", "opened_at", "updated_at", "next_step")

# Datos ficticios. No hay datos personales.
_TICKETS = MappingProxyType({
    "SOP-10427": MappingProxyType({
        "ticket_id": "SOP-10427",
        "status": "En revisión por el equipo técnico",
        "subject": "Error 403 al entrar a la clase en directo del jueves en CampusNube",
        "priority": "Alta",
        "opened_at": "2026-11-19 18:05",
        "updated_at": "2026-11-20 09:30",
        "next_step": "Se está regenerando el permiso de acceso a la clase. Respuesta prevista antes de 48 h.",
        "internal_note": "No mostrar: nota interna del equipo",
    }),
    "SOP-10388": MappingProxyType({
        "ticket_id": "SOP-10388",
        "status": "Resuelta",
        "subject": "No se descarga el PDF del tema 3",
        "priority": "Media",
        "opened_at": "2026-11-12 10:14",
        "updated_at": "2026-11-13 16:40",
        "next_step": "Ninguno. El PDF se volvió a publicar.",
        "internal_note": "No mostrar: nota interna del equipo",
    }),
})


class ToolError(ValueError):
    """Argumento inválido o recurso inexistente."""


def validate_ticket_id(ticket_id: object) -> str:
    if not isinstance(ticket_id, str):
        raise ToolError("ticket_id debe ser texto")
    normalized = ticket_id.strip().upper().replace(" ", "")
    if not TICKET_ID_PATTERN.fullmatch(normalized):
        raise ToolError(f"Identificador no válido: {ticket_id!r}. Formato esperado: SOP- y cinco cifras")
    return normalized


def get_ticket(ticket_id: object) -> dict:
    """Devuelve el estado de una incidencia. Lanza ToolError si el argumento no es válido."""

    normalized = validate_ticket_id(ticket_id)
    ticket = _TICKETS.get(normalized)
    if ticket is None:
        raise ToolError(f"No existe la incidencia {normalized}")

    return {field: ticket[field] for field in ALLOWED_FIELDS}


TOOLS = {"get_ticket": get_ticket}
