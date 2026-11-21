"""aiogram FSM holatlarini PostgreSQL'da saqlash.

Bot qayta ishga tushsa ham yarim to'ldirilgan ariza, murojaat va boshqa jarayonlar yo'qolmaydi.
Redis kerak emas — mavjud PostgreSQL bazasidagi `fsm_storage` jadvali ishlatiladi.
"""
import json
from typing import Any, Mapping

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey

import db


def _key(key: StorageKey) -> str:
    return ":".join(str(p) for p in (key.bot_id, key.chat_id, key.user_id, key.thread_id or 0,
                                      key.business_connection_id or "", key.destiny))


class PostgresStorage(BaseStorage):
    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        value = state.state if isinstance(state, State) else state
        await db.fsm_set_state(_key(key), value)

    async def get_state(self, key: StorageKey) -> str | None:
        return await db.fsm_get_state(_key(key))

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        await db.fsm_set_data(_key(key), json.dumps(dict(data), ensure_ascii=False))

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        raw = await db.fsm_get_data(_key(key))
        return json.loads(raw) if raw else {}

    async def close(self) -> None:
        pass
