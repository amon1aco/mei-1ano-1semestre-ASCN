import os
import random
import django
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "moonshot.settings")
django.setup()

from api.models import (
    DigitalGreenCertificate,
    User,
    Manager,
    Notifier,
    Laboratory,
    Person,
    Vaccination,
    Test,
    Recovery,
)

# Debug: print DB
print("DB:")
print(f"Managers: {Manager.objects.count()}")
print(f"Notifiers: {Notifier.objects.count()}")
print(f"DGC: {DigitalGreenCertificate.objects.count()}")

# Create Laboratories
laboratories_data = [
    {
        "name": "Farmácia Pedrosa",
        "nif": "123456789",
        "ers_number": "123456789",
        "telephone": "123456789",
    },
    {
        "name": "Hospital de Braga",
        "nif": "987654321",
        "ers_number": "987654321",
        "telephone": "987654321",
    },
]

for i, laboratory_data in enumerate(laboratories_data):
    laboratory, created = Laboratory.objects.get_or_create(**laboratory_data)

    laboratories_data[i] = laboratory

    if created:
        print(f"Laboratory '{laboratory.name}' created successfully.")
    else:
        print(f"Laboratory '{laboratory.name}' already exists.")


# Create Users (admins or managers)
users_data = [
    {"email": "admin@moonshot.pt", "password": "123456", "is_superuser": True},
    {"email": "manager@moonshot.pt", "password": "123456", "type": Manager},
    {
        "email": "notifier@moonshot.pt",
        "password": "123456",
        "type": Notifier,
        "nic": "123456789",
    },
]

for user_data in users_data:
    type = user_data.get("type", User).__name__

    # Just to prevent a sporadic error
    if len(User.objects.filter(email=user_data["email"])) > 0:
        print(f"{type} '{user_data['email']}' already exists.")
        continue

    user, created = User.objects.get_or_create(
        **{
            "email": user_data["email"],
            "is_staff": user_data.get("is_superuser", False),
            "is_superuser": user_data.get("is_superuser", False),
            "is_active": True,
        },
    )

    if created:
        user.set_password(user_data["password"])
        user.save()

        match type:
            case Manager.__name__:
                manager = Manager.objects.create(user=user)
                manager.laboratories.set([random.choice(laboratories_data)])
                manager.save()
            case Notifier.__name__:
                notifier = Notifier.objects.create(user=user, nic=user_data["nic"])
                notifier.laboratories.set([random.choice(laboratories_data)])
                notifier.save()

        print(f"{type} '{user.email}' created successfully.")
    else:
        print(f"{type} '{user.email}' already exists.")


# Create Persons
people_data = [
    {
        "name": "Rui",
        "date_of_birth": "2001-01-01",
        "identifier": "123",
        "sex": "male",
    },
    {
        "name": "Mariana",
        "date_of_birth": "2002-02-02",
        "identifier": "456",
        "sex": "female",
    },
    {
        "name": "Luís",
        "date_of_birth": "2003-03-03",
        "identifier": "789",
        "sex": "male",
    },
]

for i, person_data in enumerate(people_data):
    person, created = Person.objects.get_or_create(**person_data)

    people_data[i] = person

    if created:
        print(f"Person '{person.name}' created successfully.")
    else:
        print(f"Person '{person.name}' already exists.")


# Create Recoveries, Vaccinations and Tests
notifiers = Notifier.objects.all()
people = Person.objects.all()

certificates_data = [
    {
        "type": Vaccination,
        "disease": "XN109",
        "vaccine": "1119305005|J07BX03",
        "medicinal_product": "EMEA/H/C/005737",
        "marketing_authorization_holder": "ORG-100001417",
        "dosage_number": "1/2",
        "vaccination_date": "2020-12-12",
        "administering_centre": "Hospital",
        "country": "PT",
    },
    {
        "type": Recovery,
        "disease": "SARS-CoV-2",
        "first_positive_test_date": "2021-01-01",
        "country": "PT",
    },
    {
        "type": Test,
        "disease": "XN109",
        "test_type": "PC",
        "test_name": "string",
        "test_manufacturer": "string",
        "sample_origin": "461911000124106",
        "sample_collection_date_time": "2024-08-21T10:21:11.669Z",
        "result": "897034005",
        "testing_centre": "string",
        "country": "PT",
    },
]

for certificate_data in certificates_data:
    type = certificate_data.pop("type", None).__name__
    certificate = None
    created = False

    match type:
        case Vaccination.__name__:
            certificate, created = Vaccination.objects.get_or_create(
                health_professional_id=random.choice(notifiers),
                person=random.choice(people),
                **certificate_data,
            )
        case Recovery.__name__:
            certificate, created = Recovery.objects.get_or_create(
                health_professional_id=random.choice(notifiers),
                person=random.choice(people),
                **certificate_data,
            )
        case Test.__name__:
            certificate, created = Test.objects.get_or_create(
                health_professional_id=random.choice(notifiers),
                person=random.choice(people),
                **certificate_data,
            )

    if created:
        print(f"{type} '{certificate}' created successfully.")
    else:
        print(f"{type} '{certificate}' already exists.")

print("Seed complete.")
