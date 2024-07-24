import requests
import re
from utils import download


def get_last_release_assets(repo_url: str) -> list:
    url = f"https://api.github.com/repos/{repo_url}/releases/latest"

    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Failed to fetch github")

    return response.json()["assets"]


def download_release_asset(repo: str, regex: str, out_dir: str, filename=None):
    assets = get_last_release_assets(repo)

    link = None
    for i in assets:
        if re.search(regex, i["name"]):
            link = i["browser_download_url"]
            if filename is None:
                filename = i["name"]
            break

    download(link, f"{out_dir.lstrip("/")}/{filename}")


def download_apkeditor():
    print("Downloading apkeditor")
    download_release_asset(
        "REAndroid/APKEditor", "APKEditor", "bins", "apkeditor.jar"
    )


def download_revanced_bins():
    print("Downloading cli")
    download_release_asset(
        "inotia00/revanced-cli", "^revanced-cli.*jar$", "bins", "cli.jar"
    )

    print("Downloading patches")
    download_release_asset("crimera/piko", "^piko.*jar$", "bins", "patches.jar")

    print("Downloading integrations")
    download_release_asset(
        "crimera/revanced-integrations",
        "^rev.*apk$",
        "bins",
        "integrations.apk",
    )


if __name__ == "__main__":
    download_apkeditor()
    download_revanced_bins()
