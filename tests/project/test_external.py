import httpx
import pytest
from httpx import Response

from apps.project.services import fetch_external_posts


@pytest.mark.services
async def test_fetch_external_posts(mocker):
    """Тест асинхронного запроса к внешнему API с моками."""
    fake_data = [{'id': 1, 'title': 'mock post'}]
    url = 'https://jsonplaceholder.typicode.com/posts'

    mock_response = Response(
        200, json=fake_data, request=httpx.Request('GET', url)
    )

    mock_get = mocker.patch(
        'apps.project.services.httpx.AsyncClient.get',
        return_value=mock_response,
    )

    result = await fetch_external_posts(limit=1)

    assert result == fake_data
    mock_get.assert_called_once_with(url, params={'_limit': 1, '_page': 1})
