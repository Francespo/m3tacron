import reflex as rx
import os

config = rx.Config(
    app_name="m3tacron-beta",
    db_url=os.environ.get("DATABASE_URL", "sqlite:///test.db"),
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)
