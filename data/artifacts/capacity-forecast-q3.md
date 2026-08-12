# Q3 capacity forecast (synthetic)

Owner: Release Engineering.

Baseline authorization volume is 1.9 million transactions per day with a weekday peak of 62
transactions per second at 19:00 ca-central. The Q3 forecast projects an 18 percent increase
driven by two merchant onboardings in August.

Headroom at current provisioning is 3.1 times peak on the application tier and 2.2 times peak on
the primary database. The database tier is therefore the binding constraint, and the connection
pool ceiling is reached before CPU saturation.

Planned work is a read-replica split for reporting queries in early August. No capacity work is
scheduled against the routing scorer, whose cost is negligible relative to authorization I/O.
