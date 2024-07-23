import requests
import os
from dataclasses import dataclass
from bs4 import BeautifulSoup
import subprocess

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


def panic(message: str):
    print(message)
    exit(1)


@dataclass
class Version:
    version: str
    link: str


@dataclass
class Variant:
    is_bundle: bool
    link: str
    arcithecture: str

def get_versions(url: str) -> list[Version] | None:
    """
    Get the latest version of the app from the given apkmirror url
    """
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    bs4 = BeautifulSoup(response.text, "html.parser")
    versions = bs4.find("div", attrs={"class": "listWidget"})

    if versions is not None:
        out: list[Version] = []
        for versionRow in versions.findChildren("div", recursive=False)[1:]:
            if versionRow is None:
                print("versionRow is None")
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


def get_latest_release(versions: list[Version]) -> Version | None:
    for i in versions:
        if i.version.find("release") >= 0:
            return i


# Download apk endpoint (version where all . are changed to -)-android-apk-download/
def download_apk(url: str) -> None:
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        panic("Failed to fetch the download page")

    response_body = BeautifulSoup(response.content, "html.parser")

    downloadButton = response_body.find("a", {"class": "downloadButton"})
    if downloadButton is None:
        panic("Failed to find the download button")

    download_page_link = f"https://www.apkmirror.com/{downloadButton.attrs["href"]}"

    # get direct link
    download_page = requests.get(download_page_link, headers=headers)
    if response.status_code != 200:
        panic("Failed to fetch the real download page")

    download_page_body = BeautifulSoup(download_page.content, "html.parser")

    direct_link = download_page_body.find("a", {"rel": "nofollow"})
    if direct_link is None:
        panic("Failed to find the direct download link")

    direct_link = f"https://www.apkmirror.com/{direct_link.attrs["href"]}"
    print(f"Direct link: {direct_link}")

    # https://www.slingacademy.com/article/python-requests-module-how-to-download-files-from-urls/#Streaming_Large_Files
    with requests.get(direct_link, stream=True, headers=headers) as r:
        r.raise_for_status()
        with open("big_file.apkm", "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        
def merge_apk(path: str):
    subprocess.run(["java", "-jar", "./bins/apkeditor.jar", "m", "-i", path]).check_returncode()

def patch_apk(cli: str, integrations: str, patches: str, apk: str, includes: list[str]):
    # java -jar .\revanced-cli-4.5.0-all.jar patch -b .\piko\build\libs\*.jar -m .\revanced-integrations\app\build\outputs\apk\release\*.apk -i "Enable app downgrading" -i "Hide FAB" -i "Disable chirp font" -i "Add ability to copy media link" -i "Hide Banner" -i "Hide promote button" "$apk.apk"
    command = ["java", "-jar", cli, "patch", "-b", patches, "-m", integrations]

    for i in includes:
        command.append("-i")
        command.append(i)

    command.append(apk)

    subprocess.run(command).check_returncode()

def get_variants(url: str) -> list[Variant] | None:
    variants_page = requests.get(url, headers=headers)
    if variants_page is None:
        panic("Failed to fetch the variants page")

    variants_page_body = BeautifulSoup(variants_page.content, "html.parser")

    variants_table = variants_page_body.find("div", {"class": "table"})
    if variants_table is None:
        panic("Failed to find the variants table")

    variants_table_rows = variants_table.findChildren("div", recursive=False)[1:]

    variants: list[Variant] = []
    for variant_row in variants_table_rows: 

        cells = variant_row.findChildren("div", {"class": "table-cell"}, recursive=False)
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
        variants.append(Variant(is_bundle=is_bundle, link=link, arcithecture=architecture))

    print(variants)
    return variants

if __name__ == "__main__":
    # get latest version
    url: str = "https://www.apkmirror.com/apk/x-corp/twitter/"
    repo_url: str = "crimera/twitter-apk"

    versions = get_versions(url)

    latest_version: Version = get_latest_release(versions)
    if latest_version is None:
        panic("Failed to fetch the latest version")

    # only continue if it's a release
    if latest_version.version.find("release") < 0:
        panic("Latest version is not a release version")

    last_build_version = get_last_build_version(repo_url)
    if last_build_version is None:
        panic("Failed to fetch the latest build version")

    # Begin stuff
    if last_build_version != latest_version.version:
        print(f"New version found: {latest_version.version}")

    # get bundle and universal variant
    variants: list[Variant] = get_variants(latest_version.link)

    download_link: str | None = None
    for variant in variants: 
        if variant.is_bundle and variant.arcithecture == "universal":
            download_link = variant.link
            break

    if download_link is None:
        panic("Could not find the bundle") 

    download_apk(download_link)
    if not os.path.exists("big_file.apkm"):
        panic("Failed to download apk")
    
    # merge apkm
    # merge command java -jar ./bins/APKEditor-1.3.8.jar
    merge_apk("big_file.apkm")

    # patch
    patch_apk(
        "bins/cli.jar",
        "bins/integrations.apk",
        "bins/patches.jar",
        "big_file_merged.apk",
        [
            "Enable app downgrading",
            "Hide FAB",
            "Disable chirp font",
            "Add ability to copy media link",
            "Hide Banner",
            "Hide promote button"
            "Hide Community Notes"
            "Delete from database"
        ],
    )