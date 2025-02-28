import pytest
from pathlib import Path
from unittest.mock import Mock
from weather.api import WeatherAPI

@pytest.fixture
def mock_db(tmp_path):
    db_path = tmp_path / "test.db"
    return WeatherDatabase(db_path)

@pytest.fixture
def mock_api(monkeypatch):
    def mock_get(*args, **kwargs):
        mock_resp = Mock()
        mock_resp.json.return_value = {
            "status": "1",
            "infocode": "10000",
            "lives": [{
                "province": "北京",
                "city": "北京市",
                "weather": "晴",
                "temperature": "25",
                "reporttime": "2023-08-20 14:00:00"
            }]
        }
        return mock_resp
    monkeypatch.setattr(requests, "get", mock_get)
    return WeatherAPI()
