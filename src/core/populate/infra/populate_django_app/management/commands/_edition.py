from core.edition.infra.edition_django_app.models import Edition
from core.edition.infra.edition_django_app.models import Image
from core.populate.infra.resources.data_edition import editions
from django.core.files.base import ContentFile
import requests
from io import BytesIO
from django.core.files import File


def download_random_image():
    # Replace this URL with any random image API of your choice
    url = "https://picsum.photos/500"

    response = requests.get(url)
    if response.status_code == 200:
        return response.content  # Return image content as bytes
    return None


def populate_images():
    if Image.objects.exists():
        return

    images_to_create = []  # List for batch creation

    for edition_id in range(1, (len(editions)) * 2 + 1):
        image_content = download_random_image()
        if image_content:
            # Use ContentFile to handle the image content
            image_file = ContentFile(image_content)

            # Create the Image object but don't save it yet
            image = Image(description=f"Random image for edition {edition_id}")

            # Save the file (this creates the file name and attaches it)
            file_name = f"random_image_edition_{edition_id}.jpg"
            image.file.save(file_name, image_file, save=False)

            # Add image to the bulk creation list
            images_to_create.append(image)

            print(f"Prepared image for edition {edition_id}")
        else:
            print(f"No image content for edition {edition_id}")

    # Bulk create the images with files attached
    Image.objects.bulk_create(images_to_create)

    print("Images populated successfully.")


def populate_editions():
    if Edition.objects.exists():
        return

    for index_edition, edition_data in enumerate(editions):
        edition = Edition.objects.create(
            year=edition_data["year"],
            theme=edition_data["theme"],
            edition_name=edition_data["edition_name"],
            event_date=edition_data["event_date"],
            final_event_date=edition_data["final_event_date"],
            initial_submission_date=edition_data["initial_submission_date"],
            final_submission_date=edition_data["final_submission_date"],
            initial_second_submission_date=edition_data[
                "initial_second_submission_date"
            ],
            final_second_submission_date=edition_data["final_second_submission_date"],
            initial_advisor_acceptance=edition_data["initial_advisor_acceptance"],
            final_advisor_acceptance=edition_data["final_advisor_acceptance"],
            initial_second_advisor_date=edition_data["initial_second_advisor_date"],
            final_second_advisor_date=edition_data["final_second_advisor_date"],
            initial_evaluators_date=edition_data["initial_evaluators_date"],
            final_evaluators_date=edition_data["final_evaluators_date"],
            workload=edition_data["workload"],
            words_per_work_max=edition_data["words_per_work_max"],
        )

        images = list(Image.objects.all())

        edition.banner = images[index_edition * 2]
        edition.logo = images[index_edition * 2 + 1]

        edition.save()
