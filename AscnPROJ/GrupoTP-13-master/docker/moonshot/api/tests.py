from django.test import TestCase
from django.contrib.auth import get_user_model
from moonshot.settings import SIGNING_CERTIFICATE_FILE, SIGNING_CERTIFICATE_KEY_FILE
import jwt
from cryptography.hazmat.primitives import serialization


# Create your tests here.
class UserManagerTests(TestCase):

    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(email="bob@moonshot.pt", password="alice")
        self.assertEqual(user.email, "bob@moonshot.pt")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertIsNone(user.username)

    def test_create_super_user(self):
        User = get_user_model()
        admin = User.objects.create_superuser(
            email="superbob@moonshot.pt", password="superalice"
        )
        self.assertEqual(admin.email, "superbob@moonshot.pt")
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


class CertificateTest(TestCase):
    priv_key = None
    cert = None
    pub_key = None

    def setUp(self):
        f = open(SIGNING_CERTIFICATE_FILE, "rb")
        self.cert = f.read()
        f.close()

        f = open(SIGNING_CERTIFICATE_KEY_FILE, "rb")
        self.priv_key = f.read()
        f.close()

        self.pub_key = (
            serialization.load_pem_private_key(self.priv_key, password=None)
            .public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )

    def test_load_cert_and_keys(self):
        self.assertIsNotNone(self.cert)
        self.assertIsNotNone(self.priv_key)
        self.assertIsNotNone(self.pub_key)

    def test_sign_and_verify(self):
        token = {"to-encode": "string"}

        encoded = jwt.encode(token, key=self.priv_key, algorithm="ES384")
        decoded = jwt.decode(encoded, key=self.pub_key, algorithms="ES384")

        self.assertEqual(token, decoded)
