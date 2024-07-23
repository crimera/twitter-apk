import requests
import re


def get_last_release_assets(repo_url: str) -> list | None:
    url = f"https://api.github.com/repos/{repo_url}/releases/latest"

    response = requests.get(url)
    if response.status_code != 200:
        return None

    return response.json()["assets"]

def download(link, filename):
    # https://www.slingacademy.com/article/python-requests-module-how-to-download-files-from-urls/#Streaming_Large_Files
    with requests.get(link, stream=True) as r:
        r.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

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

if __name__ == "__main__":
    download_release_asset("REAndroid/APKEditor", "APKEditor", "bins", "apkeditor.jar")
    download_release_asset("ReVanced/revanced-cli", "^revanced-cli.*jar$", "bins", "cli.jar")
    download_release_asset("crimera/piko", "^piko.*jar$", "bins", "patches.jar")
    download_release_asset("crimera/revanced-integrations", "^rev.*apk$", "bins", "integrations.apk")