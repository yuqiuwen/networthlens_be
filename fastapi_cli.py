from pathlib import Path

import typer

app = typer.Typer()


def snake_to_camel(name: str) -> str:
    return "".join(word.capitalize() for word in name.split("_"))


def create_file(path: Path, content: str = ""):
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        typer.echo(f"Skip: {path}")
        return

    path.write_text(content, encoding="utf-8")
    typer.echo(f"Create: {path}")


@app.command()
def startapp(
    name: str,
    version: str = typer.Option("v1", "-v", "--version"),
):
    """
    Create FastAPI module.
    """

    class_name = snake_to_camel(name)

    files = {
        f"app/models/{name}.py": "",
        f"app/schemas/{name}.py": "",
        f"app/routers/{version}/{name}.py": "",
        f"app/repo/{name}.py": f"""from app.models._mixin import BaseMixin
from app.models.{name} import {class_name}


class {class_name}Repo(BaseMixin[{class_name}]):
    ...


{name}_repo = {class_name}Repo({class_name})
""",
        f"app/services/{name}.py": f"""class {class_name}Service:
    ...
""",
    }

    for file_path, content in files.items():
        create_file(Path(file_path), content)

    typer.echo(f"\n✅ App '{name}' created successfully")


@app.command()
def version():
    """
    Show cli version.
    """
    typer.echo("fastapi-cli 0.1.0")


if __name__ == "__main__":
    app()