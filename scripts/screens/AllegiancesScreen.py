from typing import Union, Dict, Optional

import i18n
import pygame
import pygame_gui
from pygame_gui.core import ObjectID

from scripts.cat.cats import Cat
from scripts.game_structure.game_essentials import game
from scripts.game_structure.screen_settings import MANAGER
from scripts.game_structure.ui_elements import (
    UIImageButton,
    UIDropDownContainer,
    UISurfaceImageButton,
)
from scripts.utility import (
    get_text_box_theme,
    ui_scale,
    get_alive_clan_queens,
    get_alive_outside_queens,
    ui_scale_offset,
    adjust_list_text,
    event_text_adjust,
)
from .Screens import Screens
from scripts.ui.generate_button import ButtonStyles, get_button_dict
from ..cat.enums import CatRank
from ..game_structure.ui_elements import UIModifiedScrollingContainer


class AllegiancesScreen(Screens):
    allegiance_list = []

    def __init__(self, name=None):
        super().__init__(name)
        self.names_boxes = None
        self.ranks_boxes = None
        self.scroll_container = None
        self.heading = None
        self.cat_list_bar = None
        self.current_group = "clan"
        self.living_cats = []
        self.cat_list_bar_elements: Dict[
            str,
            Union[
                UIImageButton,
                UISurfaceImageButton,
                pygame_gui.elements.UIImage,
                pygame_gui.elements.UITextEntryLine,
                None,
            ],
        ] = {
            "choose_group_button": None,
        }
        self.living_groups_container = None
        self.choose_living_dropdown = None
        self.choose_group_buttons = {}
        self.sort_by_buttons: Dict[str, Optional[UISurfaceImageButton]] = {
            "view_your_clan_button": None,
            "view_cotc_button": None,
            "view_oc0_button": None,
            "view_oc1_button": None,
            "view_oc2_button": None,
            "view_oc3_button": None,
            "view_oc4_button": None,
        }

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            element = event.ui_element
            if element == self.cat_list_bar_elements["choose_group_button"]:
                if self.choose_living_dropdown.is_open:
                    self.choose_living_dropdown.close()
                else:
                    self.choose_living_dropdown.open()
            elif element in self.choose_group_buttons.values():
                self.current_page = 1
                # close dropdowns
                self.choose_living_dropdown.close()
                # get cat list for button pressed, then update
                if element == self.choose_group_buttons["view_your_clan_button"]:
                    self.get_your_clan_cats()
                elif element == self.choose_group_buttons["view_cotc_button"]:
                    self.get_cotc_cats()
                elif element == self.choose_group_buttons["view_oc0_button"]:
                    self.get_oc_cats(0)
                elif element == self.choose_group_buttons["view_oc1_button"]:
                    self.get_oc_cats(1)
                elif element == self.choose_group_buttons["view_oc2_button"]:
                    self.get_oc_cats(2)
                elif element == self.choose_group_buttons["view_oc3_button"]:
                    self.get_oc_cats(3)
                elif element == self.choose_group_buttons["view_oc4_button"]:
                    self.get_oc_cats(4)
                self.update_cat_list()
            self.menu_button_pressed(event)
            self.mute_button_pressed(event)

    def on_use(self):
        super().on_use()

    def screen_switches(self):
        super().screen_switches()

        # BAR CONTAINER
        self.cat_list_bar = pygame_gui.core.UIContainer(
            ui_scale(pygame.Rect((0, 115), (700, 400))),
            object_id="#cat_list_bar",
            starting_height=3,
            manager=MANAGER,
            anchors={"leftx": "leftx"},
        )

        # CHOOSE GROUP DROPDOWN
        self.cat_list_bar_elements["choose_group_button"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((0, 0), (190, 34))),
            "screens.list.choose_group",
            get_button_dict(ButtonStyles.DROPDOWN, (190, 34)),
            container=self.cat_list_bar,
            object_id="@buttonstyles_dropdown",
            manager=MANAGER,
            starting_height=1,
            anchors={"leftx": "leftx"},
        )

        # living groups
        self.living_groups_container = pygame_gui.elements.UIAutoResizingContainer(
            ui_scale(pygame.Rect((0, 0), (0, 0))),
            container=self.cat_list_bar,
            object_id="#choose_group_container",
            manager=MANAGER,
            starting_height=1,
            anchors={"leftx": "leftx"},
        )

        y_pos = 32
        screens_list = [
            ("screens.list.your_clan", "#view_your_clan_button"),
            ["screens.list.cotc", "#view_cotc_button"],
            [f"{game.clan.all_clans[0].name}Clan", "#view_oc0_button"],
            [f"{game.clan.all_clans[1].name}Clan", "#view_oc1_button"],
            [f"{game.clan.all_clans[2].name}Clan", "#view_oc2_button"],
        ]
        if (len(game.clan.all_clans) >= 4) :
            screens_list.append((f"{game.clan.all_clans[3].name}Clan", "#view_oc3_button"))
        if (len(game.clan.all_clans) == 5) :
            screens_list.append((f"{game.clan.all_clans[4].name}Clan", "#view_oc4_button"))

        for text, object_id in screens_list:
            self.choose_group_buttons[object_id.strip("#")] = UISurfaceImageButton(
                ui_scale(pygame.Rect((0, y_pos), (190, 34))),
                text,
                get_button_dict(ButtonStyles.DROPDOWN, (190, 34)),
                container=self.living_groups_container,
                object_id=ObjectID(class_id="@buttonstyles_dropdown", object_id=None),
                starting_height=2,
                manager=MANAGER,
            )
            y_pos += 32

        self.choose_living_dropdown = UIDropDownContainer(
            self.living_groups_container.relative_rect,
            container=self.cat_list_bar,
            object_id="#choose_living_dropdown",
            starting_height=1,
            parent_button=self.cat_list_bar_elements["choose_group_button"],
            child_button_container=self.living_groups_container,
            manager=MANAGER,
        )

        self.choose_living_dropdown.close()
        self.choose_living_dropdown.show()
        
        # Heading
        self.heading = pygame_gui.elements.UITextBox(
            "screens.allegiances.heading",
            ui_scale(pygame.Rect((0, 115), (400, 40))),
            text_kwargs={"clan_name": game.clan.name},
            object_id=get_text_box_theme("#text_box_34_horizcenter_vertcenter"),
            manager=MANAGER,
            anchors={"centerx": "centerx"},
        )

        # Set Menu Buttons.
        self.show_menu_buttons()
        self.show_mute_buttons()
        self.set_disabled_menu_buttons(["allegiances"])
        self.update_heading_text(f"{game.clan.name}Clan")

        self.scroll_container = UIModifiedScrollingContainer(
            ui_scale(pygame.Rect((50, 165), (715, 470))),
            allow_scroll_x=False,
            allow_scroll_y=True,
            manager=MANAGER,
        )

        self.get_cat_list()
        self.update_cat_list()

    def exit_screen(self):
        self.current_group = "clan"
        for x in self.ranks_boxes:
            x.kill()
        del self.ranks_boxes
        for x in self.names_boxes:
            x.kill()
        del self.names_boxes
        self.scroll_container.kill()
        del self.scroll_container
        self.heading.kill()
        del self.heading
        self.living_groups_container.kill()
        self.choose_living_dropdown.kill()
        self.cat_list_bar.kill()

    @staticmethod
    def generate_one_entry(cat, extra_details=""):
        """Extra Details will be placed after the cat description, but before the apprentice (if they have one)."""
        output = f"{str(cat.name).upper()} - {cat.describe_cat()} {extra_details}"

        if len(cat.apprentice) == 0:
            return event_text_adjust(Cat, output, main_cat=cat)

        output += f"\n      {i18n.t('general.apprentice', count=len(cat.apprentice)).upper()}: "
        output += adjust_list_text(
            [
                str(Cat.fetch_cat(i).name).upper()
                for i in cat.apprentice
                if Cat.fetch_cat(i)
            ]
        ).upper()

        return event_text_adjust(Cat, output, main_cat=cat)
    
    def get_cat_list(self):
        """
        grabs the correct cat list for current group
        """
        if self.current_group:
            if self.current_group == "cotc":
                self.get_cotc_cats()
            elif self.current_group == "oc0":
                self.get_oc_cats(0)
            elif self.current_group == "oc1":
                self.get_oc_cats(1)
            elif self.current_group == "oc2":
                self.get_oc_cats(2)
            elif self.current_group == "oc3":
                self.get_oc_cats(3)
            elif self.current_group == "oc4":
                self.get_oc_cats(4)
            else:
                self.get_your_clan_cats()
        else:
            self.get_your_clan_cats()

    def update_cat_list(self):
        """
        updates the cat list and display, search text is taken into account
        """
        if self.heading:
            self.heading.kill()
        
        if self.current_group == "clan":
            self.set_bg(None)
            self.heading = pygame_gui.elements.UITextBox(
            "screens.allegiances.heading",
            ui_scale(pygame.Rect((0, 115), (400, 40))),
            text_kwargs={"clan_name": game.clan.name},
            object_id=get_text_box_theme("#text_box_34_horizcenter_vertcenter"),
            manager=MANAGER,
            anchors={"centerx": "centerx"},
            )
        elif self.current_group == "cotc":
            self.set_bg(None)
            self.heading = pygame_gui.elements.UITextBox(
            "screens.allegiances.heading",
            ui_scale(pygame.Rect((0, 115), (400, 40))),
            text_kwargs={"clan_name": "Cats Outside the "},
            object_id=get_text_box_theme("#text_box_34_horizcenter_vertcenter"),
            manager=MANAGER,
            anchors={"centerx": "centerx"},
            )
        elif self.current_group == "oc0":
            self.set_bg(None)
            self.heading = pygame_gui.elements.UITextBox(
            "screens.allegiances.heading",
            ui_scale(pygame.Rect((0, 115), (400, 40))),
            text_kwargs={"clan_name": (game.clan.all_clans[0]).name},
            object_id=get_text_box_theme("#text_box_34_horizcenter_vertcenter"),
            manager=MANAGER,
            anchors={"centerx": "centerx"},
            )
        elif self.current_group == "oc1":
            self.set_bg(None)
            self.heading = pygame_gui.elements.UITextBox(
            "screens.allegiances.heading",
            ui_scale(pygame.Rect((0, 115), (400, 40))),
            text_kwargs={"clan_name": (game.clan.all_clans[1]).name},
            object_id=get_text_box_theme("#text_box_34_horizcenter_vertcenter"),
            manager=MANAGER,
            anchors={"centerx": "centerx"},
            )
        elif self.current_group == "oc2":
            self.set_bg(None)
            self.heading = pygame_gui.elements.UITextBox(
            "screens.allegiances.heading",
            ui_scale(pygame.Rect((0, 115), (400, 40))),
            text_kwargs={"clan_name": (game.clan.all_clans[2]).name},
            object_id=get_text_box_theme("#text_box_34_horizcenter_vertcenter"),
            manager=MANAGER,
            anchors={"centerx": "centerx"},
            )
        elif len(game.clan. all_clans) >= 4 and self.current_group == "oc3":
            self.set_bg(None)
            self.heading = pygame_gui.elements.UITextBox(
            "screens.allegiances.heading",
            ui_scale(pygame.Rect((0, 115), (400, 40))),
            text_kwargs={"clan_name": (game.clan.all_clans[3]).name},
            object_id=get_text_box_theme("#text_box_34_horizcenter_vertcenter"),
            manager=MANAGER,
            anchors={"centerx": "centerx"},
            )
        elif len(game.clan. all_clans) == 5 and self.current_group == "oc4":
            self.set_bg(None)
            self.heading = pygame_gui.elements.UITextBox(
            "screens.allegiances.heading",
            ui_scale(pygame.Rect((0, 115), (400, 40))),
            text_kwargs={"clan_name": (game.clan.all_clans[4]).name},
            object_id=get_text_box_theme("#text_box_34_horizcenter_vertcenter"),
            manager=MANAGER,
            anchors={"centerx": "centerx"},
            )

        self._update_allegiance_display()

    def _update_allegiance_display(self):
        """
        updates the allegiance display
        """
        try:
            for x in self.ranks_boxes:
                x.kill()

            for x in self.names_boxes:
                x.kill()
        except:
            self.ranks_boxes = []
            self.names_boxes = []
        
        allegiance_list = self.get_allegiances_text()
        self.ranks_boxes = []
        self.names_boxes = []
        for x in allegiance_list:
            self.ranks_boxes.append(
                pygame_gui.elements.UITextBox(
                    x[0],
                    ui_scale(pygame.Rect((0, 0), (150, -1))),
                    object_id=get_text_box_theme("#text_box_30_horizleft"),
                    container=self.scroll_container,
                    manager=MANAGER,
                    anchors=(
                        {"top_target": self.names_boxes[-1]}
                        if len(self.names_boxes) > 0
                        else None
                    ),
                )
            )
            self.ranks_boxes[-1].disable()

            self.names_boxes.append(
                pygame_gui.elements.UITextBox(
                    x[1],
                    pygame.Rect(
                        (0, -self.ranks_boxes[-1].get_relative_rect()[3]),
                        ui_scale_offset((565, -1)),
                    ),
                    object_id=get_text_box_theme("#text_box_30_horizleft"),
                    container=self.scroll_container,
                    manager=MANAGER,
                    anchors={
                        "top_target": self.ranks_boxes[-1],
                        "left_target": self.ranks_boxes[-1],
                        "left": "left",
                        "right": "right",
                    },
                )
            )
            self.names_boxes[-1].disable()

    def get_your_clan_cats(self):
        """
        grabs clan cats
        """
        self.current_group = "clan"
        self.living_cats = [
            cat for cat in Cat.all_cats_list if cat.status.alive_in_player_clan
        ]

    def get_cotc_cats(self):
        """
        grabs cats outside the clan
        """
        self.current_group = "cotc"
        self.living_cats = [cat for cat in Cat.all_cats_list if cat.status.is_outsider]
    
    def get_oc_cats(self, clan_number):
        """
        grabs cats from other clans
        """
        self.current_group = "oc" + str(clan_number)
        self.living_cats = [cat for cat in Cat.all_cats_list if cat.status.is_clancat and get_cat_clan(cat.status.group) == game.clan.all_clans[clan_number]]

    def get_allegiances_text(self):
        """Determine Text. Ouputs list of tuples."""
        living_leader = None
        living_deputy = None

        living_cats = [
            i for i in Cat.all_cats.values() if i.status.alive_in_player_clan
        ]
        living_meds = []
        living_mediators = []
        living_warriors = []
        living_apprentices = []
        living_kits = []
        living_elders = []
        for cat in self.living_cats:
            if cat.status.rank == CatRank.LEADER:
                living_leader = cat
            if cat.status.rank == CatRank.DEPUTY:
                living_deputy = cat
            if cat.status.rank == CatRank.MEDICINE_CAT:
                living_meds.append(cat)
            elif cat.status.rank == CatRank.WARRIOR:
                living_warriors.append(cat)
            elif cat.status.rank == CatRank.MEDIATOR:
                living_mediators.append(cat)
            elif cat.status.rank.is_any_apprentice_rank():
                living_apprentices.append(cat)
            elif cat.status.rank.is_baby():
                living_kits.append(cat)
            elif cat.status.rank == CatRank.ELDER:
                living_elders.append(cat)

        # Find Queens:
        queen_dict, living_kits = get_alive_clan_queens(self.living_cats)

        # Remove queens from warrior or elder lists, if they are there.  Let them stay on any other lists.
        for q in queen_dict:
            queen = Cat.fetch_cat(q)
            if not queen:
                continue
            if queen in living_warriors:
                living_warriors.remove(queen)
            elif queen in living_elders:
                living_elders.remove(queen)

        # Clan Leader Box:
        # Pull the Clan leaders
        outputs = []
        if living_leader and game.clan.leader and game.clan.leader.status.alive_in_player_clan:
            outputs.append(
                [
                    f"<b><u>{i18n.t('general.leader', count=1).upper()}</u></b>",
                    self.generate_one_entry(living_leader),
                ]
            )
        elif living_leader:
            outputs.append(
                [
                    f"<b><u>{i18n.t('general.leader', count=1).upper()}</u></b>",
                    self.generate_one_entry(living_leader),
                ]
            )

        # Deputy Box:
        if living_deputy and game.clan.deputy and game.clan.deputy.status.alive_in_player_clan:
            outputs.append(
                [
                    f"<b><u>{i18n.t('general.deputy', count=1).upper()}</u></b>",
                    self.generate_one_entry(living_deputy),
                ]
            )
        elif living_deputy:
            outputs.append(
                [
                    f"<b><u>{i18n.t('general.deputy', count=1).upper()}</u></b>",
                    self.generate_one_entry(living_deputy),
                ]
            )

        # Medicine Cat Box:
        if living_meds:
            _box = ["", ""]
            _box[
                0
            ] = f"<b><u>{i18n.t('general.medicine cat', count=len(living_meds)).upper()}</u></b>"

            _box[1] = "\n".join([self.generate_one_entry(i) for i in living_meds])
            outputs.append(_box)

        # Mediator Box:
        if living_mediators:
            _box = ["", ""]
            _box[
                0
            ] = f"<b><u>{i18n.t('general.mediator', count=len(living_mediators)).upper()}</u></b>"

            _box[1] = "\n".join([self.generate_one_entry(i) for i in living_mediators])
            outputs.append(_box)

        # Warrior Box:
        if living_warriors:
            _box = ["", ""]
            _box[
                0
            ] = f"<b><u>{i18n.t('general.warrior', count=len(living_warriors)).upper()}</u></b>"

            _box[1] = "\n".join([self.generate_one_entry(i) for i in living_warriors])
            outputs.append(_box)

        # Apprentice Box:
        if living_apprentices:
            _box = ["", ""]
            _box[0] = f"<b><u>{i18n.t('general.apprentice', count=2).upper()}</u></b>"

            _box[1] = "\n".join(
                [self.generate_one_entry(i) for i in living_apprentices]
            )
            outputs.append(_box)

        # Queens and Kits Box:
        if queen_dict or living_kits:
            _box = ["", ""]
            _box[
                0
            ] = f"<b><u>{i18n.t('general.queen', count=2).upper()} AND {i18n.t('general.kit', count=2).upper()}</u></b>"

            # This one is a bit different.  First all the queens, and the kits they are caring for.
            all_entries = []
            for q in queen_dict:
                queen = Cat.fetch_cat(q)
                if not queen:
                    continue
                kittens = []
                for k in queen_dict[q]:
                    kittens += [
                        event_text_adjust(
                            Cat, f"{k.name} - {k.describe_cat(short=True)}", main_cat=k
                        )
                    ]
                if len(kittens) == 1:
                    kittens = i18n.t(
                        "screens.allegiances.caring_for",
                        kitten=kittens[0],
                        count=len(kittens),
                    )
                else:
                    kittens = i18n.t(
                        "screens.allegiances.caring_for",
                        kitten_list=", ".join(kittens[:-1]),
                        last_kitten=kittens[-1],
                        count=len(kittens),
                    )
                all_entries.append(self.generate_one_entry(queen, kittens))

            # Now kittens without carers
            for k in living_kits:
                all_entries.append(
                    event_text_adjust(
                        Cat,
                        f"{str(k.name).upper()} - {k.describe_cat(short=True)}",
                        main_cat=k,
                    )
                )

            _box[1] = "\n".join(all_entries)
            outputs.append(_box)

        # Elder Box:
        if living_elders:
            _box = ["", ""]
            _box[0] = f"<b><u>{i18n.t('general.elder', count=2).upper()}</u></b>"

            _box[1] = "\n".join([self.generate_one_entry(i) for i in living_elders])
            outputs.append(_box)
        
        living_kitties = []
        living_loners = []
        living_rogues = []
        living_exiled = []
        
        for cat in self.living_cats:
            if cat.status == "kittypet":
                living_kitties.append(cat)
            elif cat.status == "loner":
                living_loners.append(cat)
            elif cat.status == "rogue":
                living_rogues.append(cat)
            elif cat.exiled:
                living_exiled.append(cat)
        
        # Find Queens:
        queen_dict, living_kits = get_alive_outside_queens(self.living_cats)

        # Kittypet Box:
        if living_kitties:
            _box = ["", ""]
            _box[
                0
            ] = f"<b><u>{i18n.t('kittypets', count=len(living_kitties)).upper()}</u></b>"

            _box[1] = "\n".join([self.generate_one_entry(i) for i in living_kitties])
            outputs.append(_box)

        # Loner Box:
        if living_loners:
            _box = ["", ""]
            _box[
                0
            ] = f"<b><u>{i18n.t('loners', count=len(living_loners)).upper()}</u></b>"

            _box[1] = "\n".join([self.generate_one_entry(i) for i in living_loners])
            outputs.append(_box)
        
        # Rogue Box:
        if living_rogues:
            _box = ["", ""]
            _box[
                0
            ] = f"<b><u>{i18n.t('rouges', count=len(living_rogues)).upper()}</u></b>"

            _box[1] = "\n".join([self.generate_one_entry(i) for i in living_rogues])
            outputs.append(_box)

        # Exiled Box:
        if living_exiled:
            _box = ["", ""]
            _box[
                0
            ] = f"<b><u>{i18n.t('exiled', count=len(living_exiled)).upper()}</u></b>"

            _box[1] = "\n".join([self.generate_one_entry(i) for i in living_exiled])
            outputs.append(_box)

        return outputs
