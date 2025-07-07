from datetime import datetime, timedelta
import asyncio
from typing import Dict, Optional
from pydantic import BaseModel
import uuid

class Timer(BaseModel):
    """计时器数据模型"""
    id: str
    name: str
    duration: int  # 持续时间（秒）
    remaining: int  # 剩余时间（秒）
    status: str  # 状态：running, paused, completed
    created_at: datetime
    last_updated: datetime

class TimerManager:
    """计时器管理器，负责管理所有计时器实例"""
    
    def __init__(self):
        self.timers: Dict[str, Timer] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        
    def create_timer(self, name: str, duration: int) -> Timer:
        """创建新的计时器"""
        timer_id = str(uuid.uuid4())
        now = datetime.now()
        timer = Timer(
            id=timer_id,
            name=name,
            duration=duration,
            remaining=duration,
            status="paused",
            created_at=now,
            last_updated=now
        )
        self.timers[timer_id] = timer
        return timer
    
    async def start_timer(self, timer_id: str) -> Optional[Timer]:
        """启动计时器"""
        timer = self.timers.get(timer_id)
        if not timer or timer.status == "completed":
            return None
            
        if timer.status == "running":
            return timer
            
        timer.status = "running"
        timer.last_updated = datetime.now()
        
        # 创建异步任务来处理倒计时
        self._tasks[timer_id] = asyncio.create_task(
            self._countdown(timer_id)
        )
        
        return timer
    
    async def pause_timer(self, timer_id: str) -> Optional[Timer]:
        """暂停计时器"""
        timer = self.timers.get(timer_id)
        if not timer or timer.status != "running":
            return None
            
        if timer_id in self._tasks:
            self._tasks[timer_id].cancel()
            del self._tasks[timer_id]
            
        timer.status = "paused"
        timer.last_updated = datetime.now()
        return timer
    
    async def reset_timer(self, timer_id: str) -> Optional[Timer]:
        """重置计时器"""
        timer = self.timers.get(timer_id)
        if not timer:
            return None
            
        if timer.status == "running":
            await self.pause_timer(timer_id)
            
        timer.remaining = timer.duration
        timer.status = "paused"
        timer.last_updated = datetime.now()
        return timer
    
    async def _countdown(self, timer_id: str):
        """内部方法：处理计时器的倒计时"""
        timer = self.timers[timer_id]
        try:
            while timer.remaining > 0 and timer.status == "running":
                await asyncio.sleep(1)
                timer.remaining -= 1
                timer.last_updated = datetime.now()
                
            if timer.remaining <= 0:
                timer.status = "completed"
                timer.last_updated = datetime.now()
                
        except asyncio.CancelledError:
            # 任务被取消，不需要额外处理
            pass
        finally:
            if timer_id in self._tasks:
                del self._tasks[timer_id]
    
    def get_timer(self, timer_id: str) -> Optional[Timer]:
        """获取计时器信息"""
        return self.timers.get(timer_id)
    
    def get_all_timers(self) -> Dict[str, Timer]:
        """获取所有计时器信息"""
        return self.timers.copy()
    
    def delete_timer(self, timer_id: str) -> bool:
        """删除计时器"""
        if timer_id not in self.timers:
            return False
            
        if timer_id in self._tasks:
            self._tasks[timer_id].cancel()
            del self._tasks[timer_id]
            
        del self.timers[timer_id]
        return True
