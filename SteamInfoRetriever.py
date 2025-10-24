import datetime
import json
import json
import gevent
from steam.client import SteamClient

class AppInfoRetriever:
    def __init__(self):
        self.client = SteamClient()
        self.connect_timeout = 10
        self.connected = False

    def login(self):
        if not self.connected:
            if not self.client.connected:
                self.client.anonymous_login()
                self.client.verbose_debug = False
                self.connected = True

    def retrieve_app_info(self, app_id, retry_attempts=3):
        attempt = 0
        while attempt < retry_attempts:
            try:
                with gevent.Timeout(self.connect_timeout):
                    if not self.connected:
                        self.login()  # Ensure we're connected

                    print(f"Retrieving app info for app ID: {app_id}")

                    # Increase the timeout duration if necessary
                    info = self.client.get_product_info(apps=[app_id], timeout=120)
                    info_dict = json.loads(json.dumps(info, indent=2))
                    return info_dict

            except gevent.timeout.Timeout:
                self.client._connecting = False
                self.connected = False  # Mark connection as lost
                attempt += 1
                print(f"Attempt {attempt} - Connection timeout. Retrying...")
                if attempt >= retry_attempts:
                    raise Exception("Connection timeout after multiple attempts")

            except Exception as err:
                print(f"Failed to retrieve app info for app ID {app_id} on attempt {attempt}: {err}")
                self.connected = False  # Mark connection as lost
                attempt += 1
                if attempt >= retry_attempts:
                    raise Exception(f"Failed to retrieve app info for app ID {app_id} after multiple attempts: {err}")
        