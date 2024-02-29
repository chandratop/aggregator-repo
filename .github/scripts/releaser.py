import argparse
import yaml
import re
from utils.utils import run

def get_last_tag() -> str:
    cmd = 'gh release list --limit 1 --json tagName'
    result = run(cmd)
    if result.fine:
        return eval(result.what)[0]["tagName"]
    else:
        raise ValueError(f"Command failed: {cmd}\nError: {result.what}")

def get_bump(release) -> int:
    if "### Breaking Changes" in release:
        return 0
    elif "### New Features & Enhancements" in release:
        return 1
    else:
        return 2

def get_next_tag(old_tag, bump) -> str:
    """
    Calculate the next tag based on what to update (major/minor/patch)
    """

    pattern = r'^(\w*_*)(\d+\.\d+\.\d+)$'
    match = re.match(pattern, old_tag)
    if bool(match):
        tag = match.group(2)
        tag_split: list[int] = list(map(int, tag.split(".")))
        tag_split[bump] += 1
        for i in range(bump+1, 3):
            tag_split[i] = 0
        return match.group(1) + ".".join(list(map(str, tag_split)))
    else:
        raise ValueError(f"Unable to calculate next tag for {old_tag}")

def get_title_release(pr: str) -> str:
    """
    Get the type and description from the pr title.
    """

    cmd = f'gh pr view "{pr}" --json title'
    result = run(cmd)
    if result.fine:
        full_title = eval(result.what)["title"]
        title_split = full_title.split("release-")
        return title_split[1].strip()
    else:
        raise ValueError(f"Command failed: {cmd}\nError: {result.what}")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Get action')
    parser.add_argument('action', help='update or pr number')
    args = parser.parse_args()

    if args.action == "update":
        old_tag = get_last_tag()

        releases = "" # yaml
        release = "" # md

        repos = ["release-note-generator", "monorepo-release-notes-demo"]
        parent_keys = ["release_note_generator", "monorepo_release_notes_demo"]
        for i in range(len(repos)):
            # From original repo
            with open(f"../{repos[i]}/releases.yaml") as f:
                releases_yaml_current = f.read()
            with open(f"../{repos[i]}/RELEASE.md") as f:
                md_release_yaml_current = f.read()
            # From this repo
            with open(f"{repos[i]}/releases.yaml") as f:
                releases_yaml_existing = f.read()
            with open(f"{repos[i]}/releases.yaml") as f:
                md_release_yaml_existing = f.read()
            # convert into dict
            releases_yaml_current_dict = yaml.safe_load(releases_yaml_current)
            releases_yaml_existing_dict = yaml.safe_load(releases_yaml_existing)
            # If no version change then skip
            if releases_yaml_current_dict[parent_keys[i]]["release"] == releases_yaml_existing_dict[parent_keys[i]]["release"]:
                # append to releases.yaml
                releases += "\n" + releases_yaml_current + "\n"
                continue
            # update this repo's stuff
            releases_yaml_existing = releases_yaml_current
            md_release_yaml_existing = md_release_yaml_current
            releases += "\n" + releases_yaml_existing + "\n"
            release += "\n" + f'# {repos[i]}\n' + md_release_yaml_existing + "\n"

            with open(f"{repos[i]}/releases.yaml", "w+") as f:
                f.write(releases_yaml_existing)

            with open(f"{repos[i]}/RELEASE.md", "w+") as f:
                f.write(md_release_yaml_existing)


        if release == "":
            raise ValueError(f"No change")

        with open(f"releases.yaml", "w") as f:
            f.write(releases)

        with open(f"RELEASE.md", "w") as f:
            f.write(release)

        bump = get_bump(release)

        next_tag = get_next_tag(old_tag, bump)

        # Configure the bot
        cmd = f'git config --local user.email "action@github.com"'
        result = run(cmd)
        if not result.fine:
            raise ValueError(f"Command failed: {cmd}\nError: {result.what}")
        cmd = f'git config --local user.name "GitHub Action"'
        result = run(cmd)
        if not result.fine:
            raise ValueError(f"Command failed: {cmd}\nError: {result.what}")

        # Add the changes
        cmd = 'git add .'
        result = run(cmd)
        if not result.fine:
            raise ValueError(f"Command failed: {cmd}\nError: {result.what}")

        # Create a branch
        branch = f'release-{next_tag}'
        cmd = f'git checkout -b {branch}'
        result = run(cmd)
        if not result.fine:
            raise ValueError(f"Command failed: {cmd}\nError: {result.what}")

        # Commit the changes
        cmd = f'git commit -m "{branch}"'
        result = run(cmd)
        if not result.fine:
            raise ValueError(f"Command failed: {cmd}\nError: {result.what}")

        # Push the changes
        cmd = f'git push --set-upstream origin {branch}'
        result = run(cmd)
        if not result.fine:
            raise ValueError(f"Command failed: {cmd}\nError: {result.what}")

        # Checkout to main branch
        cmd = f'git checkout main'
        result = run(cmd)
        if not result.fine:
            raise ValueError(f"Command failed: {cmd}\nError: {result.what}")

        # Create a pull request
        cmd = f'gh pr create --base main --head {branch} --title "{branch}" --label release --body {release}'
        result = run(cmd)
        if not result.fine:
            raise ValueError(f"Command failed: {cmd}\nError: {result.what}")

    else:

        release_tag: str = get_title_release(args.action)

        # Create the release
        cmd = f'gh release create {release_tag} --notes-file RELEASE.md --title "{release_tag}"'
        result = run(cmd)
        if not result.fine:
            raise ValueError(f"Command failed: {cmd}\nError: {result.what}")
