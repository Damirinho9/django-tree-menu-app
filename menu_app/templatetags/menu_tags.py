from __future__ import annotations

from typing import Dict, List, Optional

from django import template
from menu_app.models import Menu, MenuItem

register = template.Library()


def build_tree(items: List[MenuItem]) -> Dict[Optional[int], List[MenuItem]]:
    """Build a mapping from parent_id to a list of children items.

    This helper function organizes all menu items by their parent identifier.
    """
    tree: Dict[Optional[int], List[MenuItem]] = {}
    for item in items:
        parent_id = item.parent_id
        tree.setdefault(parent_id, []).append(item)
    # Items are already ordered via model Meta, but ensure stability.
    for children in tree.values():
        children.sort(key=lambda obj: (obj.order, obj.id))
    return tree


@register.inclusion_tag('menu/menu.html', takes_context=True)
def draw_menu(context: template.Context, menu_name: str) -> dict:
    """
    Template tag for rendering a hierarchical menu by its name.

    This tag performs a single database query to fetch all menu items belonging
    to the specified menu. It then builds a nested tree structure in Python
    memory and marks the current navigation path as open. The first level of
    descendants under the active element is also expanded.

    Usage example in a Django template:

        {% load menu_tags %}
        {% draw_menu 'main_menu' %}

    :param context: The template context. Must include the HTTP request.
    :param menu_name: Name of the menu to render.
    :return: Context dictionary with a `menu_tree` key consumed by
             `menu/menu.html` template.
    """
    request = context.get('request')
    if request is None:
        raise RuntimeError("draw_menu requires 'request' to be in the context")

    # Resolve the menu by its name. If it doesn't exist, return empty list.
    try:
        menu = Menu.objects.get(name=menu_name)
    except Menu.DoesNotExist:
        return {'menu_tree': []}

    # Fetch all items related to this menu. Use select_related to reduce queries.
    items: List[MenuItem] = list(
        MenuItem.objects.filter(menu=menu)
        .select_related('parent')
        .order_by('order', 'id')
    )

    # Build a mapping from parent_id to children list.
    tree = build_tree(items)

    current_path = request.path
    node_map: Dict[int, dict] = {}
    active_item: Optional[MenuItem] = None

    def build_subtree(item: MenuItem) -> dict:
        nonlocal active_item
        # Determine if the current item matches the request path
        url = item.get_absolute_url()
        is_active = (url == current_path)
        node = {
            'item': item,
            'children': [],
            'active': is_active,
            'open': False,
        }
        if is_active:
            active_item = item
        node_map[item.id] = node
        # Recursively build subtrees for children
        for child in tree.get(item.id, []):
            node['children'].append(build_subtree(child))
        return node

    # Build the full tree starting from root items (parent_id is None)
    menu_tree: List[dict] = [build_subtree(item) for item in tree.get(None, [])]

    # Mark ancestors of the active item as open, and ensure the active item itself is open
    if active_item:
        for ancestor in active_item.ancestors:
            node = node_map.get(ancestor.id)
            if node:
                node['open'] = True
        # The active node should also be open to reveal its immediate children
        active_node = node_map.get(active_item.id)
        if active_node:
            active_node['open'] = True

    return {'menu_tree': menu_tree}
