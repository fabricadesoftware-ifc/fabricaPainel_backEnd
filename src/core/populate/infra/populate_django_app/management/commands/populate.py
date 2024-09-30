from django.core.management.base import BaseCommand, CommandError, CommandParser
from core.populate.infra.populate_django_app.management.commands._cross_cutting_themes import populate_cross_cutting_themes
from core.populate.infra.populate_django_app.management.commands._ods import populate_ods
from core.populate.infra.populate_django_app.management.commands._basic import populate_users, populate_team
from core.populate.infra.populate_django_app.management.commands._field import populate_fields
from core.populate.infra.populate_django_app.management.commands._edition import populate_editions, populate_images
from core.populate.infra.populate_django_app.management.commands._work import populate_works



class Command(BaseCommand):
    """
    Populates the database with the minimum information for the system to work.
    If the database is not empty, some data will not be populated.

    Raises:
        CommandError: If something goes wrong
    """

    help = """
        Populates the database with the minimum information for the system to work.
        If the database is not empty, some data will not be populated.
    """
    
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--basic",
            action="store_true",
            help="add users in database",
        )
        parser.add_argument(
            "--ods",
            action="store_true",
            help="Insert ods in database"
        )
        parser.add_argument(
            "--fields",
            action="store_true",
            help="Insert field in database"
        )
        parser.add_argument(
            "--cross_cutting_themes",
            action="store_true",
            help="insert themes in database"
        )
        parser.add_argument(
            "--works",
            action="store_true",
            help="insert work in database"
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="insert all in database"
        )

    def handle(self, *args, **options):
        try:
            if options.get("basic"):
                self.__handle_basic_info()
            if options.get("ods"):
                self.__handle_ods()
            if options.get("fields"):
                self.__handle_field()
            if options.get("cross_cutting_themes"):
                self.__handle_cross_cutting_themes()
            if options.get("works"):
                self.__handle_work()
            if options.get("all"):
                self.__handle_all()

            self.stdout.write(
                    self.style.SUCCESS(  # pylint: disable=no-member
                        "\n Data successfully populated :D"
                    )
                )
            
        except CommandError as exc:
            raise CommandError("Check if the parameters are correct") from exc

        except Exception as e:
            self.stdout.write(self.style.ERROR(e))  # pylint: disable=no-member


    def __handle_basic_info(self) -> None:
        self.stdout.write("Populating basic data in the database...", ending=" ")
        populate_users()
        populate_team()
        self.stdout.write(self.style.SUCCESS("OK"))  # pylint: disable=no-member


    def __handle_ods(self) -> None:
        self.stdout.write("Populating ods data in the database...", ending=" ")
        populate_ods()
        self.stdout.write(self.style.SUCCESS("OK"))  # pylint: disable=no-member


    def __handle_field(self) -> None:
        self.stdout.write("Populating field data in the database...", ending=" ")
        populate_fields()
        self.stdout.write(self.style.SUCCESS("OK"))  # pylint: disable=no-member

    def __handle_cross_cutting_themes(self) -> None:
        self.stdout.write("Populating themes data in the database...", ending=" ")
        populate_cross_cutting_themes()
        self.stdout.write(self.style.SUCCESS("OK"))  # pylint: disable=no-member

    def __handle_work(self) -> None:
        self.stdout.write("Populating work data in the database...", ending=" ")
        populate_works()
        self.stdout.write(self.style.SUCCESS("OK"))


    def __handle_all(self) -> None:
        self.stdout.write("Populating all data in the database...", ending=" ")
        populate_users()
        populate_team()
        populate_ods()
        populate_images()
        populate_editions()
        populate_fields()
        populate_cross_cutting_themes()
        populate_works()
        self.stdout.write(self.style.SUCCESS("OK"))  # pylint: disable=no-member
