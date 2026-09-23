# Upload pyChangaIDE to GitHub

Keep the editor, `pyChanga_package`, examples, and course together in one repository
named **pyChangaIDE**. The Python import remains `from pyChanga import *`.

## First upload

Git and the GitHub command-line tool (`gh`) are already installed on this Mac.
Open Terminal and run these commands, one at a time:

```sh
cd "/Volumes/DADES/TecPROG/Editor"
git init -b main
git add .
git status
git commit -m "Initial pyChangaIDE and pyChanga package"
gh auth login
gh repo create pyChangaIDE --private --source=. --remote=origin --push
gh repo view --web
```

Choose GitHub.com and browser sign-in when `gh auth login` asks. If you are already
signed in, skip that command. The repository is private with the command above;
use `--public` instead of `--private` if you want everyone to see the source.
If Git asks for your author name/email, follow its instructions, then retry the commit.

The `.gitignore` keeps downloaded runtimes, dependencies, generated applications,
test output, and historical E-mu soundfonts out of the repository. The licensed
TimGM6mb soundfont inside the Python package stays included.

These steps follow [GitHub's existing-code upload guide](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github)
and the [GitHub CLI repository command](https://cli.github.com/manual/gh_repo_create).

## Share the downloadable app

In your repository, choose **Releases → Draft a new release**. Create the tag
`v1.0.0`, use the title **pyChangaIDE 1.0.0**, and attach:

```text
out/release/make/pyChangaIDE-1.0.0-arm64.dmg
```

The DMG is the Mac Apple Silicon installer. Explain in the release notes that this
build is unsigned. Mark it as a pre-release while testing on other machines.
Save a draft or publish when ready. Installers belong in Releases, not in Git
commits. See [GitHub's release guide](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).

The included Actions workflow also builds macOS Apple Silicon, macOS Intel, and
Windows x64 installers. Check each successful run under **Actions** for its
downloadable artifacts; it does not automatically publish releases. Signing and
notarization still need your release credentials.

## Upload later changes

```sh
git add .
git commit -m "Describe the changes"
git push
```
