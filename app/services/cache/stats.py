from app.database import redcache
from app.schemas.stats import DashboardMetrics
from app.services.cache import BaseCache, CacheKey


class OverviewMetricsCache(BaseCache):
    __KEY__ = CacheKey.OVERVIEW_METRICS.value

    def __init__(self, user_id, query: str):
        self.key = self.__KEY__.format(user_id, query)

    async def get(self):
        ret = await redcache.get(self.key)
        if ret:
            return DashboardMetrics.model_validate_json(ret)

        return ret

    async def add(self, data: DashboardMetrics, expire=30 * 60):
       
        ret = await redcache.set(self.key, data.model_dump_json(), ex=expire)
        return ret

    async def delete(self):
        return await redcache.delete(self.key)

    async def exists(self):
        return await redcache.exists(self.key)
