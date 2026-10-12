import re
import shutil
import subprocess
import tempfile

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


# ------------------------------------------------------------
# Helper
# ------------------------------------------------------------

def run(command, cwd=None, capture=False, check=True):
    result = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        text=True,
        capture_output=capture
    )

    if check and result.returncode != 0:
        error = result.stderr.strip() if capture else command
        raise RuntimeError(error)

    if capture:
        return result.stdout.strip()

    return result


# ------------------------------------------------------------
# Checks
# ------------------------------------------------------------

def check_tools():
    run("git --version")
    run("gh --version")
    run("gh auth status")


# ------------------------------------------------------------
# Username
# ------------------------------------------------------------

def get_username():
    return run(
        "gh api user --jq .login",
        capture=True
    )


# ------------------------------------------------------------
# Repo name
# ------------------------------------------------------------

def extract_repo_name(url):

    m = re.search(r"/([^/]+?)(?:\.git)?$", url)

    if not m:
        raise RuntimeError("Invalid GitHub URL.")

    return m.group(1)


# ------------------------------------------------------------
# Find available backup name
# ------------------------------------------------------------

def get_available_name(base_name):

    username = get_username()

    number = 1

    while True:

        if number == 1:
            candidate = base_name + "-backup"
        else:
            candidate = f"{base_name}-backup-{number}"

        result = subprocess.run(
            f"gh repo view {username}/{candidate}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if result.returncode != 0:
            return candidate

        number += 1


# ------------------------------------------------------------
# Main Backup
# ------------------------------------------------------------

def backup_repository(repo_url):

    check_tools()

    username = get_username()

    repo_name = extract_repo_name(repo_url)

    backup_name = get_available_name(repo_name)

    temp_dir = tempfile.mkdtemp()

    progress = Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        console=console,
    )

    try:

        with progress:

            task = progress.add_task("Cloning repository...", total=None)

            run(
                f'git clone "{repo_url}" "{temp_dir}"'
            )

            progress.update(
                task,
                description="Creating GitHub repository..."
            )

            run(
                f'gh repo create "{backup_name}" --private'
            )

            progress.update(
                task,
                description="Fetching LFS objects..."
            )

            lfs_result = run(
                "git lfs fetch --all",
                cwd=temp_dir,
                check=False
            )

            if lfs_result.returncode != 0:
                console.print(
                    "[yellow]Warning: Some LFS objects could not be fetched. "
                    "Continuing with backup.[/yellow]"
                )

            progress.update(
                task,
                description="Removing original remote..."
            )

            run(
                "git remote remove origin",
                cwd=temp_dir
            )

            progress.update(
                task,
                description="Adding new remote..."
            )

            new_remote = (
                f"https://github.com/{username}/{backup_name}.git"
            )

            run(
                f'git remote add origin "{new_remote}"',
                cwd=temp_dir
            )

            progress.update(
                task,
                description="Uploading branches..."
            )

            run(
                "git config lfs.allowincompletepush true",
                cwd=temp_dir
            )

            run(
                "git push -u origin --all",
                cwd=temp_dir
            )

            progress.update(
                task,
                description="Uploading tags..."
            )

            run(
                "git push origin --tags",
                cwd=temp_dir
            )

            run(
                "git lfs push --all origin",
                cwd=temp_dir,
                check=False
            )

            progress.update(
                task,
                description="Cleaning temporary files..."
            )

        shutil.rmtree(
            temp_dir,
            ignore_errors=True
        )

        console.print()

        console.print(
            "[bold green]✓ Backup completed successfully![/bold green]"
        )

        console.print()

        console.print(
            f"https://github.com/{username}/{backup_name}"
        )

    except Exception:

        shutil.rmtree(
            temp_dir,
            ignore_errors=True
        )

        raise
