import logging
import os
import re
from abc import ABC, abstractmethod
from time import sleep
from typing import Self, TypeVar, Type

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, InvalidSessionIdException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app.orchestrator.exceptions import UnsupportedConferencingPlatformError
from app.schema import Conference, ConferencingPlatform

BOT_NAME = 'Meeting Recorder'

REMOTE_ADDRESS = os.getenv('REMOTE_ADDRESS')

WAIT_DURATION_SECONDS = 5
WAIT_LONG_DURATION_SECONDS = 20 * 60

ZOOM_URL_TEMPLATE = 'https://us04web.zoom.us/wc/{}/join?pwd={}'
URL_PATTERN = r'/j/(\d+)\?pwd=([^&]+)'

Bot = TypeVar('Bot', bound='ConferenceBot')

log = logging.getLogger(__name__)


def from_conference(conference: Conference) -> Bot:
    match conference.platform:
        case ConferencingPlatform.ZOOM:
            return ZoomBot(conference, os.getenv('ZOOM_BROWSER_VERSION'))
        case ConferencingPlatform.MEET:
            return GoogleMeetBot(
                conference, os.getenv('MEET_BROWSER_VERSION')
            )
        case _:
            raise UnsupportedConferencingPlatformError(
                'Link of unsupported conferencing platform provided.'
            )


def _configure_options(
    video_name: str, browser_version: str
) -> webdriver.ChromeOptions:
    options = webdriver.ChromeOptions()

    options.add_argument('--start-maximized')
    options.add_argument('--use-fake-ui-for-media-stream')
    options.add_argument('--use-fake-device-for-media-stream')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-blink-features')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--incognito')

    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('prefs', {
        'profile.default_content_setting_values.media_stream_mic': 1,
        'profile.default_content_setting_values.media_stream_camera': 1,
        'profile.default_content_setting_values.geolocation': 0,
        'profile.default_content_setting_values.notifications': 1
    })

    options.set_capability('browserName', os.getenv('BROWSER_NAME'))
    options.set_capability('browserVersion', browser_version)
    options.set_capability('selenoid:options', {
        'enableVideo': eval(os.getenv('ENABLE_VIDEO')),
        'enableVNC': eval(os.getenv('ENABLE_VNC')),
        'sessionTimeout': os.getenv('SESSION_TIMEOUT'),
        'videoFrameRate': int(os.getenv('VIDEO_FRAME_RATE')),
        'videoName': video_name
    })
    return options


def _prepare_participant_name(conference: Conference) -> str:
    return f'{conference.settings.participant_name} | {BOT_NAME}'


class ConferenceBot(ABC):
    @abstractmethod
    def __init__(
        self: Self, conference: Conference, browser_version: str
    ) -> None:
        self._conference = conference
        self._participant_name = _prepare_participant_name(conference)
        self._browser_version = browser_version

    @abstractmethod
    def join_conference(self: Self) -> None:
        ...

    @abstractmethod
    def send_message(self: Self) -> None:
        ...

    @abstractmethod
    def leave_conference(self: Self) -> None:
        ...


class ZoomBot(ConferenceBot):

    _SELECTORS: dict[str, tuple[str, str]] = {
        'name_input': (By.ID, 'input-for-name'),
        'join_audio_btn': (By.CSS_SELECTOR, '.join-audio-by-voip > button'),
        'leave_btn': 
            (By.CSS_SELECTOR, '.footer__leave-btn-container > button'),
        'confirm_leave_btn': 
            (By.CSS_SELECTOR, '.leave-meeting-options__inner > button')
    }

    def __init__(
        self: Self, conference: Conference, browser_version: str
    ) -> None:
        super().__init__(conference, browser_version)

        self._driver = webdriver.Remote(
            REMOTE_ADDRESS,
            options=_configure_options(
                self._conference.recording.filename, self._browser_version
            )
        )

        self._wait = WebDriverWait(self._driver, WAIT_DURATION_SECONDS)
        self._long_wait = WebDriverWait(
            self._driver, WAIT_LONG_DURATION_SECONDS
        )

        self._driver.get(
            self._transform_invite_link(self._conference.invite_link)
        )

    def join_conference(self: Self) -> None:
        # Input participant name and join
        self._input_info_and_join()
        
        # Waiting in the guest room for joining audio
        self._connect_audio()

    def send_message(self: Self) -> None:
        pass

    def leave_conference(self: Self) -> None:
        # Click Leave
        leave_btn = self._driver.find_element(*self._SELECTORS['leave_btn'])
        leave_btn.click()

        # Confirm leave
        self._confirm_leave()

        self._driver.quit()

    @staticmethod
    def _transform_invite_link(invite_link: str) -> str:
        match_ = re.search(URL_PATTERN, invite_link)
        return ZOOM_URL_TEMPLATE.format(match_.group(1), match_.group(2))

    def _input_info_and_join(self: Self) -> None:
        try:
            input_ = self._wait.until(
                EC.presence_of_element_located(self._SELECTORS['name_input'])
            )
        except TimeoutException as e:
            log.exception(e)
        else:
            input_.send_keys(self._participant_name)
            input_.send_keys(Keys.RETURN)

    def _connect_audio(self: Self) -> None:
        try:
            join_audio_btn = self._long_wait.until(
                EC.element_to_be_clickable(self._SELECTORS['join_audio_btn'])
            )
        except TimeoutException as e:
            # Host doesn't admit bot or already removed bot
            log.exception(e)
        else:
            join_audio_btn.click()

    def _confirm_leave(self: Self) -> None:
        try:
            confirm_leave_btn = self._wait.until(
                EC.element_to_be_clickable(
                    self._SELECTORS['confirm_leave_btn']
                )
            )
        except TimeoutException as e:
            log.exception(e)
        else:
            confirm_leave_btn.click()
    
    def __del__(self) -> None:
        try:
            self._driver.quit()
        except InvalidSessionIdException:
            pass


class GoogleMeetBot(ConferenceBot):

    _SELECTORS: dict[str, tuple[str, str]] = {
        'name_input': (By.CSS_SELECTOR, 'input[jsname="YPqjbf"]'),
        'micro_and_camera_btns': (By.CSS_SELECTOR, 'div[jsname="BOHaEe"]'),
        'popup_ok_btn': (By.CSS_SELECTOR, 'button[jsname="EszDEe"]'),
        'leave_btn': (By.CSS_SELECTOR, 'button[jsname="CQylAd"]')
    }

    _DELAY_SECONDS = 1
    _TYPING_DELAY_SECONDS = 0.2

    def __init__(
        self: Self, conference: Conference, browser_version: str
    ) -> None:
        super().__init__(conference, browser_version)

        self._driver = webdriver.Remote(
            REMOTE_ADDRESS,
            options=_configure_options(
                self._conference.recording.filename, self._browser_version
            )
        )

        self._wait = WebDriverWait(self._driver, WAIT_DURATION_SECONDS)
        self._long_wait = WebDriverWait(
            self._driver, WAIT_LONG_DURATION_SECONDS
        )

        self._driver.get(self._conference.invite_link)

    def join_conference(self: Self) -> None:
        # Joining meeting
        self._prepare_to_join()
        
        # Closing security pop up
        self._close_popup()

    def send_message(self: Self) -> None:
        pass

    def leave_conference(self: Self) -> None:
        leave_btn = self._driver.find_element(*self._SELECTORS['leave_btn'])
        leave_btn.click()

        self._driver.quit()

    def _prepare_to_join(self: Self) -> None:
        try:
            input_ = self._wait.until(
                EC.presence_of_element_located(self._SELECTORS['name_input'])
            )
            micro_btn, camera_btn = self._driver.find_elements(
                *self._SELECTORS['micro_and_camera_btns']
            )
        except TimeoutException as e:
            log.exception(e)
        else:
            self._input_name_and_prepare_inputs(input_, micro_btn, camera_btn)

    def _input_name_and_prepare_inputs(
        self: Self,
        input_: WebElement,
        micro_btn: WebElement,
        camera_btn: WebElement
    ) -> None:
        sleep(self._DELAY_SECONDS)
        micro_btn.click()

        sleep(self._DELAY_SECONDS)
        camera_btn.click()

        sleep(self._DELAY_SECONDS)
        for letter in self._participant_name:
            input_.send_keys(letter)
            sleep(self._TYPING_DELAY_SECONDS)

        sleep(self._DELAY_SECONDS)
        input_.send_keys(Keys.RETURN)

    def _close_popup(self: Self) -> None:
        try:
            ok_btn = self._long_wait.until(
                EC.presence_of_element_located(
                    self._SELECTORS['popup_ok_btn']
                )
            )
        except TimeoutException as e:
            log.exception(e)
        else:
            ok_btn.click()

    def __del__(self) -> None:
        try:
            self._driver.quit()
        except InvalidSessionIdException:
            pass
