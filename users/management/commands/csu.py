from django.core.management import BaseCommand

from users.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        if not User.objects.filter(username="admin").exists():
            user = User.objects.create_user(
                username="admin",
                email="admin@mail.ru",
                password="123"
            )
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS("Superuser created."))
        else:
            self.stdout.write(self.style.WARNING("Superuser already exists."))
