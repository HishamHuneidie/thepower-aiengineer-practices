CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    status VARCHAR(10) NOT NULL CHECK (status IN ('created', 'updated', 'deleted')),
    price DOUBLE PRECISION NOT NULL,
    currency VARCHAR(3) NOT NULL CHECK (currency IN ('EUR', 'USD'))
);

INSERT INTO orders (id, title, status, price, currency) VALUES
    (1234, 'Pedido de portátil', 'created', 1299.99, 'EUR'),
    (4567, 'Pedido de monitor', 'updated', 249.50, 'USD'),
    (7890, 'Pedido de teclado', 'deleted', 79.90, 'EUR')
ON CONFLICT (id) DO NOTHING;
