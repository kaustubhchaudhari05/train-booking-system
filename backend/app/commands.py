import click

from app.services.expiry import expire_stale_holds


def register_commands(app):
    @app.cli.command("expire-holds")
    def expire_holds_command():
        """Expire PENDING bookings whose seat hold has passed."""
        result = expire_stale_holds()
        click.echo(
            f"Expired {result['expired_bookings']} booking(s) and "
            f"{result['expired_reservations']} reservation(s)."
        )
