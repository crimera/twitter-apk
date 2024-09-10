import requests
import re
from utils import download


def download_release_asset(repo: str, regex: str, out_dir: str, filename=None, include_prereleases: bool = True):
    url = f"https://api.github.com/repos/{repo}/releases"

    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Failed to fetch github")

    # Use a list comprehension to filter based on pre-releases and regex
    releases = [r for r in response.json() if (include_prereleases or r["tag_name"].find("release") >= 0)]

    if not releases:
        raise Exception(f"No releases found for {repo}")  # Handle no releases case

    latest_release = sorted(releases, key=lambda r: r["created_at"], reverse=True)[0]

    assets = latest_release["assets"]

    link = None
    for i in assets:
        if re.search(regex, i["name"]):
            link = i["browser_download_url"]
            if filename is None:
                filename = i["name"]
            break

    download(link, f"{out_dir.lstrip('/')}/{filename}")

    return latest_release


def download_apkeditor():
    print("Downloading apkeditor")
    download_release_asset("REAndroid/APKEditor", "APKEditor", "bins", "apkeditor.jar")


def download_revanced_bins():
    print("Downloading cli")
    download_release_asset(
        "inotia00/revanced-cli", "^revanced-cli.*jar$", "bins", "cli.jar"
    )
