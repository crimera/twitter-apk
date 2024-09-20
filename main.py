from apkmirror import Version, Variant
from build_variants import build_apks
from download_bins import download_apkeditor, download_revanced_bins
import github
from utils import panic, merge_apk, publish_release, report_to_telegram
from download_bins import download_release_asset
import apkmirror
import os
import argparse


def get_latest_release(versions: list[Version]) -> Version | None:
    for i in versions:
        if i.version.find("release") >= 0:
            return i


def process(latest_version: Version):
    # get bundle and universal variant
    variants: list[Variant] = apkmirror.get_variants(latest_version)

    download_link: Variant | None = None
    for variant in variants:
        if variant.is_bundle and variant.arcithecture == "universal":
            download_link = variant
            break

    if download_link is None:
        raise Exception("Bundle not Found")

    apkmirror.download_apk(download_link)
    if not os.path.exists("big_file.apkm"):
        panic("Failed to download apk")

    download_apkeditor()

    if not os.path.exists("big_file_merged.apk"):
        merge_apk("big_file.apkm")
    else:
        print("apkm is already merged")

    download_revanced_bins()

    print("Downloading patches")
    pikoRelease = download_release_asset(
        "crimera/piko", "^piko.*jar$", "bins", "patches.jar"
    )

    print("Downloading integrations")
    integrationsRelease = download_release_asset(
        "crimera/revanced-integrations",
        "^rev.*apk$",
        "bins",
        "integrations.apk",
    )

    print(integrationsRelease["body"])

    message: str = f"""
Changelogs:
[piko-{pikoRelease["tag_name"]}]({pikoRelease["html_url"]})
[integrations-{integrationsRelease["tag_name"]}]({integrationsRelease["html_url"]})
"""

    build_apks(latest_version)

    publish_release(
        latest_version.version,
        [
            f"x-piko-v{latest_version.version}.apk",
            f"x-piko-material-you-v{latest_version.version}.apk",
            f"twitter-piko-v{latest_version.version}.apk",
            f"twitter-piko-material-you-v{latest_version.version}.apk",
        ],
        message,
        latest_version.version
    )

    report_to_telegram()


def main():
    # get latest version
    url: str = "https://www.apkmirror.com/apk/x-corp/twitter/"
    repo_url: str = "crimera/twitter-apk"

    versions = apkmirror.get_versions(url)

    latest_version = get_latest_release(versions)
    if latest_version is None:
        raise Exception("Could not find the latest version")

    # only continue if it's a release
    if latest_version.version.find("release") < 0:
        panic("Latest version is not a release version")

    last_build_version: github.GithubRelease | None = github.get_last_build_version(
        repo_url
    )

    if last_build_version is None:
        panic("Failed to fetch the latest build version")
        return

    # Begin stuff
    if last_build_version.tag_name != latest_version.version:
        print(f"New version found: {latest_version.version}")
    else:
        print("No new version found")
        return
    
    process(latest_version)


def manual(version:str):
    link = f'https://www.apkmirror.com/apk/x-corp/twitter/twitter-{version.replace(".","-")}-release'
    latest_version = Version(link=link,version=version)
    process(latest_version)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Piko APK')
    # 0 = auto; 1 = manual;
    parser.add_argument('--m', action="store", dest='mode', default=0)
    parser.add_argument('--v', action="store", dest='version', default=0)
    
    args = parser.parse_args()
    mode = args.mode
    
    if not mode: # auto
        main()
    else: # manual
        version = args.version
        if not version:
            raise Exception("Version is required.")
        manual(version)
