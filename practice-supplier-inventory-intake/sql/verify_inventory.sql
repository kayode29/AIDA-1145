USE aida1145;

SELECT COUNT(*) AS loaded_records
FROM stg_supplier_inventory;

SELECT supplier_id, COUNT(*) AS product_records, SUM(quantity) AS total_quantity
FROM stg_supplier_inventory
GROUP BY supplier_id
ORDER BY total_quantity DESC;

SELECT *
FROM stg_supplier_inventory
WHERE quantity <= 0 OR unit_cost <= 0;
