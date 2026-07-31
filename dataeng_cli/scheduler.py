import time
import schedule
import logging

logger = logging.getLogger("dataeng")

def run_scheduled_sync(sync_func, interval_seconds: int = 10, max_runs: int = 3):
    """简单的内置定时触发器演示"""
    runs = 0
    def job():
        nonlocal runs
        runs += 1
        logger.info(f"⏰ [定时调度器] 触发第 {runs} 次增量同步任务...")
        sync_func()

    schedule.every(interval_seconds).seconds.do(job)
    logger.info(f"调度器已启动，每 {interval_seconds} 秒运行一次 sync (示范运行 {max_runs} 次)...")
    
    while runs < max_runs:
        schedule.run_pending()
        time.sleep(1)
    logger.info("调度演示结束。")
