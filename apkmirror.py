from dataclasses import dataclass
from typing import cast
from bs4 import BeautifulSoup, Tag
import requests

from utils import download

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "en-GB,en;q=0.9",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
}


@dataclass
class Version:
    version: str
    link: str


@dataclass
class Variant:
    is_bundle: bool
    link: str
    arcithecture: str


@dataclass
class App:
    name: str
    link: str


class FailedToFindElement(Exception):
    def __init__(self, message=None) -> None:
        self.message = f"Failed to find element{" "+message if message is not None else ""}"  # noqa: E501
        super().__init__(self.message)


class FailedToFetch(Exception):
    def __init__(self, url=None) -> None:
        self.message = f"Failed to fetch{" "+url if url is not None else ""}"  # noqa: E501
        super().__init__(self.message)


def get_versions(url: str) -> list[Version]:
    """
    Get the latest version of the app from the given apkmirror url
    """
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise FailedToFetch(url)

    bs4 = BeautifulSoup(response.text, "html.parser")
    versions = bs4.find("div", attrs={"class": "listWidget"})

    out: list[Version] = []
    if versions is not None:
        for versionRow in cast(Tag, versions).findChildren(
            "div", recursive=False
        )[1:]:
            if versionRow is None:
                print(f"{versionRow} is None")
                continue

            version = versionRow.find("span", {"class": "infoSlide-value"})
            if version is None:
                continue

            version = version.string.strip()
            link = f"https://www.apkmirror.com/{versionRow.find("a")["href"]}"
            out.append(Version(version=version, link=link))

    return out


def get_last_build_version(repo_url: str) -> str | None:
    url = f"https://api.github.com/repos/{repo_url}/releases/latest"
    response = requests.get(url, headers=headers)

    print(response.status_code)
    if response.status_code == 200:
        return response.json()["tag_name"]
    elif response.status_code == 404:
        return ""


def download_apk(variant: Variant):
    """Download apk from the variant link"""

    url = variant.link

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise FailedToFetch(url)

    response_body = BeautifulSoup(response.content, "html.parser")

    downloadButton = response_body.find("a", {"class": "downloadButton"})
    if downloadButton is None:
        raise FailedToFindElement("Download button")

    download_page_link = (
        f"https://www.apkmirror.com/{cast(Tag, downloadButton).attrs["href"]}"
    )

    # get direct link
    download_page = requests.get(download_page_link, headers=headers)
    if response.status_code != 200:
        raise FailedToFetch(download_page_link)

    download_page_body = BeautifulSoup(download_page.content, "html.parser")

    direct_link = download_page_body.find("a", {"rel": "nofollow"})
    if direct_link is None:
        raise FailedToFindElement("download link")

    direct_link = (
        f"https://www.apkmirror.com/{cast(Tag, direct_link).attrs["href"]}"
    )
    print(f"Direct link: {direct_link}")

    download(direct_link, "big_file.apkm", headers=headers)

def get_variants(version: Version) -> list[Variant]:
    url = version.link
    variants_page = requests.get(url, headers=headers)
    if variants_page is None:
        raise FailedToFetch(url)

    variants_page_body = BeautifulSoup(variants_page.content, "html.parser")

    variants_table = variants_page_body.find("div", {"class": "table"})
    if variants_table is None:
        raise FailedToFindElement("variants table")

    variants_table_rows = cast(Tag, variants_table).findChildren(
        "div", recursive=False
    )[1:]

    variants: list[Variant] = []
    for variant_row in variants_table_rows:
        cells = variant_row.findChildren(
            "div", {"class": "table-cell"}, recursive=False
        )
        if len(cells) == 0:
            print("Could not find cells")

        is_bundle = variant_row.find("span", {"class": "apkm-badge"})
        if is_bundle is None:
            print("Failed to find apk-badge")
        else:
            is_bundle = is_bundle.string.strip() == "BUNDLE"

        architecture: str = cells[1].string
        link_element = variant_row.find("a", {"class": "accent_color"})
        if link_element is None:
            print("Failed to find the link element")

        link: str = f"https://www.apkmirror.com{link_element.attrs["href"]}"
        variants.append(
            Variant(is_bundle=is_bundle, link=link, arcithecture=architecture)
        )

    print(variants)
    return variants
