{
    "name": "Discord Odoo Integration",
    "version": "19.0.1.0.0",
    "category": "Tools",
    "summary": "Send Odoo notifications to Discord via webhook",
    "description": """
Discord Odoo Integration
========================

This addon provides:

* Discord webhook configuration in Odoo Settings
* A test button to verify the webhook
* An opt-in mixin for sending create/write notifications to Discord
    """,
    "author": "thetzin",
    "license": "LGPL-3",
    "images": [
        "static/description/icon.png",
        "static/description/banner.png",
    ],
    "depends": ["base", "web"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": True,
}
