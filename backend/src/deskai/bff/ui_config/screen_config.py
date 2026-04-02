"""BFF UI config screen configuration -- review screen and consultation list."""


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


def get_consultation_list_config() -> dict:
    """Return default configuration for the consultation list screen."""
    return {
        "page_size": 20,
        "default_sort": "created_at_desc",
        "default_status_filter": "all",
    }
