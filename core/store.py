from __future__ import annotations

from core.exceptions import StoreConnectionError, StoreDataError
from settings.settings import Setting


class StoreDescriptor:
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, '_store_data', {}).copy()

    def __set__(self, instance, value):
        if not isinstance(value, dict):
            raise StoreDataError('Хранилище должно быть словарём')
        setattr(instance, '_store_data', value)

    def __delete__(self, instance):
        if hasattr(instance, '_store_data'):
            delattr(instance, '_store_data')


class Store:
    _instance: Store | None = None
    _data = StoreDescriptor()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_store_data'):
            setattr(self, '_store_data', {})

    def get_store(self) -> dict:
        return self._data

    def set_store_data(self, data: dict) -> None:
        self._data = data


class DatabaseSession:
    def __init__(self, store: Store | None = None):
        self._db_connection_url = Setting().db_connection_url
        self._store = store or Store()

    def __enter__(self) -> Store:
        try:
            print(f'[DB] Подключение к базе: {self._db_connection_url}')
            print('[DB] Соединение успешно установлено.')
        except Exception as e:
            raise StoreConnectionError(f'Ошибка при подключении к базе: {e}')
        return self._store

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            print(f'[DB] Отключение от базы: {self._db_connection_url}')
            print('[DB] Соединение закрыто.')
        except Exception as e:
            raise StoreConnectionError(f'Ошибка при отключении от базы: {e}')
