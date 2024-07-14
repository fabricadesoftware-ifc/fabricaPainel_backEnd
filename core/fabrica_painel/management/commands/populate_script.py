from typing import Any, Final

from django.core.management.base import BaseCommand, CommandParser
from faker import Faker

from .utils.populate import (
    create_assessment,
    create_assessments,
    create_edition,
    create_field,
    create_keyword,
    create_team,
    create_user,
    create_work,
)


class Command(BaseCommand):
    help = "This is a script used for populating the database. For testing purpose."

    def add_arguments(self, parser: CommandParser):
        # Positional (obligatory) arguments
        parser.add_argument("models", nargs="+", type=str)

        # Named (optional) arguments
        parser.add_argument(
            # Name/flag of the argument
            "--locale",
            # Help message
            help="Defines a location to the Faker instance.",
            # What it will do with the passed argument
            action="store",
            # Type casts the argument passed
            type=str,
        )
        parser.add_argument(
            "--instances",
            help="Defines the number of instances created.",
            action="store",
            type=int,
        )
        # parser.add_argument(
        #     "--models",
        #     help="Defines to which model(s) the created instances are going to be.",
        #     action="store",
        #     type=str,
        # )

    def handle(self, *args: Any, **kwargs: Any) -> str | None:
        DEFAULT_LOCATION: Final[str] = "pt_BR"
        DEFAULT_NUMBER_INSTANCES: Final[int] = 1

        # If the location has not been passed, it will use the default
        # This also supports passing a list of locations
        instance_location: str | list[str] = (
            DEFAULT_LOCATION if not kwargs["locale"] else kwargs["locale"].split(",")
        )
        instances_created: int = (
            DEFAULT_NUMBER_INSTANCES if not kwargs["instances"] else kwargs["instances"]
        )

        if not kwargs["models"]:
            raise ValueError("Please inform at least one model.")

        faker_gen: Faker = Faker(locale=instance_location)

        base_configs: dict = {
            "generator": faker_gen,
            "instances_created": instances_created,
        }

        if "field" in kwargs["models"]:
            create_field(
                base_configs,
            )
            self.stdout.write(self.style.SUCCESS("Fields succesfully created!"))

        if "edition" in kwargs["models"]:
            create_edition(
                base_configs,
            )
            self.stdout.write(self.style.SUCCESS("Editions succesfully created!"))

        # Daqui pra baixo tem FK
        if "user" in kwargs["models"] or "usuario" in kwargs["models"]:
            create_user(
                base_configs,
                advisor_chance=25,
                evaluator_chance=10,
            )
            self.stdout.write(self.style.SUCCESS("Users succesfully created!"))

        if "work" in kwargs["models"]:
            create_work(
                base_configs,
            )
            self.stdout.write(self.style.SUCCESS("Work succesfully created!"))

        if "keyword" in kwargs["models"]:
            create_keyword(
                base_configs,
            )
            self.stdout.write(self.style.SUCCESS("Keyword succesfully created!"))

        if "team" in kwargs["models"]:
            create_team(
                base_configs,
            )
            self.stdout.write(self.style.SUCCESS("Team succesfully created!"))

        if "assessment" in kwargs["models"]:
            create_assessment(
                base_configs,
                min_grade=0,
                max_grade=10
            )
            self.stdout.write(self.style.SUCCESS("Assessment succesfully created!"))

        if "assessments" in kwargs["models"]:
            create_assessments(
                base_configs,
            )
            self.stdout.write(self.style.SUCCESS("Assessments succesfully created!"))
