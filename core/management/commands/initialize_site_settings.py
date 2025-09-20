from django.core.management.base import BaseCommand
from core.models import SiteSettings

class Command(BaseCommand):
    help = 'Initialize site settings if they do not exist'

    def handle(self, *args, **kwargs):
        if not SiteSettings.objects.exists():
            site_settings = SiteSettings.objects.create(
                site_name="Trederwen Springs",
                site_description="Pure Welsh Mountain Spring Water",
                contact_email="info@trederwensprings.co.uk",
                contact_phone="+44 1234 567890",
                address="Wales, UK",
                facebook_url="https://facebook.com/trederwensprings",
                twitter_url="https://twitter.com/trederwensprings",
                instagram_url="https://instagram.com/trederwensprings",
                delivery_info="Free delivery on orders over £25",
                returns_policy="30-day returns policy",
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created site settings: {site_settings.site_name}'))
        else:
            site_settings = SiteSettings.objects.filter(is_active=True).first()
            if not site_settings:
                # If no active settings exist, activate the first one
                site_settings = SiteSettings.objects.first()
                site_settings.is_active = True
                site_settings.save()
                self.stdout.write(self.style.SUCCESS(f'Activated existing site settings: {site_settings.site_name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Site settings already exist: {site_settings.site_name}'))
