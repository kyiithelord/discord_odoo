from odoo import api, models


class DiscordNotifyMixin(models.AbstractModel):
    _name = "discord.notify.mixin"
    _description = "Discord Notification Mixin"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        config = self.env["discord.webhook.service"].sudo()._discord_get_config()
        if config["enabled"] and config["webhook_url"]:
            for record, vals in zip(records, vals_list):
                record._discord_notify("created", vals)
        return records

    def write(self, vals):
        tracked_fields = {
            name: self.mapped(name)
            for name in vals
            if name in self._fields
        }
        result = super().write(vals)
        config = self.env["discord.webhook.service"].sudo()._discord_get_config()
        if config["enabled"] and config["webhook_url"]:
            for record in self:
                old_values = {}
                for field_name, values_before in tracked_fields.items():
                    index = self.ids.index(record.id)
                    old_values[field_name] = values_before[index]
                record._discord_notify("updated", vals, old_values=old_values)
        return result

    def _discord_notify(self, action, vals, old_values=None):
        self.ensure_one()
        service = self.env["discord.webhook.service"].sudo()
        title = f"{self._description or self._name} {action}"
        description = f"Record: {self.display_name}"
        if action == "created":
            fields = [
                (field_name, service._discord_format_input_value(self._fields[field_name], value))
                for field_name, value in vals.items()
                if field_name in self._fields
            ]
        else:
            fields = []
            old_values = old_values or {}
            for field_name, new_value in vals.items():
                if field_name not in self._fields:
                    continue
                field = self._fields[field_name]
                old_value = old_values.get(field_name)
                fields.append(
                    (
                        f"{field.string or field_name} changed",
                        f"{service._discord_format_value(field, old_value)} -> {service._discord_format_input_value(field, new_value)}",
                    )
                )

        embeds = service._discord_build_embed(title, description, fields)
        service._discord_send_message(
            content=f"{title}: {self.display_name}",
            username="Odoo",
            embeds=embeds,
        )
