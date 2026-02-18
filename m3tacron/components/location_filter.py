"""
Hierarchical Location Filter Component.
"""
import reflex as rx
from ..theme import TEXT_SECONDARY, MONOSPACE_FONT
from .searchable_filter_accordion import searchable_filter_accordion




def location_filter(state: any, on_change: any = None) -> rx.Component:
    """
    Render hierarchical location filter.
    """
    def wrap_toggle(toggle_fn):
        if on_change:
            return lambda v, c: [toggle_fn(v, c), on_change]
        return toggle_fn

    content = rx.vstack(
        # Continent
        searchable_filter_accordion(
            "Continent",
            state.continent_options,
            state.selected_continents,
            wrap_toggle(state.toggle_continent),
            state.continent_search,
            state.set_continent_search
        ),
        
        # Country
        searchable_filter_accordion(
            "Country",
            state.country_options,
            state.selected_countries,
            wrap_toggle(state.toggle_country),
            state.country_search,
            state.set_country_search
        ),
        
        # City
        searchable_filter_accordion(
            "City",
            state.city_options,
            state.selected_cities,
            wrap_toggle(state.toggle_city),
            state.city_search,
            state.set_city_search
        ),
        spacing="2",
        width="100%"
    )

    return rx.accordion.root(
        rx.accordion.item(
            rx.accordion.header(
                rx.accordion.trigger(
                    rx.text(
                        "Location", 
                        size="1", 
                        weight="bold", 
                        color=TEXT_SECONDARY, 
                        font_family=MONOSPACE_FONT,
                        letter_spacing="1px"
                    ),
                    rx.accordion.icon(),
                    align_items="center",
                    display="flex",
                    justify_content="space-between",
                    width="100%",
                    padding_y="8px",
                    padding_x="0px",
                    _hover={"background": "transparent"},
                )
            ),
            rx.accordion.content(
                rx.box(
                    content,
                    width="100%",
                    padding_left="8px",
                    padding_top="0px"
                )
            ),
            value="main",
            style={
                "background": "transparent", 
                "border": "none",
                "_hover": {"background": "transparent"}
            }
        ),
        type="multiple",
        collapsible=True,
        width="100%",
        color_scheme="gray", 
        variant="ghost"
    )
