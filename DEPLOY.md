# BondsApp — Deploy en Railway

## Pasos

1. **Crear proyecto en Railway**
   - railway.app → New Project → Deploy from GitHub repo
   - Conectar el repo, seleccionar la carpeta `bondsapp/` como root (o apuntar al Dockerfile)

2. **Crear Railway Volume**
   - En el dashboard del servicio → Storage → Add Volume
   - Mount path: `/data`

3. **Variables de entorno** (Settings → Variables)
   ```
   SECRET_KEY=<generar: python -c "import secrets; print(secrets.token_hex(32))">
   DATA_DIR=/data
   COOKIE_SECURE=true
   ```

4. **Deploy**
   - Push a main → Railway buildea y deploya automáticamente
   - Health check en `/health` — debe devolver `{"status":"ok"}`

5. **Primera vez**
   - Abrir la URL pública → `/login`
   - Login con `admin` / `admin123`
   - **Cambiar la contraseña del admin** en Admin → Usuarios
   - Ir a Admin → Config PPI → ingresar credenciales de portfoliopersonal.com
   - Ir a Admin → Holdings → cargar las posiciones
   - Verificar Mercado y Cartera funcionan

## Variables opcionales

| Variable | Default | Descripción |
|----------|---------|-------------|
| `SECRET_KEY` | `dev-secret-...` | Clave JWT — **obligatoria en prod** |
| `DATA_DIR` | `data` | Directorio para SQLite — `/data` en Railway |
| `COOKIE_SECURE` | `false` | `true` en prod (HTTPS) |
