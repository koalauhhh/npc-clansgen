from typing import Union, Dict, Optional

import i18n
import pygame
import pygame_gui
from pygame_gui.core import ObjectID

from scripts.cat.cats import Cat
from scripts.game_structure.game_essentials import game
from scripts.game_structure.screen_settings import MANAGER
from scripts.game_structure.game.switches import (
    switch_set_value,
    switch_get_value,
    Switch,
)
from scripts.game_structure.ui_elements import (
    UIImageButton,
    UIDropDown,
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
    get_cat_clan,
)
from .Screens import Screens
from scripts.ui.generate_button import ButtonStyles, get_button_dict
from ..cat.enums import CatRank, CatSocial
from ..game_structure.ui_elements import UIModifiedScrollingContainer


class AllegiancesScreen(Screens):
    living_group_names = (
        "general.your_clan", 
        "general.cotc", 
    )
    allegiance_list = []

    def __init__(self, name=None):
        super().__init__(name)
        self.names_boxes = None
        self.ranks_boxes = None
        self.scroll_container = None
        self.heading = None
        
        self.cat_list_bar = None
        self.current_group = "your_clan"
        self.full_cat_list = []
        self.current_listed_cats = []
        
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
            "sort_by_button": None,
            "sort_by_label": None,
        }
        
        self.choose_group_dropdown = None
        self.sort_by_dropdown = None
        
        self.clan_name = None

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_ON_HOVERED:
            if event.ui_element == self.cat_list_bar_elements["sort_by_label"]:
                self.cat_list_bar_elements["sort_by_button"].on_hovered()

        elif event.type == pygame_gui.UI_BUTTON_ON_UNHOVERED:
            if event.ui_element == self.cat_list_bar_elements["sort_by_label"]:
                self.cat_list_bar_elements["sort_by_button"].on_unhovered()
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            self.menu_button_pressed(event)
            self.mute_button_pressed(event)

    def on_use(self):
        super().on_use()
        
        if (
            self.choose_group_dropdown
            and self.choose_group_dropdown.selected_list[0].replace("general.", "")
            != self.current_group
        ):
            new_group = self.choose_group_dropdown.selected_list[0].replace(
                "general.", ""
            )
            if new_group == "your_clan":
                self.get_your_clan_cats()
            elif new_group == "cotc":
                self.get_cotc_cats()
            elif new_group == f"{game.clan.all_clans[0].name}Clan":
                self.get_oc_cats(0)
            elif new_group == f"{game.clan.all_clans[1].name}Clan":
                self.get_oc_cats(1)
            elif new_group == f"{game.clan.all_clans[2].name}Clan":
                self.get_oc_cats(2)
            elif len(game.clan. all_clans) >= 4 and new_group == f"{game.clan.all_clans[3].name}Clan":
                self.get_oc_cats(3)
            elif len(game.clan. all_clans) == 5 and new_group == f"{game.clan.all_clans[4].name}Clan":
                self.get_oc_cats(4)
            self.update_cat_list()

        # SORT BY DROPDOWN
        if self.sort_by_dropdown and self.sort_by_dropdown.selected_list[0].replace(
            "screens.list.filter_", ""
        ) != switch_get_value(Switch.sort_type):
            sort_type = self.sort_by_dropdown.selected_list[0].replace(
                "screens.list.filter_", ""
            )
            switch_set_value(Switch.sort_type, sort_type)
            self.sort_by_dropdown.parent_button.set_text(
                f"screens.list.filter_{switch_get_value(Switch.sort_type)}"
            )
            self.update_cat_list()
        

    def screen_switches(self):
        super().screen_switches()
        self.show_mute_buttons()
        self.clan_name = game.clan.name + "Clan"

        if not f"{game.clan.all_clans[0].name}Clan" in self.living_group_names:
            self.living_group_names += (f"{game.clan.all_clans[0].name}Clan", f"{game.clan.all_clans[1].name}Clan", f"{game.clan.all_clans[2].name}Clan",)
            
            if (len(game.clan.all_clans) >= 4) :
                self.living_group_names += (f"{game.clan.all_clans[3].name}Clan",)
                if (len(game.clan.all_clans) == 5) :
                    self.living_group_names += (f"{game.clan.all_clans[4].name}Clan",)
        
        # SCREEN CONTAINER - everything should come back to here
        self.list_screen_container = pygame_gui.core.UIContainer(
            ui_scale(pygame.Rect((0, 0), (800, 700))),
            object_id="#list_screen",
            starting_height=1,
            manager=MANAGER,
            visible=True,
        )

        # BAR CONTAINER
        self.cat_list_bar = pygame_gui.core.UIContainer(
            ui_scale(pygame.Rect((104, 134), (700, 400))),
            object_id="#cat_list_bar",
            starting_height=3,
            manager=MANAGER,
        )

        self.heading = pygame_gui.elements.UITextBox(
            "screens.allegiances.heading",
            ui_scale(pygame.Rect((0, 115), (400, 40))),
            text_kwargs={"clan_name": game.clan.name},
            object_id=get_text_box_theme("#text_box_34_horizcenter_vertcenter"),
            manager=MANAGER,
            anchors={"centerx": "centerx"},
        )

        # need to use add_element instead of specifying container in self.cat_list_bar
        # to prevent blinking on screen switch
        self.list_screen_container.add_element(self.cat_list_bar)

        # CHOOSE GROUP DROPDOWN
        self.choose_group_dropdown = UIDropDown(
            pygame.Rect((-2, 0), (190, 34)),
            parent_text="screens.list.choose_group",
            item_list=self.living_group_names,
            manager=MANAGER,
            container=self.cat_list_bar,
            starting_selection=['general.your_clan'],
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
        # this speeds up the load time 1000%
        # don't ask why
        # MANAGER.update(1)

        # Determine the starting list of cats.
        self.get_cat_list()
        self.update_cat_list()

    def exit_screen(self):
        for x in self.ranks_boxes:
            x.kill()
        del self.ranks_boxes
        for x in self.names_boxes:
            x.kill()
        del self.names_boxes
        self.scroll_container.kill()
        del self.scroll_container
        # self.choose_group_dropdown.kill()
        # del self.choose_group_dropdown
        self.list_screen_container.kill()
        del self.list_screen_container
        self.update_heading_text(self.clan_name)
        self.heading.kill()
        del self.heading

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
        updates the cat list
        """
        self.current_listed_cats = []

        # make sure cat list is the same everywhere else in the game.
        Cat.sort_cats(self.full_cat_list)
        Cat.sort_cats(Cat.all_cats_list)

        Cat.ordered_cat_list = self.current_listed_cats
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

            if self.current_group == "your_clan":
                self.update_heading_text(self.clan_name)
            elif self.current_group == "cotc":
                self.update_heading_text("general.cotc")
            elif self.current_group == "oc0":
                self.update_heading_text(game.clan.all_clans[0].name + "Clan")
            elif self.current_group == "oc1":
                self.update_heading_text(game.clan.all_clans[1].name + "Clan")
            elif self.current_group == "oc2":
                self.update_heading_text(game.clan.all_clans[2].name + "Clan")
            elif len(game.clan. all_clans) >= 4 and self.current_group == "oc3":
                self.update_heading_text(game.clan.all_clans[3].name + "Clan")
            elif len(game.clan. all_clans) == 5 and self.current_group == "oc4":
                self.update_heading_text(game.clan.all_clans[4].name + "Clan")

    def get_your_clan_cats(self):
        """
        grabs clan cats
        """
        self.current_group = "your_clan"
        self.living_cats = [
            cat for cat in Cat.all_cats_list if cat.status.alive_in_player_clan
        ]

        self.heading.kill()
        self.heading = pygame_gui.elements.UITextBox(
            "screens.allegiances.heading",
            ui_scale(pygame.Rect((0, 115), (400, 40))),
            text_kwargs={"clan_name": game.clan.name},
            object_id=get_text_box_theme("#text_box_34_horizcenter_vertcenter"),
            manager=MANAGER,
            anchors={"centerx": "centerx"},
        )

    def get_cotc_cats(self):
        """
        grabs cats outside the clan
        """
        self.current_group = "cotc"
        self.living_cats = [cat for cat in Cat.all_cats_list if cat.status.is_outsider and not cat.dead]

        self.heading.kill()
        self.heading = pygame_gui.elements.UITextBox(
            "screens.allegiances.heading",
            ui_scale(pygame.Rect((0, 115), (400, 40))),
            text_kwargs={"clan_name": "Cats Outside the "},
            object_id=get_text_box_theme("#text_box_34_horizcenter_vertcenter"),
            manager=MANAGER,
            anchors={"centerx": "centerx"},
        )
    
    def get_oc_cats(self, clan_number):
        """
        grabs cats from other clans
        """
        self.current_group = "oc" + str(clan_number)
        self.living_cats = [cat for cat in Cat.all_cats_list if cat.status.is_clancat and get_cat_clan(cat.status.group) == game.clan.all_clans[clan_number]]

        self.heading.kill()
        self.heading = pygame_gui.elements.UITextBox(
            "screens.allegiances.heading",
            ui_scale(pygame.Rect((0, 115), (400, 40))),
            text_kwargs={"clan_name": game.clan.all_clans[clan_number].name},
            object_id=get_text_box_theme("#text_box_34_horizcenter_vertcenter"),
            manager=MANAGER,
            anchors={"centerx": "centerx"},
        )

    def get_allegiances_text(self):
        """Determine Text. Ouputs list of tuples."""
        living_leader = None
        living_deputy = None

        living_meds = []
        living_mediators = []
        living_warriors = []
        living_apprentices = []
        living_kits = []
        living_elders = []
        living_meds = []
        living_mediators = []
        living_warriors = []
        living_apprentices = []
        living_kits = []
        living_elders = []
        for cat in self.living_cats:
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
            if cat.status.social == CatSocial.KITTYPET:
                living_kitties.append(cat)
            elif cat.status.social == CatSocial.LONER:
                living_loners.append(cat)
            elif cat.status.social == CatSocial.ROGUE:
                living_rogues.append(cat)
            elif cat.status.is_exiled():
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
