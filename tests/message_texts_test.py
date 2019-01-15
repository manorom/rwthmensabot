from mensabot.message_texts import _get_menu_item

ITEM_TEMPLATE = '<i>{name}</i>{price}\n' \
                '{description}'


def test_formats_single_bar_delimited_menu_item():
    menu = {'Vegetarisch': {'name': 'Kürbis-Chia-Taler | Texicanasauce', 'price': 2.1}}
    name = 'Vegetarisch'

    result = _get_menu_item(menu, name)
    assert result == ITEM_TEMPLATE.format(
        name='Vegetarisch',
        price=' - 2.10€',
        description='<b>Kürbis-Chia-Taler</b> mit Texicanasauce'
    )


def test_formats_menu_item_with_mit():
    menu = {
        'Tellergericht': {
            'name': 'Pfannkuchen mit Quark-Rosinen-Füllung und Waldfruchtsauce',
            'price': 1.5}}
    name = 'Tellergericht'

    result = _get_menu_item(menu, name)
    assert result == ITEM_TEMPLATE.format(
        name='Tellergericht',
        price=' - 1.50€',
        description='<b>Pfannkuchen</b> mit Quark-Rosinen-Füllung und Waldfruchtsauce'
    )


def test_multiple_items_with_bars():
    menu = {
        'Pasta': {
            'name': 'Gnocchi al forno | Brokkoli, Kochschinken, Käse | Béchamel\n'
                    'Maccheroni Classica | Blattspinat, ital. Hartkäse | Béchamel\n'
                    'Farfalloni Rosati | Hähnchen, getrocknete Tomaten | Pesto | Tomatensauce',
            'price': 3.5}, }
    name = 'Pasta'

    result = _get_menu_item(menu, name)
    assert result == ITEM_TEMPLATE.format(
        name='Pasta',
        price=' - 3.50€',
        description='<b>Gnocchi al forno</b> mit Brokkoli, Kochschinken, Käse & Béchamel\n'
                    '<b>Maccheroni Classica</b> mit Blattspinat, ital. Hartkäse & Béchamel\n'
                    '<b>Farfalloni Rosati</b> mit Hähnchen, getrocknete Tomaten, Pesto & Tomatensauce'
    )


def test_multiple_items_with_mit_and_bars():
    menu = {
        'Fingerfood': {
            'name': 'Hähnchennuggets 9 Stück mit 2 Dips A,A1 | Pommes | Getränk 0,25 L',
            'price': 3.5}, }
    name = 'Fingerfood'

    result = _get_menu_item(menu, name)
    assert result == ITEM_TEMPLATE.format(
        name='Fingerfood',
        price=' - 3.50€',
        description='<b>Hähnchennuggets 9 Stück</b> mit 2 Dips A,A1, Pommes & Getränk 0,25 L'
    )
