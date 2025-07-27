from __future__ import annotations

from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property


class Menu(models.Model):
    """Represents a named menu grouping a collection of menu items."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        verbose_name = "Menu"
        verbose_name_plural = "Menus"

    def __str__(self) -> str:  # pragma: no cover - human readable representation
        return self.name


class MenuItem(models.Model):
    """Represents a single entry in a menu.

    Menu items can be nested using the parent relationship. Each item can define
    either a literal URL or a named URL. Ordering of siblings is controlled via
    the ``order`` field.
    """

    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=255)
    url = models.CharField(
        max_length=255,
        blank=True,
        help_text="Direct URL to navigate to. Ignored if 'named_url' is provided.",
    )
    named_url = models.CharField(
        max_length=255,
        blank=True,
        help_text="Name of the URL pattern to reverse. If provided, takes precedence over 'url'.",
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='children',
        null=True,
        blank=True,
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Menu item"
        verbose_name_plural = "Menu items"
        ordering = ['order', 'id']

    def __str__(self) -> str:  # pragma: no cover - human readable representation
        return self.title

    def get_absolute_url(self) -> str:
        """Resolve the URL for this menu item.

        If ``named_url`` is provided, ``reverse`` is used to resolve it. Otherwise
        the value of ``url`` is returned as-is.
        """
        if self.named_url:
            try:
                return reverse(self.named_url)
            except Exception:
                # In case named_url cannot be reversed, fall back to the stored URL
                return self.url or '#'
        return self.url or '#'

    @cached_property
    def ancestors(self) -> list['MenuItem']:
        """Return a list of ancestor items up the tree from this item."""
        ancestors: list[MenuItem] = []
        parent = self.parent
        while parent:
            ancestors.append(parent)
            parent = parent.parent
        return ancestors
