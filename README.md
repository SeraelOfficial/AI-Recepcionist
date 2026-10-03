# AI-Recepcionist

Agenda para agentes de IA de Serael, basada en Easy!Appointments 1.6.0 (GPL-3.0).
Código original en el submódulo upstream/easyappointments, fijado al tag 1.6.0. El despliegue usa la imagen del mantenedor.

## Despliegue en el servidor WHM

Requiere Docker Engine y Docker Compose v2 existentes, Git, Python 3 y acceso a Docker. No instala ni modifica WHM.

```bash
git clone --recurse-submodules https://github.com/SeraelOfficial/AI-Recepcionist.git
cd AI-Recepcionist
python3 scripts/init_env.py https://citas.TU-DOMINIO.com
# Revisar .env y configurar SMTP antes de usar notificaciones.
docker compose config --quiet
docker compose pull
docker compose up -d
 docker compose ps
```

La app escucha solo en 127.0.0.1:8095. Configurar el proxy HTTPS del subdominio hacia http://127.0.0.1:8095 mediante la configuración de includes admitida por el Apache/NGINX de tu WHM. No sustituir httpd.conf ni ocupar 80/443. Validar el proxy antes de exponer el sitio. No hay cambios automáticos de DNS ni Apache.

Abrir el subdominio y completar el instalador: administrador, empresa, servicios, profesionales, horarios y zona America/Costa_Rica. Configurar una API key en ajustes. Guardar el token en una credencial n8n Header Auth (Authorization: Bearer TOKEN), nunca en Git ni en el prompt.

## Validación de integración

```bash
python3 scripts/check_api.py https://citas.TU-DOMINIO.com
```

El script solicita el token sin mostrarlo y verifica servicios/profesionales; no crea clientes ni reservas. La prueba completa requiere una cita de demo: disponibilidad → cliente → cita → consultar ID → reprogramar → cancelar, verificando el calendario en cada paso. Esta prueba todavía debe ejecutarse tras la instalación.

API base: https://citas.TU-DOMINIO.com/index.php/api/v1

| Acción | Endpoint |
|---|---|
| Servicios | GET /services |
| Profesionales | GET /providers |
| Disponibilidad | GET /availabilities?providerId=ID&serviceId=ID&date=YYYY-MM-DD |
| Cliente | POST /customers |
| Cita | POST /appointments |
| Reprogramar | PUT /appointments/ID |
| Cancelar | DELETE /appointments/ID |

Ejemplo de cuerpo para crear cita (IDs reales obtenidos de API):

```json
{"start":"2026-10-08 09:00:00","end":"2026-10-08 09:30:00","serviceId":1,"providerId":2,"customerId":3,"notes":"Demo"}
```

El agente debe confirmar el horario con el cliente, consultar disponibilidad y solo confirmar la reserva cuando la API devuelva éxito e ID. Serializar reservas del mismo profesional y verificar conflictos: consultar disponibilidad antes del POST por sí solo no garantiza exclusión entre peticiones concurrentes. Manejar timeouts consultando si la reserva ya existe antes de reintentar.

## Operación

Datos MySQL en volumen persistente; no ejecutar docker compose down -v. Programar backups de la base de datos antes de uso productivo. No actualizar imágenes ni versión de MySQL sin respaldo. SMTP queda sin configurar inicialmente.

CI valida Compose y sintaxis de scripts; no representa instalación ni prueba real de reservas.

Referencias: https://github.com/alextselegidis/easyappointments-docker y https://developers.easyappointments.org/api/
