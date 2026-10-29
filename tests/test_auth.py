from core.auth import authenticate, create_user, ensure_default_admin, hash_password
from core.db import init_db


def test_first_run_creates_default_admin():
    init_db()
    assert authenticate("admin", "demo1234")
    assert not authenticate("admin", "wrong")


def test_default_admin_not_recreated():
    init_db()
    assert ensure_default_admin() is None  # users already exist


def test_passwords_are_salted_per_user():
    salt_a, hash_a = hash_password("same-password")
    salt_b, hash_b = hash_password("same-password")
    assert salt_a != salt_b and hash_a != hash_b


def test_created_user_can_authenticate():
    create_user("khoa", "s3cret")
    assert authenticate("khoa", "s3cret")
    assert not authenticate("khoa", "S3cret")
    assert not authenticate("ghost", "s3cret")
