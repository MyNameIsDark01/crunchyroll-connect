import requests

from .utils.collections import Series, Collection
from .utils.types import RequestType, Filters, Genres
from .utils.user import Config, User, datetime
from .utils.media import Media


def validate_request(req):
    if not isinstance(req, dict):
        return False

    if req['error'] is False and req['code'] == 'ok':
        return True
    else:
        return False


def login_required(function):
    def wrap(self, *args, **kwargs):
        if self.settings.store['user'] is not None:
            return function(self, *args, **kwargs)
        else:
            raise ValueError('Must be logged in to access to function')

    return wrap


def session_required(function):
    def wrap(self, *args, **kwargs):
        if self.settings.store['session_id'] != "":
            return function(self, *args, **kwargs)
        else:
            raise ValueError('Illegal action: A valid session must be started.')

    return wrap


class CrunchyrollServer:
    def __init__(self):
        self.domain = 'api.crunchyroll.com'
        self.token = 'LNDJgOit5yaRIWN'
        self.device_type = 'com.crunchyroll.windows.desktop'
        self.version = 0
        self.english = 'enUS'
        self.settings = Config()
        self.settings.init_store()
        self.session = requests.Session()

    def get_url(self, req):
        if not isinstance(req, RequestType):
            return "https://{}".format(self.domain)
        else:
            return "https://{}/{}.{}.json".format(self.domain, req.value, self.version)

    def start_session(self):
        if self.settings.store['session_id'] == "":
            url = self.get_url(RequestType.CREATE_SESSION)

            device_id = self.settings.store['device_id']

            params = {
                'access_token': self.token,
                'device_type': self.device_type,
                'device_id': device_id,
                'version': 1.1
            }

            response = self.session.post(url, params, cookies=self.session.cookies).json()
            if validate_request(response):
                self.settings.store['session_id'] = response['data']['session_id']
                self.settings.store['device_id'] = device_id

            else:
                raise ValueError('Request Failed!\n\n{}'.format(response))

    @session_required
    def login(self, account=None, password=None):

        if self.settings.store['user'] is not None:
            current_datetime = datetime.now().astimezone().replace(microsecond=0)
            expires = self.settings.store['user'].expires

            if expires <= current_datetime:
                # If login session expired, login again
                self.logout()

            else:
                print('User is already logged in')
                return True

        if account is None:
            account = self.settings.store['account']

        if password is None:
            password = self.settings.store['password']

        url = self.get_url(RequestType.LOGIN)
        data = {
            'account': account,
            'password': password,
            'session_id': self.settings.store['session_id']
        }

        response = self.session.post(url, data).json()
        # Note to check for expiration of the session and clear data to prevent re-using the same session maybe.
        if validate_request(response):
            # Create user object
            user_data = response['data']['user']
            user = User(
                user_id=user_data['user_id'],
                etp_guid=user_data['etp_guid'],
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                premium=user_data['premium'],
                access_type=user_data['access_type'],
                created=user_data['created'],
                expires=response['data']['expires'],
                is_publisher=user_data['is_publisher']
            )

            self.settings.store['account'] = account
            self.settings.store['password'] = password
            self.settings.store['auth'] = response['data']['auth']
            self.settings.store['user'] = user

            return True

        return False

    @login_required
    @session_required
    def logout(self):
        url = self.get_url(RequestType.LOGOUT)
        data = {
            'user': self.settings.store['user_id'],
            'session_id': self.settings.store['session_id']
        }

        response = self.session.post(url, data, cookies=self.session.cookies)

        if validate_request(response.json()):
            self.settings.clear_store()
            self.session.cookies.clear()

        else:
            raise ValueError('Request Failed!\n\n{}'.format(response))

    def end_session(self):
        self.settings.close_store()
        self.session.close()

    @login_required
    @session_required
    def fetch_locales(self):
        url = self.get_url(RequestType.LIST_LOCALES)

        data = {
            'session_id': self.settings.store['session_id'],
            'device_type': self.device_type,
            'device_id': self.settings.store['device_id']
        }
        response = self.session.get(url, data).json()

        if validate_request(response):
            self.settings.store['cr_locales'] = response['data']
            return True

        return False

    @login_required
    @session_required
    def get_series_id(self, query):
        """
        Searches for the seriesID of an anime in the Crunchyroll catalogue. If it is present return the ID
        :param query: the name of the anime
        :return: the Crunchyroll series ID
        """
        url = self.get_url(RequestType.AUTOCOMPLETE)

        data = {
            'session_id': self.settings.store['session_id'],
            'device_type': self.device_type,
            'device_id': self.settings.store['device_id'],
            'q': query,
            'media_types': 'anime',
            'limit': 10  # Artificially limit to 10 results
        }

        response = self.session.get(url, params=data, cookies=self.session.cookies).json()
        if validate_request(response):
            search_results = response['data']
            if len(search_results) < 1:
                return 269071 #Some random value

            print(response)

            for anime in response['data']:

                anime_name = anime['name'].lower()
                series_id = anime['series_id']
                search_query = query.lower()

                if search_query in anime_name:
                    return series_id

                else:
                    continue
        else:
            raise ValueError('Request Failed!\n\n{}'.format(response))

    @login_required
    @session_required
    def get_collections(self, series_id):

        url = self.get_url(RequestType.LIST_COLLECTION)

        data = {
            'session_id': self.settings.store['session_id'],
            'device_type': self.device_type,
            'device_id': self.settings.store['device_id'],
            'media_type': 'anime',
            'series_id': series_id
        }

        response = self.session.get(url, params=data, cookies=self.session.cookies).json()

        if validate_request(response):
            data = response['data']

            collections = []
            for el in data:
                collection = Collection(
                    availability_notes=el['availability_notes'],
                    series_id=series_id,
                    collection_id=el['collection_id'],
                    etp_guid=el['etp_guid'],
                    series_etp_guid=el['series_etp_guid'],
                    complete=el['complete'],
                    name=el['name'],
                    description=el['description'],
                    landscape_image=el['landscape_image'],
                    portrait_image=el['portrait_image'],
                    season=el['season'],
                    created=el['created']
                )

                collections.append(collection)

            return collections
        else:
            raise ValueError('Request Failed!\n\n{}'.format(response))

    @login_required
    @session_required
    def filter_series(self, limit: int = 10, offset: int = 0, filter_type: Filters = None, filter_tag: str = None):
        """
        Returns a list of series
        :param limit: The maximum number of items to return
        :param filter_tag: The tag, if any to be associated with the filter. Only if filter_type == PREFIX or TAG
        :param filter_type: The filter type as defined in utils.types.Filters
        :param offset: offset from the start to return. This enables a pagination system
        :return:
        """
        url = self.get_url(RequestType.LIST_SERIES)

        # If the passed in value is a genre get the string value
        if isinstance(filter_tag, Genres):
            filter_tag = filter_tag.value

        if filter_tag is not None and (filter_type == Filters.PREFIX or filter_type == Filters.TAG):
            tag = filter_type.value + filter_tag
        elif filter_type is not None:
            tag = filter_type.value
        else:
            tag = None

        data = {
            'session_id': self.settings.store['session_id'],
            'device_type': self.device_type,
            'device_id': self.settings.store['device_id'],
            'media_type': 'anime',
            'limit': limit,
            'offset': offset,
            'filter': tag
        }

        response = self.session.get(url, params=data, cookies=self.session.cookies).json()
        if validate_request(response):
            series = []

            for el in response['data']:
                series.append(Series(
                    series_id=el['series_id'],
                    etp_guid=el['etp_guid'],
                    name=el['name'],
                    description=el['description'],
                    url=el['url'],
                    landscape_image=el['landscape_image'],
                    portrait_image=el['portrait_image'],
                ))

            return series

        else:
            raise ValueError('Request Failed!\n\n{}'.format(response))

    @login_required
    @session_required
    def get_episodes(self, collection_id, limit=1000, offset=0):
        url = self.get_url(RequestType.LIST_MEDIA)

        data = {
            'session_id': self.settings.store['session_id'],
            'device_type': self.device_type,
            'device_id': self.settings.store['device_id'],
            'media_type': 'anime',
            'limit': limit,
            'offset': offset,
            'collection_id': collection_id
        }

        response = self.session.get(url, params=data, cookies=self.session.cookies).json()

        if validate_request(response):
            media_list = []
            episode_list = response['data']

            for ep in episode_list:
                media_list.append(Media(
                    media_id=ep['media_id'],
                    etp_guid=ep['etp_guid'],
                    collection_id=ep['collection_id'],
                    collection_etp_guid=ep['collection_etp_guid'],
                    series_id=ep['series_id'],
                    series_etp_guid=ep['series_etp_guid'],
                    episode_number=ep['episode_number'],
                    name=ep['name'],
                    description=ep['description'],
                    screenshot_image=ep['screenshot_image'],
                    bif_url=ep['bif_url'],
                    url=ep['url'],
                    clip=ep['clip'],
                    available=ep['available'],
                    premium_available=ep['premium_available'],
                    free_available=ep['free_available'],
                    availability_notes=ep['availability_notes'],
                    created=ep['created'],
                    playhead=ep['playhead']))

            return media_list

        else:
            raise ValueError('Request Failed!\n\n{}'.format(response))

    @login_required
    @session_required
    def get_stream(self, media_id):
        url = self.get_url(RequestType.INFO)

        data = {
            'session_id': self.settings.store['session_id'],
            'device_type': self.device_type,
            'device_id': self.settings.store['device_id'],
            'media_type': 'anime',
            'media_id': media_id,
            'fields': 'media.stream_data,media.playhead'
        }

        response = self.session.get(url, params=data, cookies=self.session.cookies).json()

        if validate_request(response):
            return response['data']['stream_data']

        else:
            raise ValueError('Request Failed!\n\n{}'.format(response))

