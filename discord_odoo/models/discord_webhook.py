import json
import logging
import re
import urllib.error
import urllib.request
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from odoo import api, models

_logger = logging.getLogger(__name__)


class DiscordWebhookService(models.AbstractModel):
    _name = "discord.webhook.service"
    _description = "Discord Webhook Service"

    _WEBHOOK_PATTERN = re.compile(r"^https://(discord(?:app)?\.com)/api/webhooks/\d+/[\w-]+(?:\?.*)?$", re.IGNORECASE)

    @api.model
    def _discord_normalize_webhook_url(self, webhook_url):
        webhook_url = (webhook_url or "").strip()
        if webhook_url.startswith("<") and webhook_url.endswith(">"):
            webhook_url = webhook_url[1:-1].strip()
        md_match = re.match(r"^\[(https?://[^\]]+)\]\((https?://[^)]+)\)$", webhook_url)
        if md_match:
            webhook_url = md_match.group(2).strip()
        return webhook_url

    @api.model
    def _discord_with_wait_param(self, webhook_url):
        parsed = urlparse(webhook_url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query["wait"] = "true"
        return urlunparse(parsed._replace(query=urlencode(query)))

    @api.model
    def _discord_get_config(self):
        icp = self.env["ir.config_parameter"].sudo()
        return {
            "enabled": icp.get_param("discord_odoo.enabled", default="False") == "True",
            "webhook_url": icp.get_param("discord_odoo.webhook_url", default=""),
            "username": icp.get_param("discord_odoo.username", default="Odoo"),
            "avatar_url": icp.get_param("discord_odoo.avatar_url", default=""),
        }

    @api.model
    def _discord_send_payload(self, payload, *, webhook_url=None, enabled=None):
        config = self._discord_get_config()
        if enabled is None:
            enabled = config["enabled"]
        if not enabled:
            return False
        webhook_url = webhook_url if webhook_url is not None else config["webhook_url"]
        webhook_url = self._discord_normalize_webhook_url(webhook_url)
        if not webhook_url:
            _logger.info("Discord webhook is enabled but no URL has been configured.")
            return False
        if not self._WEBHOOK_PATTERN.match(webhook_url):
            _logger.warning("Discord webhook URL does not look valid: %s", webhook_url)
            return False

        webhook_url = self._discord_with_wait_param(webhook_url)

        request = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Odoo-Discord-Webhook/19.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                status = getattr(response, "status", 204)
                body = response.read().decode("utf-8", "replace")
                _logger.info("Discord webhook delivered successfully with HTTP %s body=%s", status, body)
                return 200 <= status < 300
        except urllib.error.HTTPError as err:
            body = ""
            try:
                body = err.read().decode("utf-8", "replace")
            except Exception:
                body = "<unable to read response body>"
            _logger.exception("Discord webhook returned HTTP %s body=%s", err.code, body)
        except Exception:
            _logger.exception("Failed to send payload to Discord webhook")
        return False

    @api.model
    def _discord_send_message(
        self,
        content,
        *,
        username=None,
        avatar_url=None,
        embeds=None,
        webhook_url=None,
        enabled=None,
    ):
        config = self._discord_get_config()
        payload = {
            "content": content,
            "username": username or config["username"] or "Odoo",
        }
        resolved_avatar_url = avatar_url or config["avatar_url"] or ""
        if resolved_avatar_url:
            payload["avatar_url"] = resolved_avatar_url
        if embeds:
            payload["embeds"] = embeds
        return self._discord_send_payload(payload, webhook_url=webhook_url, enabled=enabled)

    @api.model
    def _discord_format_value(self, field, value):
        if value in (False, None):
            return "False"

        field_type = field.type
        if field_type == "many2one":
            if isinstance(value, int):
                value = self.env[field.comodel_name].browse(value)
            return value.display_name or str(value.id)
        if field_type in {"many2many", "one2many"}:
            if hasattr(value, "mapped"):
                names = value.mapped("display_name")
                return ", ".join(names) if names else "[]"
            if isinstance(value, (list, tuple)):
                return ", ".join(str(item) for item in value)
        if field_type == "boolean":
            return "Yes" if bool(value) else "No"
        return str(value)

    @api.model
    def _discord_format_input_value(self, field, value):
        if field.type == "many2one":
            if isinstance(value, int):
                record = self.env[field.comodel_name].browse(value)
                return record.display_name or str(record.id)
            if hasattr(value, "display_name"):
                return value.display_name or str(value.id)
        if field.type in {"many2many", "one2many"}:
            if isinstance(value, (list, tuple)) and value and isinstance(value[0], tuple):
                parts = []
                for command in value:
                    parts.append(str(command))
                return ", ".join(parts)
        return self._discord_format_value(field, value)

    @api.model
    def _discord_build_embed(self, title, description, fields):
        embed_fields = []
        for name, value in fields:
            embed_fields.append(
                {
                    "name": name[:256],
                    "value": value[:1024] if isinstance(value, str) else str(value)[:1024],
                    "inline": False,
                }
            )
        return [
            {
                "title": title[:256],
                "description": description[:4096],
                "color": 0x5865F2,
                "fields": embed_fields[:25],
            }
        ]
