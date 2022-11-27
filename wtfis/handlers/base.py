import abc

from pydantic import ValidationError
from requests.exceptions import HTTPError, JSONDecodeError
from rich.console import Console
from rich.progress import Progress
from shodan.exception import APIError
from typing import Callable, List, Union

from wtfis.clients.ip2whois import Ip2WhoisClient
from wtfis.clients.ipwhois import IpWhoisClient
from wtfis.clients.passivetotal import PTClient
from wtfis.clients.shodan import ShodanClient
from wtfis.clients.virustotal import VTClient
from wtfis.models.common import WhoisType
from wtfis.models.ipwhois import IpWhoisMap
from wtfis.models.shodan import ShodanIpMap
from wtfis.models.virustotal import Domain, IpAddress
from wtfis.utils import error_and_exit, refang


def common_exception_handler(func: Callable) -> Callable:
    """ Decorator for handling common fetch errors """
    def inner(*args, **kwargs):
        progress: Progress = args[0].progress  # args[0] is the method's self input
        try:
            func(*args, **kwargs)
        except (HTTPError, JSONDecodeError, APIError) as e:
            progress.stop()
            error_and_exit(f"Error fetching data: {e}")
        except ValidationError as e:
            progress.stop()
            error_and_exit(f"Data model validation error: {e}")
    return inner


class BaseHandler(abc.ABC):
    def __init__(
        self,
        entity: str,
        console: Console,
        progress: Progress,
        vt_client: VTClient,
        ip_enricher_client: Union[IpWhoisClient, ShodanClient],
        whois_client: Union[Ip2WhoisClient, PTClient, VTClient],
    ):
        # Process-specific
        self.entity = refang(entity)
        self.console = console
        self.progress = progress

        # Clients
        self._vt = vt_client
        self._enricher = ip_enricher_client
        self._whois = whois_client

        # Dataset containers
        self.vt_info = None    # type: Union[Domain, IpAddress]        # type: ignore
        self.ip_enrich = None  # type: Union[IpWhoisMap, ShodanIpMap]  # type: ignore
        self.whois = None      # type: WhoisType                       # type: ignore

        # Warning messages container
        self.warnings = []  # type: List[str]

    @abc.abstractmethod
    def fetch_data(self) -> None:
        """ Main method that controls what get fetched """
        return NotImplemented  # type: ignore  # pragma: no coverage
