from main import get_latest_release
from apkmirror import get_versions

if __name__ == "__main__":
    version = get_latest_release(
        get_versions("https://www.apkmirror.com/apk/x-corp/twitter/")
    )
    if version is None:
        print("Failed to fetch the latest version")
        exit(1)
    print(version.version, end="")
