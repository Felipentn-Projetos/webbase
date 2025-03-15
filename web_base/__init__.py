import re
import sys
from time import sleep
from pathlib import Path
from json import dumps
from pynguin.syswin import Winapi
from pynguin import DecoratorTools
from selenium.webdriver import Edge  # Chrome, Ie, IeOptions, Firefox
import undetected_chromedriver as uc
from selenium.common.exceptions import (
    InvalidArgumentException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.ie.service import Service as IeService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options as EdgeOptions

# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.select import Select
# from selenium.webdriver.firefox.options import Options as FirefoxOptions

sys.path.insert(0, str(Path(__file__).parent.absolute().parent.absolute()))


class WebBaseConfig:
    """Configuração do Navegador."""

    def __init__(
        self, download_path="", anonimus=False, hidden=False, browser="Chrome"
    ):
        self.service = None

        browser = browser.capitalize()

        settings = {
            "recentDestinations": [
                {
                    "id": "Save as PDF",
                    "origin": "local",
                    "account": "",
                }
            ],
            "selectedDestinationId": "Save as PDF",
            "version": 2,
        }
        self.browser = browser
        match browser:
            case "Chrome":
                self.options = uc.ChromeOptions()
                self.driver_config = uc.Chrome
                browser_name = "chrome"
            case "Edge":
                self.options = EdgeOptions()
                self.driver_config = Edge
                browser_name = "msedge"

        self.options.add_argument("--ignore-certificate-errors")

        if hidden:
            self.options.add_argument(f"--headless=new")

        if download_path:
            prefs = {
                "download.default_directory": download_path,
                "savefile.default_directory": download_path,
                "printing.print_preview_sticky_settings.appState": dumps(settings),
            }
            self.options.add_experimental_option("prefs", prefs)
            self.options.add_argument("--kiosk-printing")

        if anonimus:
            self.options.add_argument("--incognito")

        path = f"c:\\transformacao_digital_fis\\web_portable\\{browser}\\Application\\"

        if browser == "Ie":
            self.service = IeService(
                f"c:\\transformacao_digital_fis\\web_portable\\Edge\\Application\\IEDriverServer.exe"
            )
        else:
            self.binary_location = f"{path}{browser_name}.exe"
            self.driver_path = f"{path}{browser_name}driver.exe"


class WebBase(WebBaseConfig):
    """Configuração inicial do navegador e do driver."""

    def __init__(self, download_path="", anonimus=True, hidden=True, browser="Chrome"):
        super().__init__(download_path, anonimus, hidden, browser)
        self.download_path = download_path
        self.anonimus = anonimus
        self.hidden = hidden
        self.status = False
        self.browser = browser
        self.win = Winapi()

    def validate_driver(self):
        try:
            if self.driver.current_url:
                return True
        except Exception:
            return False

    def start_driver(self):
        """Start no driver com as opções pré-configuradas."""
        try:
            if self.browser == "Chrome":
                self.driver = self.driver_config(
                    options=self.options,
                    driver_executable_path=self.driver_path,
                    browser_executable_path=self.binary_location,
                )
            else:
                self.driver = self.driver_config(
                    service=self.service, options=self.options
                )
        except FileNotFoundError:
            raise Exception("Favor solicitar a instalação do Navegador!")
        except Exception as ex:
            try:
                self.__init__(self.user, self.email, self.password)
            except Exception:
                self.__init__(user=self.user, password=self.password)

            self.start_driver()
            return
        self.driver.maximize_window()
        self.status = True

    def restart_driver(self):
        """Fecha e abre um novo driver."""
        try:
            self.get_last_page()
        except Exception:
            self.close()
            self.start_driver()
        return True

    def get_last_page(self):
        return str(self.driver.current_url).split("/")[-1]

    def close(self):
        """Fecha o driver."""
        try:
            self.driver.quit()
            return True, "sucesso"
        except Exception as error:
            return False, error

    @DecoratorTools.loop_repet
    def navigate(self, url, count=3):
        """Navega até uma página."""
        try:
            self.driver.get(url)
            return True
        except TimeoutException:
            return False
        except WebDriverException:
            return False

    def remove_alert(self, msg: str = "", timeout=1):
        """Aceita o alerta."""
        try:
            if msg:
                WebDriverWait(self.driver, timeout).until(EC.alert_is_present(), msg)
            else:
                WebDriverWait(self.driver, timeout).until(EC.alert_is_present())

            self.driver.switch_to.alert.accept()
            return True
        except TimeoutException:
            pass
        return False

    def click_js(self, By, element, timeout=0.3):
        """Clica em um elemento atravez do javascript."""
        self.wait_clickable(By, element, timeout=timeout)
        try:
            if By == "id":
                self.driver.execute_script(
                    f"document.getElementById('{element}').click()"
                )
                sleep(0.03)
                return True
        except Exception:
            pass

        try:
            self.driver.find_element(By, element).click()
            sleep(0.03)
            return True
        except Exception as ex:
            pass

        try:
            self.driver.execute_script(
                "arguments[0].click();", self.driver.find_element(By, element)
            )
            sleep(0.03)
            return True
        except Exception as ex:
            pass

        return False

    @DecoratorTools.loop_repet
    def value_js(self, By, element, value="", timeout=0.3):
        """passa o value em um elemento atravez do javascript."""
        self.wait(By, element, timeout=timeout)

        if By == "id":
            self.clear_js(element)
        else:
            self.driver.find_element(By, element).clear()

        try:
            self.driver.find_element(By, element).send_keys(value)
        except Exception:
            pass

        if self.wait_inner_html(By, element, value, timeout=timeout):
            return True

        try:
            self.driver.execute_script(
                f'arguments[0].value = "{value}";',
                self.driver.find_element(By, element),
            )
        except Exception:
            pass

        if self.wait_inner_html(By, element, value, timeout=timeout):
            return True

        return False

    def print_pdf(self):
        """Realiza o print da janela atual e salva em pdf."""
        self.driver.execute_script("window.print();")

    def clear_js(self, element):
        """Limpa um input atravez do javascript, precisa ter ID."""
        self.driver.execute_script(f'document.getElementById("{element}").value=""')

    def full_loading(self, delay=10):
        sleep(0.5)
        WebDriverWait(self.driver, delay).until(
            lambda _: self.driver.execute_script("return document.readyState")
            == "complete"
        )

    @DecoratorTools.timeout
    def wait(self, by, element, present=True):
        """Aguarda um elemento estar ou não presente na página."""
        try:
            WebDriverWait(self.driver, 0.3).until(
                EC.presence_of_element_located((by, element))
            )
            if present:
                return True
        except InvalidArgumentException:
            if not present:
                return True
        except TimeoutException:
            if present:
                return False

            return True

        return False

    @DecoratorTools.timeout
    def wait_clickable(self, by, element, present=True):
        """Aguarda um elemento estar ou não presente na página."""
        try:
            WebDriverWait(self.driver, 0.3).until(
                EC.element_to_be_clickable((by, element))
            )
            if present:
                return True
        except InvalidArgumentException:
            if not present:
                return True
        except TimeoutException:
            if present:
                return False
            return True
        return False

    @DecoratorTools.timeout
    def wait_list_elements(self, elements: list) -> None:
        for by, element, present in elements:
            if self.wait(by, element, present, timeout=0.5):
                return element
        return False

    @DecoratorTools.timeout
    def wait_jquery(self, jquery: str, present=True):
        """Aguarda um elemento estar ou não presente na página."""
        if self.driver.execute_script(f"return $('{jquery}').length"):
            return present
        elif present:
            return False
        else:
            return True

    @DecoratorTools.timeout
    def wait_inner_html(
        self,
        by: str,
        element: str,
        regex: str = None,
        time_sleep: int = 0.1,
        timeout: int = 0.3,
    ):
        """
        Aguarda que o elemento possua algum valor interno nele (limite de timeout).
        """
        sleep(time_sleep)
        for _ in range(5):
            el = self.driver.find_element(by, element)
            html = el.get_attribute("value")
            if regex is not None:
                pattern = re.compile(".*?" + re.escape(regex) + ".*?")
                if re.search(pattern, html):
                    continue
            elif html:
                continue
            return False
        # el.send_keys(Keys.TAB)
        return True


if __name__ == "__main__":
    wb = WebBase(browser="Chrome")
    wb.start_driver()
    pass
