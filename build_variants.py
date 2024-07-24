from apkmirror import Version
from utils import patch_apk


def build_apks(latest_version: Version):
    # patch
    apk = "big_file_merged.apk"
    integrations = "bins/integrations.apk"
    patches = "bins/patches.jar"
    cli = "bins/cli.jar"

    patch_apk(
        cli,
        integrations,
        patches,
        apk,
        includes=[
            "Enable app downgrading",
            "Hide FAB",
            "Disable chirp font",
            "Add ability to copy media link",
            "Hide Banner",
            "Hide promote button",
            "Hide Community Notes",
            "Delete from database",
        ],
        out=f"x-piko-material-you-v{latest_version.version}.apk",
    )

    patch_apk(
        cli,
        integrations,
        patches,
        apk,
        includes=[
            "Enable app downgrading",
            "Hide FAB",
            "Disable chirp font",
            "Add ability to copy media link",
            "Hide Banner",
            "Hide promote button",
            "Hide Community Notes",
            "Delete from database",
        ],
        excludes=["Dynamic color"],
        out=f"x-piko-v{latest_version.version}.apk",
    )

    patch_apk(
        cli,
        integrations,
        patches,
        apk,
        includes=[
            "Bring back twitter" "Enable app downgrading",
            "Hide FAB",
            "Disable chirp font",
            "Add ability to copy media link",
            "Hide Banner",
            "Hide promote button",
            "Hide Community Notes",
            "Delete from database",
        ],
        out=f"twitter-piko-material-you-v{latest_version.version}.apk",
    )

    patch_apk(
        cli,
        integrations,
        patches,
        apk,
        includes=[
            "Bring back twitter" "Enable app downgrading",
            "Hide FAB",
            "Disable chirp font",
            "Add ability to copy media link",
            "Hide Banner",
            "Hide promote button",
            "Hide Community Notes",
            "Delete from database",
        ],
        excludes=["Dynamic color"],
        out=f"twitter-piko-v{latest_version.version}.apk",
    )
