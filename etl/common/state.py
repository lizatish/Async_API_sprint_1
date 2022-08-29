import abc
import json
import os
from typing import Any, Optional


class BaseStorage:
    """Базовый класс хранения данных."""

    @abc.abstractmethod
    def save_state(self, state: dict) -> None:
        """Сохранить состояние в постоянное хранилище."""
        pass

    @abc.abstractmethod
    def retrieve_state(self) -> dict:
        """Загрузить состояние локально из постоянного хранилища."""
        pass


class JsonFileStorage(BaseStorage):
    """Json-реализация хранилища данных."""

    def __init__(self, file_path: Optional[str]):
        """Инициализирует переменные класса.

        Args:
            file_path: Путь к json файлу
        """
        self.file_path = file_path

        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as read_file:
                json.dump({}, read_file)

    def save_state(self, state: dict):
        """Сохраняет состояние.

        Args:
            state: Состояние данных
        """
        with open(self.file_path, 'r') as read_file:
            state_data = json.load(read_file)

        for key_elem, val_elem in state.items():
            state_data[key_elem] = val_elem

        with open(self.file_path, 'w') as write_file:
            json.dump(state_data, write_file)

    def retrieve_state(self) -> dict:
        """Возвращает словарь состояния хранилища.

        Returns:
            dict: Словарь состояний хранилища
        """
        with open(self.file_path, 'r') as read_file:
            state_data = json.load(read_file)
        return state_data


class State:
    """Класс для хранения состояния при работе с данными.

    Нужен, чтобы постоянно не перечитывать данные с начала.
    Здесь представлена реализация с сохранением состояния в файл.
    В целом ничего не мешает поменять это поведение на работу с БД
    или распределённым хранилищем.
    """

    def __init__(self, storage: BaseStorage):
        """Инициализирует переменные класса.

        Args:
            storage: Экземпляр хранилища
        """
        self.storage = storage
        self.states = self.storage.retrieve_state()

    def set_state(self, key_elem: str, value_elem: Any):
        """Сохранить состояние.

        Args:
            key_elem: Ключ для сохранения
            value_elem: Значение для сохранения
        """
        self.storage.save_state({key_elem: value_elem})
        self.states[key_elem] = value_elem

    def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу.

        Args:
            key: Ключ

        Returns:
            Any: Данные хранилища по ключу
        """
        return self.states.get(key)
