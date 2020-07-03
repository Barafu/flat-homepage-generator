from typing import List


import sys
import configparser
from pathlib import Path
from pprint import pprint
from collections import OrderedDict

import jinja2 as j2
from jinja2 import PackageLoader, FileSystemLoader


class PageItem:
    max_id = 0  # Counter for incrementig IDs.

    def __init__(self, data: dict):
        self.data = dict(data)
        PageItem.max_id += 1
        self.element_id = PageItem.max_id
        self.parent = None


class PageButton(PageItem):
    def build_style(self):
        """Create a string with CSS style of the button"""
        css_dict = {
            "color": "background-color",
            "text color": "color",
            "hover color": "",
        }
        css_commands = []
        for local_key, css_key in css_dict.items():
            css_commands.append(f"{css_key}:{self.data[local_key]}")
        css_text = ";".join(css_commands) + ";"
        return css_text


class PageList(PageItem):
    def __init__(self, data):
        self.buttons: List[PageButton] = []
        super().__init__(data)

    def add_button(self, button: PageButton):
        self.buttons.append(button)
        button.parent = self


class PageTab(PageItem):
    def __init__(self, data):
        self.pagelists: List[PageList] = []
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

    def get_all_buttons(self):
        """Return all buttons on the page, regardless of the list. Used in button_grid template"""
        for page_list in self.pagelists:
            for button in page_list.buttons:
                yield button


def main(args):
    settings = parse_config("test_config.ini")

    jenv = j2.Environment()
    jenv.loader = FileSystemLoader("templates")
    jenv.autoescape = j2.select_autoescape(["html", "xml"])
    jenv.trim_blocks = True
    jenv.lstrip_blocks = True
    template_name = settings["page"]["template"]
    template = jenv.get_template(f"{template_name}.jinja2")

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

    # Parse defaults
    page = dict(config["Page"])
    page_style = dict(config["Page Style"])
    button_style = dict(config["Button Style"])

    for i in ("page", "button_style", "page_style"):
        settings[i] = locals()[i]

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
                full_dict = dict(button_style)  # Copy default button settings
                full_dict.update(
                    butt_dict
                )  # and override them with this particular, if any
                butt_obj = PageButton(full_dict)
                temp_lists_reference[list_id].add_button(butt_obj)
            else:
                raise SyntaxError(f"No list with id {list_id}")

    settings["tabs"] = list(tabs.values())

    return settings


if __name__ == "__main__":
    main(sys.argv)
