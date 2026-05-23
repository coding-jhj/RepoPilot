class GitHubService:
    def create_pull_request(
        self,
        repo_id: str,
        title: str,
        body: str,
        diff: str,
        confirmed: bool,
    ) -> dict:
        if not confirmed:
            return {
                "status": "blocked",
                "url": None,
                "message": "PR creation requires explicit confirmation.",
            }
        return {
            "status": "mocked",
            "url": f"https://github.com/repopilot/demo/pull/{repo_id[-4:]}",
            "message": f"Mock PR created for: {title}",
        }
