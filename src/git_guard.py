import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple


class ProjectLockManager:
    """
    Manages per-project asyncio locks to prevent concurrent Git operations
    or overlapping AI modifications on the same codebase.
    """

    def __init__(self):
        self._locks: Dict[str, asyncio.Lock] = {}
        self._active_info: Dict[str, Tuple[datetime, str]] = {}

    def get_lock(self, project_alias: str) -> asyncio.Lock:
        alias = project_alias.lower().strip()
        if alias not in self._locks:
            self._locks[alias] = asyncio.Lock()
        return self._locks[alias]

    def is_locked(self, project_alias: str) -> bool:
        alias = project_alias.lower().strip()
        lock = self._locks.get(alias)
        return lock.locked() if lock else False

    def get_active_info(self, project_alias: str) -> Optional[Tuple[datetime, str]]:
        return self._active_info.get(project_alias.lower().strip())

    def mark_started(self, project_alias: str, command_name: str):
        self._active_info[project_alias.lower().strip()] = (datetime.now(), command_name)

    def mark_finished(self, project_alias: str):
        self._active_info.pop(project_alias.lower().strip(), None)


# Global project lock instance
lock_manager = ProjectLockManager()


async def run_git(cwd: Path, *args: str) -> Tuple[int, str, str]:
    """
    Executes a Git command in the target directory asynchronously.
    Returns (returncode, stdout, stderr) decoded as UTF-8.
    """
    proc = await asyncio.create_subprocess_exec(
        "git",
        *args,
        cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    out_decoded = stdout.decode("utf-8", errors="replace").strip()
    err_decoded = stderr.decode("utf-8", errors="replace").strip()
    return proc.returncode, out_decoded, err_decoded


async def is_git_repo(project_path: Path) -> bool:
    """Checks whether the directory is a valid Git repository."""
    code, _, _ = await run_git(project_path, "rev-parse", "--is-inside-work-tree")
    return code == 0


async def get_current_branch(project_path: Path) -> str:
    """Returns the current Git branch name."""
    code, out, _ = await run_git(project_path, "rev-parse", "--abbrev-ref", "HEAD")
    return out if code == 0 else "unknown"


async def get_status_short(project_path: Path) -> str:
    """Returns concise git status (-sb)."""
    if not await is_git_repo(project_path):
        return "⚠️ Not a Git repository."

    code, out, err = await run_git(project_path, "status", "-sb")
    if code != 0:
        return f"Git error:\n{err}"
    return out if out else "Clean working tree (nothing to commit)."


async def check_clean_working_tree(project_path: Path) -> Tuple[bool, str]:
    """
    Checks if there are uncommitted local changes.
    Returns (is_clean, dirty_details).
    """
    if not await is_git_repo(project_path):
        return True, ""

    code, out, err = await run_git(project_path, "status", "--porcelain")
    if code != 0:
        return False, f"Git status error: {err}"

    if out.strip():
        return False, out.strip()
    return True, ""


async def create_mobile_branch(project_path: Path) -> Tuple[bool, str]:
    """
    Creates and checks out a new branch: 'mobile/YYYYMMDD-HHMMSS'.
    Protects base branch from accidental direct edits.
    """
    if not await is_git_repo(project_path):
        return True, "Directory is not a Git repo. Continuing without branch protection."

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    branch_name = f"mobile/{timestamp}"

    code, out, err = await run_git(project_path, "checkout", "-b", branch_name)
    if code != 0:
        return False, f"Failed to create mobile branch '{branch_name}': {err}"

    return True, branch_name


async def get_diff(project_path: Path, stat_only: bool = False) -> str:
    """Retrieves current git diff or git diff --stat."""
    if not await is_git_repo(project_path):
        return "⚠️ Not a Git repository."

    args = ["diff", "--stat"] if stat_only else ["diff"]
    code, out, err = await run_git(project_path, *args)
    if code != 0:
        return f"Git diff error: {err}"

    if not out.strip():
        # Also check staged changes if unstaged is empty
        staged_args = ["diff", "--cached", "--stat"] if stat_only else ["diff", "--cached"]
        _, staged_out, _ = await run_git(project_path, *staged_args)
        if staged_out.strip():
            return f"(Staged changes)\n{staged_out.strip()}"
        return "No code changes detected."

    return out.strip()


async def stage_commit_and_push(
    project_path: Path,
    commit_message: Optional[str] = None,
    author_name: str = "RemoteDevBridge",
    author_email: str = "bot@remotedevbridge.local",
) -> Tuple[bool, str]:
    """
    Stages all changes (git add -A), commits them, and pushes current branch to origin.
    """
    if not await is_git_repo(project_path):
        return False, "Directory is not a Git repository. Cannot push."

    # 1. Stage all changes
    code, _, err = await run_git(project_path, "add", "-A")
    if code != 0:
        return False, f"Failed to stage changes ('git add -A'): {err}"

    # 2. Check if there are changes to commit
    code, status_out, _ = await run_git(project_path, "status", "--porcelain")
    if not status_out.strip():
        # Check if current branch has unpushed commits
        branch = await get_current_branch(project_path)
    else:
        # Perform commit
        msg = commit_message.strip() if commit_message else "mobile: updates via RemoteDevBridge"
        code, commit_out, err = await run_git(
            project_path,
            "-c",
            f"user.name={author_name}",
            "-c",
            f"user.email={author_email}",
            "commit",
            "-m",
            msg,
        )
        if code != 0:
            return False, f"Failed to commit changes: {err}"

    # 3. Push to remote
    current_branch = await get_current_branch(project_path)
    code, push_out, push_err = await run_git(project_path, "push", "-u", "origin", current_branch)
    if code != 0:
        return False, f"Failed to push to origin/{current_branch}:\n{push_err or push_out}"

    return True, f"Successfully pushed branch '{current_branch}' to origin!"
