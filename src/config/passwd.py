import subprocess

import typer


def generate_hashed_password() -> str:
    """Generate hashed password for pitool.yml"""

    password = typer.prompt("Password", hide_input=True)
    confirm = typer.prompt("Confirm password", hide_input=True)

    if password != confirm:
        typer.secho("Passwords don't match", err=True)
        raise typer.Abort()

    salt_result = subprocess.run(
        ["openssl", "rand", "-base64", "6"], capture_output=True, text=True, check=True
    )

    salt = salt_result.stdout.strip()

    hash_result = subprocess.run(
        ["openssl", "passwd", "-6", "-salt", salt, password],
        capture_output=True,
        text=True,
        check=True,
    )

    hashed = hash_result.stdout.strip()

    typer.echo(f"\nHashed password:\n{hashed}")
