"""BFF UI config screen configuration -- review screen layout."""


def get_review_screen_config() -> dict:
    """Return the review screen layout configuration."""
    return {
        "section_order": [
            "transcript",
            "medical_history",
            "summary",
            "insights",
        ],
        "sections": {
            "transcript": {
                "title": "Transcricao",
                "editable": False,
                "visible": True,
            },
            "medical_history": {
                "title": "Historia Clinica",
                "editable": True,
                "visible": True,
            },
            "summary": {
                "title": "Resumo da Consulta",
                "editable": True,
                "visible": True,
            },
            "insights": {
                "title": "Insights",
                "editable": False,
                "visible": True,
            },
        },
    }
