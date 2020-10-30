project = {
    ".": {
        "is_public": True,
        "corner_cases": []
    },
    "pipelines": {
        "is_public": True,
        "corner_cases": []
    },
    "utils": {
        "is_public": True,
        "corner_cases": []
    },
    "extractors": {
        "is_public": True,
        "corner_cases": []
    },
    "models": {
        "is_public": True,
        "corner_cases": [
            {
                "script": "registry.py",
                "target": "def __get_registry_template"
            }
        ]
    },
    "tables": {
        "is_public": False,
        "corner_cases": []
    },
    "registries": {
        "is_public": False,
        "corner_cases": []
    }
}
