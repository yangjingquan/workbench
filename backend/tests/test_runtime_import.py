import importlib


def test_fastapi_application_imports_on_supported_python():
    module = importlib.import_module("app.main")
    assert module.app.title == "Dev Workbench API"
