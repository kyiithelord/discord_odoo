# Discord Odoo Integration

Odoo addon for sending notifications to Discord through a webhook.

## What it does

- Adds Discord settings to Odoo General Settings
- Lets you test the webhook from the UI
- Provides an opt-in mixin for create/write notifications

## Installation

1. Copy `addons/discord_odoo` into your Odoo addons path, or keep this repo and point `--addons-path` to `C:/Users/thetz/Desktop/discord_odoo/addons`.
2. Update the app list in Odoo.
3. Install **Discord Odoo Integration**.

## Configuration

1. Go to **Settings**.
2. Open the **Discord Integration** section.
3. Enable the integration.
4. Paste your Discord webhook URL.
5. Click **Send Test Message**.

## Using the mixin

To send Discord messages from a model, inherit from `discord.notify.mixin` in your model.

Example:

```python
from odoo import models


class SaleOrder(models.Model):
    _inherit = ["sale.order", "discord.notify.mixin"]
```

The mixin will post create and write changes to Discord when the integration is enabled.
