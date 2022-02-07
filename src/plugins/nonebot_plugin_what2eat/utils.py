import os
import json
import random
import nonebot

from enum import Enum
from pathlib import Path
from typing import Optional
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment

SUPERUSERS = nonebot.get_driver().config.superusers
_WHAT2EAT_PATH = nonebot.get_driver().config.what2eat_path
DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "resource")
WHAT2EAT_PATH = DEFAULT_PATH if not _WHAT2EAT_PATH else _WHAT2EAT_PATH
_EATING_LIMIT = nonebot.get_driver().config.eating_limit
EATING_LIMIT = 6 if not _EATING_LIMIT else _EATING_LIMIT

'''
    需要群发问候的群组列表
'''
_GROUPS_ID = nonebot.get_driver().config.groups_id
GROUPS_ID = [] if not _GROUPS_ID else _GROUPS_ID

class Meals(Enum):
    BREAKFAST   = "breakfast"
    LUNCH       = "lunch"
    SNACK       = "snack"
    DINNER      = "dinner"
    MIDNIGHT    = "midnight"

class EatingManager:

    def __init__(self, path: Optional[Path]):
        self._data = {}
        self._greating = {}
        if not path:
            data_file = Path(WHAT2EAT_PATH) / "data.json"
            greating_file = Path(WHAT2EAT_PATH) / "greating.json"
        else:
            data_file = path / "data.json"
            greating_file = path / "greating.json"
        
        self.data_file = data_file
        self.greating_file = greating_file
        if data_file.exists():
            with open(data_file, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        
        if greating_file.exists():
            with open(greating_file, "r", encoding="utf-8") as f:
                self._greating = json.load(f)

        self._init_json()

    def _init_json(self) -> None:
        # 建议["basic_food"]初始非空
        if "basic_food" not in self._data.keys():
            self._data["basic_food"] = []
        if "group_food" not in self._data.keys():
            self._data["group_food"] = {}
        if "eating" not in self._data.keys():
            self._data["eating"] = {}
        
        # 建议greating.json初始非空，即至少有一个键
        for meal in Meals:
            if meal.value not in self._greating.keys():
                self._greating[meal.value] = []
    
    def _init_data(self, event: GroupMessageEvent) -> None:
        '''
            初始化用户信息
        '''
        user_id = str(event.user_id)
        group_id = str(event.group_id)
        
        if group_id not in self._data["group_food"].keys():
            self._data["group_food"][group_id] = []
        if group_id not in self._data["eating"].keys():
            self._data["eating"][group_id] = {}
        if user_id not in self._data["eating"][group_id].keys():
            self._data["eating"][group_id][user_id] = 0

    def get2eat(self, event: GroupMessageEvent) -> str:
        '''
            今天吃什么
        '''
        user_id = str(event.user_id)
        group_id = str(event.group_id)

        self._init_data(event)
        if not self.eating_check(event):
            return random.choice(
                [
                    "你已经吃了很多啦！",
                    "吃这么多的吗？等会还……吃得下我吗？",
                    "害搁这吃呢？不援交的吗？",
                    "再吃肚子就要爆炸咯~"
                ]
            )
        else:
            # 菜单全为空，建议避免["basic_food"]为空
            if len(self._data["basic_food"]) == 0 and len(self._data["group_food"][group_id]) == 0:
                return "还没有菜单呢，就先饿着肚子吧，可以[添加 菜名]哦~"
            
            food_list = self._data["basic_food"].copy()
            if len(self._data["group_food"][group_id]) > 0:
                food_list.extend(self._data["group_food"][group_id])

            msg = "建议" + random.choice(food_list) + "哦~"
            self._data["eating"][group_id][user_id] += 1
            self.save()

            return msg
    
    '''
        检查菜品是否存在
        1:  存在于基础菜单
        2:  存在于群菜单
        0:  不存在
    '''
    def food_exists(self, _food_: str) -> int:
        for food in self._data["basic_food"]:
            if food == _food_:
                return 1

        for group_id in self._data["group_food"]:
            for food in self._data["group_food"][group_id]:
                if food == _food_:
                    return 2
        
        return 0

    '''
        检查是否吃饱
    '''
    def eating_check(self, event: GroupMessageEvent) -> bool:
        user_id = str(event.user_id)
        group_id = str(event.group_id)
        return False if self._data["eating"][group_id][user_id] >= EATING_LIMIT else True

    '''
        添加至群菜单中 GROUP_ADMIN | GROUP_OWNER 权限
    '''
    def add_group_food(self, new_food: str, event: GroupMessageEvent) -> str:
        group_id = str(event.group_id)
        self._init_data(event)
        status = self.food_exists(new_food)
        if status == 1:
            return f"{new_food} 已在基础菜单中~"
        elif status == 2:
            return f"{new_food} 已在群特色菜单中~"

        self._data["group_food"][group_id].append(new_food)
        self.save()
        return f"{new_food} 已加入群特色菜单~"

    '''
        添加至基础菜单 SUPERUSER 权限
    '''
    def add_basic_food(self, new_food: str) -> str:
        status = self.food_exists(new_food)
        if status == 1:
            return f"{new_food} 已在基础菜单中~"
        elif status == 2:
            return f"{new_food} 已在群特色菜单中~"

        self._data["basic_food"].append(new_food)
        self.save()
        return f"{new_food} 已加入基础菜单~"

    '''
        从基础菜单移除 SUPERUSER 权限
        从群菜单中移除 GROUP_ADMIN | GROUP_OWNER 权限
    '''
    def remove_food(self, food_to_remove: str, event: GroupMessageEvent) -> str:
        user_id = str(event.user_id)
        group_id = str(event.group_id)
        
        status = self.food_exists(food_to_remove)
        if not status:
            return f"{food_to_remove} 不在菜单中哦~"

        # 在群菜单
        if status == 2:
            self._data["group_food"][group_id].remove(food_to_remove)
            self.save()
            return f"{food_to_remove} 已从群菜单中删除~"
        # 在基础菜单
        else:
            if user_id not in SUPERUSERS:
                return f"{food_to_remove} 在基础菜单中，非主人不可操作哦~"
            else:
                self._data["basic_food"].remove(food_to_remove)
                self.save()
                return f"{food_to_remove} 已从基础菜单中删除~"    

    def reset_eating(self) -> None:
        '''
            重置三餐eating times
        '''
        for group_id in self._data["eating"].keys():
            for user_id in self._data["eating"][group_id].keys():
                self._data["eating"][group_id][user_id] = 0
        
        self.save()

    def save(self) -> None:
        '''
            保存数据
        '''
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=4)
        
        with open(self.greating_file, 'w', encoding='utf-8') as f:
            json.dump(self._greating, f, ensure_ascii=False, indent=4)

    def show_menu(self, event: GroupMessageEvent, show_basic: bool) -> str:
        group_id = str(event.group_id)
        msg = []
        self._init_data(event)
        if len(self._data["group_food"][group_id]) > 0:
            msg += MessageSegment.text("---群特色菜单---\n")
            for food in self._data["group_food"][group_id]:
                msg += MessageSegment.text(f"{food}\n")

        if len(self._data["basic_food"]) > 0 and show_basic:
            msg += MessageSegment.text("---基础菜单---\n")
            for food in self._data["basic_food"]:
                msg += MessageSegment.text(f"{food}\n")
        
        if show_basic:
            return msg if len(msg) > 0 else "还没有菜单呢，可以[添加 菜名]哦~"
        else:
            return msg if len(msg) > 0 else "没有群特色菜单，可以[添加 菜名]哦~"
        
    '''
        干饭/摸鱼小助手，获取问候语，可能问候语为空返回None
        负责群发早餐、午餐、下午茶、晚餐、夜宵问候语
    '''
    def get2greating(self, meal: Meals) -> Optional[str]:
        if len(self._greating.get(meal.value)) > 0:
            greatings = self._greating[meal.value]
            return random.choice(greatings)
        else:
            return None

    '''
        增加问候语
        Reserved for next version
    '''
    def add_greating(self, new_greating: str, meal: Meals) -> str:
        self._greating[meal.value].append(new_greating)
        self.save()

        return f"{new_greating} 已加入 {meal.value} 问候~"

    '''
        移除问候语，通过索引移除
        Reserved for next version
    '''
    def remove_greating(self, remove_index: int, meal: Meals) -> str:
        greating = self._greating[meal.value].pop(remove_index)
        self.save()

        return f"{greating} 已从 {meal.value} 问候中移除~"


eating_manager = EatingManager(Path(WHAT2EAT_PATH))