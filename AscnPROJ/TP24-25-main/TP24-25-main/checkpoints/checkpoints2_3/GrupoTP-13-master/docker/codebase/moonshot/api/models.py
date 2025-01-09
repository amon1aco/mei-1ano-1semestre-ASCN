from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import uuid
import time
from cryptography import x509
from cryptography.hazmat.primitives import serialization
import base64
import jwt
from django_countries.fields import CountryField
from luhn import generate

from .managers import UserManager
from .validators import dosage_num_validator


class User(AbstractUser):
    """
    Extend abstract user model
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


class RecordEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Laboratory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(blank=False, null=False, max_length=128)
    nif = models.CharField(blank=False, null=False, max_length=32)
    ers_number = models.CharField(blank=False, null=False, max_length=32)
    telephone = models.CharField(blank=False, null=False, max_length=16)

    def __str__(self):
        return self.name

    class Meta:
        permissions = [
            ("can_create_recovery", _("Can create DGC for Recoveries")),
            ("can_create_test", _("Can create DGC for Tests")),
            ("can_create_vaccination", _("Can create DGC for Vaccinations")),
        ]
        verbose_name_plural = "Laboratories"


class Manager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    laboratories = models.ManyToManyField(Laboratory)

    def __str__(self):
        return self.user.email


class Notifier(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nic = models.CharField(blank=False, null=False, max_length=32, unique=True)
    laboratories = models.ManyToManyField(Laboratory, blank=True)

    class Meta:
        permissions = [
            ("can_create_recovery", _("Can create DGC for Recoveries")),
            ("can_create_test", _("Can create DGC for Tests")),
            ("can_create_vaccination", _("Can create DGC for Vaccinations")),
        ]

    def __str__(self):
        return self.nic


class Person(models.Model):
    name = models.CharField(blank=False, null=False, max_length=128)
    date_of_birth = models.DateField(null=False)
    identifier = models.CharField(null=True, blank=False, max_length=32)
    # https://www.hl7.org/fhir/valueset-administrative-gender.html
    SEX = [
        ("male", _("Male")),
        ("female", _("Female")),
        ("other", _("Other")),
        ("unknown", _("Unknown")),
    ]
    sex = models.CharField(blank=False, null=True, max_length=16, choices=SEX)

    def __str__(self):
        return self.name


class Vaccination(models.Model):
    # ICD-11 or SNOMED CT, opted for ICD-11
    ICD_11_DISEASES = [
        ("XN109", "SARS-CoV-2"),
    ]
    disease = models.CharField(
        blank=False, null=False, max_length=32, choices=ICD_11_DISEASES, default="XN109"
    )
    SNOMED_CT_VACCINES = [
        ("1119305005|J07BX03", _("COVID-19 antigen vaccine")),
        ("1119349007|J07BX03", _("COVID-19 mRNA vaccine")),
    ]
    vaccine = models.CharField(
        blank=False,
        null=False,
        max_length=64,
        choices=SNOMED_CT_VACCINES,
        default="1119349007|J07BX03",
    )
    # https://www.ema.europa.eu/en/human-regulatory/overview/public-health-threats/coronavirus-disease-covid-19/treatments-vaccines/covid-19-vaccines
    PRODUCT_NAMES = [
        (
            "EMEA/H/C/005735",
            _("Comirnaty concentrate for dispersion for injection"),
        ),  # noqa: E501
        (
            "EMEA/H/C/005737",
            _("COVID-19 Vaccine Janssen suspension for injection"),
        ),  # noqa: E501
        (
            "EMEA/H/C/005791",
            _("COVID-19 Vaccine Moderna dispersion for injection "),
        ),  # noqa: E501
        (
            "EMEA/H/C/005675",
            _("COVID-19 Vaccine AstraZeneca suspension for injection"),
        ),  # noqa: E501
    ]
    medicinal_product = models.CharField(
        blank=False,
        null=False,
        max_length=128,
        choices=PRODUCT_NAMES,
        default="EMEA/H/C/005735",
    )
    # From SPOR and Conditional Market Authorizations
    MAH = [
        ("ORG-100030215", "BioNTech Manufacturing GmbH"),
        ("ORG-100001417", "Janssen-Cilag International"),
        ("ORG-100031184", "Moderna Biotech Spain, S.L."),
        ("ORG-100001699", "Astrazeneca AB"),
    ]
    marketing_authorization_holder = models.CharField(
        blank=False, null=False, max_length=128, choices=MAH
    )

    dosage_number = models.CharField(
        blank=False,
        null=False,
        max_length=3,
        validators=[dosage_num_validator],
        default="1/2",
    )
    batch_number = models.CharField(blank=False, null=True, max_length=32)
    vaccination_date = models.DateField(null=False)
    administering_centre = models.CharField(blank=False, null=True, max_length=128)
    health_professional_id = models.ForeignKey(Notifier, on_delete=models.CASCADE)
    country = CountryField()
    next_vaccination_date = models.DateField(null=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    def __str__(self):
        return self.person.name


class Recovery(models.Model):
    # ICD-11 or SNOMED CT, opted for ICD-11
    ICD_11_DISEASES = [
        ("XN109", "SARS-CoV-2"),
    ]
    disease = models.CharField(
        blank=False, null=False, max_length=32, choices=ICD_11_DISEASES, default="XN109"
    )
    first_positive_test_date = models.DateField()
    country = CountryField()
    health_professional_id = models.ForeignKey(Notifier, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Recoveries"

    def __str__(self):
        return self.person.name


class Test(models.Model):
    # ICD-11 or SNOMED CT, opted for ICD-11
    ICD_11_DISEASES = [
        ("XN109", "SARS-CoV-2"),
    ]
    disease = models.CharField(
        blank=False, null=False, max_length=32, choices=ICD_11_DISEASES, default="XN109"
    )
    TEST_TYPES = [("PC", _("PCR test")), ("AG", _("Rapid antigen test"))]
    test_type = models.CharField(
        blank=False, null=False, max_length=2, choices=TEST_TYPES, default="PC"
    )

    test_name = models.CharField(blank=False, null=True, max_length=128)
    test_manufacturer = models.CharField(blank=False, null=True, max_length=128)
    # https://confluence.ihtsdotools.org/display/snomed/SNOMED+CT+COVID-19+Related+Content
    SNOMED_ORIGINS = [
        ("461911000124106", _("Oropharyngeal swab")),
        ("119334006", _("Nasopharyngeal swab")),
        ("871810001", _("Nasal swab")),
        ("119342007", _("Saliva")),
    ]
    sample_origin = models.CharField(
        blank=False,
        null=True,
        max_length=32,
        choices=SNOMED_ORIGINS,
        default="119334006",
    )
    sample_collection_date_time = models.DateTimeField()
    # https://confluence.ihtsdotools.org/display/snomed/SNOMED+CT+COVID-19+Related+Content
    TEST_RESULTS = [
        ("897034005", _("SARS-CoV-2 antibody test positive")),
        ("897035006", _("SARS-CoV-2 antibody test negative")),
    ]
    result = models.CharField(
        blank=False,
        null=False,
        max_length=32,
        choices=TEST_RESULTS,
        default="897035006",
    )
    testing_centre = models.CharField(blank=False, null=False, max_length=64)
    health_professional_id = models.ForeignKey(Notifier, on_delete=models.CASCADE)
    country = CountryField()
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    def __str__(self):
        return self.person.name


class DigitalGreenCertificate(models.Model):
    uvci = models.CharField(blank=False, null=False, unique=True, max_length=64)
    notifier = models.ForeignKey(Notifier, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    CERTIFICATE_TYPES = [
        ("TE", _("Test")),
        ("RE", _("Recovery")),
        ("VC", _("Vaccination")),
    ]
    certificate_type = models.CharField(
        blank=False, null=False, max_length=2, choices=CERTIFICATE_TYPES, default="TE"
    )
    qrcode = models.TextField(default="")

    def gen_uvci(self):
        opaque = str(uuid.uuid4())
        opaque = opaque.replace("-", "0")
        opaque = opaque.upper()
        uvci = f"01#PT#{self.certificate_type}{opaque}"
        checksum = generate("".join(str(ord(c)) for c in uvci))
        self.uvci = f"{uvci}#{checksum}".replace("#", "-")

    def __str__(self):
        return self.uvci


class SignedToken(object):
    body = None
    token = None
    headers = None

    def __init__(self, record={}, token=None):
        self.body = {}
        self.token = token
        for field in record:
            self.body[field] = record.get(field)

    def __load_cert(self, cert_file):
        f = open(cert_file, "rb")
        cert = f.read()
        f.close()
        cert = x509.load_pem_x509_certificate(cert)
        cert_der = cert.public_bytes(encoding=serialization.Encoding.DER)
        cert_der = str(base64.b64encode(cert_der), "utf-8")

        return cert_der

    def __load_key(self, key_file):
        f = open(key_file, "rb")
        priv_key = f.read()
        f.close()

        return priv_key

    def __extract_pub_key(self, priv_key):
        priv_key = serialization.load_pem_private_key(priv_key, password=None)
        pub_key = priv_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return pub_key

    def gen_jws(self, cert_file, key_file, algorithm="ES384"):
        algorithms = ["ES512", "ES384", "ES256"]
        if algorithm not in algorithms:
            algorithm = "ES384"

        cert_chain = [self.__load_cert(cert_file)]
        priv_key = self.__load_key(key_file)

        self.headers = {"x5c": cert_chain, "alg": algorithm, "iat": int(time.time())}

        self.token = jwt.encode(
            self.body, priv_key, algorithm="ES384", headers=self.headers
        )

    def validate_jws(self, key_file, algorithm="ES384"):
        try:
            if self.token is None:
                return False

            priv_key = self.__load_key(key_file)
            pub_key = self.__extract_pub_key(priv_key)

            is_valid = (
                jwt.decode(self.token, key=pub_key, algorithms=algorithm) is not None
            )

            return is_valid
        except:
            return False
