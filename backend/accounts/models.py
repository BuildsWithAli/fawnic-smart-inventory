from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        INVENTORY_MANAGER = "inventory_manager", "Inventory Manager"
        SUPPORT = "support", "Support"

    role = models.CharField(max_length=32, choices=Role.choices, default=Role.SUPPORT)

    def __str__(self):
        return self.username

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER

    @property
    def is_inventory_manager(self):
        return self.role == self.Role.INVENTORY_MANAGER
