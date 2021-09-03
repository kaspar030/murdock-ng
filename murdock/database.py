import asyncio

from typing import List, Optional

import motor.motor_asyncio as aiomotor

from murdock.config import DB_CONFIG
from murdock.log import LOGGER
from murdock.job import MurdockJob
from murdock.models import (
    CommitModel, FinishedJobModel, JobQueryModel, PullRequestInfo
)


class Database:

    db = None

    async def init(self):
        LOGGER.info("Initializing database connection")
        loop = asyncio.get_event_loop()
        conn = aiomotor.AsyncIOMotorClient(
            f"mongodb://{DB_CONFIG.host}:{DB_CONFIG.port}",
            maxPoolSize=5,
            io_loop=loop
        )
        self.db = conn[DB_CONFIG.name]
    
    def close(self):
        LOGGER.info("Closing database connection")
        self.db.client.close()

    async def insert_job(self, job : MurdockJob):
        LOGGER.debug(f"Inserting job {job} to database")
        await self.db.job.insert_one(MurdockJob.to_db_entry(job))

    async def find_job(self, uid : str) -> MurdockJob:
        if not (entry := await self.db.job.find_one({"uid": uid})):
            LOGGER.warning(f"Cannot find job matching uid '{uid}'")
            return

        commit = CommitModel(**entry["commit"])
        if entry["prinfo"] is not None:
            prinfo = PullRequestInfo(**entry["prinfo"])
        else:
            prinfo = None
        
        return MurdockJob(commit, pr=prinfo, branch=entry["branch"])

    async def find_jobs(self, query: JobQueryModel) -> List[FinishedJobModel]:
        jobs = await (
            self.db.job
                .find(query.to_mongodb_query())
                .sort("since", -1)
                .to_list(length=query.limit)
        )

        return [MurdockJob.from_db_entry(job) for job in jobs]

    async def count_jobs(self, query: JobQueryModel) -> int:
        return await self.db.job.count_documents(query.to_mongodb_query())

    async def delete_jobs(self, query: JobQueryModel):
        await self.db.job.delete_many(query.to_mongodb_query())