import pytest
from weather.api import WeatherAPI

def test_get_current_success(mock_api):
    result = mock_api.get_current("北京")
    assert "city" in result
    assert result["temp"] == "25℃"

def test_invalid_city():
    api = WeatherAPI()
    result = api.get_current("哥谭市")
    assert "error" in result
