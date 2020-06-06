import jinja2 as j2

import sys
import configparser
from pathlib import Path
from pprint import pprint
from collections import OrderedDict

from jinja2 import PackageLoader, FileSystemLoader


class PageItem:
    def __init__(self, data: dict):
        for name, value in data.items():
            setattr(self, name, value)
        self.parent = None


class PageButton(PageItem):
    pass


class PageList(PageItem):
    def __init__(self, data):
        self.buttons = []
        super().__init__(data)

    def add_button(self, button: PageButton):
        self.buttons.append(button)
        button.parent = self


class PageTab(PageItem):
    def __init__(self, data):
        self.pagelists = []
        super().__init__(data)

    def add_list(self, page_list: PageList):
        self.pagelists.append(page_list)

    @property
    def width(self) -> str:
        if not self.pagelists or len(self.pagelists) > 3:
            return "100%"
        # width = max(30, 100 // len(self.pagelists)
        else:
            width = 25 * len(self.pagelists)
            return f"{width}%"


def main(args):
    jenv = j2.Environment()
    jenv.loader = FileSystemLoader("templates")
    jenv.autoescape = j2.select_autoescape(["html", "xml"])
    jenv.trim_blocks = True
    jenv.lstrip_blocks = True
    template = jenv.get_template("vertical_list.jinja2")
    settings = parse_config("test_config.ini")
    # pprint(settings)
    content = template.render(settings)
    with open("generated.html", "w") as f:
        f.writelines(content)


def parse_config(settings_file_name: str):
    config = configparser.ConfigParser()
    settings_file = Path("test_config.ini")
    settings_file = Path(settings_file_name)
    if not settings_file.is_file():
        raise FileNotFoundError(f"Settings file {settings_file_name} was not found!")
    config.read(settings_file)
    settings = dict()

    # Parse tabs
    tabs = OrderedDict()
    for c in config.sections():
        if c[:4] == "Tab:":
            tab_dict = dict(config[c])
            tab_id = c[4:]
            tab_dict["id"] = tab_id
            tab_obj = PageTab(tab_dict)
            tabs[tab_id] = tab_obj

    # parse button lists
    temp_lists_reference = dict()
    for c in config.sections():
        if c[:5] == "List:":
            list_dict = dict(config[c])  # Ineffective, but who cares
            tab_id = list_dict["tab"]
            if tab_id in tabs.keys():
                list_id = c[5:]
                list_dict["id"] = list_id
                list_obj = PageList(list_dict)
                tabs[tab_id].add_list(list_obj)
                temp_lists_reference[list_id] = list_obj
            else:
                raise SyntaxError(f"No tab with id {tab_id}")

    for c in config.sections():
        if "url" in config[c]:
            butt_dict = dict(config[c])
            list_id = butt_dict["list"]
            if list_id in temp_lists_reference.keys():
                butt_obj = PageButton(butt_dict)
                temp_lists_reference[list_id].add_button(butt_obj)
            else:
                raise SyntaxError(f"No list with id {list_id}")

    # Parse defaults
    page_style = dict(config["Page Style"])
    button_style = dict(config["Button Style"])

    settings = dict()
    settings["tabs"] = list(tabs.values())
    for i in ("button_style", "page_style"):
        settings[i] = locals()[i]

    return settings


if __name__ == "__main__":
    main(sys.argv)
