from typing import Any

from dotenv import dotenv_values
import requests as rq

from .common import ENV_FILE_NAME, ENV_TFL_APP_ID, ENV_TFL_APP_KEY, TFL_MODALITIES


class TflApi:
    def __init__(self):
        self.url_base = "https://api.tfl.gov.uk/"
        self.app_id, self.app_key = self._get_api_creds()

    @staticmethod
    def _get_api_creds() -> (str, str):
        env = dotenv_values(ENV_FILE_NAME)
        return env[ENV_TFL_APP_ID], env[ENV_TFL_APP_KEY]

    def _query(self, endpoint: str, params: dict[str, Any]) -> rq.Response:
        response = rq.get(
            self.url_base + endpoint,
            params={"app_id": self.app_id, "app_key": self.app_key} | params,
        )
        if not response.ok:
            raise Exception
        else:
            return response

    def search_stop_points(
        self, name: str, modes: list[TFL_MODALITIES]
    ) -> dict[str, Any]:
        search_response = self._query(
            "StopPoint/Search",
            params={
                "query": name,
                "modes": ",".join(modes),
            },
        )
        return search_response.json()
