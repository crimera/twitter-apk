import requests
from constants import HEADERS
from dataclasses import dataclass


@dataclass
class Asset:
    browser_download_url: str
    name: str


@dataclass
class GithubRelease:
    tag_name: str
    html_url: str
    assets: list[Asset]


def get_last_build_version(repo_url: str) -> GithubRelease | None:
    url = f"https://api.github.com/repos/{repo_url}/releases/latest"
    response = requests.get(url, headers=HEADERS)

    print(response.status_code)
    if response.status_code == 200:
        release = response.json()

        assets = [
            Asset(
                browser_download_url=asset["browser_download_url"], name=asset["name"]
            )
            for asset in release["assets"]
        ]

        return GithubRelease(
            tag_name=release["tag_name"], html_url=release["html_url"], assets=assets
        )
    elif response.status_code == 404:
        return
