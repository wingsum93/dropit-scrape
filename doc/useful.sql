// Find the product with the longest unit name
SELECT *
FROM product
ORDER BY LENGTH(unit) DESC
LIMIT 1;

