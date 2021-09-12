from datetime import datetime
from datetime import time as dtime
from typing import Optional, List

from pydantic import BaseModel, Field

from murdock.config import GLOBAL_CONFIG


class PullRequestInfo(BaseModel):
    title: str = Field(
        None,
        title="Pull Request title",
    )
    number: int = Field(
        None,
        title="Pull Request number",
    )
    merge_commit: str = Field(
        None,
        title="SHA value of the merged commit",
    )
    user: str = Field(
        None,
        title="Github user corresponding to the pull request author",
    )
    url: str = Field(
        None,
        title="Github URL of the pull request",
    )
    base_repo: str = Field(
        None,
        title="URL of the base repository",
    )
    base_branch: str = Field(
        None,
        title="Name of the target branch",
    )
    base_commit: str = Field(
        None,
        title="Last commit of the target branch",
    )
    base_full_name: str = Field(
        None,
        title="Target repository name",
    )
    mergeable: bool = Field(
        None,
        title="True if the pull request is mergeable, False otherwise",
    )
    labels: list[str] = Field(
        None,
        title="List of Github labels assigned to the pull request",
    )


class CommitModel(BaseModel):
    sha: str = Field(
        None,
        title="SHA value of the commit to process",
    )
    message: str = Field(
        None,
        title="Commit message",
    )
    author: str = Field(
        None,
        title="Author of the commit",
    )

class JobModel(BaseModel):
    uid: str = Field(
        None,
        title="Unique identifier of the job (hex format)",
    )
    commit: CommitModel = Field(
        None,
        title="Information of the commit to process",
    )
    ref: Optional[str] = Field(
        None,
        title="Reference (if any), can be branch name or tag name",
    )
    prinfo: Optional[PullRequestInfo] = Field(
        None,
        title="Pull Request detailed information (if any)",
    )
    since: float = Field(
        None,
        title="Time of last update of the job",
    )
    fasttracked: Optional[bool] = Field(
        None,
        title="Whether the job can be fasttracked",
    )
    status: Optional[dict] = Field(
        None,
        title="Status of the job",
    )
    output: str = Field(
        None,
        title="Output of the job",
    )


class FinishedJobModel(JobModel):
    result: str = Field(
        None,
        title="Final result of a job (passed or errored)",
    )
    output_url: str = Field(
        None,
        title="URL where html output of the job is available",
    )
    runtime: float = Field(
        None,
        title="Runtime of the job",
    )


class CategorizedJobsModel(BaseModel):
    queued: List[JobModel] = Field(
        None,
        title="List of all queued jobs",
    )
    building: List[JobModel] = Field(
        None,
        title="List of all building jobs",
    )
    finished: List[FinishedJobModel] = Field(
        None,
        title="List of all finished jobs",
    )


class JobQueryModel(BaseModel):
    limit: Optional[int] = Field(
        GLOBAL_CONFIG.max_finished_length_default,
        title="Limit length of items returned",
    )
    uid: Optional[str] = Field(
        None,
        title="uid of the job"
    )
    prnum: Optional[int] = Field(
        None,
        title="PR number",
    )
    branch: Optional[str] = Field(
        None,
        title="Name of the branch",
    )
    sha: Optional[str] =  Field(
        None,
        title="Commit SHA",
    )
    author: Optional[str] =  Field(
        None,
        title="Author of the commit",
    )
    result: Optional[str] =  Field(
        None,
        title="Result of the job",
    )
    after: Optional[str] =  Field(
        None,
        title="Date after which the job finished",
    )
    before: Optional[str] =  Field(
        None,
        title="Date before which the job finished (included)",
    )

    def to_mongodb_query(self):
        _query = {}
        if self.uid is not None:
            _query.update({"uid": self.uid})
        if self.prnum is not None:
            _query.update({"prinfo.number": self.prnum})
        if self.branch is not None:
            _query.update({"branch": self.branch})
        if self.sha is not None:
            _query.update({"commit.sha": self.sha})
        if self.author is not None:
            _query.update({"commit.author": self.author})
        if self.result in ["errored", "passed"]:
            _query.update({"result": self.result})
        if self.after is not None:
            date = datetime.strptime(self.after, "%Y-%m-%d")
            _query.update({"since": {"$gte": date.timestamp()}})
        if self.before is not None:
            date = datetime.combine(
                datetime.strptime(self.before, "%Y-%m-%d"),
                dtime(hour=23, minute=59, second=59, microsecond=999)
            )
            if "since" in _query:
                _query["since"].update({"$lte": date.timestamp()})
            else:
                _query.update({"since": {"$lte": date.timestamp()}})
        return _query
