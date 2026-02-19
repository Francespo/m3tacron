import reflex as rx

config = rx.Config(
    app_name="m3tacron",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)