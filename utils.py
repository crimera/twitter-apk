import os
import shutil
import requests
import subprocess
import sys
from github import get_last_build_version


def panic(message: str):
    print(message, file=sys.stderr)
    exit(1)


def send_message(message: str, token: str, chat_id: str, thread_id: str):
    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"

    data = {
        "parse_mode": "Markdown",
        "disable_web_page_preview": "true",
        "text": message,
        "message_thread_id": thread_id,
        "chat_id": chat_id,
    }

    requests.post(endpoint, data=data)


def report_to_telegram():
    tg_token = os.environ["TG_TOKEN"]
    tg_chat_id = os.environ["TG_CHAT_ID"]
    tg_thread_id = os.environ["TG_THREAD_ID"]
    release = get_last_build_version("crimera/twitter-apk")

    if release is None:
        raise Exception("Could not fetch release")

    downloads = [
        f"[{asset.name}]({asset.browser_download_url})" for asset in release.assets
    ]

    message = f"""
[New Update Released !]({release.html_url})

▼ Downloads ▼

{"\n\n".join(downloads)}
"""

    print(message)

    send_message(message, tg_token, tg_chat_id, tg_thread_id)


def download(link, out, headers=None):
    if os.path.exists(out):
        print(f"{out} already exists skipping download")
        return

    # https://www.slingacademy.com/article/python-requests-module-how-to-download-files-from-urls/#Streaming_Large_Files
    with requests.get(link, stream=True, headers=headers) as r:
        r.raise_for_status()
        with open(out, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def run_command(command: list[str]):
    cmd = subprocess.run(command, capture_output=True, shell=True)

    try:
        cmd.check_returncode()
    except subprocess.CalledProcessError:
        print(cmd.stdout)
        print(cmd.stderr)
        exit(1)


def merge_apk(path: str):
    subprocess.run(
        ["java", "-jar", "./bins/apkeditor.jar", "m", "-i", path]
    ).check_returncode()


def patch_apk(
    cli: str,
    integrations: str,
    patches: str,
    apk: str,
    includes: list[str] | None = None,
    excludes: list[str] | None = None,
    out: str | None = None,
):
    command = [
        "java",
        "-jar",
        cli,
        "patch",
        "-b",
        patches,
        "-m",
        integrations,
        # use j-hc's keystore so we wouldn't need to reinstall
        "--keystore",
        "ks.keystore",
        "--keystore-entry-password",
        "123456789",
        "--keystore-password",
        "123456789",
        "--signer",
        "jhc",
        "--keystore-entry-alias",
        "jhc",
    ]

    if includes is not None:
        for i in includes:
            command.append("-i")
            command.append(i)

    if excludes is not None:
        for e in excludes:
            command.append("-e")
            command.append(e)

    command.append(apk)

    subprocess.run(command).check_returncode()

    # remove -patched from the apk to match out
    if out is not None:
        cli_output = f"{str(apk).removesuffix(".apk")}-patched.apk"
        if os.path.exists(out):
            os.unlink(out)
        shutil.move(cli_output, out)


def publish_release(tag: str, files: list[str], message: str, title = ""):
    key = os.environ.get("GH_TOKEN")
    if key is None:
        raise Exception("GH_TOKEN is not set")

    command = ["gh", "release", "create", "--latest", tag, "--notes", message, "--title", title]

    if len(files) == 0:
        raise Exception("Files should have atleast one item")

    for file in files:
        command.append(file)

    subprocess.run(command, env=os.environ.copy()).check_returncode()
