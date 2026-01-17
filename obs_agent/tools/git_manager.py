"""Git operations manager for Obsidian vault."""

import os
import subprocess
from pathlib import Path
from typing import Optional


class GitManager:
    """Manage git operations for the Obsidian vault repository."""

    def __init__(
        self,
        repo_url: Optional[str] = None,
        branch: Optional[str] = None,
        local_path: Optional[str] = None,
    ):
        """Initialize the Git manager.

        Args:
            repo_url: GitHub repository URL. If not provided, uses OBSIDIAN_GIT_REPO env var.
            branch: Branch name. If not provided, uses OBSIDIAN_GIT_BRANCH env var.
            local_path: Local path for the repo. If not provided, uses OBSIDIAN_VAULT_PATH env var.
        """
        self.repo_url = repo_url or os.getenv("OBSIDIAN_GIT_REPO", "")
        self.branch = branch or os.getenv("OBSIDIAN_GIT_BRANCH", "main")
        self.local_path = Path(local_path or os.getenv("OBSIDIAN_VAULT_PATH", ""))

        if not self.repo_url:
            raise ValueError("OBSIDIAN_GIT_REPO is required")
        if not self.local_path:
            raise ValueError("OBSIDIAN_VAULT_PATH is required")

    def _run_git_command(self, args: list[str], cwd: Optional[Path] = None) -> tuple[bool, str]:
        """Run a git command and return the result.

        Args:
            args: Git command arguments (without 'git' prefix)
            cwd: Working directory for the command

        Returns:
            Tuple of (success, output/error message)
        """
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=cwd or self.local_path,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
            return False, result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "Git command timed out"
        except Exception as e:
            return False, str(e)

    def ensure_repo_exists(self) -> tuple[bool, str]:
        """Ensure the repository is cloned locally.

        Returns:
            Tuple of (success, message)
        """
        git_dir = self.local_path / ".git"
        if git_dir.exists():
            return True, "Repository already exists"

        # Clone the repository
        self.local_path.parent.mkdir(parents=True, exist_ok=True)
        success, output = self._run_git_command(
            ["clone", "-b", self.branch, self.repo_url, str(self.local_path)],
            cwd=self.local_path.parent,
        )
        if success:
            return True, f"Repository cloned successfully"
        return False, f"Failed to clone repository: {output}"

    def pull(self) -> tuple[bool, str]:
        """Pull latest changes from remote.

        Returns:
            Tuple of (success, message)
        """
        # First ensure repo exists
        exists_success, exists_msg = self.ensure_repo_exists()
        if not exists_success:
            return False, exists_msg

        # Pull changes
        success, output = self._run_git_command(["pull", "origin", self.branch])
        if success:
            return True, f"Pull successful: {output}" if output else "Already up to date"
        return False, f"Pull failed: {output}"

    def add_all(self) -> tuple[bool, str]:
        """Stage all changes.

        Returns:
            Tuple of (success, message)
        """
        success, output = self._run_git_command(["add", "-A"])
        if success:
            return True, "Changes staged"
        return False, f"Failed to stage changes: {output}"

    def commit(self, message: str) -> tuple[bool, str]:
        """Commit staged changes.

        Args:
            message: Commit message

        Returns:
            Tuple of (success, message)
        """
        # Check if there are changes to commit
        status_success, status_output = self._run_git_command(["status", "--porcelain"])
        if status_success and not status_output:
            return True, "No changes to commit"

        success, output = self._run_git_command(["commit", "-m", message])
        if success:
            return True, f"Committed: {message}"
        # Check if it's just "nothing to commit"
        if "nothing to commit" in output:
            return True, "No changes to commit"
        return False, f"Commit failed: {output}"

    def push(self) -> tuple[bool, str]:
        """Push commits to remote.

        Returns:
            Tuple of (success, message)
        """
        success, output = self._run_git_command(["push", "origin", self.branch])
        if success:
            return True, "Push successful"
        return False, f"Push failed: {output}"

    def sync_and_save(self, commit_message: str) -> tuple[bool, str]:
        """Complete workflow: pull, add, commit, push.

        Args:
            commit_message: Commit message for the changes

        Returns:
            Tuple of (success, message)
        """
        steps = []

        # Step 1: Pull
        pull_success, pull_msg = self.pull()
        steps.append(f"Pull: {pull_msg}")
        if not pull_success:
            return False, " | ".join(steps)

        # Step 2: Add
        add_success, add_msg = self.add_all()
        steps.append(f"Add: {add_msg}")
        if not add_success:
            return False, " | ".join(steps)

        # Step 3: Commit
        commit_success, commit_msg = self.commit(commit_message)
        steps.append(f"Commit: {commit_msg}")
        if not commit_success:
            return False, " | ".join(steps)

        # Step 4: Push (only if there was something to commit)
        if "No changes to commit" not in commit_msg:
            push_success, push_msg = self.push()
            steps.append(f"Push: {push_msg}")
            if not push_success:
                return False, " | ".join(steps)

        return True, " | ".join(steps)
