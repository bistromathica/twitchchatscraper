from pydantic import BaseModel, PositiveInt
from typing import Optional, List
from pathlib import Path
import yaml
import logging


class Config(BaseModel):
    chats: List[str]
    db_url: str
    loop_seconds: Optional[PositiveInt]
    headless: Optional[bool]
    concurrency: Optional[PositiveInt] = 3

    class Config:
        extra = 'forbid'


defaults = {
    'chats': [{'name': 'OurChickenLife', 'where': 'twitch'}],
    'db_url': 'sqlite:///:memory:',
    'loop_seconds': 5,
    'headless': True,
    'concurrency': 3,
}


def load_config_file(config_file_path: str) -> Config:
    with open(config_file_path, 'r') as f:
        config_data = yaml.safe_load(f)
        logging.info(f"Loaded config from {config_file_path}")
    return Config(**config_data)


def get(custom=None):
    if custom:
        return load_config_file(custom)
    for path in ('/etc/twitchchatscraper.yaml', './twitchchatscraper.yaml'):
        if Path(path).is_file():
            return load_config_file(path)
    return Config(**defaults)
