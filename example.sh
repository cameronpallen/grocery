echo "> cart empty"
cart empty
echo "> cart view"
cart view
echo "> products clear"
products clear
echo "> products view"
products view

echo '> cart add_item "bulk kombucha" lb 3.35 4.192'
cart add_item "bulk kombucha" lb 3.35 4.192
echo '> cart add_item "pepperoni pizza" pies 12 1'
cart add_item "pepperoni pizza" pies 12 1
echo "> cart add_item bread loafs 3.25 2"
cart add_item bread loafs 3.25 2

echo "\n> cart view"
cart view
echo "\n> cart view --sortby Price"
cart view --sortby Price

echo "\n> cart view --sortby Subtotal"
cart view --sortby Subtotal

echo "\n> cart update_quantity 2 4"
cart update_quantity 2 4

echo "> cart view --sortby Subtotal"
cart view --sortby Subtotal

echo "\n> cart remove 1"
cart remove 1
echo "\n> cart view"
cart view


echo '\n> products add_item bacon "packs" 7.5'
products add_item bacon "packs" 7.5
echo "> products to_cart 3 2"
products to_cart 3 2
echo "> products to_cart 2 1"
products to_cart 2 1
echo "\n> products view"
products view
echo "\n> cart view"
cart view

echo "\n> products remove 2"
products remove 2
echo "\n> products view"
products view
echo "\n> cart view"
cart view
