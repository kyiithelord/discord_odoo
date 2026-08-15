from odoo import fields, models
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    discord_enabled = fields.Boolean(
        string="Enable Discord Integration",
        config_parameter="discord_odoo.enabled",
    )
    discord_webhook_url = fields.Char(
        string="Discord Webhook URL",
        config_parameter="discord_odoo.webhook_url",
    )
    discord_username = fields.Char(
        string="Discord Username",
        default="Odoo",
        config_parameter="discord_odoo.username",
    )
    discord_avatar_url = fields.Char(
        string="Discord Avatar URL",
        config_parameter="discord_odoo.avatar_url",
    )

    def action_test_discord_webhook(self):
        self.ensure_one()
        service = self.env["discord.webhook.service"].sudo()
        if not self.discord_enabled:
            raise UserError("Enable Discord Integration before sending a test message.")
        if not self.discord_webhook_url:
            raise UserError("Please provide a Discord webhook URL.")

        ok = service._discord_send_message(
            content="Test message from odoo",
            webhook_url=self.discord_webhook_url or "",
            enabled=self.discord_enabled,
        )
        if not ok:
            raise UserError("Discord test message could not be delivered. Check the webhook URL and server logs.")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Discord",
                "message": "Test message sent successfully to Discord.",
                "type": "success",
                "sticky": False,
            },
        }
