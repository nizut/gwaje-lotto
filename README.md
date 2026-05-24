## Docker Compose

```yaml
services:
	db:
		image: postgres:18.4
		environment:
			POSTGRES_DB: lotto_db
			POSTGRES_USER: lotto
			POSTGRES_PASSWORD: lotto
		volumes:
			- db_data:/var/lib/postgresql

	web:
		build: .
		ports:
			- "8000:8000"
		environment:
			- DATABASE_URL=postgres://lotto:lotto@db:5432/lotto_db
			- DJANGO_SETTINGS_MODULE=config.settings
		depends_on:
			- db
		volumes:
			- .:/app

volumes:
	db_data:
```
